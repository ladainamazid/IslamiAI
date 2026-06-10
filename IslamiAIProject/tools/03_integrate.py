"""
03_integrate.py — Corpus Integration Validator
══════════════════════════════════════════════════════════════════
Dijalankan setelah 02_build_db.py selesai.

Yang dilakukan script ini:
  1. Verifikasi corpus DB valid dan bisa di-query
  2. Copy corpus_retrieval.py ke root project (jika belum ada)
  3. Patch retrieval.py untuk menambah Layer 4 corpus (non-destructive)
  4. Test end-to-end: pertanyaan → hasil dari corpus
  5. Print laporan integrasi lengkap

PRINSIP: Tidak ada file yang dihapus atau diubah secara destruktif.
Patch retrieval.py hanya menambahkan import dan dua baris kode.
Rollback tersedia jika diperlukan.
══════════════════════════════════════════════════════════════════
"""

import logging
import shutil
import sqlite3
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("shamela.integrator")

SCRIPT_DIR     = Path(__file__).parent
PROJECT_DIR    = SCRIPT_DIR.parent
CORPUS_DIR     = PROJECT_DIR / "corpus"
MASTER_DB      = CORPUS_DIR  / "shamela_corpus.db"
RETRIEVAL_FILE = PROJECT_DIR / "retrieval.py"
CORPUS_MOD_SRC = SCRIPT_DIR  / "corpus_retrieval.py"
CORPUS_MOD_DST = PROJECT_DIR / "corpus_retrieval.py"
BACKUP_FILE    = PROJECT_DIR / "retrieval.py.bak"


# ── Step 1: Verifikasi Corpus ──────────────────────────────────────────────────

def verify_corpus() -> dict:
    """Verifikasi corpus DB dan return statistik."""
    log.info("STEP 1: Verifikasi corpus DB...")

    if not MASTER_DB.exists():
        log.error("❌ Corpus DB tidak ditemukan: %s", MASTER_DB)
        log.error("   Jalankan dulu: python3 tools/02_build_db.py")
        return {}

    try:
        conn = sqlite3.connect(str(MASTER_DB))
        conn.row_factory = sqlite3.Row

        passages = conn.execute("SELECT COUNT(*) FROM passage").fetchone()[0]
        kitab    = conn.execute("SELECT COUNT(*) FROM kitab").fetchone()[0]

        # Test FTS5
        test = conn.execute(
            "SELECT COUNT(*) FROM passage_fts WHERE passage_fts MATCH 'طهارة'"
        ).fetchone()[0]

        # Per-blok breakdown
        breakdown = conn.execute(
            "SELECT blok, COUNT(*) as n FROM kitab GROUP BY blok"
        ).fetchall()

        conn.close()

        stats = {
            "passages": passages,
            "kitab":    kitab,
            "fts_test": test,
            "breakdown": {row["blok"]: row["n"] for row in breakdown},
        }

        log.info("  ✅ Corpus DB valid")
        log.info("     Kitab    : %d", kitab)
        log.info("     Passages : %d", passages)
        log.info("     FTS test : %d hasil untuk 'طهارة'", test)
        for blok, n in stats["breakdown"].items():
            log.info("     %-25s: %d kitab", blok, n)

        return stats

    except sqlite3.Error as e:
        log.error("❌ Error membaca corpus DB: %s", e)
        return {}


# ── Step 2: Copy corpus_retrieval.py ──────────────────────────────────────────

def deploy_corpus_module() -> bool:
    """Copy corpus_retrieval.py ke root project."""
    log.info("STEP 2: Deploy corpus_retrieval.py ke root project...")

    if not CORPUS_MOD_SRC.exists():
        log.error("❌ corpus_retrieval.py tidak ditemukan di: %s", CORPUS_MOD_SRC)
        return False

    if CORPUS_MOD_DST.exists():
        log.info("  ℹ️  corpus_retrieval.py sudah ada — overwrite.")

    shutil.copy2(str(CORPUS_MOD_SRC), str(CORPUS_MOD_DST))
    log.info("  ✅ Disalin ke: %s", CORPUS_MOD_DST)
    return True


# ── Step 3: Patch retrieval.py ─────────────────────────────────────────────────

PATCH_IMPORT = "from corpus_retrieval import search_corpus"

