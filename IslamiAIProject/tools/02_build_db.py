"""
02_build_db.py — Shamela Corpus Builder
══════════════════════════════════════════════════════════════════
Mengubah file EPUB hasil download menjadi SQLite .db terstruktur.
Dijalankan setelah 01_download.py selesai.

Output:
  corpus/db/{nama_kitab}.db   ← satu .db per kitab
  corpus/shamela_corpus.db    ← database master gabungan (FTS5)

Schema:
  kitab       → metadata kitab (nama, mualif, blok, level)
  passage     → potongan teks per bab
  passage_fts → FTS5 index untuk pencarian Arab
══════════════════════════════════════════════════════════════════
"""

import json
import logging
import re
import sqlite3
import unicodedata
from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CORPUS_DIR  = PROJECT_DIR / "corpus"
EPUB_DIR    = CORPUS_DIR  / "epub"
DB_DIR      = CORPUS_DIR  / "db"
MASTER_DB   = CORPUS_DIR  / "shamela_corpus.db"
STATE_FILE  = CORPUS_DIR  / "download_state.json"

DB_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(CORPUS_DIR / "build_db.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("shamela.builder")


# ── Arabic Text Processing ─────────────────────────────────────────────────────

def normalize_arabic(text: str) -> str:
    """
    Normalisasi teks Arab untuk pencarian konsisten.
    - Hapus tashkil (harakat)
    - Normalisasi varian huruf (alef, ta marbuta, dll)
    - Strip noise characters dari Shamela
    """
    # Hapus harakat (U+064B – U+065F, U+0670)
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)

    # Normalisasi varian alef → ا
    text = re.sub(r"[أإآ]", "ا", text)

    # Normalisasi ta marbuta → ه (opsional, kadang membantu)
    # text = text.replace("ة", "ه")

    # Normalisasi ya → ي
    text = text.replace("ى", "ي")

    # Hapus karakter non-Arab dan non-spasi yang tidak diperlukan
    # (kecuali angka Arab dan tanda baca dasar)
    text = re.sub(r"[^\u0600-\u06FF\u0750-\u077F\s\d،.؟!:]", " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_fiqh_topic_hints(text: str) -> list[str]:
    """
    Ekstrak hint topik fiqh dari teks (heuristik sederhana).
    Mencari kata kunci bab/kitab yang menunjukkan topik.
    """
    TOPIC_PATTERNS = {
        "thaharah":  r"(طهار|وضوء|غسل|تيمم|نجاس)",
        "shalat":    r"(صلا|ركوع|سجود|قيام|إمام|جماع)",
        "zakat":     r"(زكا|نصاب|أموال|فقير|مسكين)",
        "puasa":     r"(صوم|صيام|إفطار|سحور|رمضان)",
        "haji":      r"(حج|عمر|إحرام|طواف|سعي|منى)",
        "nikah":     r"(نكاح|زواج|طلاق|مهر|ولي|شهود)",
        "waris":     r"(وراث|إرث|تركة|فريضة|عصبة)",
        "muamalah":  r"(بيع|شرا|إجار|رها|قرض|ربا)",
        "jenazah":   r"(جنازة|ميت|دفن|تكفين|غسل الميت)",
        "hudud":     r"(حدود|قصاص|دية|حد|زنا|سرق)",
    }
    found = []
    for topic, pattern in TOPIC_PATTERNS.items():
        if re.search(pattern, text):
            found.append(topic)
    return found


def parse_epub_to_passages(epub_path: Path) -> list[dict]:
    """
    Parse file EPUB menjadi list passage terstruktur.
    Setiap passage adalah satu unit teks bermakna (bab atau sub-bab).
    """
    passages = []
    try:
        book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
    except Exception as e:
        log.error("Gagal parse EPUB %s: %s", epub_path.name, e)
        return []

    page_order = 0
    current_chapter = ""

    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        try:
            soup = BeautifulSoup(item.get_body_content(), "lxml")
        except Exception:
            soup = BeautifulSoup(item.get_body_content(), "html.parser")

        # Deteksi judul bab/pasal
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            current_chapter = heading.get_text(strip=True)[:200]
            break  # ambil heading pertama saja

        # Ambil semua paragraf bermakna
        for elem in soup.find_all(["p", "div"]):
            raw_text = elem.get_text(separator=" ", strip=True)

            # Filter: terlalu pendek atau bukan Arab
            if len(raw_text) < 30:
                continue
            # Harus mengandung minimal beberapa karakter Arab
            arab_chars = len(re.findall(r"[\u0600-\u06FF]", raw_text))
            if arab_chars < 15:
                continue

            normalized = normalize_arabic(raw_text)
            if len(normalized) < 20:
                continue

            topics = extract_fiqh_topic_hints(normalized)
            page_order += 1

            passages.append({
                "chapter":        current_chapter,
                "page_order":     page_order,
                "text_raw":       raw_text[:5000],   # cap 5000 char
                "text_normalized": normalized[:5000],
                "topic_hints":    ",".join(topics),
            })

    return passages


# ── Database Functions ─────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS kitab (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key             TEXT NOT NULL UNIQUE,
    label           TEXT NOT NULL,
    blok            TEXT,    -- 'tafsir_ahkam'|'fiqh_syafii'|'qawaid'
    level           TEXT,    -- 'mutamad'|'sharh_mutamad'|'pesantren'|...
    madhab          TEXT DEFAULT 'shafii',
    shamela_id      INTEGER,
    epub_file       TEXT,
    total_passages  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS passage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kitab_id        INTEGER NOT NULL REFERENCES kitab(id),
    chapter         TEXT,
    page_order      INTEGER,
    text_arabic     TEXT NOT NULL,
    text_normalized TEXT NOT NULL,
    topic_hints     TEXT    -- comma-separated topic hints
);

