"""
corpus_retrieval.py — Shamela Corpus Retrieval Layer
══════════════════════════════════════════════════════════════════
Interface-compatible dengan retrieve_ruling() di retrieval.py.
Digunakan sebagai fallback Layer 4 ketika static + cache tidak
menemukan jawaban.

CARA PENGGUNAAN di retrieval.py (TANPA mengubah signature):

    from corpus_retrieval import search_corpus

    # Di retrieve_ruling(), setelah Layer 3:
    corpus_result = search_corpus(topic_lower, madhab)
    if corpus_result:
        return corpus_result

TIDAK ADA perubahan pada fungsi yang sudah ada.
══════════════════════════════════════════════════════════════════
"""

import logging
import os
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger("islamiai.corpus_retrieval")

# ── Path ke corpus DB ──────────────────────────────────────────────────────────
_CORPUS_DB = Path(__file__).parent / "corpus" / "shamela_corpus.db"

# ── Konfigurasi ───────────────────────────────────────────────────────────────
TOP_K_PASSAGES   = 3    # berapa passage dikembalikan per query
MIN_PASSAGE_LEN  = 40   # passage lebih pendek dari ini diabaikan


# ── Arabic Normalization (sama dengan 02_build_db.py) ─────────────────────────

def _normalize_arabic(text: str) -> str:
    """Normalisasi teks Arab untuk query FTS5."""
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[أإآ]", "ا", text)
    text = text.replace("ى", "ي")
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Lazy-loaded Connection ─────────────────────────────────────────────────────

_conn: Optional[sqlite3.Connection] = None
_corpus_available: Optional[bool] = None