PATCH_LAYER4 = '''
    # ── Layer 4: Corpus Shamela (FTS5 dari 29 kitab klasik) ────────────────
    corpus_result = search_corpus(topic_lower, madhab)
    if corpus_result:
        return corpus_result
'''

PATCH_MARKER = "# [CORPUS_PATCH_APPLIED]"


def patch_retrieval_py() -> bool:
    """
    Tambahkan Layer 4 corpus ke retrieval.py secara non-destructif.

    Strategi:
    1. Backup retrieval.py → retrieval.py.bak
    2. Tambah import di bagian atas (setelah import yang sudah ada)
    3. Tambah Layer 4 sebelum 'return None' terakhir di retrieve_ruling()
    4. Jika sudah di-patch sebelumnya, skip.
    """
    log.info("STEP 3: Patch retrieval.py...")

    if not RETRIEVAL_FILE.exists():
        log.error("❌ retrieval.py tidak ditemukan: %s", RETRIEVAL_FILE)
        return False

    with open(RETRIEVAL_FILE, encoding="utf-8") as f:
        original = f.read()

    # Cek apakah sudah di-patch
    if PATCH_MARKER in original:
        log.info("  ℹ️  retrieval.py sudah di-patch sebelumnya — skip.")
        return True

    # Backup
    shutil.copy2(str(RETRIEVAL_FILE), str(BACKUP_FILE))
    log.info("  ✅ Backup: %s", BACKUP_FILE)

    patched = original

    # Tambah import (setelah baris 'from islamic_data import ...')
    import_anchor = "from islamic_data import"
    if import_anchor in patched and PATCH_IMPORT not in patched:
        lines = patched.split("\n")
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip().startswith(import_anchor):
                new_lines.append("")
                new_lines.append("# Corpus Shamela — Layer 4 retrieval")
                new_lines.append("# Aktif hanya jika corpus/shamela_corpus.db tersedia")
                new_lines.append(PATCH_IMPORT)
        patched = "\n".join(new_lines)
        log.info("  ✅ Import ditambahkan")
    else:
        log.warning("  ⚠️  Tidak bisa menemukan anchor import — import manual diperlukan")

    # Tambah Layer 4 sebelum 'return None' terakhir di fungsi retrieve_ruling()
    # Cari baris terakhir 'return None' yang ada di dalam fungsi
    last_return_none = patched.rfind(
        'logger.info("Topik \'%s\' tidak ditemukan di static maupun cache.", topic_lower)\n    return None'
    )

    if last_return_none != -1:
        insert_point = last_return_none
        patched = (
            patched[:insert_point]
            + PATCH_LAYER4
            + "\n"
            + patched[insert_point:]
        )
        log.info("  ✅ Layer 4 corpus ditambahkan")
    else:
        # Fallback: cari pola lebih sederhana
        simple_anchor = "\n    return None\n"
        last_pos = patched.rfind(simple_anchor)
        if last_pos != -1:
            patched = (
                patched[:last_pos]
                + PATCH_LAYER4
                + patched[last_pos:]
            )
            log.info("  ✅ Layer 4 ditambahkan (fallback mode)")
        else:
            log.warning("  ⚠️  Tidak bisa menemukan titik sisip — patch manual diperlukan")
            log.warning("     Tambahkan di retrieval.py sebelum 'return None' terakhir:")
            log.warning("     %s", PATCH_LAYER4.strip())

    # Tambah marker
    patched = patched + f"\n\n{PATCH_MARKER}\n"

    # Tulis hasil patch
    with open(RETRIEVAL_FILE, "w", encoding="utf-8") as f:
        f.write(patched)

    log.info("  ✅ retrieval.py berhasil di-patch")
    log.info("     Rollback: cp %s %s", BACKUP_FILE, RETRIEVAL_FILE)
    return True


# ── Step 4: End-to-End Test ────────────────────────────────────────────────────

