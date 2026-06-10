"""
schema_kitab.py — Inisialisasi SQLite schema untuk kitab corpus
═══════════════════════════════════════════════════════════════
Jalankan sekali untuk membuat database baru, atau --reset untuk rebuild.

Usage (dari direktori tools/):
    python3 schema_kitab.py                    # buat jika belum ada
    python3 schema_kitab.py --reset            # drop semua tabel, rebuild
    python3 schema_kitab.py --db /path/to.db   # path custom

Usage (dari IslamiAIProject/):
    python3 tools/schema_kitab.py

Tabel yang dibuat:
    kitab_books     — registry kitab yang sudah diingest
    kitab_corpus    — data utama: passage teks + metadata
    kitab_fts       — FTS5 virtual table (external content dari kitab_corpus)
"""

import argparse
import logging
import os
import sqlite3
import sys

logger = logging.getLogger("islamiai.schema_kitab")

# ─── Default path ─────────────────────────────────────────────────────────────
# File ini ada di tools/ → database ada di direktori induk (IslamiAIProject/)
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB  = os.path.join(_PROJECT_DIR, "islamiai.db")


# ─── DDL Statements ───────────────────────────────────────────────────────────

DDL_KITAB_BOOKS = """
CREATE TABLE IF NOT EXISTS kitab_books (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    slug             TEXT    NOT NULL UNIQUE,   -- e.g. "al_umm"
    name_id          TEXT    NOT NULL,          -- nama Bahasa Indonesia/Arab
    author           TEXT    NOT NULL,
    category         TEXT    NOT NULL,
        -- "tafsir_ahkam" | "fiqh_syafii" | "qawaid"
    authority_level  INTEGER NOT NULL DEFAULT 3,
        -- 1 = Qawl Imam          : Al-Umm, Al-Risalah (Imam Al-Syafi'i langsung)
        -- 2 = Qawl Ashhab        : Mukhtasar al-Muzani (murid langsung)
        -- 3 = Mu'tamad           : Nawawi, Mawardi, Juwayni (madzhab mapan)
        -- 4 = Syarh Mu'tamad     : Tuhfat, Nihayat, Mughni, Fath al-Mu'in
        -- 5 = Tafsir & Qawa'id   : tafsir ahkam, qawa'id fiqhiyyah
    shamela_id       INTEGER,                   -- ID di shamela.ws (metadata)
    total_passages   INTEGER DEFAULT 0,
    ingested_at      TEXT                        -- ISO datetime
);
"""

DDL_KITAB_CORPUS = """
CREATE TABLE IF NOT EXISTS kitab_corpus (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    book_slug        TEXT    NOT NULL REFERENCES kitab_books(slug),
    authority_level  INTEGER NOT NULL DEFAULT 3,
    category         TEXT    NOT NULL,
    chapter_title    TEXT    DEFAULT '',        -- judul bab / nama file halaman
    page_ref         TEXT    DEFAULT '',        -- referensi halaman shamela
    arabic_text      TEXT    NOT NULL,          -- teks Arab asli (dengan harakat)
    text_length      INTEGER NOT NULL DEFAULT 0
);
"""

# FTS5 external content: data dibaca dari kitab_corpus, tidak diduplikasi
DDL_KITAB_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS kitab_fts
USING fts5(
    arabic_text,
    chapter_title,
    book_slug,
    content       = kitab_corpus,
    content_rowid = id,
    tokenize      = "unicode61 remove_diacritics 1"
);
"""

# Triggers untuk sync FTS setelah bulk ingest (incremental INSERT)
DDL_TRIGGER_INSERT = """
CREATE TRIGGER IF NOT EXISTS kitab_corpus_ai
AFTER INSERT ON kitab_corpus BEGIN
    INSERT INTO kitab_fts(rowid, arabic_text, chapter_title, book_slug)
    VALUES (new.id, new.arabic_text, new.chapter_title, new.book_slug);
END;
"""

DDL_TRIGGER_DELETE = """
CREATE TRIGGER IF NOT EXISTS kitab_corpus_ad
AFTER DELETE ON kitab_corpus BEGIN
    INSERT INTO kitab_fts(kitab_fts, rowid, arabic_text, chapter_title, book_slug)
    VALUES ('delete', old.id, old.arabic_text, old.chapter_title, old.book_slug);
END;
"""

DDL_TRIGGER_UPDATE = """
CREATE TRIGGER IF NOT EXISTS kitab_corpus_au
AFTER UPDATE ON kitab_corpus BEGIN
    INSERT INTO kitab_fts(kitab_fts, rowid, arabic_text, chapter_title, book_slug)
    VALUES ('delete', old.id, old.arabic_text, old.chapter_title, old.book_slug);
    INSERT INTO kitab_fts(rowid, arabic_text, chapter_title, book_slug)
    VALUES (new.id, new.arabic_text, new.chapter_title, new.book_slug);
