"""
ingest_corpus.py — Parse EPUB kitab → SQLite FTS5
══════════════════════════════════════════════════
Jalankan sekali untuk ingest semua EPUB, atau per-kitab untuk update.

Usage (dari tools/ atau IslamiAIProject/):
    python3 ingest_corpus.py                          # ingest semua EPUB
    python3 ingest_corpus.py --book al_umm            # satu kitab saja
    python3 ingest_corpus.py --limit 100              # max 100 passage/kitab
    python3 ingest_corpus.py --dry-run                # test tanpa tulis ke DB
    python3 ingest_corpus.py --reset-book al_umm      # hapus & reingest
    python3 ingest_corpus.py --list-books             # tampilkan registry
    python3 ingest_corpus.py --corpus-dir /path/epub  # custom corpus dir
    python3 ingest_corpus.py --db /path/to.db         # custom db path

Arsitektur:
    EPUB → ebooklib → BeautifulSoup → teks Arab → passage (per halaman)
    → normalisasi → filter (min panjang, minimal Arab)
    → INSERT kitab_corpus (trigger FTS DINONAKTIFKAN selama bulk insert)
    → INSERT INTO kitab_fts(kitab_fts) VALUES('rebuild')  ← akhir proses

Catatan performa:
    Untuk 28 kitab estimasi ~200k–500k passages.
    FTS rebuild sekali di akhir jauh lebih cepat daripada trigger per-row.
    Estimasi rebuild: 10–60 detik tergantung ukuran corpus.
"""

import argparse
import logging
import os
import re
import sqlite3
import sys
import unicodedata
from datetime import datetime, timezone
from typing import Generator

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

# Import dari schema_kitab (berada di direktori yang sama: tools/)
from schema_kitab import (
    create_schema, DEFAULT_DB, verify_schema,
    DDL_TRIGGER_INSERT, DDL_TRIGGER_DELETE, DDL_TRIGGER_UPDATE,
)

logger = logging.getLogger("islamiai.ingest")

# ─── Paths ────────────────────────────────────────────────────────────────────
# tools/ → IslamiAIProject/ → corpus/epub/
_PROJECT_DIR          = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CORPUS_DIR  = os.path.join(_PROJECT_DIR, "corpus", "epub")


# ─── Book Registry ────────────────────────────────────────────────────────────
# Shamela IDs diverifikasi dari:
#   - userMemories (download_29_kitab.py yang berhasil dijalankan)
#   - Web search langsung ke shamela.ws
# ID yang masih "best guess" (belum dikonfirmasi download) ditandai # UNVERIFIED
#
# authority_level hierarchy:
#   1 = Qawl Imam         : Imam Al-Syafi'i langsung
#   2 = Qawl Ashhab       : Murid langsung (hanya al-Muzani)
#   3 = Mu'tamad          : Nawawi, Mawardi, Juwayni (madzhab mapan)
#   4 = Syarh Mu'tamad    : Tuhfat, Nihayat, Mughni, Fath al-Mu'in
#   5 = Tafsir & Qawa'id  : tafsir ahkam, qawa'id fiqhiyyah

