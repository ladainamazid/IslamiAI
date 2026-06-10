"""
db_retrieval.py — Layer 4: Kitab Corpus Search via SQLite FTS5
══════════════════════════════════════════════════════════════
Modul standalone untuk mencari teks di kitab corpus.
Diletakkan di IslamiAIProject/ (bukan di tools/) agar dapat diimpor
oleh retrieval.py sebagai Layer 4.

Interface utama:
    search_kitab(query, limit, category, max_authority)
    → list[dict] — kosong jika DB tidak tersedia atau tidak ada hasil

    get_corpus_stats()
    → dict — statistik corpus

    is_db_available()
    → bool — apakah islamiai.db sudah ada dan punya tabel kitab_fts

Rancangan:
    - Tidak pernah crash: semua exception ditangkap dan dikembalikan sebagai []
    - DB tidak wajib ada: jika belum diingest, fungsi mengembalikan []
    - Query otomatis di-expand untuk menangani artikel definitif Arab (ال-)
    - Mendukung query Bahasa Indonesia via ARABIC_TOPIC_MAP

Integrasi dengan retrieval.py (Phase A.5):
    Tambahkan di akhir retrieve_ruling() setelah Layer 3 mengembalikan None:

        from db_retrieval import search_kitab, is_db_available

        # ── Layer 4: Kitab Corpus ─────────────────────────
        if is_db_available():
            hits = search_kitab(topic_lower, limit=5)
            if hits:
                return {
                    "topic":        topic_lower,
                    "ruling":       "",
                    "madhab":       madhab,
                    "quran":        [],
                    "hadis":        [],
                    "confidence":   "low",
                    "reasoning":    "",
                    "keywords":     [],
                    "_source":      "kitab_corpus",
                    "_kitab_hits":  hits,
                }

    PENTING: gate_answer() akan menolak hasil ini karena confidence "low"
    dan tidak ada quran/hadis. Modifikasi gate_answer() untuk menerima
    "_source: kitab_corpus" dilakukan di Phase A.5.
"""

import logging
import os
import sqlite3
from typing import Optional

logger = logging.getLogger("islamiai.db_retrieval")

# Database ada di IslamiAIProject/ (direktori yang sama dengan file ini)
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "islamiai.db")


# ─── Tabel mapping topik Indonesia → kata kunci bahasa Arab ───────────────────
# Diperlukan karena FTS5 tidak bisa mencocokkan "wudhu" dengan "الوضوء".
# Format nilai: satu atau beberapa kata Arab dipisah spasi.

ARABIC_TOPIC_MAP: dict[str, str] = {
    # Thaharah
    "thaharah_wudhu":        "الوضوء وضوء طهارة",
    "thaharah_mandi_wajib":  "الغسل غسل جنابة",
    "najis":                 "النجاسة نجاسة",
    "najis_ringkan":         "النجاسة المخففة بول طفل",
    "najis_sedang":          "النجاسة المتوسطة دم",
    "najis_berat":           "النجاسة المغلظة كلب خنزير",
    # Shalat
    "shalat_lima_waktu":     "الصلاة صلاة فرض",
    "shalat":                "الصلاة صلاة",
    # Syahadat & Aqidah
    "syahadat":              "الشهادة شهادة توحيد إسلام",
    # Zakat
    "zakat_fitrah":          "زكاة الفطر",
    "zakat_harta":           "الزكاة زكاة نصاب",
    # Puasa
    "puasa_ramadhan":        "الصيام رمضان صوم",
    "puasa_muallaf_tengah_ramadhan": "الصيام المسلم الجديد رمضان",
    # Makanan & Halal-Haram
    "makanan_haram_umum":    "المحرمات حرام أكل",
    "makanan_haram_minuman": "الخمر مسكر حرام",
    "makanan_halal_penyembelihan": "الذبيحة ذبح حلال",
    # Aurat & Pakaian
    "aurat_laki_laki":       "عورة الرجل",
    "aurat_perempuan_shalat": "عورة المرأة الصلاة",
    "aurat_perempuan_di_luar_shalat": "الحجاب عورة النساء",
    # Keluarga & Hubungan Sosial
    "keluarga_non_muslim_hubungan": "أهل الذمة الكفار قرابة",
    "muallaf_status":        "المؤلفة قلوبهم مسلم جديد",
    # Pernikahan
    "pernikahan_suami_islam_istri_kafir": "النكاح كافر فسخ",
    "pernikahan_istri_islam_suami_kafir": "الفسخ نكاح مرأة مسلمة",
    "pernikahan_keduanya_islam": "النكاح إسلام زوجان",
    # Waris
    "waris_perbedaan_agama": "الميراث اختلاف الدين",
    "waris_muallaf_keluarga_non_muslim": "الميراث كافر مسلم",
    # Jenazah
    "jenazah_ghusl":         "غسل الميت الجنازة",
    "jenazah_takfin":        "التكفين كفن",
    "jenazah_shalat":        "صلاة الجنازة",
    "jenazah_dafan":         "الدفن القبر",
    "jenazah_keluarga_non_muslim": "جنازة كافر تعزية",
}