CREATE INDEX IF NOT EXISTS idx_passage_kitab ON passage(kitab_id);
CREATE INDEX IF NOT EXISTS idx_passage_topic ON passage(topic_hints);

CREATE VIRTUAL TABLE IF NOT EXISTS passage_fts
USING fts5(
    text_normalized,
    topic_hints,
    chapter,
    content=passage,
    content_rowid=id,
    tokenize="unicode61 remove_diacritics 2"
);

CREATE TRIGGER IF NOT EXISTS passage_fts_insert
AFTER INSERT ON passage BEGIN
    INSERT INTO passage_fts(rowid, text_normalized, topic_hints, chapter)
    VALUES (new.id, new.text_normalized, new.topic_hints, new.chapter);
END;
"""


def init_master_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def upsert_kitab(conn: sqlite3.Connection, kitab_info: dict) -> int:
    """Insert atau update record kitab, return kitab_id."""
    cur = conn.execute(
        "SELECT id FROM kitab WHERE key = ?", (kitab_info["key"],)
    )
    row = cur.fetchone()

    if row:
        conn.execute(
            """UPDATE kitab SET label=?, blok=?, level=?, madhab=?,
               shamela_id=?, epub_file=? WHERE key=?""",
            (kitab_info["label"], kitab_info["blok"], kitab_info["level"],
             kitab_info["madhab"], kitab_info["shamela_id"],
             kitab_info["epub_file"], kitab_info["key"])
        )
        return row[0]
    else:
        cur = conn.execute(
            """INSERT INTO kitab (key, label, blok, level, madhab, shamela_id, epub_file)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (kitab_info["key"], kitab_info["label"], kitab_info["blok"],
             kitab_info["level"], kitab_info["madhab"], kitab_info["shamela_id"],
             kitab_info["epub_file"])
        )
        return cur.lastrowid