BOOK_REGISTRY: dict[str, dict] = {

    # ── Tafsir Ahkam ─────────────────────────────────────────────────────────

    "al_kiya_harrasi": {
        "name_id":         "Ahkam al-Quran — Al-Kiya al-Harrasi",
        "author":          "Al-Kiya al-Harrasi",
        "category":        "tafsir_ahkam",
        "authority_level": 5,
        "shamela_id":      23582,        # ✓ dikonfirmasi dari download
        "filename":        "al_kiya_harrasi.epub",
    },
    "al_baihaqi_ahkam": {
        # Judul asli: أحكام القرآن للشافعي — جمع البيهقي
        # Ini bukan karya asli al-Baihaqi, melainkan kumpulan hukum
        # al-Qur'an dari tulisan Imam al-Syafi'i yang dikumpulkan al-Baihaqi.
        "name_id":         "Ahkam al-Quran al-Syafi'i — Riwayat al-Baihaqi",
        "author":          "Imam Al-Syafi'i (dikumpulkan Al-Baihaqi)",
        "category":        "tafsir_ahkam",
        "authority_level": 5,
        "shamela_id":      92,           # ✓ edisi al-Shawami (1 jilid)
        # Alternatif: 3328 (edisi 'Abd al-Khaliq, 2 jilid)
        "filename":        "al_baihaqi_ahkam.epub",
    },
    "al_qurtubi": {
        "name_id":         "Al-Jami' li Ahkam al-Quran — Al-Qurtubi",
        "author":          "Al-Qurtubi",
        "category":        "tafsir_ahkam",
        "authority_level": 5,
        "shamela_id":      20855,        # ✓ dikonfirmasi dari download
        "filename":        "al_qurtubi.epub",
    },
    "al_jassas": {
        "name_id":         "Ahkam al-Quran — Al-Jassas",
        "author":          "Al-Jassas (Hanafi)",
        "category":        "tafsir_ahkam",
        "authority_level": 5,
        "shamela_id":      7370,         # ✓ dikonfirmasi dari download
        "filename":        "al_jassas.epub",
    },
    "al_baghawi": {
        "name_id":         "Ma'alim al-Tanzil — Al-Baghawi",
        "author":          "Al-Baghawi",
        "category":        "tafsir_ahkam",
        "authority_level": 5,
        "shamela_id":      41,           # ✓ edisi Dar Taybah (8 jilid), paling umum
        # Alternatif: 12217 (edisi Ihya al-Turath, 5 jilid)
        "filename":        "al_baghawi.epub",
    },
    "ibn_kathir_tafsir": {
        "name_id":         "Tafsir al-Quran al-Azhim — Ibn Kathir",
        "author":          "Ibn Kathir",
        "category":        "tafsir_ahkam",
        "authority_level": 5,
        "shamela_id":      8473,         # ✓ dikonfirmasi dari download
        "filename":        "ibn_kathir_tafsir.epub",
    },
    "irshad_al_faqih": {
        "name_id":         "Irshad al-Faqih — Ibn Kathir",
        "author":          "Ibn Kathir",
        "category":        "tafsir_ahkam",
        "authority_level": 5,
        "shamela_id":      260,          # ✓ dikonfirmasi dari download
        "filename":        "irshad_al_faqih.epub",
    },
    "al_mawardi_nukat": {
        "name_id":         "Al-Nukat wa'l-Uyun (Tafsir al-Mawardi)",
        "author":          "Al-Mawardi",
        "category":        "tafsir_ahkam",
        "authority_level": 5,
        "shamela_id":      8346,         # ✓ dikonfirmasi dari web search
        "filename":        "al_mawardi_nukat.epub",
    },
    "ibn_ashur": {
        "name_id":         "Al-Tahrir wa'l-Tanwir — Ibn Ashur",
        "author":          "Muhammad al-Tahir ibn Ashur",
        "category":        "tafsir_ahkam",
        "authority_level": 5,
        "shamela_id":      9776,         # ✓ dikonfirmasi dari download
        "filename":        "ibn_ashur.epub",
    },

    # ── Fiqh Syafi'i — Level 1: Qawl Imam (Imam Al-Syafi'i) ─────────────────

    "al_umm": {
        "name_id":         "Al-Umm — Imam Al-Syafi'i",
        "author":          "Imam Al-Syafi'i",
        "category":        "fiqh_syafii",
        "authority_level": 1,
        "shamela_id":      1655,         # ✓ dikonfirmasi dari download
        "filename":        "al_umm.epub",
    },
    "al_risalah": {
        "name_id":         "Al-Risalah — Imam Al-Syafi'i",
        "author":          "Imam Al-Syafi'i",
        "category":        "fiqh_syafii",
        "authority_level": 1,
        "shamela_id":      8180,         # ✓ dikonfirmasi dari download
        "filename":        "al_risalah.epub",
    },

    # ── Fiqh Syafi'i — Level 2: Qawl Ashhab (Murid Langsung) ────────────────

    "mukhtasar_muzani": {
        # Al-Muzani adalah sahabat (murid langsung) Imam al-Syafi'i.
        # Ini satu-satunya kitab di Level 2 dalam corpus ini.
        "name_id":         "Mukhtasar al-Muzani",
        "author":          "Al-Muzani (murid langsung Imam al-Syafi'i)",
        "category":        "fiqh_syafii",
        "authority_level": 2,
        "shamela_id":      1661,         # ✓ dikonfirmasi dari web search
        "filename":        "mukhtasar_muzani.epub",
    },

    # ── Fiqh Syafi'i — Level 3: Mu'tamad (Madzhab Mapan) ────────────────────

    "nihayat_matlab": {
        # KOREKSI: Level 2 → 3. Al-Juwayni (d.478H) adalah generasi
        # mutaqaddimun, bukan ashhab langsung. Nihayat al-Matlab adalah
        # syarh dari Mukhtasar al-Muzani, tapi bukan oleh murid langsung.
        "name_id":         "Nihayat al-Matlab fi Dirayat al-Madhhab — Al-Juwayni",
        "author":          "Al-Juwayni (Imam al-Haramayn, d.478H)",
        "category":        "fiqh_syafii",
        "authority_level": 3,            # DIKOREKSI: 2 → 3 (mutaqaddimun)
        "shamela_id":      9851,         # ✓ dikonfirmasi dari web search
        "filename":        "nihayat_matlab.epub",
    },
    "minhaj_talibin": {
        "name_id":         "Minhaj al-Talibin — Al-Nawawi",
        "author":          "Al-Nawawi",
        "category":        "fiqh_syafii",
        "authority_level": 3,
        "shamela_id":      12096,        # ✓ dikonfirmasi dari download
        "filename":        "minhaj_talibin.epub",
    },
    "rawdhat_talibin": {
        "name_id":         "Rawdhat al-Talibin — Al-Nawawi",
        "author":          "Al-Nawawi",
        "category":        "fiqh_syafii",
        "authority_level": 3,
        "shamela_id":      499,          # ✓ dikonfirmasi dari download
        "filename":        "rawdhat_talibin.epub",
    },
    "al_majmu": {
        "name_id":         "Al-Majmu' Syarh al-Muhadzdzab — Al-Nawawi",
        "author":          "Al-Nawawi",
        "category":        "fiqh_syafii",
        "authority_level": 3,
        "shamela_id":      2186,         # ✓ dikonfirmasi dari download
        "filename":        "al_majmu.epub",
    },
    "al_hawi_kabir": {
        "name_id":         "Al-Hawi al-Kabir — Al-Mawardi",
        "author":          "Al-Mawardi (d.450H)",
        "category":        "fiqh_syafii",
        "authority_level": 3,
        "shamela_id":      6157,         # ✓ dikonfirmasi dari download
        "filename":        "al_hawi_kabir.epub",
    },

    # ── Fiqh Syafi'i — Level 4: Syarh Mu'tamad ───────────────────────────────

    "tuhfat_muhtaj": {
        "name_id":         "Tuhfat al-Muhtaj Syarh al-Minhaj — Ibn Hajar al-Haytami",
        "author":          "Ibn Hajar al-Haytami",
        "category":        "fiqh_syafii",
        "authority_level": 4,
        "shamela_id":      9059,         # ✓ dikonfirmasi dari download
        "filename":        "tuhfat_muhtaj.epub",
    },
    "nihayat_muhtaj": {
        "name_id":         "Nihayat al-Muhtaj Syarh al-Minhaj — Al-Ramli",
        "author":          "Al-Ramli (Syams al-Din)",
        "category":        "fiqh_syafii",
        "authority_level": 4,
        "shamela_id":      3565,         # ✓ dikonfirmasi dari download
        "filename":        "nihayat_muhtaj.epub",
    },
    "mughni_muhtaj": {
        "name_id":         "Mughni al-Muhtaj Syarh al-Minhaj — Al-Syarbini",
        "author":          "Al-Khatib al-Syarbini",
        "category":        "fiqh_syafii",
        "authority_level": 4,
        "shamela_id":      11444,        # ✓ dikonfirmasi dari download
        "filename":        "mughni_muhtaj.epub",
    },
    "asna_matalib": {
        "name_id":         "Asna al-Matalib Syarh Rawdh al-Thalib — Zakariyya al-Anshari",
        "author":          "Zakariyya al-Anshari",
        "category":        "fiqh_syafii",
        "authority_level": 4,
        "shamela_id":      11468,        # ✓ dikonfirmasi dari download
        "filename":        "asna_matalib.epub",
    },
    "fath_qarib": {
        "name_id":         "Fath al-Qarib al-Mujib (Syarh Matn Abi Syuja') — Ibn Qasim al-Ghazzi",
        "author":          "Ibn Qasim al-Ghazzi (d.918H)",
        "category":        "fiqh_syafii",
        "authority_level": 4,
        "shamela_id":      35120,        # ✓ dikonfirmasi dari web search
        "filename":        "fath_qarib.epub",
    },
    "al_iqna_shirbini": {
        # Catatan: file perlu direname: al_shirbini_iqna.epub → al_iqna_shirbini.epub
        "name_id":         "Al-Iqna' fi Hall Alfazh Abi Syuja' — Al-Syarbini",
        "author":          "Al-Khatib al-Syarbini",
        "category":        "fiqh_syafii",
        "authority_level": 4,
        "shamela_id":      6121,         # ✓ dikonfirmasi dari web search
        "filename":        "al_iqna_shirbini.epub",
    },
    "fath_muin": {
        "name_id":         "Fath al-Mu'in Syarh Qurrat al-'Ayn — Al-Malibari",
        "author":          "Zayn al-Din al-Malibari",
        "category":        "fiqh_syafii",
        "authority_level": 4,
        "shamela_id":      11327,        # ✓ dikonfirmasi dari web search
        "filename":        "fath_muin.epub",
    },
    "ianat_talibin": {
        "name_id":         "I'anat al-Talibin Hasyiyah Fath al-Mu'in — Al-Bakri",
        "author":          "Al-Bakri al-Dimyati (Al-Sayyid Abu Bakr Syatha)",
        "category":        "fiqh_syafii",
        "authority_level": 4,
        "shamela_id":      963,          # ✓ dikonfirmasi dari download
        "filename":        "ianat_talibin.epub",
    },

    # ── Qawa'id Fiqhiyyah ─────────────────────────────────────────────────────

    "al_asybah_suyuthi": {
        "name_id":         "Al-Asybah wa'l-Nazha'ir — Al-Suyuthi",
        "author":          "Al-Suyuthi",
        "category":        "qawaid",
        "authority_level": 5,
        "shamela_id":      21719,        # ✓ dikonfirmasi dari web search
        "filename":        "al_asybah_suyuthi.epub",
    },
    "al_mantsur_zarkasyi": {
        "name_id":         "Al-Mantsur fi al-Qawa'id al-Fiqhiyyah — Al-Zarkasyi",
        "author":          "Al-Zarkasyi (Badr al-Din, d.794H)",
        "category":        "qawaid",
        "authority_level": 5,
        "shamela_id":      21592,        # ✓ dikonfirmasi dari web search
        "filename":        "al_mantsur_zarkasyi.epub",
    },
    "qawaid_ahkam": {
        "name_id":         "Qawa'id al-Ahkam fi Mashalih al-Anam — Al-'Izz ibn Abd al-Salam",
        "author":          "Al-'Izz ibn Abd al-Salam (Sultan al-'Ulama, d.660H)",
        "category":        "qawaid",
        "authority_level": 5,
        "shamela_id":      8608,         # ✓ dikonfirmasi dari web search
        "filename":        "qawaid_ahkam.epub",
    },
}