# ─── Query Utilities ──────────────────────────────────────────────────────────

def _is_arabic(text: str) -> bool:
    """True jika teks mengandung karakter Arab."""
    return any(0x0600 <= ord(c) <= 0x06FF for c in text)


def _sanitize_fts_term(term: str) -> str:
    """Escape karakter khusus FTS5 dalam satu term."""
    # Karakter yang harus di-escape atau di-wrap: " ( ) * ^ - :
    term = term.replace('"', '""')
    if any(c in term for c in '()*^-:/'):
        return f'"{term}"'
    return term


def _expand_arabic_query(raw_query: str) -> str:
    """
    Expand query Arab untuk menangani artikel definitif (ال-).

    Masalah: FTS5 unicode61 remove_diacritics TIDAK memisahkan ال-.
    Sehingga query 'وضوء' (tanpa ال) TIDAK mencocokkan 'الوضوء' dalam teks.

    Solusi: setiap term yang tidak diawali ال dijadikan OR dengan variant ال-:
        'وضوء'  → '(وضوء OR الوضوء)'
        'الوضوء' → 'الوضوء'  (biarkan)

    Args:
        raw_query: Query string, bisa multi-term dipisah spasi

    Returns:
        FTS5 query string yang sudah di-expand
    """
    terms = raw_query.strip().split()
    if not terms:
        return ""

    expanded = []
    for term in terms:
        if not term:
            continue
        term_clean = _sanitize_fts_term(term)
        # Cek apakah sudah berawalan ال
        if term.startswith("ال"):
            expanded.append(term_clean)
        else:
            al_form = _sanitize_fts_term("ال" + term)
            expanded.append(f"({term_clean} OR {al_form})")

    return " ".join(expanded)


def _build_fts_query(topic: str) -> str:
    """
    Bangun FTS5 query dari topic key atau query Arab langsung.

    Priority:
    1. Topic key di ARABIC_TOPIC_MAP → gunakan kata kunci Arab
    2. Sudah mengandung Arab → expand langsung
    3. Bahasa Indonesia tidak di map → gunakan sebagai-is (akan mencari di book_slug/name_id)

    Returns:
        FTS5 query string, atau "" jika tidak bisa dibangun
    """
    topic_lower = topic.lower().strip()

    # Cek exact match di ARABIC_TOPIC_MAP
    if topic_lower in ARABIC_TOPIC_MAP:
        arabic_terms = ARABIC_TOPIC_MAP[topic_lower]
        return _expand_arabic_query(arabic_terms)

    # Cek partial match (e.g. "wudhu" → "thaharah_wudhu")
    for key, arabic_terms in ARABIC_TOPIC_MAP.items():
        if topic_lower in key or key in topic_lower:
            return _expand_arabic_query(arabic_terms)

    # Query sudah dalam Arab: expand langsung
    if _is_arabic(topic):
        return _expand_arabic_query(topic)

    # Fallback: gunakan as-is (akan mencocokkan book_slug, name_id, chapter_title)
    return _sanitize_fts_term(topic_lower)


# ─── Database Utilities ───────────────────────────────────────────────────────

def _get_connection(db_path: str = _DB_PATH) -> Optional[sqlite3.Connection]:
    """
    Buka koneksi SQLite.

    Returns:
        Connection dengan row_factory = Row, atau None jika gagal.
    """
    if not os.path.exists(db_path):
        logger.debug("islamiai.db tidak ditemukan di %s — Layer 4 belum tersedia.", db_path)
        return None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        return conn
    except sqlite3.Error as e:
        logger.error("DB connection gagal: %s", e)
        return None


def is_db_available(db_path: str = _DB_PATH) -> bool:
    """
    Cek apakah DB tersedia dan tabel kitab_fts sudah ada.

    Returns:
        True jika siap digunakan untuk search.
    """
    conn = _get_connection(db_path)
    if conn is None:
        return False
    try:
        conn.execute("SELECT COUNT(*) FROM kitab_fts").fetchone()
        return True
    except sqlite3.OperationalError:
        return False
    finally:
        conn.close()


