"""
01_download.py — Shamela Corpus Downloader
══════════════════════════════════════════════════════════════════
Mendownload 29 kitab dari shamela.ws dalam format EPUB.
Dijalankan pertama kali: python3 tools/01_download.py

Output: corpus/epub/{nama_kitab}.epub (satu file per kitab)

Kitab yang sudah punya ID langsung didownload.
Kitab yang belum punya ID dicari otomatis via shamela.ws.
Semua progress disimpan di corpus/download_state.json
sehingga jika gagal di tengah, bisa dilanjut tanpa ulang dari awal.
══════════════════════════════════════════════════════════════════
"""

import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Konfigurasi Path ───────────────────────────────────────────────────────────
# Script ini ada di IslamiAIProject/tools/01_download.py
# Semua output masuk ke IslamiAIProject/corpus/
SCRIPT_DIR   = Path(__file__).parent
PROJECT_DIR  = SCRIPT_DIR.parent
CORPUS_DIR   = PROJECT_DIR / "corpus"
EPUB_DIR     = CORPUS_DIR  / "epub"
STATE_FILE   = CORPUS_DIR  / "download_state.json"

EPUB_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(CORPUS_DIR / "download.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("shamela.downloader")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.9",
    "Referer": "https://shamela.ws/",
}

# ── Registry 29 Kitab ──────────────────────────────────────────────────────────
# Format: "key": {"id": int|None, "search": str, "blok": str, "level": str}
# id=None  → akan dicari otomatis dari shamela.ws
# id=int   → langsung download

