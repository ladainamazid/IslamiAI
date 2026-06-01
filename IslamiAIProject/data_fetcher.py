"""
data_fetcher.py — External Data Acquisition untuk IslamiAI
─────────────────────────────────────────────────────────────────
PRINSIP DESAIN:
  1. islamic_data.py TIDAK disentuh sama sekali
  2. Module ini hanya mengambil data eksternal dan menyimpannya
     ke data_cache.json dalam format yang IDENTIK dengan schema
     islamic_data.py
  3. Jika fetch gagal, sistem tetap berjalan dari data statis
  4. Cache di-refresh secara on-demand atau via cron job

SUMBER DATA:
  - Al-Quran Cloud API (api.alquran.cloud) — gratis, no auth
  - Hadith API (api.hadith.gading.dev) — gratis, no auth
  - Quran.com API (api.quran.com) — gratis, rate-limited

CATATAN PENTING:
  Data yang masuk ke cache BELUM melalui validasi manual.
  confidence diset "medium" secara default sampai diverifikasi.
  Untuk data yang akan naik ke islamic_data.py (static), harus
  ada review manual oleh reviewer yang kompeten dalam bidang fiqh.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Gunakan requests jika ada, fallback ke urllib
try:
    import requests
    _HTTP_LIB = "requests"
except ImportError:
    import urllib.request
    import urllib.error
    _HTTP_LIB = "urllib"

logger = logging.getLogger("islamiai.fetcher")

# ─── Konfigurasi ────────────────────────────────────────────────
CACHE_FILE = os.path.join(os.path.dirname(__file__), "data_cache.json")
CACHE_TTL_HOURS = 72          # Refresh cache tiap 72 jam
REQUEST_TIMEOUT = 8           # seconds — cepat gagal agar tidak block server
MAX_RETRIES = 2

# API endpoints
_QURAN_CLOUD_BASE = "https://api.alquran.cloud/v1"
_HADITH_API_BASE  = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
_QURANCOM_BASE    = "https://api.quran.com/api/v4"

# Terjemahan Kemenag RI di Al-Quran Cloud
_KEMENAG_EDITION  = "id.indonesian"
_ARABIC_EDITION   = "quran-uthmani"


# ═══════════════════════════════════════════════════════════════
# HTTP UTILITIES
# ═══════════════════════════════════════════════════════════════

def _get(url: str, params: dict = None) -> Optional[dict]:
    """
    HTTP GET dengan timeout ketat dan retry minimal.
    Return None jika gagal — JANGAN raise ke caller.
    """
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    for attempt in range(MAX_RETRIES):
        try:
            if _HTTP_LIB == "requests":
                resp = requests.get(url, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
                logger.warning("HTTP %d dari %s", resp.status_code, url)
            else:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "IslamiAI/1.0 (educational)"}
                )
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
                    return json.loads(r.read().decode())
        except Exception as e:
            logger.warning("Fetch attempt %d gagal: %s | url=%s", attempt + 1, e, url)
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)

    return None


# ═══════════════════════════════════════════════════════════════
# MAPPER: API RESPONSE → SCHEMA ISLAMIC_DATA.PY
# ═══════════════════════════════════════════════════════════════

def _map_qurancloud_verse(surah: int, ayah: int, theme: str) -> Optional[dict]:
    """
    Ambil satu ayat dari Al-Quran Cloud dan map ke schema quran_verses.
    Schema target sama persis dengan islamic_data.py.
    """
    # Ambil teks Arab
    ar_data = _get(f"{_QURAN_CLOUD_BASE}/ayah/{surah}:{ayah}/{_ARABIC_EDITION}")
    # Ambil terjemahan Kemenag
    id_data = _get(f"{_QURAN_CLOUD_BASE}/ayah/{surah}:{ayah}/{_KEMENAG_EDITION}")

    if not ar_data or not id_data:
        return None

    ar = ar_data.get("data", {})
    id_ = id_data.get("data", {})

    if not ar or not id_:
        return None

    return {
        "reference": f"{surah}:{ayah}",
        "surah_ayah": f"{surah}:{ayah}",
        "surah": surah,
        "ayah": ayah,
        "arabic_text": ar.get("text", ""),
        "transliteration": "",          # Al-Quran Cloud tidak provide ini
        "translation": id_.get("text", ""),
        "theme": theme,
        "confidence": "medium",         # Belum diverifikasi manual
        "source_check": f"Al-Quran Cloud API | QS. {surah}:{ayah} | {datetime.utcnow().date()}",
        "_fetched_from": "alquran.cloud",
        "_needs_manual_review": True,   # Flag untuk review sebelum naik ke static
    }


def _map_hadith_api(collection: str, number: int) -> Optional[dict]:
    """
    Ambil satu hadis dari fawazahmed0/hadith-api (jsDelivr CDN).
    Endpoint Arab  : {BASE}/ara-{collection}/{number}.json
    Endpoint Indo  : {BASE}/ind-{collection}/{number}.json

    collection map: "bukhari" | "muslim" | "abudawud" | "tirmidzi" | "nasai" | "ibnmajah"
    """
    # Map nama koleksi ke format API ini
    _col_map = {
        "bukhari": "bukhari", "muslim": "muslim",
        "abu-daud": "abudawud", "tirmidzi": "tirmidhi",
        "nasai": "nasai", "ibnu-majah": "ibnmajah",
    }
    col = _col_map.get(collection, collection)

    # API ini mengembalikan seluruh section, bukan satu hadis.
    # Kita fetch section yang mengandung nomor hadis yang diminta,
    # lalu cari item dengan hadithnumber == number.
    arab_data = _get(f"{_HADITH_API_BASE}/ara-{col}.json")
    indo_data = _get(f"{_HADITH_API_BASE}/ind-{col}.json")

    arab = ""
    indo = ""

    if arab_data and "hadiths" in arab_data:
        match = next(
            (h for h in arab_data["hadiths"] if h.get("hadithnumber") == number),
            None
        )
        arab = match.get("text", "") if match else ""

    if indo_data and "hadiths" in indo_data:
        match = next(
            (h for h in indo_data["hadiths"] if h.get("hadithnumber") == number),
            None
        )
        indo = match.get("text", "") if match else ""

    if not arab and not indo:
        return None

    auth = "sahih" if collection in ("bukhari", "muslim") else "hasan"

    return {
        "source": f"{collection.capitalize()} no. {number}",
        "arabic_text": arab,
        "transliteration": "",
        "translation": indo,
        "authenticity": auth,
        "grading": f"Koleksi {collection.capitalize()} (unverified per-hadis)",
        "confidence": "medium",
        "_fetched_from": "fawazahmed0/hadith-api@jsDelivr",
        "_needs_manual_review": True,
    }


# ═══════════════════════════════════════════════════════════════
# FETCH PLANS: Daftar data yang ingin di-expand
# ═══════════════════════════════════════════════════════════════

# Ayat tambahan yang ingin di-fetch (surah, ayah, theme)
# Ini perluasan dari 23 ayat yang sudah ada di islamic_data.py
_QURAN_FETCH_PLAN: List[tuple] = [
    # Puasa
    (2, 183, "puasa"),
    (2, 184, "puasa"),
    (2, 185, "puasa"),
    # Zakat
    (9, 60, "zakat"),
    (9, 103, "zakat"),
    # Haji
    (2, 196, "haji"),
    (2, 197, "haji"),
    (22, 27, "haji"),
    # Nikah
    (2, 221, "nikah"),
    (4, 3, "nikah"),
    (4, 34, "nikah"),
    # Muamalah / Riba
    (2, 275, "muamalah"),
    (2, 276, "muamalah"),
    (2, 278, "muamalah"),
    # Aqidah tambahan
    (2, 255, "aqidah"),    # Ayat Kursi
    (112, 1, "aqidah"),   # Al-Ikhlas
    (112, 2, "aqidah"),
    (112, 3, "aqidah"),
    (112, 4, "aqidah"),
]

# Hadis tambahan yang ingin di-fetch (collection, number)
# Diseleksi manual berdasarkan isi — nomor yang diketahui matn-nya
_HADIS_FETCH_PLAN: List[tuple] = [
    # ── SUDAH VERIFIED DI CACHE — tetap di plan untuk refresh ──
    ("bukhari", 1),     # Hadis niat — "semua amal tergantung niat"
    ("bukhari", 2),     # Cara turun wahyu — aqidah
    ("bukhari", 50),    # Hadis Jibril — rukun Islam/Iman/Ihsan

    # ── AQIDAH / TAUHID ─────────────────────────────────────────
    ("bukhari", 24),    # Malu bagian dari iman
    ("bukhari", 39),    # Agama itu mudah
    ("bukhari", 6098),  # Larangan mencaci maki Muslim

    # ── SHALAT ──────────────────────────────────────────────────
    ("bukhari", 528),   # Keutamaan shalat subuh
    ("bukhari", 521),   # Waktu shalat
    ("muslim", 649),    # Shalat jamaah 27 derajat

    # ── THAHARAH ────────────────────────────────────────────────
    ("bukhari", 135),   # Wudhu — membasuh tangan
    ("muslim", 223),    # Kebersihan sebagian dari iman
    ("bukhari", 158),   # Berkumur dalam wudhu

    # ── PUASA ───────────────────────────────────────────────────
    ("bukhari", 1904),  # Puasa Ramadhan wajib
    ("bukhari", 1923),  # Sahur adalah keberkahan
    ("muslim", 1151),   # Puasa menghapus dosa

    # ── ZAKAT ───────────────────────────────────────────────────
    ("bukhari", 1395),  # Zakat rukun Islam
    ("bukhari", 1461),  # Nisab zakat

    # ── HAJI ────────────────────────────────────────────────────
    ("bukhari", 1521),  # Haji mabrur
    ("muslim", 1350),   # Keutamaan haji

    # ── MUAMALAH ────────────────────────────────────────────────
    ("bukhari", 2079),  # Jual beli harus suka sama suka
    ("bukhari", 2165),  # Larangan riba

    # ── NIKAH ───────────────────────────────────────────────────
    ("bukhari", 5065),  # Anjuran menikah
    ("bukhari", 5066),  # Mahar dalam pernikahan
]


# ═══════════════════════════════════════════════════════════════
# CACHE MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def _load_cache() -> dict:
    """Muat cache dari file. Return empty structure jika tidak ada."""
    if not os.path.exists(CACHE_FILE):
        return {"_meta": {}, "quran_verses": {}, "hadis_collection": {}}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Cache corrupt atau tidak bisa dibaca: %s", e)
        return {"_meta": {}, "quran_verses": {}, "hadis_collection": {}}


def _save_cache(data: dict) -> bool:
    """Simpan cache ke file. Return False jika gagal."""
    try:
        data["_meta"]["last_updated"] = datetime.utcnow().isoformat()
        data["_meta"]["total_quran"] = len(data.get("quran_verses", {}))
        data["_meta"]["total_hadis"] = len(data.get("hadis_collection", {}))
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Cache disimpan: %d ayat, %d hadis",
                    data["_meta"]["total_quran"], data["_meta"]["total_hadis"])
        return True
    except IOError as e:
        logger.error("Gagal menyimpan cache: %s", e)
        return False


def _is_cache_fresh() -> bool:
    """True jika cache masih dalam TTL (tidak perlu refresh)."""
    cache = _load_cache()
    last_updated = cache.get("_meta", {}).get("last_updated")
    if not last_updated:
        return False
    try:
        last_dt = datetime.fromisoformat(last_updated)
        return datetime.utcnow() - last_dt < timedelta(hours=CACHE_TTL_HOURS)
    except ValueError:
        return False


# ═══════════════════════════════════════════════════════════════
# MAIN FETCH FUNCTION
# ═══════════════════════════════════════════════════════════════

def fetch_and_cache(force: bool = False) -> dict:
    """
    Entry point utama. Fetch semua data dari plan dan simpan ke cache.

    Args:
        force: Jika True, paksa refresh meski cache masih fresh.

    Returns:
        dict: Cache yang sudah diperbarui (atau cache lama jika gagal)
    """
    if not force and _is_cache_fresh():
        logger.info("Cache masih fresh (TTL %dh). Skip fetch.", CACHE_TTL_HOURS)
        return _load_cache()

    logger.info("Mulai fetch data eksternal...")
    cache = _load_cache()   # Muat yang ada (bisa diisi parsial)

    success_quran = 0
    fail_quran = 0
    for (surah, ayah, theme) in _QURAN_FETCH_PLAN:
        key = f"quran_{surah}_{ayah}"
        if key in cache["quran_verses"] and not force:
            continue   # Sudah ada, skip
        result = _map_qurancloud_verse(surah, ayah, theme)
        if result:
            cache["quran_verses"][key] = result
            success_quran += 1
        else:
            fail_quran += 1
        time.sleep(0.3)   # Rate limit courtesy

    success_hadis = 0
    fail_hadis = 0
    for (collection, number) in _HADIS_FETCH_PLAN:
        key = f"hadis_{collection}_{number}"
        if key in cache["hadis_collection"] and not force:
            continue
        result = _map_hadith_api(collection, number)
        if result:
            cache["hadis_collection"][key] = result
            success_hadis += 1
        else:
            fail_hadis += 1
        time.sleep(0.3)

    logger.info(
        "Fetch selesai | Quran: %d ok, %d fail | Hadis: %d ok, %d fail",
        success_quran, fail_quran, success_hadis, fail_hadis
    )

    _save_cache(cache)
    return cache


def get_cached_data() -> dict:
    """
    Ambil data dari cache tanpa trigger fetch.
    Digunakan oleh retrieval.py untuk lookup cepat.
    Returns empty structure jika cache tidak ada.
    """
    return _load_cache()


# ─── CLI untuk trigger manual ──────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    force = "--force" in sys.argv
    print(f"Fetching data... (force={force})")
    result = fetch_and_cache(force=force)

    print(f"\nCache sekarang berisi:")
    print(f"  Quran verses : {len(result.get('quran_verses', {}))}")
    print(f"  Hadis        : {len(result.get('hadis_collection', {}))}")
    print(f"  Last updated : {result.get('_meta', {}).get('last_updated', 'N/A')}")
    print(f"\nFile: {CACHE_FILE}")
    print("\n⚠️  Data yang di-fetch BELUM diverifikasi manual.")
    print("   Tandai _needs_manual_review=False setelah diverifikasi.")