def run_integration_test() -> bool:
    """Test bahwa corpus bisa di-query via corpus_retrieval.py."""
    log.info("STEP 4: Integration test...")

    try:
        # Import langsung dari tools/ (corpus_retrieval ada di project root)
        sys.path.insert(0, str(PROJECT_DIR))
        from corpus_retrieval import search_corpus, get_corpus_stats

        stats = get_corpus_stats()
        if not stats["available"]:
            log.warning("  ⚠️  Corpus belum tersedia untuk test")
            return False

        test_topics = [
            ("thaharah_wudhu",   "وضوء طهارة"),
            ("zakat",            "zakat"),
            ("shalat_lima_waktu", "shalat"),
            ("nikah",            "nikah"),
        ]

        passed = 0
        for topic, hint in test_topics:
            result = search_corpus(topic)
            if result and result.get("corpus_passages"):
                log.info(
                    "  ✅ %-25s → %d passages dari '%s'",
                    topic,
                    len(result["corpus_passages"]),
                    result["corpus_passages"][0]["kitab"][:40],
                )
                passed += 1
            else:
                log.warning("  ⚠️  %-25s → tidak ditemukan", topic)

        log.info("  Test: %d/%d lulus", passed, len(test_topics))
        return passed > 0

    except ImportError as e:
        log.error("  ❌ Import error: %s", e)
        return False
    except Exception as e:
        log.error("  ❌ Test error: %s", e)
        return False


# ── Step 5: Laporan ────────────────────────────────────────────────────────────

def print_integration_report(stats: dict, test_ok: bool) -> None:
    """Print laporan lengkap dan instruksi selanjutnya."""
    log.info("\n" + "═" * 60)
    log.info("LAPORAN INTEGRASI IslamiAI × Shamela Corpus")
    log.info("═" * 60)

    if stats:
        log.info("Corpus     : ✅ %d passages dari %d kitab",
                 stats["passages"], stats["kitab"])
    else:
        log.info("Corpus     : ❌ Tidak tersedia")

    log.info("Module     : %s", "✅ Terpasang" if CORPUS_MOD_DST.exists() else "❌ Tidak ada")
    log.info("retrieval.py: %s", "✅ Di-patch" if BACKUP_FILE.exists() else "⚠️  Perlu manual")
    log.info("Test e2e   : %s", "✅ Lulus" if test_ok else "⚠️  Periksa log")

    log.info("\n" + "─" * 60)
    log.info("CARA KERJA SETELAH INTEGRASI:")
    log.info("─" * 60)
    log.info("""
  Ketika user bertanya tentang topik fiqh:

  1. parse_user_query()   → 'thaharah_wudhu'
  2. retrieve_ruling()    → cek islamic_data.py (Layer 1-2)
  3. retrieve_ruling()    → cek data_cache.json (Layer 3)
  4. search_corpus()      → FTS5 search di 29 kitab Shamela (Layer 4) ← BARU
  5. gate_answer()        → validasi confidence
  6. format_answer()      → format jawaban

  Semua jawaban dari corpus ditandai:
    _source = "corpus_shamela"
    _needs_review = True  (untuk validasi ulama)
    confidence = "low" atau "medium"
""")

    log.info("─" * 60)
    log.info("FILE YANG DIBUAT:")
    log.info("─" * 60)
    log.info("  corpus/shamela_corpus.db   ← database master")
    log.info("  corpus/db/*.db             ← database individual per kitab")
    log.info("  corpus/epub/*.epub         ← file sumber EPUB")
    log.info("  corpus_retrieval.py        ← modul retrieval baru")
    log.info("  retrieval.py.bak           ← backup retrieval.py asli")

    log.info("\n" + "─" * 60)
    log.info("LANGKAH BERIKUTNYA:")
    log.info("─" * 60)
    log.info("  1. Test manual: python3 corpus_retrieval.py")
    log.info("  2. Jalankan server: python3 app.py")
    log.info("  3. Tanya tentang: thaharah, zakat, nikah, waris")
    log.info("  4. Periksa log — respons dari corpus akan ada [corpus_shamela]")
    log.info("  5. Validasi jawaban dengan ustaz/ulama sebelum publik")


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    log.info("IslamiAI — Corpus Integration")
    log.info("Project: %s\n", PROJECT_DIR)

    stats   = verify_corpus()
    mod_ok  = deploy_corpus_module()
    patch_ok = patch_retrieval_py()
    test_ok  = run_integration_test() if stats else False

    print_integration_report(stats, test_ok)

    if stats and mod_ok:
        log.info("\n✅ Integrasi selesai. Corpus siap digunakan.")
        return 0
    else:
        log.warning("\n⚠️  Integrasi partial. Periksa log di atas.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