# ─── Arabic Text Utilities ────────────────────────────────────────────────────

_ARABIC_RANGES = [
    (0x0600, 0x06FF),   # Arabic
    (0x0750, 0x077F),   # Arabic Supplement
    (0xFB50, 0xFDFF),   # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),   # Arabic Presentation Forms-B
]


def _is_arabic_char(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _ARABIC_RANGES)


def _arabic_ratio(text: str) -> float:
    """Rasio karakter Arab terhadap total karakter non-spasi."""
    stripped = text.replace(" ", "").replace("\n", "")
    if not stripped:
        return 0.0
    arabic_count = sum(1 for ch in stripped if _is_arabic_char(ch))
    return arabic_count / len(stripped)


def _normalize_arabic(text: str) -> str:
    """
    Normalisasi teks Arab:
    - Hapus control characters (kecuali \\n dan \\t)
    - Unicode NFC normalization
    - Collapse whitespace berlebihan
    - Pertahankan harakat (FTS5 akan handle via remove_diacritics)
    """
    # Hapus control chars tapi biarkan newline dan tab
    text = "".join(
        ch for ch in text
        if not unicodedata.category(ch).startswith("C") or ch in "\n\t"
    )
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ─── EPUB Parser ──────────────────────────────────────────────────────────────

MIN_PASSAGE_CHARS = 150    # Terlalu pendek = skip (header, nav)
MAX_PASSAGE_CHARS = 3000   # Cap (simpan tapi log warning)
MIN_ARABIC_RATIO  = 0.35   # Minimal 35% karakter harus Arab