def insert_passages(conn: sqlite3.Connection, kitab_id: int,
                    passages: list[dict]) -> int:
    """Batch insert passages untuk satu kitab. Return jumlah yang diinsert."""
    # Hapus passage lama jika ada (re-build)
    conn.execute("DELETE FROM passage WHERE kitab_id = ?", (kitab_id,))

    inserted = 0
    for p in passages:
        conn.execute(
            """INSERT INTO passage
               (kitab_id, chapter, page_order, text_arabic, text_normalized, topic_hints)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (kitab_id, p["chapter"], p["page_order"],
             p["text_raw"], p["text_normalized"], p["topic_hints"])
        )
        inserted += 1

    conn.execute(
        "UPDATE kitab SET total_passages = ? WHERE id = ?",
        (inserted, kitab_id)
    )
    return inserted


def build_individual_db(key: str, epub_path: Path, info: dict,
                        passages: list[dict]) -> None:
    """Buat .db individual per kitab (untuk referensi terpisah)."""
    db_path = DB_DIR / f"{key}.db"
    conn = sqlite3.connect(str(db_path))

    # Schema sederhana untuk .db individual
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT, value TEXT
        );
        CREATE TABLE IF NOT EXISTS passage (
            id              INTEGER PRIMARY KEY,
            chapter         TEXT,
            page_order      INTEGER,
            text_arabic     TEXT,
            text_normalized TEXT,
            topic_hints     TEXT
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS passage_fts
        USING fts5(text_normalized, topic_hints, content=passage, content_rowid=id,
                   tokenize="unicode61 remove_diacritics 2");
        CREATE TRIGGER IF NOT EXISTS fts_insert AFTER INSERT ON passage BEGIN
            INSERT INTO passage_fts(rowid, text_normalized, topic_hints)
            VALUES (new.id, new.text_normalized, new.topic_hints);
        END;
    """)

    # Meta
    meta_rows = [
        ("key",       key),
        ("label",     info["label"]),
        ("blok",      info["blok"]),
        ("level",     info["level"]),
        ("madhab",    info["madhab"]),
        ("shamela_id", str(info.get("id", ""))),
    ]
    conn.executemany("INSERT OR REPLACE INTO meta VALUES (?, ?)", meta_rows)

    # Passages
    for p in passages:
        conn.execute(
            """INSERT INTO passage
               (chapter, page_order, text_arabic, text_normalized, topic_hints)
               VALUES (?, ?, ?, ?, ?)""",
            (p["chapter"], p["page_order"], p["text_raw"],
             p["text_normalized"], p["topic_hints"])
        )

    conn.commit()
    conn.close()
    log.info("  → Individual DB: %s (%d passages)", db_path.name, len(passages))


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    log.info("IslamiAI — Shamela Corpus Builder")
    log.info("Input : %s", EPUB_DIR)
    log.info("Output: %s", MASTER_DB)

    # Baca state download untuk metadata kitab
    state = {}
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)

    downloaded = state.get("downloaded", {})

    # Buat/buka master DB
    master_conn = sqlite3.connect(str(MASTER_DB))
    master_conn.execute("PRAGMA journal_mode=WAL")
    master_conn.execute("PRAGMA synchronous=NORMAL")
    init_master_db(master_conn)

    total_passages = 0
    processed = 0

    for epub_path in sorted(EPUB_DIR.glob("*.epub")):
        key = epub_path.stem
        info = downloaded.get(key, {})

        if not info:
            # Fallback: coba tebak metadata dari nama file
            info = {
                "id": None, "blok": "unknown", "level": "unknown",
                "madhab": "shafii", "label": key,
            }

        log.info("Memproses: %s", info.get("label", key))

        # Parse EPUB → passages
        passages = parse_epub_to_passages(epub_path)
        if not passages:
            log.warning("  → Tidak ada passage ditemukan, skip.")
            continue

        log.info("  → Ditemukan %d passages", len(passages))

        # Upsert ke master DB
        kitab_data = {
            "key":       key,
            "label":     info.get("label", key),
            "blok":      info.get("blok", "unknown"),
            "level":     info.get("level", "unknown"),
            "madhab":    info.get("madhab", "shafii"),
            "shamela_id": info.get("id"),
            "epub_file": str(epub_path),
        }
        kitab_id = upsert_kitab(master_conn, kitab_data)
        n = insert_passages(master_conn, kitab_id, passages)
        master_conn.commit()

        # Buat individual .db
        build_individual_db(key, epub_path, info, passages)

        total_passages += n
        processed += 1

    master_conn.close()

    log.info("═" * 60)
    log.info("SELESAI")
    log.info("  Kitab diproses : %d", processed)
    log.info("  Total passages : %d", total_passages)
    log.info("  Master DB      : %s", MASTER_DB)
    log.info("  Individual DB  : %s/*.db", DB_DIR)
    log.info("  Ukuran DB      : %.1f MB",
             MASTER_DB.stat().st_size / 1_048_576 if MASTER_DB.exists() else 0)
    log.info("\nJalankan berikutnya: python3 tools/03_integrate.py")


if __name__ == "__main__":
    main()
