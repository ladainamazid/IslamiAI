"""
download_30_kitab.py — IslamiAI Shamela Downloader
═══════════════════════════════════════════════════
30 kitab korpus IslamiAI dari Shamela.ws — semua memiliki ID.

  GRUP 1 (24) → Sudah diunduh, SKIP instan
  GRUP 2  (1) → Kecil, selesai dalam 1 run
  GRUP 3  (5) → Besar, butuh beberapa run (cache checkpoint aktif)

Prasyarat (satu kali):
  python3 apply_shamela_patch.py

Cara pakai:
  cd /home/muhammad/IslamiAI/IslamiAIProject
  python3 tools/download_29_kitab.py

Jalankan berulang jika timeout — cache menyimpan progress per halaman.
═══════════════════════════════════════════════════
"""

import json, logging, os, re, subprocess, sys, time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# ── Path Setup ──────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CORPUS_DIR  = PROJECT_DIR / "corpus"
EPUB_DIR    = CORPUS_DIR  / "epub"
STATE_FILE  = CORPUS_DIR  / "download_state.json"

CORPUS_DIR.mkdir(parents=True, exist_ok=True)
EPUB_DIR.mkdir(parents=True, exist_ok=True)

# Fix PATH untuk ~/.local/bin
LOCAL_BIN = Path.home() / ".local" / "bin"
if str(LOCAL_BIN) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str(LOCAL_BIN) + ":" + os.environ.get("PATH", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(CORPUS_DIR / "download.log", encoding="utf-8"),
    ],
)
log = logging.getLogger()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9",
}

# ── Konfigurasi ─────────────────────────────────────────────────────────────
DOWNLOAD_TIMEOUT  = 600   # 10 menit per kitab per run
MAX_TIMEOUT_SKIP  = 8     # Skip otomatis hanya jika timeout ≥ 8× (naik dari 2)
                          # Dengan cache shamela2epub: setiap run menyimpan
                          # ~12.000 halaman. 8 run = ~96.000 halaman (cukup
                          # untuk kitab paling besar sekalipun).
MAX_CONN_RETRIES  = 2     # Retry untuk connection/exit error (total = 3 percobaan)
MIN_VALID_SIZE_KB = 5     # File < 5 KB dianggap parsial/corrupt

# ── Riwayat timeout dari run-run sebelumnya ─────────────────────────────────
# Mencegah pemborosan 10 menit pada kitab yang belum mulai.
# Catatan: dengan patch shamela2epub, timeout ≠ gagal total — hanyalah
# checkpoint. PRE_TIMEOUT_HISTORY diturunkan agar kitab mendapat lebih
# banyak kesempatan via cache.
PRE_TIMEOUT_HISTORY = {
    "al_mawardi_nukat_uyun"    : 1,
    "nihayat_al_matlab_juwaini": 1,
    "ibn_ashur_tahrir_tanwir"  : 0,
}

# Reset state untuk kitab yang ID-nya berubah sejak run sebelumnya
RESET_TIMEOUT_KEYS = [
    "fath_al_aziz_rafii",
    "al_iqna_shirbini",
]