def _extract_text_from_item(item) -> str:
    """Extract teks bersih dari satu EPUB item (XHTML page)."""
    try:
        content = item.get_content()
        soup = BeautifulSoup(content, "lxml")
        for tag in soup.find_all(["script", "style", "nav", "head"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        return _normalize_arabic(text)
    except Exception as e:
        logger.debug("Gagal parse item %s: %s", getattr(item, "get_name", lambda: "?")(), e)
        return ""


def _get_page_ref(item) -> str:
    """Dapatkan referensi halaman dari nama file item (page anchor)."""
    item_name = item.get_name()
    basename  = os.path.basename(item_name)
    return os.path.splitext(basename)[0]   # e.g. "page_001"


def _get_chapter_title(item) -> str:
    """
    Ekstrak judul bab Arab dari heading pertama yang valid dalam EPUB item.

    Phase B2 — Perbaikan dari Phase A:
    Sebelumnya: mengembalikan nama file item (e.g. "page_001") yang merupakan
    page anchor shamela2epub, bukan judul bab bermakna.

    Sekarang: parse HTML item, cari heading (h1–h4) yang mengandung ≥4
    karakter Arab dan bukan merupakan page anchor (pola "page_NNN").
    Jika tidak ada heading Arab yang valid → kembalikan string kosong
    (lebih baik kosong daripada page anchor yang misleading).

    Args:
        item: ebooklib EPUB document item

    Returns:
        Judul bab Arab (max 200 karakter), atau "" jika tidak ditemukan.
    """
    try:
        content = item.get_content()
        soup    = BeautifulSoup(content, "lxml")
        for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
            text = tag.get_text(strip=True)
            # Skip page anchors: "page_001", "page_1_0265", dll.
            if re.match(r"^page_\d", text):
                continue
            # Hitung karakter Arab (U+0600–U+06FF + Arabic supplement ranges)
            arabic_count = sum(1 for c in text if _is_arabic_char(c))
            if arabic_count >= 4:
                return text[:200]
    except Exception as e:
        logger.debug(
            "Gagal extract chapter_title dari %s: %s",
            getattr(item, "get_name", lambda: "?")(), e,
        )
    return ""   # Tidak ada judul bab ditemukan


def parse_epub(epub_path: str, limit: int = 0) -> Generator[dict, None, None]:
    """
    Parse satu file EPUB, yield dict passage per halaman.

    Args:
        epub_path: Path ke file .epub
        limit:     Max jumlah passage (0 = tak terbatas)

    Yields:
        dict: {arabic_text, chapter_title, page_ref, text_length}
    """
    try:
        book = epub.read_epub(epub_path, options={"ignore_ncx": True})
    except Exception as e:
        logger.error("Gagal buka EPUB %s: %s", epub_path, e)
        return

    count = 0
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        if limit and count >= limit:
            break

        text = _extract_text_from_item(item)

        if len(text) < MIN_PASSAGE_CHARS:
            continue
        if _arabic_ratio(text) < MIN_ARABIC_RATIO:
            continue
        if len(text) > MAX_PASSAGE_CHARS:
            logger.debug("Passage panjang (%d chars): %s",
                         len(text), os.path.basename(epub_path))

        chapter_title = _get_chapter_title(item)
        page_ref      = _get_page_ref(item)
        yield {
            "arabic_text":   text,
            "chapter_title": chapter_title,
            "page_ref":      page_ref,
            "text_length":   len(text),
        }
        count += 1


# ─── Ingestion Core ───────────────────────────────────────────────────────────

def _get_or_create_book(conn: sqlite3.Connection, slug: str, meta: dict):
    """Insert buku ke kitab_books jika belum ada."""
    existing = conn.execute(
        "SELECT id FROM kitab_books WHERE slug = ?", (slug,)
    ).fetchone()
    if not existing:
        conn.execute("""
            INSERT INTO kitab_books
                (slug, name_id, author, category, authority_level, shamela_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            slug,
            meta["name_id"],
            meta["author"],
            meta["category"],
            meta["authority_level"],
            meta.get("shamela_id"),
        ))


def _disable_fts_triggers(conn: sqlite3.Connection):
    """
    Nonaktifkan triggers FTS selama bulk insert.
    SQLite tidak mendukung DISABLE TRIGGER → kita DROP dan recreate sesudahnya.
    """
    conn.execute("DROP TRIGGER IF EXISTS kitab_corpus_ai")
    conn.execute("DROP TRIGGER IF EXISTS kitab_corpus_ad")
    conn.execute("DROP TRIGGER IF EXISTS kitab_corpus_au")


def _rebuild_fts(conn: sqlite3.Connection):
    """
    Rebuild FTS5 index dari kitab_corpus.
    Untuk external content FTS5, 'rebuild' otomatis membaca dari tabel konten.
    Lebih cepat dan aman dibanding per-row trigger selama bulk insert.
    """
    logger.info("Rebuilding FTS5 index dari kitab_corpus...")
    conn.execute("INSERT INTO kitab_fts(kitab_fts) VALUES('rebuild')")
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM kitab_fts").fetchone()[0]
    logger.info("FTS5 rebuild selesai: %d passages diindeks.", count)


def _recreate_triggers(conn: sqlite3.Connection):
    """
    Recreate triggers FTS setelah bulk insert.
    DDL diimpor dari schema_kitab untuk menghindari duplikasi definisi.
    """
    conn.execute(DDL_TRIGGER_INSERT)
    conn.execute(DDL_TRIGGER_DELETE)
    conn.execute(DDL_TRIGGER_UPDATE)
    conn.commit()


def ingest_book(
    conn:     sqlite3.Connection,
    slug:     str,
    epub_path: str,
    meta:     dict,
    limit:    int  = 0,
    dry_run:  bool = False,
) -> int:
    """
    Ingest satu kitab ke database.

    Returns:
        Jumlah passages yang berhasil diinsert (atau diparsing jika dry_run)
    """
    logger.info("Ingest: %s (%s)", meta["name_id"], os.path.basename(epub_path))

    _get_or_create_book(conn, slug, meta)

    passages = list(parse_epub(epub_path, limit=limit))
    logger.info("  Parsed: %d passages", len(passages))

    if dry_run or not passages:
        return len(passages)

    rows = [
        (
            slug,
            meta["authority_level"],
            meta["category"],
            p["chapter_title"],
            p["page_ref"],
            p["arabic_text"],
            p["text_length"],
        )
        for p in passages
    ]

    conn.executemany("""
        INSERT INTO kitab_corpus
            (book_slug, authority_level, category, chapter_title,
             page_ref, arabic_text, text_length)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.execute("""
        UPDATE kitab_books
        SET total_passages = ?, ingested_at = ?
        WHERE slug = ?
    """, (len(passages), datetime.now(timezone.utc).isoformat(), slug))

    conn.commit()
    logger.info("  ✓ %d passages diinsert untuk %s", len(passages), slug)
    return len(passages)


def ingest_all(
    conn:            sqlite3.Connection,
    corpus_dir:      str,
    limit_per_book:  int  = 0,
    only_book:       str  | None = None,
    dry_run:         bool = False,
    reset_book:      str  | None = None,
) -> dict:
    """
    Ingest semua kitab dari corpus_dir.

    Returns:
        dict {slug: passages_count}
    """
    results: dict = {}
    errors:  list = []

    # Filter registry jika --book diberikan
    registry = BOOK_REGISTRY
    if only_book:
        if only_book not in registry:
            logger.error("Slug '%s' tidak ada di BOOK_REGISTRY. "
                         "Jalankan dengan --list-books untuk melihat daftar.", only_book)
            return {}
        registry = {only_book: BOOK_REGISTRY[only_book]}

    # Reset satu buku jika diminta
    if reset_book and not dry_run:
        logger.info("Reset book: %s", reset_book)
        conn.execute("DELETE FROM kitab_corpus WHERE book_slug = ?", (reset_book,))
        conn.execute("DELETE FROM kitab_books  WHERE slug = ?",      (reset_book,))
        conn.commit()

    # Nonaktifkan FTS triggers untuk bulk insert
    if not dry_run:
        _disable_fts_triggers(conn)

    total_inserted = 0

    for slug, meta in registry.items():
        epub_filename = meta.get("filename", f"{slug}.epub")
        epub_path     = os.path.join(corpus_dir, epub_filename)

        # Fallback ke nama file berdasarkan slug
        if not os.path.exists(epub_path):
            alt_path = os.path.join(corpus_dir, f"{slug}.epub")
            if os.path.exists(alt_path):
                epub_path = alt_path
            else:
                logger.warning("File tidak ditemukan: %s (skip)", epub_filename)
                errors.append(slug)
                continue

        # Skip jika sudah diingest (kecuali sedang di-reset)
        if not dry_run and slug != reset_book:
            row = conn.execute(
                "SELECT total_passages FROM kitab_books WHERE slug = ?", (slug,)
            ).fetchone()
            if row and row[0] and row[0] > 0:
                logger.info("  Skip %s (sudah ada %d passages)", slug, row[0])
                results[slug] = row[0]
                continue

        try:
            count = ingest_book(
                conn, slug, epub_path, meta,
                limit=limit_per_book, dry_run=dry_run,
            )
            results[slug] = count
            total_inserted += count
        except Exception as e:
            logger.exception("Error ingest %s: %s", slug, e)
            errors.append(slug)

    # Rebuild FTS sekali setelah semua insert selesai
    if not dry_run and total_inserted > 0:
        _rebuild_fts(conn)
        _recreate_triggers(conn)

    if errors:
        logger.warning("Kitab yang gagal/tidak ditemukan: %s", ", ".join(errors))

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Ingest EPUB kitab ke SQLite FTS5 untuk IslamiAI"
    )
    parser.add_argument("--db",         default=DEFAULT_DB,
                        help=f"Path database SQLite (default: {DEFAULT_DB})")
    parser.add_argument("--corpus-dir", default=DEFAULT_CORPUS_DIR,
                        help=f"Direktori EPUB (default: {DEFAULT_CORPUS_DIR})")
    parser.add_argument("--book",       default=None,
                        help="Ingest satu kitab saja (slug, e.g. 'al_umm')")
    parser.add_argument("--limit",      type=int, default=0,
                        help="Max passages per kitab (0 = semua)")
    parser.add_argument("--dry-run",    action="store_true",
                        help="Test parsing tanpa tulis ke database")
    parser.add_argument("--reset-book", default=None,
                        help="Hapus dan reingest satu kitab (slug)")
    parser.add_argument("--list-books", action="store_true",
                        help="Tampilkan daftar kitab di registry dan exit")
    args = parser.parse_args()

    if args.list_books:
        print(f"\n{'Slug':<28} {'Lvl':>3}  {'Category':<14}  {'Shamela ID':>10}  Nama")
        print("─" * 80)
        for slug, meta in BOOK_REGISTRY.items():
            sid = meta.get("shamela_id") or "?"
            print(f"{slug:<28} {meta['authority_level']:>3}  "
                  f"{meta['category']:<14}  {str(sid):>10}  {meta['name_id']}")
        print(f"\nTotal: {len(BOOK_REGISTRY)} kitab\n")
        return

    # Buat atau buka database
    conn = create_schema(args.db, reset=False)
    if not verify_schema(conn):
        print("❌ Schema tidak valid. Jalankan:\n"
              "   python3 tools/schema_kitab.py --reset")
        sys.exit(1)

    if args.dry_run:
        print(f"\n🔍 DRY RUN — tidak ada yang ditulis ke database\n")

    start   = datetime.now()
    results = ingest_all(
        conn,
        corpus_dir     = args.corpus_dir,
        limit_per_book = args.limit,
        only_book      = args.book,
        dry_run        = args.dry_run,
        reset_book     = args.reset_book,
    )
    elapsed = (datetime.now() - start).total_seconds()
    conn.close()

    total = sum(results.values())
    print(f"\n{'='*62}")
    print(f"  HASIL INGEST {'(DRY RUN)' if args.dry_run else ''}")
    print(f"{'='*62}")
    for slug, count in results.items():
        status = "DRY" if args.dry_run else "✓"
        print(f"  [{status}] {slug:<30} {count:>7} passages")
    print(f"{'─'*62}")
    print(f"  Total  : {total:,} passages dalam {elapsed:.1f}s")
    if not args.dry_run:
        print(f"  DB     : {args.db}")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    main()