END;
"""

DDL_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_corpus_book      ON kitab_corpus(book_slug);",
    "CREATE INDEX IF NOT EXISTS idx_corpus_category  ON kitab_corpus(category);",
    "CREATE INDEX IF NOT EXISTS idx_corpus_authority ON kitab_corpus(authority_level);",
]

TABLES_TO_DROP = ["kitab_fts", "kitab_corpus", "kitab_books"]
TRIGGERS_TO_DROP = ["kitab_corpus_ai", "kitab_corpus_ad", "kitab_corpus_au"]


# ─── Core Functions ───────────────────────────────────────────────────────────

def create_schema(db_path: str, reset: bool = False) -> sqlite3.Connection:
    """
    Buat atau reset schema.

    Args:
        db_path: Path ke file SQLite
        reset:   Jika True, drop semua tabel dulu

    Returns:
        sqlite3.Connection yang sudah dikonfigurasi
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")

    if reset:
        logger.info("Reset mode: menghapus schema lama...")
        cur = conn.cursor()
        for trg in TRIGGERS_TO_DROP:
            cur.execute(f"DROP TRIGGER IF EXISTS {trg}")
        for tbl in TABLES_TO_DROP:
            cur.execute(f"DROP TABLE IF EXISTS {tbl}")
        conn.commit()
        logger.info("Schema lama dihapus.")

    conn.execute(DDL_KITAB_BOOKS)
    conn.execute(DDL_KITAB_CORPUS)
    conn.execute(DDL_KITAB_FTS)
    conn.execute(DDL_TRIGGER_INSERT)
    conn.execute(DDL_TRIGGER_DELETE)
    conn.execute(DDL_TRIGGER_UPDATE)
    for ddl in DDL_INDEXES:
        conn.execute(ddl)

    conn.commit()
    logger.info("Schema berhasil dibuat di: %s", db_path)
    return conn


def verify_schema(conn: sqlite3.Connection) -> bool:
    """Verifikasi bahwa semua tabel dan FTS5 berfungsi."""
    try:
        conn.execute("SELECT COUNT(*) FROM kitab_books").fetchone()
        conn.execute("SELECT COUNT(*) FROM kitab_corpus").fetchone()
        conn.execute("SELECT COUNT(*) FROM kitab_fts").fetchone()
        return True
    except sqlite3.OperationalError as e:
        logger.error("Schema verification failed: %s", e)
        return False


def get_schema_stats(conn: sqlite3.Connection) -> dict:
    """Return statistik schema saat ini."""
    stats: dict = {}
    try:
        stats["books"]    = conn.execute("SELECT COUNT(*) FROM kitab_books").fetchone()[0]
        stats["passages"] = conn.execute("SELECT COUNT(*) FROM kitab_corpus").fetchone()[0]
        total = conn.execute("SELECT SUM(text_length) FROM kitab_corpus").fetchone()[0]
        stats["total_chars"] = total or 0
        stats["by_category"] = dict(conn.execute(
            "SELECT category, COUNT(*) FROM kitab_corpus GROUP BY category"
        ).fetchall())
        stats["by_authority"] = dict(conn.execute(
            "SELECT authority_level, COUNT(*) FROM kitab_corpus GROUP BY authority_level"
        ).fetchall())
    except sqlite3.OperationalError:
        pass
    return stats


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Inisialisasi SQLite schema untuk IslamiAI kitab corpus"
    )
    parser.add_argument("--db", default=DEFAULT_DB,
                        help=f"Path ke database (default: {DEFAULT_DB})")
    parser.add_argument("--reset", action="store_true",
                        help="Drop semua tabel dan rebuild dari awal")
    args = parser.parse_args()

    if args.reset:
        confirm = input(
            f"⚠️  Reset akan menghapus semua data corpus di:\n"
            f"   {args.db}\n"
            "Ketik 'yes' untuk konfirmasi: "
        )
        if confirm.strip().lower() != "yes":
            print("Dibatalkan.")
            sys.exit(0)

    conn = create_schema(args.db, reset=args.reset)

    if verify_schema(conn):
        stats = get_schema_stats(conn)
        print(f"\n✅ Schema siap di: {args.db}")
        print(f"   Kitab    : {stats.get('books', 0)}")
        print(f"   Passages : {stats.get('passages', 0)}")
        print(f"   Chars    : {stats.get('total_chars', 0):,}")
    else:
        print("❌ Schema verification gagal.")
        sys.exit(1)

    conn.close()


if __name__ == "__main__":
    main()