# ══════════════════════════════════════════════════════════════════════════════
# REGISTRY 30 KITAB — semua memiliki ID Shamela.ws
#
#   GRUP 1 (24) → Sudah terunduh — SKIP instan
#   GRUP 2  (1) → Perlu diunduh, kecil/menengah
#   GRUP 3  (5) → Perlu diunduh, besar (beberapa run via cache)
#
# Jalankan script berulang sampai semua ✅.
# ══════════════════════════════════════════════════════════════════════════════
KITAB = [

    # ═══════════════════════════════════════════════════════════════════════════
    # GRUP 1 — Sudah diunduh (24 kitab) — SKIP instan
    # ═══════════════════════════════════════════════════════════════════════════

    # ─── Tafsir Ahkam ───────────────────────────────────────────────────────
    {"key": "al_kiya_harrasi_ahkam_quran",
     "label": "Ahkam al-Quran — Al-Kiya al-Harrasi",
     "id": 23582,  # ✅
     "note": "",
     "author": "الهراسي", "blok": "tafsir_ahkam"},

    {"key": "al_baihaqi_ahkam_quran_syafii",
     "label": "Ahkam al-Quran al-Syafi'i — Al-Baihaqi (ت الشوامي)",
     "id": 92,     # ✅
     "note": "Edisi alternatif tahqiq Abd al-Khaliq: ID 3328",
     "author": "البيهقي", "blok": "tafsir_ahkam"},

    {"key": "al_qurtubi_jami_ahkam_quran",
     "label": "Al-Jami' li Ahkam al-Quran — Al-Qurtubi",
     "id": 20855,  # ✅
     "note": "",
     "author": "القرطبي", "blok": "tafsir_ahkam"},

    {"key": "al_jassas_ahkam_quran",
     "label": "Ahkam al-Quran — Al-Jassas",
     "id": 7370,   # ✅
     "note": "",
     "author": "الجصاص", "blok": "tafsir_ahkam"},

    {"key": "al_baghawi_maalim_tanzil",
     "label": "Ma'alim al-Tanzil — Al-Baghawi (Dar Taybah, 8 jilid)",
     "id": 41,     # ✅
     "note": "Edisi alternatif Dar Ihya al-Turath: ID 12217",
     "author": "البغوي", "blok": "tafsir_ahkam"},

    {"key": "ibn_kathir_tafsir_quran_azhim",
     "label": "Tafsir al-Quran al-Azhim — Ibn Kathir (ط السلامة)",
     "id": 8473,   # ✅
     "note": "",
     "author": "ابن كثير", "blok": "tafsir_ahkam"},

    {"key": "ibn_kathir_irsyad_faqih",
     "label": "Irshad al-Faqih ila Ma'rifat Adillat al-Tanbih — Ibn Kathir",
     "id": 260,    # ✅
     "note": "Kitab dalil fiqh Shafi'i. Relevan untuk field illat & cara_pendalilan.",
     "author": "ابن كثير", "blok": "tafsir_ahkam"},

    # ─── Fiqh Syafi'i — Qawl Imam ───────────────────────────────────────────
    {"key": "al_umm_syafii",
     "label": "Al-Umm — Al-Syafi'i",
     "id": 1655,   # ✅
     "note": "",
     "author": "الشافعي", "blok": "fiqh_syafii"},

    {"key": "al_risalah_syafii",
     "label": "Al-Risalah — Al-Syafi'i",
     "id": 8180,   # ✅
     "note": "",
     "author": "الشافعي", "blok": "fiqh_syafii"},

    {"key": "mukhtasar_al_muzani",
     "label": "Mukhtasar al-Muzani (ت الداغستاني)",
     "id": 914,    # ✅
     "note": "Edisi lain (ط الفكر, bersama al-Umm): ID 1661",
     "author": "المزني", "blok": "fiqh_syafii"},

    # ─── Fiqh Syafi'i — Mu'tamad ────────────────────────────────────────────
    {"key": "minhaj_al_talibin_nawawi",
     "label": "Minhaj al-Talibin — Al-Nawawi",
     "id": 12096,  # ✅
     "note": "",
     "author": "النووي", "blok": "fiqh_syafii"},

    {"key": "rawdhat_al_talibin_nawawi",
     "label": "Rawdhat al-Talibin — Al-Nawawi",
     "id": 499,    # ✅
     "note": "",
     "author": "النووي", "blok": "fiqh_syafii"},

    {"key": "al_majmu_syarh_muhadhdhab_nawawi",
     "label": "Al-Majmu' Sharh al-Muhadhdhab — Al-Nawawi",
     "id": 2186,   # ✅
     "note": "",
     "author": "النووي", "blok": "fiqh_syafii"},

    # ─── Fiqh Syafi'i — Sharh Mu'tamad ─────────────────────────────────────
    {"key": "tuhfat_al_muhtaj_ibn_hajar",
     "label": "Tuhfat al-Muhtaj — Ibn Hajar al-Haytami",
     "id": 9059,   # ✅
     "note": "",
     "author": "الهيتمي", "blok": "fiqh_syafii"},

    {"key": "nihayat_al_muhtaj_al_ramli",
     "label": "Nihayat al-Muhtaj — Al-Ramli",
     "id": 3565,   # ✅
     "note": "",
     "author": "الرملي", "blok": "fiqh_syafii"},

    {"key": "mughni_al_muhtaj_syarbini",
     "label": "Mughni al-Muhtaj ila Ma'rifat Ma'ani Alfazh al-Minhaj — Al-Syarbini",
     "id": 11444,  # ✅
     "note": "",
     "author": "الشربيني", "blok": "fiqh_syafii"},

    {"key": "asna_al_matalib_zakariyya",
     "label": "Asna al-Matalib — Zakariyya al-Ansari",
     "id": 11468,  # ✅
     "note": "",
     "author": "زكريا الأنصاري", "blok": "fiqh_syafii"},

    {"key": "al_hawi_al_kabir_mawardi",
     "label": "Al-Hawi al-Kabir — Al-Mawardi",
     "id": 6157,   # ✅
     "note": "",
     "author": "الماوردي", "blok": "fiqh_syafii"},

    # ─── Fiqh Syafi'i — Rantai Pesantren ────────────────────────────────────
    {"key": "fath_al_qarib_ibn_qasim",
     "label": "Fath al-Qarib al-Mujib — Ibn Qasim al-Ghazzi",
     "id": 35120,  # ✅
     "note": "",
     "author": "ابن قاسم الغزي", "blok": "fiqh_syafii"},

    {"key": "fath_al_muin_malibari",
     "label": "Fath al-Mu'in bi Syarh Qurrat al-'Ayn — Al-Malibari",
     "id": 11327,  # ✅
     "note": "I'anat al-Talibin (hasyiyah atasnya): ID 963.",
     "author": "الملبار", "blok": "fiqh_syafii"},

    {"key": "ianat_al_talibin_bakri",
     "label": "I'anat al-Talibin — Al-Bakri al-Dimyati",
     "id": 963,    # ✅
     "note": "",
     "author": "البكري", "blok": "fiqh_syafii"},

    # ─── Qawa'id Fiqhiyyah ───────────────────────────────────────────────────
    {"key": "al_asybah_wa_nazair_suyuthi",
     "label": "Al-Ashbah wa'l-Nazha'ir — Al-Suyuthi",
     "id": 21719,  # ✅
     "note": "",
     "author": "السيوطي", "blok": "qawaid"},

    {"key": "al_mantsur_qawaid_zarkasyi",
     "label": "Al-Mantsur fi al-Qawa'id al-Fiqhiyyah — Al-Zarkasyi",
     "id": 21592,  # ✅
     "note": "",
     "author": "الزركشي", "blok": "qawaid"},

    {"key": "qawaid_al_ahkam_izz_abd_salam",
     "label": "Qawa'id al-Ahkam fi Masalih al-Anam — Al-'Izz ibn Abd al-Salam",
     "id": 8608,   # ✅
     "note": "",
     "author": "العز بن عبد السلام", "blok": "qawaid"},

    # ═══════════════════════════════════════════════════════════════════════════
    # GRUP 2 — Perlu diunduh, kecil/menengah (2 kitab)
    # Estimasi selesai dalam 1 run (≤ 10 menit)
    # ═══════════════════════════════════════════════════════════════════════════

    # ─── Fiqh Syafi'i — Rantai Pesantren (sharh matn Abi Shuja') ────────────
    {"key": "al_iqna_shirbini",
     "label": "Al-Iqna' fi Hall Alfadh Abi Shuja' — Al-Khatib Al-Shirbini",
     "id": 6121,   # ✅
     "note": "Sharh matn Ghayat al-Ikhtishar (Abi Shuja'). "
             "Teks primer pesantren Indonesia. Pengarang sama dengan Mughni al-Muhtaj.",
     "author": "الشربيني", "blok": "fiqh_syafii"},

    # ═══════════════════════════════════════════════════════════════════════════
    # GRUP 3 — Kitab besar, butuh beberapa run (4 kitab + 1 baru)
    # Dengan patch shamela2epub: cache halaman tersimpan per-disk.
    # Setiap run menambah ~12.000 halaman. Jalankan berulang sampai ✅.
    # ═══════════════════════════════════════════════════════════════════════════

    # ─── Fiqh Syafi'i — Qawl Ashhab (baru, mengisi gap abad 5-6H) ───────────
    {"key": "al_bayan_imrani",
     "label": "Al-Bayan fi Madhhab al-Imam al-Shafi'i — Al-Imrani al-Yamani",
     "id": 21721,  # ✅
     "note": "Abu al-Husayn Yahya al-Imrani (d. 558H), murid Al-Baghawi. "
             "13 jilid, Dar al-Minhaj. Qawl ashhab, antara Al-Hawi (450H) dan Minhaj (676H).",
     "author": "العمراني اليمني", "blok": "fiqh_syafii"},

    {"key": "fath_al_aziz_rafii",
     "label": "Fath al-Aziz (al-Sharh al-Kabir) — Al-Rafi'i (DKI)",
     "id": 13577,  # ✅
     "note": "Al-Rafi'i (d. 623H). Edisi kritis DKI, 13 jilid. Qawl ashhab.",
     "author": "الرافعي", "blok": "fiqh_syafii"},

    {"key": "nihayat_al_matlab_juwaini",
     "label": "Nihayat al-Matlab fi Dirayat al-Madhhab — Al-Juwayni",
     "id": 9851,   # ✅
     "note": "Dar al-Minhaj, tahqiq Abd al-Azim al-Dib. 10.768 halaman.",
     "author": "الجويني", "blok": "fiqh_syafii"},

    {"key": "al_mawardi_nukat_uyun",
     "label": "Al-Nukat wa'l-Uyun (Tafsir al-Mawardi) — Al-Mawardi",
     "id": 8346,   # ✅
     "note": "4.439 halaman.",
     "author": "الماوردي", "blok": "tafsir_ahkam"},

    {"key": "ibn_ashur_tahrir_tanwir",
     "label": "Al-Tahrir wa'l-Tanwir — Ibn 'Ashur",
     "id": 9776,   # ✅
     "note": "Dar al-Tunisiyyah, 30 jilid. Butuh ~4 run berurutan via cache.",
     "author": "ابن عاشور", "blok": "tafsir_ahkam"},
]