# ─── Core Search Functions ────────────────────────────────────────────────────

def search_kitab(
    query:         str,
    *,
    limit:         int           = 5,
    category:      Optional[str] = None,
    max_authority: int           = 5,
    min_authority: int           = 1,
    db_path:       str           = _DB_PATH,
) -> list[dict]:
    """
    Cari teks di kitab corpus via FTS5.

    Args:
        query:         Topik (Indonesian/transliterasi) ATAU kata kunci Arab.
                       Contoh: "wudhu", "thaharah_wudhu", "الوضوء"
        limit:         Maksimal hasil yang dikembalikan (default: 5)
        category:      Filter kategori: "fiqh_syafii" | "tafsir_ahkam" |
                       "qawaid" | None (semua)
        max_authority: Filter authority_level ≤ nilai ini (default: 5 = semua)
        min_authority: Filter authority_level ≥ nilai ini (default: 1 = semua)
        db_path:       Path ke file islamiai.db

    Returns:
        list[dict] dengan keys:
            id, book_slug, book_name_id, author, category, authority_level,
            chapter_title, arabic_text, page_ref, rank
        Mengembalikan [] jika DB tidak ada, query kosong, atau tidak ada hasil.

    Tidak pernah raise exception.
    """
    if not query or not query.strip():
        return []

    fts_query = _build_fts_query(query)
    if not fts_query:
        return []

    conn = _get_connection(db_path)
    if conn is None:
        return []

    try:
        # Bangun WHERE clause dengan filter opsional
        where_parts  = ["kitab_fts MATCH ?"]
        params: list = [fts_query]

        if category:
            where_parts.append("c.authority_level IS NOT NULL")  # always true, for join
            where_parts.append("c.category = ?")
            params.append(category)
        if min_authority > 1:
            where_parts.append("c.authority_level >= ?")
            params.append(min_authority)
        if max_authority < 5:
            where_parts.append("c.authority_level <= ?")
            params.append(max_authority)

        params.append(limit)

        sql = f"""
            SELECT
                fts_result.rowid        AS id,
                c.book_slug,
                b.name_id               AS book_name_id,
                b.author,
                c.category,
                c.authority_level,
                c.chapter_title,
                c.arabic_text,
                c.page_ref,
                fts_result.rank
            FROM (
                SELECT rowid, rank
                FROM kitab_fts
                WHERE {' AND '.join(where_parts[0:1])}
            ) fts_result
            JOIN kitab_corpus c ON c.id = fts_result.rowid
            JOIN kitab_books  b ON b.slug = c.book_slug
            WHERE {' AND '.join(where_parts[1:] if len(where_parts) > 1 else ['1=1'])}
            ORDER BY
                c.authority_level ASC,  -- otoritas lebih tinggi (level 1) lebih diprioritaskan
                fts_result.rank ASC     -- BM25: lebih negatif = lebih relevan
            LIMIT ?
        """

        rows    = conn.execute(sql, params).fetchall()
        results = [dict(row) for row in rows]

        logger.info("search_kitab('%s') → %d hasil (query FTS: '%s')",
                    query[:50], len(results), fts_query[:80])
        return results

    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            logger.warning("Tabel kitab_fts belum ada. "
                           "Jalankan: python3 tools/ingest_corpus.py")
        else:
            logger.error("FTS search error: %s | query: %s", e, fts_query)
        return []
    except Exception as e:
        logger.error("Error tidak terduga di search_kitab: %s", e)
        return []
    finally:
        conn.close()


def search_by_authority(
    query:         str,
    *,
    max_authority: int           = 3,
    limit:         int           = 5,
    db_path:       str           = _DB_PATH,
) -> list[dict]:
    """
    Shortcut: cari hanya di kitab dengan authority_level ≤ max_authority.

    Berguna untuk mendapatkan jawaban dari sumber-sumber paling otoritatif.
    Contoh: max_authority=3 → hanya dari Level 1 (Imam), 2 (Ashhab), 3 (Mu'tamad).
    """
    return search_kitab(
        query,
        max_authority=max_authority,
        limit=limit,
        db_path=db_path,
    )