KITAB_REGISTRY = {

    # ── BLOK A: TAFSIR AHKAM ──────────────────────────────────────────────────

    "al_kiya_harrasi_ahkam_quran": {
        "id": None,
        "search": "أحكام القرآن للكيا الهراسي",
        "label": "Ahkam al-Quran — Al-Kiya al-Harrasi",
        "blok": "tafsir_ahkam",
        "level": "tafsir_primer_syafii",
        "madhab": "shafii",
    },
    "al_baihaqi_ahkam_quran_syafii": {
        "id": None,
        "search": "أحكام القرآن للشافعي البيهقي",
        "label": "Ahkam al-Quran al-Syafi'i — Al-Baihaqi",
        "blok": "tafsir_ahkam",
        "level": "tafsir_primer_syafii",
        "madhab": "shafii",
    },
    "al_qurtubi_jami_ahkam_quran": {
        "id": None,
        "search": "الجامع لأحكام القرآن القرطبي",
        "label": "Al-Jami' li Ahkam al-Quran — Al-Qurtubi",
        "blok": "tafsir_ahkam",
        "level": "tafsir_komparatif",
        "madhab": "maliki",
    },
    "al_jassas_ahkam_quran": {
        "id": None,
        "search": "أحكام القرآن الجصاص",
        "label": "Ahkam al-Quran — Al-Jassas",
        "blok": "tafsir_ahkam",
        "level": "tafsir_komparatif",
        "madhab": "hanafi",
    },
    "al_baghawi_maalim_tanzil": {
        "id": None,
        "search": "معالم التنزيل البغوي",
        "label": "Ma'alim al-Tanzil — Al-Baghawi",
        "blok": "tafsir_ahkam",
        "level": "tafsir_sekunder_syafii",
        "madhab": "shafii",
    },
    "ibn_kathir_tafsir_quran_azhim": {
        "id": None,
        "search": "تفسير القرآن العظيم ابن كثير",
        "label": "Tafsir al-Quran al-Azhim — Ibn Kathir",
        "blok": "tafsir_ahkam",
        "level": "tafsir_sekunder_syafii",
        "madhab": "shafii",
    },
    "al_mawardi_nukat_uyun": {
        "id": None,
        "search": "النكت والعيون الماوردي تفسير",
        "label": "Al-Nukat wa'l-Uyun — Al-Mawardi",
        "blok": "tafsir_ahkam",
        "level": "tafsir_sekunder_syafii",
        "madhab": "shafii",
    },
    "ibn_ashur_tahrir_tanwir": {
        "id": None,
        "search": "التحرير والتنوير ابن عاشور",
        "label": "Al-Tahrir wa'l-Tanwir — Ibn Ashur",
        "blok": "tafsir_ahkam",
        "level": "tafsir_maqasid",
        "madhab": "maliki",
    },

    # ── BLOK B: FIQH SYAFI'I — QAWL IMAM ─────────────────────────────────────

    "al_umm_syafii": {
        "id": None,
        "search": "كتاب الأم الشافعي",
        "label": "Al-Umm — Al-Syafi'i",
        "blok": "fiqh_syafii",
        "level": "qawl_imam",
        "madhab": "shafii",
    },
    "al_risalah_syafii": {
        "id": None,
        "search": "الرسالة الشافعي أصول الفقه",
        "label": "Al-Risalah — Al-Syafi'i",
        "blok": "fiqh_syafii",
        "level": "qawl_imam",
        "madhab": "shafii",
    },
    "mukhtasar_al_muzani": {
        "id": None,
        "search": "مختصر المزني فقه شافعي",
        "label": "Mukhtasar al-Muzani",
        "blok": "fiqh_syafii",
        "level": "qawl_ashhab",
        "madhab": "shafii",
    },

    # ── BLOK B: FIQH SYAFI'I — MU'TAMAD ──────────────────────────────────────

    "al_muharrar_rafii": {
        "id": None,
        "search": "المحرر الرافعي فقه شافعي",
        "label": "Al-Muharrar — Al-Rafi'i",
        "blok": "fiqh_syafii",
        "level": "pra_mutamad",
        "madhab": "shafii",
    },
    "minhaj_al_talibin_nawawi": {
        "id": None,
        "search": "منهاج الطالبين النووي",
        "label": "Minhaj al-Talibin — Al-Nawawi",
        "blok": "fiqh_syafii",
        "level": "mutamad_matn",
        "madhab": "shafii",
    },
    "rawdhat_al_talibin_nawawi": {
        "id": 499,       # ✅ CONFIRMED
        "search": "روضة الطالبين النووي",
        "label": "Rawdhat al-Talibin — Al-Nawawi",
        "blok": "fiqh_syafii",
        "level": "mutamad",
        "madhab": "shafii",
    },
    "al_majmu_syarh_muhadhdhab_nawawi": {
        "id": 2186,      # ✅ CONFIRMED
        "search": "المجموع شرح المهذب النووي",
        "label": "Al-Majmu' Sharh al-Muhadhdhab — Al-Nawawi",
        "blok": "fiqh_syafii",
        "level": "mutamad_ensiklopedis",
        "madhab": "shafii",
    },

    # ── BLOK B: FIQH SYAFI'I — SHARH MU'TAMAD ────────────────────────────────

    "tuhfat_al_muhtaj_ibn_hajar": {
        "id": 9059,      # ✅ CONFIRMED
        "search": "تحفة المحتاج ابن حجر الهيتمي",
        "label": "Tuhfat al-Muhtaj — Ibn Hajar al-Haytami",
        "blok": "fiqh_syafii",
        "level": "sharh_mutamad_hijaz",
        "madhab": "shafii",
    },
    "nihayat_al_muhtaj_al_ramli": {
        "id": 3565,      # ✅ CONFIRMED
        "search": "نهاية المحتاج الرملي",
        "label": "Nihayat al-Muhtaj — Al-Ramli",
        "blok": "fiqh_syafii",
        "level": "sharh_mutamad_mesir",
        "madhab": "shafii",
    },
    "mughni_al_muhtaj_syarbini": {
        "id": 11444,     # ✅ CONFIRMED
        "search": "مغني المحتاج الشربيني",
        "label": "Mughni al-Muhtaj — Al-Syarbini",
        "blok": "fiqh_syafii",
        "level": "sharh_mutamad_aksesibel",
        "madhab": "shafii",
    },
    "asna_al_matalib_zakariyya": {
        "id": None,
        "search": "أسنى المطالب زكريا الأنصاري",
        "label": "Asna al-Matalib — Zakariyya al-Ansari",
        "blok": "fiqh_syafii",
        "level": "sharh_mutamad",
        "madhab": "shafii",
    },

    # ── BLOK B: FIQH SYAFI'I — REFERENSI BESAR ───────────────────────────────

    "al_hawi_al_kabir_mawardi": {
        "id": None,
        "search": "الحاوي الكبير الماوردي فقه",
        "label": "Al-Hawi al-Kabir — Al-Mawardi",
        "blok": "fiqh_syafii",
        "level": "referensi_besar",
        "madhab": "shafii",
    },
    "nihayat_al_matlab_juwaini": {
        "id": None,
        "search": "نهاية المطلب الجويني إمام الحرمين",
        "label": "Nihayat al-Matlab — Al-Juwaini",
        "blok": "fiqh_syafii",
        "level": "referensi_besar",
        "madhab": "shafii",
    },

    # ── BLOK B: FIQH SYAFI'I — RANTAI PESANTREN ──────────────────────────────

    "fath_al_qarib_ibn_qasim": {
        "id": None,
        "search": "فتح القريب المجيب ابن قاسم الغزي",
        "label": "Fath al-Qarib — Ibn Qasim al-Ghazzi",
        "blok": "fiqh_syafii",
        "level": "pesantren",
        "madhab": "shafii",
    },
    "fath_al_muin_malibari": {
        "id": None,
        "search": "فتح المعين الملبار زين الدين",
        "label": "Fath al-Mu'in — Zayn al-Din al-Malibari",
        "blok": "fiqh_syafii",
        "level": "pesantren",
        "madhab": "shafii",
    },
    "ianat_al_talibin_bakri": {
        "id": None,
        "search": "إعانة الطالبين البكري الدمياطي",
        "label": "I'anat al-Talibin — Al-Bakri al-Dimyati",
        "blok": "fiqh_syafii",
        "level": "pesantren",
        "madhab": "shafii",
    },
    "bughyat_al_mustarsyidin_baalawi": {
        "id": None,
        "search": "بغية المسترشدين الباعلوي",
        "label": "Bughyat al-Mustarsyidin — Al-Ba'alawi",
        "blok": "fiqh_syafii",
        "level": "pesantren_nusantara",
        "madhab": "shafii",
    },
    "hasyiyat_al_bajuri": {
        "id": None,
        "search": "حاشية الباجوري على فتح القريب",
        "label": "Hasyiyat al-Bajuri — Al-Bajuri",
        "blok": "fiqh_syafii",
        "level": "pesantren",
        "madhab": "shafii",
    },

    # ── BLOK C: QAWA'ID FIQHIYYAH ─────────────────────────────────────────────

    "al_asybah_wa_nazair_suyuthi": {
        "id": None,
        "search": "الأشباه والنظائر السيوطي الشافعي",
        "label": "Al-Asybah wa'l-Nazha'ir — Al-Suyuthi",
        "blok": "qawaid",
        "level": "qawaid_syafii",
        "madhab": "shafii",
    },
    "al_mantsur_qawaid_zarkasyi": {
        "id": None,
        "search": "المنثور في القواعد الزركشي",
        "label": "Al-Mantsur fi al-Qawa'id — Al-Zarkasyi",
        "blok": "qawaid",
        "level": "qawaid_teknis",
        "madhab": "shafii",
    },
    "qawaid_al_ahkam_izz_abd_salam": {
        "id": None,
        "search": "قواعد الأحكام العز بن عبد السلام",
        "label": "Qawa'id al-Ahkam — Al-'Izz ibn Abd al-Salam",
        "blok": "qawaid",
        "level": "qawaid_maslahah",
        "madhab": "shafii",
    },
}