def _get_conn() -> Optional[sqlite3.Connection]:
    """
    Buka koneksi ke corpus DB.
    Lazy-load: hanya dibuka saat pertama kali digunakan.
    Return None jika DB tidak ada (graceful degradation).
    """
    global _conn, _corpus_available

    if _corpus_available is False:
        return None  # sudah dicek, tidak ada

    if _conn is not None:
        return _conn

    if not _CORPUS_DB.exists():
        logger.info(
            "Corpus DB tidak ditemukan di %s. "
            "Jalankan tools/01_download.py dan tools/02_build_db.py terlebih dahulu.",
            _CORPUS_DB
        )
        _corpus_available = False
        return None

    try:
        _conn = sqlite3.connect(str(_CORPUS_DB), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA query_only = ON")  # read-only safety

        # Verify schema
        tables = {row[0] for row in
                  _conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "passage" not in tables or "passage_fts" not in tables:
            logger.warning("Corpus DB schema tidak valid.")
            _conn = None
            _corpus_available = False
            return None

        total = _conn.execute("SELECT COUNT(*) FROM passage").fetchone()[0]
        logger.info("Corpus DB loaded: %d passages dari %s", total, _CORPUS_DB)
        _corpus_available = True
        return _conn

    except sqlite3.Error as e:
        logger.error("Gagal buka corpus DB: %s", e)
        _corpus_available = False
        return None


# ── Topic → Query Mapping ─────────────────────────────────────────────────────

# Peta dari topic key bahasa Indonesia/Latin → kata kunci Arab untuk FTS5
TOPIC_ARABIC_MAP = {
    # Thaharah
    "thaharah_wudhu":    "وضوء طهارة",
    "thaharah_ghusl":    "غسل طهارة جنابة",
    "thaharah_tayammum": "تيمم طهارة",
    "najis_ringan":      "نجاسة خفيفة",
    "najis_berat":       "نجاسة مغلظة كلب",
    "thaharah":          "طهارة وضوء غسل",

    # Shalat
    "shalat_lima_waktu": "صلاة فرض وقت",
    "shalat_jumat":      "صلاة الجمعة خطبة",
    "shalat_jamak":      "جمع صلاة قصر سفر",
    "shalat_qasar":      "قصر صلاة مسافر",
    "shalat":            "صلاة فرض",

    # Zakat
    "zakat_mal":         "زكاة مال نصاب",
    "zakat_fitrah":      "زكاة الفطر رمضان",
    "zakat_muallaf":     "مؤلفة قلوبهم زكاة",
    "zakat":             "زكاة",

    # Puasa
    "puasa_ramadhan":    "صوم رمضان",
    "puasa":             "صيام صوم",

    # Haji
    "haji":              "حج فريضة إحرام",
    "umrah":             "عمرة إحرام طواف",

    # Nikah
    "nikah":             "نكاح زواج",
    "talak":             "طلاق فرقة",
    "wali_nikah":        "ولي نكاح",
    "mahar":             "مهر صداق",
    "pernikahan_suami_islam_istri_kafir": "زواج مسلم كتابية",
    "pernikahan_istri_islam_suami_kafir": "مسلمة كافر نكاح فسخ",

    # Waris
    "waris":             "وراثة إرث فريضة",
    "waris_perbedaan_agama": "وراثة اختلاف الدين",
    "waris_muallaf":     "وراثة مسلم كافر",

    # Jenazah
    "jenazah":           "جنازة ميت",
    "jenazah_ghusl":     "غسل الميت",
    "jenazah_takfin":    "تكفين كفن",
    "jenazah_shalat":    "صلاة الجنازة",
    "jenazah_dafan":     "دفن القبر",

    # Makanan
    "makanan_haram_umum":      "حرام طعام",
    "makanan_haram_minuman":   "خمر مسكر حرام",
    "makanan_halal_penyembelihan": "ذبح حلال",

    # Muamalah
    "riba":              "ربا بيع",
    "jual_beli":         "بيع شراء",
    "hutang_piutang":    "دين قرض",

    # Akidah/Syahadat
    "syahadat":          "شهادة إسلام",
    "rukun_islam":       "أركان الإسلام",
}


def _build_fts_query(topic: str) -> str:
    """
    Bangun query FTS5 dari topic key.
    Coba dari map dulu; jika tidak ada, normalize topic sebagai query langsung.
    """
    # Cek exact match di map
    if topic in TOPIC_ARABIC_MAP:
        return TOPIC_ARABIC_MAP[topic]

    # Cek partial match (topic adalah prefix atau suffix)
    for key, arabic in TOPIC_ARABIC_MAP.items():
        if topic in key or key in topic:
            return arabic

    # Fallback: pakai topic langsung (mungkin sudah Arab atau latin)
    normalized = _normalize_arabic(topic)
    return normalized if normalized else topic


# ── Main Search Function ───────────────────────────────────────────────────────

def search_corpus(
    topic: str,
    madhab: str = "shafii",
    top_k: int = TOP_K_PASSAGES,
) -> Optional[dict]:
    """
    Cari di corpus Shamela berdasarkan topic.

    Interface IDENTIK dengan retrieve_ruling():
      Args:
        topic  — topic key (sama seperti parse_user_query() output)
        madhab — default "shafii"
      Returns:
        dict dengan key: topic, ruling, madhab, quran, hadis,
                         confidence, reasoning, _source
        None jika tidak ditemukan

    Bisa langsung digunakan sebagai fallback di retrieval.py.
    """
    conn = _get_conn()
    if conn is None:
        return None

    fts_query = _build_fts_query(topic)
    if not fts_query:
        return None

    try:
        # FTS5 search di corpus
        # Filter madhab shafii lebih diutamakan
        rows = conn.execute(
            """
            SELECT p.text_arabic, p.text_normalized, p.chapter,
                   p.topic_hints, k.label, k.level, k.madhab, k.blok
            FROM   passage_fts
            JOIN   passage p ON passage_fts.rowid = p.id
            JOIN   kitab   k ON p.kitab_id = k.id
            WHERE  passage_fts MATCH ?
              AND  length(p.text_arabic) >= ?
            ORDER BY
              CASE WHEN k.madhab = 'shafii' THEN 0 ELSE 1 END,
              CASE k.level
                WHEN 'mutamad'              THEN 0
                WHEN 'mutamad_ensiklopedis' THEN 1
                WHEN 'sharh_mutamad_hijaz'  THEN 2
                WHEN 'sharh_mutamad_mesir'  THEN 3
                WHEN 'pesantren_nusantara'  THEN 4
                WHEN 'pesantren'            THEN 5
                ELSE 9
              END,
              rank
            LIMIT ?
            """,
            (fts_query, MIN_PASSAGE_LEN, top_k),
        ).fetchall()

    except sqlite3.OperationalError as e:
        logger.warning("FTS5 query error untuk '%s': %s", fts_query, e)
        return None

    if not rows:
        logger.debug("Corpus: tidak ada hasil untuk topic '%s'", topic)
        return None

    # Format output kompatibel dengan retrieve_ruling()
    passages_out = []
    sources_out  = []

    for row in rows:
        passages_out.append({
            "text":    row["text_arabic"],
            "chapter": row["chapter"] or "",
            "kitab":   row["label"],
            "level":   row["level"],
            "madhab":  row["madhab"],
        })
        sources_out.append(row["label"])

    # Gabung teks untuk "reasoning"
    reasoning_parts = [
        f"[{p['kitab']} — {p['chapter']}]\n{p['text'][:400]}"
        for p in passages_out
    ]

    # Confidence: lebih tinggi jika kitab mu'tamad ditemukan
    top_level = rows[0]["level"] if rows else ""
    if top_level in ("mutamad", "mutamad_ensiklopedis"):
        confidence = "medium"
    elif top_level in ("sharh_mutamad_hijaz", "sharh_mutamad_mesir"):
        confidence = "medium"
    else:
        confidence = "low"

    logger.info(
        "Corpus hit: topic='%s' → %d passages dari [%s]",
        topic, len(rows), ", ".join(set(sources_out))
    )

    return {
        "topic":     topic,
        "ruling":    "",          # corpus tidak menyimpan ruling ringkas
        "madhab":    madhab,
        "quran":     [],          # referensi Quran ada di text, belum di-extract
        "hadis":     [],          # referensi hadis ada di text, belum di-extract
        "confidence": confidence,
        "reasoning":  "\n\n---\n\n".join(reasoning_parts),
        "keywords":   [topic],
        "corpus_passages": passages_out,  # data tambahan untuk formatter
        "_source":   "corpus_shamela",
        "_needs_review": True,    # selalu flag untuk review ulama
    }


def get_corpus_stats() -> dict:
    """Statistik corpus untuk endpoint /status."""
    conn = _get_conn()
    if conn is None:
        return {"available": False, "passages": 0, "kitab": 0}

    try:
        passages = conn.execute("SELECT COUNT(*) FROM passage").fetchone()[0]
        kitab    = conn.execute("SELECT COUNT(*) FROM kitab").fetchone()[0]
        return {
            "available": True,
            "passages":  passages,
            "kitab":     kitab,
            "db_path":   str(_CORPUS_DB),
        }
    except sqlite3.Error:
        return {"available": False, "passages": 0, "kitab": 0}


# ── Self-test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    print("=== corpus_retrieval.py — Self Test ===\n")

    stats = get_corpus_stats()
    print(f"Corpus status: {stats}")

    if stats["available"]:
        test_topics = ["thaharah_wudhu", "zakat", "nikah", "waris"]
        for topic in test_topics:
            result = search_corpus(topic)
            if result:
                print(f"\n✅ '{topic}': {len(result['corpus_passages'])} passages")
                print(f"   Confidence: {result['confidence']}")
                print(f"   Sumber: {result['corpus_passages'][0]['kitab']}")
            else:
                print(f"\n❌ '{topic}': tidak ditemukan")
    else:
        print("⚠️  Corpus belum siap. Jalankan 01_download.py dan 02_build_db.py")