TOTAL = len(KITAB)  # 30 (semua memiliki ID Shamela.ws)


# ── State Management ─────────────────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"found_ids": {}, "downloaded": {}}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ── Utilitas ─────────────────────────────────────────────────────────────────

def _delete_if_exists(path):
    """Hapus file jika ada; abaikan error permission."""
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


# ── Download ─────────────────────────────────────────────────────────────────

def download_epub(book_id, output_path, timeout=DOWNLOAD_TIMEOUT):
    """
    Download satu kitab dari shamela.ws via shamela2epub.

    Dengan patch shamela2epub aktif: cache halaman tersimpan ke disk,
    sehingga run berikutnya melanjutkan dari halaman terakhir yang berhasil.

    Returns:
        (True,  "ok")      — berhasil, EPUB tersimpan
        (False, "timeout") — habis waktu (cache sudah menyimpan progress)
        (False, "failed")  — gagal setelah semua retry connection error
        (False, "error")   — exception tak terduga
    """
    url = f"https://shamela.ws/book/{book_id}"
    log.info("    ⬇  %s", url)

    for attempt in range(1, MAX_CONN_RETRIES + 2):  # percobaan 1, 2, 3
        if attempt > 1:
            wait = 30 * (attempt - 1)  # 30s, 60s
            log.info("    ↻  Retry %d/%d — tunggu %ds...",
                     attempt - 1, MAX_CONN_RETRIES, wait)
            time.sleep(wait)

        # Bersihkan file parsial/kecil sebelum tiap percobaan
        if output_path.exists():
            sz = output_path.stat().st_size
            if sz < MIN_VALID_SIZE_KB * 1024:
                _delete_if_exists(output_path)
                log.info("    🗑  File parsial (%d B) dihapus sebelum percobaan %d",
                         sz, attempt)

        try:
            r = subprocess.run(
                [sys.executable, "-m", "shamela2epub", "download", url,
                 "-o", str(output_path)],
                capture_output=True, text=True, timeout=timeout,
            )

            if r.returncode == 0 and output_path.exists():
                size_kb = output_path.stat().st_size // 1024
                if size_kb < MIN_VALID_SIZE_KB:
                    _delete_if_exists(output_path)
                    log.warning("    ⚠  File terlalu kecil (%d KB) — retry...", size_kb)
                    continue
                log.info("    ✅ %s (%d KB)", output_path.name, size_kb)
                return True, "ok"

            # Connection / server error → retry
            err_raw = (r.stderr or r.stdout or "").strip()
            err_short = err_raw[:300] if err_raw else "(no output)"
            log.warning("    ⚠  exit %d (percobaan %d/%d): %s",
                        r.returncode, attempt, MAX_CONN_RETRIES + 1, err_short)
            _delete_if_exists(output_path)

        except subprocess.TimeoutExpired:
            log.warning(
                "    ⏰  Timeout setelah %ds — progress cache tersimpan, "
                "run berikutnya akan lanjut dari checkpoint", timeout
            )
            _delete_if_exists(output_path)
            return False, "timeout"

        except Exception as e:
            log.error("    ❌ Error tak terduga: %s", e)
            return False, "error"

    log.error("    ❌ Gagal setelah %d percobaan", MAX_CONN_RETRIES + 1)
    return False, "failed"


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    log.info("╔══════════════════════════════════════════════════════╗")
    log.info("║     IslamiAI — Download 30 Kitab dari Shamela.ws    ║")
    log.info("╚══════════════════════════════════════════════════════╝")
    log.info("  Output : %s", EPUB_DIR)
    log.info("  Timeout: %ds/run | Retry conn: %d× | Skip timeout: >=%d×",
             DOWNLOAD_TIMEOUT, MAX_CONN_RETRIES, MAX_TIMEOUT_SKIP)
    log.info("  Cache  : ~/.cache/shamela2epub/ (aktif jika patch diterapkan)\n")

    # Cek shamela2epub
    r = subprocess.run([sys.executable, "-m", "shamela2epub", "--help"],
                       capture_output=True, timeout=10)
    if r.returncode != 0:
        log.error("shamela2epub tidak ditemukan.")
        log.error("Jalankan: pip install shamela2epub --break-system-packages")
        sys.exit(1)

    state = load_state()

    # ── Migrasi: terapkan riwayat timeout dari PRE_TIMEOUT_HISTORY ───────────
    migrated = False
    for k in KITAB:
        pre_tc = PRE_TIMEOUT_HISTORY.get(k["key"], 0)
        if pre_tc <= 0:
            continue
        dl = state["downloaded"].get(k["key"], {})
        if dl.get("timeout_count", 0) < pre_tc:
            if k["key"] not in state["downloaded"]:
                state["downloaded"][k["key"]] = {
                    "id": k["id"], "label": k["label"], "blok": k["blok"],
                    "success": False, "reason": "timeout", "timeout_count": pre_tc,
                }
            else:
                state["downloaded"][k["key"]]["timeout_count"] = pre_tc
            migrated = True
    if migrated:
        save_state(state)
        log.info("  ℹ  State dimigrasikan dari PRE_TIMEOUT_HISTORY.")

    # ── Reset state untuk kitab yang ID-nya diganti ───────────────────────────
    reset_done = False
    for reset_key in RESET_TIMEOUT_KEYS:
        dl = state["downloaded"].get(reset_key, {})
        # Reset hanya jika ID di state berbeda dari ID di KITAB (ID berubah)
        kitab_id = next((k["id"] for k in KITAB if k["key"] == reset_key), None)
        if dl.get("id") and dl["id"] != kitab_id and not dl.get("success"):
            old_id = dl["id"]
            state["downloaded"][reset_key] = {
                **dl,
                "id": kitab_id, "timeout_count": 0, "success": False, "reason": "",
            }
            log.info("  ♻  Reset state '%s': ID %s → %s (timeout_count: %d → 0)",
                     reset_key, old_id, kitab_id, dl.get("timeout_count", 0))
            reset_done = True
    if reset_done:
        save_state(state)

    # ── Auto-detect: epub valid di disk tapi belum tercatat di state ─────────
    detected = 0
    for k in KITAB:
        epub_path = EPUB_DIR / f"{k['key']}.epub"
        if epub_path.exists() and epub_path.stat().st_size >= MIN_VALID_SIZE_KB * 1024:
            dl = state["downloaded"].get(k["key"], {})
            if not dl.get("success"):
                state["downloaded"][k["key"]] = {
                    **dl,
                    "id": k["id"], "label": k["label"], "blok": k["blok"],
                    "success": True, "reason": "ok",
                    "timeout_count": dl.get("timeout_count", 0),
                }
                log.info("  📂  Auto-detect: %s (%d KB)",
                         k["label"], epub_path.stat().st_size // 1024)
                detected += 1
    if detected:
        save_state(state)
        log.info("")

    log.info("  Total kitab: %d (semua memiliki ID Shamela.ws)", TOTAL)

    # Hitung kitab yang akan di-skip karena timeout berulang
    will_skip_timeout = [
        k for k in KITAB
        if state["downloaded"].get(k["key"], {}).get("timeout_count", 0) >= MAX_TIMEOUT_SKIP
        and not state["downloaded"].get(k["key"], {}).get("success")
    ]
    if will_skip_timeout:
        log.info("  Auto-skip (timeout ≥%d×): %d kitab",
                 MAX_TIMEOUT_SKIP, len(will_skip_timeout))
    log.info("")
    log.info("─── Memulai proses download ───\n")

    new_count   = 0
    skip_count  = 0
    failed_list = []
    manual_list = []

    for i, k in enumerate(KITAB, 1):
        epub_path = EPUB_DIR / f"{k['key']}.epub"
        dl = state["downloaded"].get(k["key"], {})
        timeout_count = dl.get("timeout_count", 0)

        # ── Sudah berhasil (state + file valid) ───────────────────────────────
        if dl.get("success") and epub_path.exists() \
                and epub_path.stat().st_size >= MIN_VALID_SIZE_KB * 1024:
            log.info("[%2d/%d] SKIP ✓ (%d KB): %s",
                     i, TOTAL, epub_path.stat().st_size // 1024, k["label"])
            skip_count += 1
            continue  # tidak tidur setelah SKIP

        # ── Sudah timeout terlalu banyak → skip ───────────────────────────────
        if timeout_count >= MAX_TIMEOUT_SKIP:
            log.info("[%2d/%d] SKIP ⏰ (timeout %d× — unduh manual): %s",
                     i, TOTAL, timeout_count, k["label"])
            manual_list.append(k)
            continue

        # ── Proses download ───────────────────────────────────────────────────
        log.info("[%2d/%d] %s  (ID: %d)", i, TOTAL, k["label"], k["id"])
        if k["note"]:
            log.info("        ℹ  %s", k["note"][:130])

        success, reason = download_epub(k["id"], epub_path)

        new_timeout_count = timeout_count + (1 if reason == "timeout" else 0)
        state["downloaded"][k["key"]] = {
            "id"           : k["id"],
            "label"        : k["label"],
            "blok"         : k["blok"],
            "success"      : success,
            "reason"       : reason,
            "timeout_count": new_timeout_count,
        }
        save_state(state)

        if success:
            new_count += 1
            time.sleep(3)
        else:
            failed_list.append((k["label"], reason, new_timeout_count))
            time.sleep(12)

    # ── Ringkasan ─────────────────────────────────────────────────────────────
    log.info("\n═══════════════════════════════════════════════════════")
    log.info("  RINGKASAN AKHIR")
    log.info("═══════════════════════════════════════════════════════")
    log.info("  Total kitab        : %d", TOTAL)
    log.info("  Baru diunduh       : %d", new_count)
    log.info("  Sudah ada (skip)   : %d", skip_count)
    log.info("  Gagal unduh        : %d", len(failed_list))

    if failed_list:
        log.info("\n  Gagal didownload:")
        for lbl, rsn, tc in failed_list:
            if rsn == "timeout":
                if tc >= MAX_TIMEOUT_SKIP:
                    note = f"⏰ Timeout — batas {MAX_TIMEOUT_SKIP}× tercapai, unduh manual"
                else:
                    note = f"⏰ Timeout ({tc}/{MAX_TIMEOUT_SKIP}×) — jalankan lagi, cache melanjutkan"
            elif rsn == "failed":
                note = "❌ Gagal setelah semua retry connection"
            else:
                note = f"❌ {rsn}"
            log.warning("    ✗ %s — %s", lbl, note)

    if manual_list:
        log.info("\n  ⚠  Perlu unduh manual (timeout berulang):")
        for k in manual_list:
            tc = state["downloaded"].get(k["key"], {}).get("timeout_count", 0)
            log.warning("    • %s (ID: %s, timeout: %d×)", k["label"], k["id"], tc)
            if k["note"]:
                log.info("      → %s", k["note"][:130])

    epub_count = len(list(EPUB_DIR.glob("*.epub")))
    total_ok = new_count + skip_count
    log.info("\n  Total EPUB tersimpan : %d file", epub_count)
    log.info("  Progress kitab       : %d/%d (%.0f%%)",
             total_ok, TOTAL, total_ok / TOTAL * 100)
    log.info("  Folder               : %s", EPUB_DIR)

    if any(rsn == "timeout" for _, rsn, _ in failed_list):
        log.info("\n  ℹ  Ada kitab yang timeout — jalankan lagi untuk melanjutkan:")
        log.info("     python3 tools/download_29_kitab.py")

    if epub_count > 0 and not failed_list and not manual_list:
        log.info("\n  Semua kitab berhasil! Langkah berikutnya:")
        log.info("  → python3 tools/02_build_db.py")


if __name__ == "__main__":
    main()