# ── Fungsi Utama ───────────────────────────────────────────────────────────────

def load_state() -> dict:
    """Baca state download yang sudah ada (resume jika gagal)."""
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def find_book_id_on_shamela(search_query: str) -> int | None:
    """
    Cari book ID di shamela.ws berdasarkan query Arab.
    Parsing halaman hasil pencarian untuk menemukan /book/{ID}.
    """
    try:
        resp = requests.get(
            "https://shamela.ws/search",
            params={"q": search_query},
            headers=HEADERS,
            timeout=20,
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Pattern 1: link langsung ke /book/ID
        for a in soup.find_all("a", href=True):
            m = re.match(r"^/book/(\d+)$", a["href"])
            if m:
                return int(m.group(1))

        # Pattern 2: data attribute atau JS variable
        for script in soup.find_all("script"):
            if script.string:
                m = re.search(r"book[_/](\d{3,6})", script.string)
                if m:
                    return int(m.group(1))

        return None

    except requests.RequestException as e:
        log.warning("Gagal mencari '%s': %s", search_query, e)
        return None


def verify_book_id(book_id: int) -> bool:
    """Verifikasi bahwa book ID valid di shamela.ws."""
    try:
        resp = requests.head(
            f"https://shamela.ws/book/{book_id}",
            headers=HEADERS,
            timeout=10,
            allow_redirects=True,
        )
        return resp.status_code == 200
    except requests.RequestException:
        return False


def download_epub(book_id: int, output_path: Path) -> bool:
    """
    Download satu kitab dari shamela.ws sebagai EPUB.
    Menggunakan shamela2epub (pip install shamela2epub).
    """
    url = f"https://shamela.ws/book/{book_id}"

    result = subprocess.run(
        [sys.executable, "-m", "shamela2epub", "download", url,
         "-o", str(output_path)],
        capture_output=True,
        text=True,
        timeout=300,  # 5 menit timeout per kitab
    )

    if result.returncode == 0 and output_path.exists():
        size_kb = output_path.stat().st_size // 1024
        log.info("✅ %s (%d KB)", output_path.name, size_kb)
        return True
    else:
        log.error("❌ Gagal download ID %d: %s", book_id, result.stderr[:200])
        return False


def resolve_all_ids(state: dict) -> None:
    """
    Pastikan semua kitab punya ID.
    Yang belum ada → cari di shamela.ws.
    """
    log.info("═" * 60)
    log.info("FASE 1: Resolusi ID Kitab")
    log.info("═" * 60)

    missing = [k for k, v in KITAB_REGISTRY.items()
               if v["id"] is None and k not in state.get("ids_resolved", {})]

    if not missing:
        log.info("Semua ID sudah tersedia.")
        return

    log.info("%d kitab perlu pencarian ID...", len(missing))
    ids_resolved = state.get("ids_resolved", {})

    for key in missing:
        info = KITAB_REGISTRY[key]
        log.info("Mencari: %s...", info["label"])

        found_id = find_book_id_on_shamela(info["search"])
        time.sleep(1.5)  # jangan flood server

        if found_id:
            log.info("  → Ditemukan ID: %d", found_id)
            ids_resolved[key] = found_id
            KITAB_REGISTRY[key]["id"] = found_id
        else:
            log.warning("  → Tidak ditemukan. Masukkan ID manual:")
            print(f"\n  Cari di: https://shamela.ws/search?q={info['search']}")
            print(f"  Kitab  : {info['label']}")
            manual = input("  Masukkan ID (Enter untuk skip): ").strip()
            if manual.isdigit():
                ids_resolved[key] = int(manual)
                KITAB_REGISTRY[key]["id"] = int(manual)
                log.info("  → ID manual: %d", int(manual))
            else:
                ids_resolved[key] = None
                log.warning("  → Skip %s", key)

        state["ids_resolved"] = ids_resolved
        save_state(state)

    # Update KITAB_REGISTRY dari state
    for key, book_id in ids_resolved.items():
        if key in KITAB_REGISTRY:
            KITAB_REGISTRY[key]["id"] = book_id


def download_all(state: dict) -> None:
    """Download semua kitab yang sudah punya ID."""
    log.info("═" * 60)
    log.info("FASE 2: Download Kitab")
    log.info("═" * 60)

    downloaded = state.get("downloaded", {})
    total = sum(1 for v in KITAB_REGISTRY.values() if v["id"])
    done  = 0

    for key, info in KITAB_REGISTRY.items():
        book_id = info.get("id")
        if not book_id:
            log.warning("SKIP %s — ID tidak ditemukan", key)
            continue

        epub_path = EPUB_DIR / f"{key}.epub"

        # Sudah didownload sebelumnya
        if key in downloaded and epub_path.exists():
            log.info("SKIP %s — sudah ada", key)
            done += 1
            continue

        done += 1
        log.info("[%d/%d] %s (ID: %d)", done, total, info["label"], book_id)

        success = download_epub(book_id, epub_path)

        downloaded[key] = {
            "id": book_id,
            "path": str(epub_path),
            "success": success,
            "blok": info["blok"],
            "level": info["level"],
            "madhab": info["madhab"],
        }
        state["downloaded"] = downloaded
        save_state(state)

        if success:
            time.sleep(2)  # jeda sopan antar request
        else:
            time.sleep(5)  # jeda lebih panjang jika error


def print_summary(state: dict) -> None:
    """Print ringkasan hasil download."""
    downloaded = state.get("downloaded", {})
    success = [k for k, v in downloaded.items() if v.get("success")]
    failed  = [k for k, v in downloaded.items() if not v.get("success")]

    log.info("═" * 60)
    log.info("RINGKASAN DOWNLOAD")
    log.info("═" * 60)
    log.info("✅ Berhasil: %d kitab", len(success))
    log.info("❌ Gagal   : %d kitab", len(failed))

    if failed:
        log.info("\nKitab yang gagal:")
        for k in failed:
            log.info("  - %s (ID: %s)", k, downloaded[k].get("id"))

    log.info("\nFile EPUB tersimpan di: %s", EPUB_DIR)
    log.info("Jalankan berikutnya  : python3 tools/02_build_db.py")


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("IslamiAI — Shamela Corpus Downloader")
    log.info("Project: %s", PROJECT_DIR)
    log.info("Output : %s", EPUB_DIR)

    # Cek shamela2epub tersedia
    try:
        subprocess.run(
            [sys.executable, "-m", "shamela2epub", "--help"],
            capture_output=True, timeout=10
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        log.error("shamela2epub tidak terinstall.")
        log.error("Jalankan: pip install shamela2epub --break-system-packages")
        sys.exit(1)

    state = load_state()

    # Muat ID yang sudah diketahui dari state sebelumnya
    for key, book_id in state.get("ids_resolved", {}).items():
        if key in KITAB_REGISTRY and book_id:
            KITAB_REGISTRY[key]["id"] = book_id

    resolve_all_ids(state)
    download_all(state)
    print_summary(state)