def get_corpus_stats(db_path: str = _DB_PATH) -> dict:
    """
    Statistik corpus: jumlah kitab, passages, chars per kategori/authority.

    Returns:
        dict dengan keys: available, books, passages, total_chars,
        by_category, by_authority
    """
    conn = _get_connection(db_path)
    if conn is None:
        return {"available": False}

    try:
        stats: dict = {"available": True}

        stats["books"] = conn.execute(
            "SELECT COUNT(*) FROM kitab_books"
        ).fetchone()[0]

        stats["passages"] = conn.execute(
            "SELECT COUNT(*) FROM kitab_corpus"
        ).fetchone()[0]

        total = conn.execute(
            "SELECT SUM(text_length) FROM kitab_corpus"
        ).fetchone()[0]
        stats["total_chars"] = total or 0

        stats["by_category"] = dict(conn.execute("""
            SELECT category, COUNT(*) as cnt
            FROM kitab_corpus
            GROUP BY category
            ORDER BY cnt DESC
        """).fetchall())

        stats["by_authority"] = dict(conn.execute("""
            SELECT authority_level, COUNT(*) as cnt
            FROM kitab_corpus
            GROUP BY authority_level
            ORDER BY authority_level
        """).fetchall())

        stats["books_detail"] = conn.execute("""
            SELECT slug, name_id, authority_level, total_passages
            FROM kitab_books
            ORDER BY authority_level, slug
        """).fetchall()
        stats["books_detail"] = [dict(r) for r in stats["books_detail"]]

        return stats

    except sqlite3.Error as e:
        logger.error("Gagal ambil stats: %s", e)
        return {"available": True, "error": str(e)}
    finally:
        conn.close()


# ─── Standalone CLI ───────────────────────────────────────────────────────────

def _print_stats():
    """Tampilkan statistik corpus ke stdout."""
    stats = get_corpus_stats()
    if not stats.get("available"):
        print("❌ Database tidak tersedia.")
        print(f"   Jalankan: python3 tools/ingest_corpus.py")
        return

    print(f"\n{'='*60}")
    print("  ISLAMIAI CORPUS STATS")
    print(f"{'='*60}")
    print(f"  Kitab       : {stats.get('books', 0)}")
    print(f"  Passages    : {stats.get('passages', 0):,}")
    print(f"  Total chars : {stats.get('total_chars', 0):,}")

    print(f"\n  By Category:")
    for cat, cnt in stats.get("by_category", {}).items():
        print(f"    {cat:<18} {cnt:>8,} passages")

    print(f"\n  By Authority Level:")
    level_labels = {
        1: "Qawl Imam",
        2: "Qawl Ashhab",
        3: "Mu'tamad",
        4: "Syarh Mu'tamad",
        5: "Tafsir & Qawa'id",
    }
    for lvl, cnt in sorted(stats.get("by_authority", {}).items()):
        label = level_labels.get(int(lvl), f"Level {lvl}")
        print(f"    Level {lvl} ({label:<18}) {cnt:>7,} passages")

    print(f"\n  Kitab detail:")
    for book in stats.get("books_detail", []):
        print(f"    [{book['authority_level']}] {book['slug']:<28} "
              f"{book['total_passages']:>6} passages — {book['name_id']}")
    print(f"{'='*60}\n")


def _demo_search(query: str, limit: int = 3):
    """Demo pencarian ke stdout."""
    print(f"\n🔍 Query: '{query}'")
    print(f"   FTS5 expanded: '{_build_fts_query(query)}'")
    results = search_kitab(query, limit=limit)
    if not results:
        print("   Tidak ada hasil.")
        return
    for i, r in enumerate(results, 1):
        print(f"\n  [{i}] {r['book_name_id']} (Level {r['authority_level']})")
        print(f"       Bab : {r['chapter_title']}")
        preview = r['arabic_text'][:120].replace('\n', ' ')
        print(f"       Teks: {preview}...")
        print(f"       Rank: {r['rank']:.4f}")


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Test Layer 4 db_retrieval.py"
    )
    parser.add_argument("--stats",  action="store_true",
                        help="Tampilkan statistik corpus")
    parser.add_argument("--search", nargs="+",
                        help="Cari topik (bisa bahasa Indonesia atau Arab)")
    parser.add_argument("--db", default=_DB_PATH,
                        help=f"Path ke database (default: {_DB_PATH})")
    parser.add_argument("--limit", type=int, default=3,
                        help="Jumlah hasil per query (default: 3)")
    args = parser.parse_args()

    if not args.stats and not args.search:
        parser.print_help()
        print(f"\nDB path: {_DB_PATH}")
        print(f"DB available: {is_db_available()}")
    else:
        if args.stats:
            _print_stats()
        if args.search:
            for q in args.search:
                _demo_search(q, args.limit)
