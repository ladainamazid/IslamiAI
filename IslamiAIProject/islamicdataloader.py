# islamicdataloader.py
# IslamiAI — Data Loader v3.0
# ============================================================
# Perubahan dari v2.0:
#   • Semua block (blok1–blok9) SUDAH DIGABUNG ke islamic_data.py.
#     Loader tidak lagi mengimpor file block terpisah.
#   • API cache diterapkan secara ADITIF (tidak menimpa data statis).
#   • run_integrity_check() dan get_database_stats() dipertahankan
#     untuk monitoring dan debugging.
# ============================================================
# Cara pakai:
#   from islamicdataloader import quran_verses, hadis_collection, shafii_rules
#   from islamicdataloader import run_integrity_check, get_database_stats
# ============================================================

from __future__ import annotations
import json
import logging
import os
from collections import Counter
from typing import Optional

logger = logging.getLogger("islamiai.loader")

# ── Primary data import ───────────────────────────────────────────────────────
# islamic_data.py adalah satu-satunya sumber data statik.
# Tidak ada lagi import dari file block terpisah.
from islamic_data import (
    quran_verses     as _qv_static,
    hadis_collection as _hc_static,
    shafii_rules     as _sr_static,
)

# Buat salinan yang bisa dimodifikasi (cache enrichment)
quran_verses:     dict = dict(_qv_static)
hadis_collection: dict = dict(_hc_static)
shafii_rules:     dict = dict(_sr_static)


# ── API Cache Application (ADITIF ONLY) ──────────────────────────────────────
def _apply_cache(
    cache_path: str = "data_cache.json",
    overwrite: bool = False,
) -> dict:
    """
    Muat data_cache.json dan terapkan ke quran_verses / hadis_collection.

    Prinsip:
      overwrite=False (default): cache hanya menambahkan ENTRI BARU
        yang belum ada di data statis. Data terverifikasi (confidence=high)
        TIDAK pernah ditimpa oleh cache (confidence=medium).
      overwrite=True: izinkan cache menimpa entri yang sudah ada.
        Gunakan hanya untuk debugging.

    Returns dict dengan statistik: added, skipped, errors.
    """
    stats = {"qv_added": 0, "hc_added": 0, "qv_skipped": 0,
             "hc_skipped": 0, "errors": []}

    if not os.path.exists(cache_path):
        logger.debug("Cache tidak ditemukan: %s — dilewati.", cache_path)
        return stats

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache: dict = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Gagal membaca cache '%s': %s", cache_path, e)
        stats["errors"].append(str(e))
        return stats

    # quran_verses dari cache
    for key, entry in cache.get("quran_verses", {}).items():
        if key in quran_verses and not overwrite:
            stats["qv_skipped"] += 1
            continue
        quran_verses[key] = entry
        stats["qv_added"] += 1

    # hadis_collection dari cache
    for key, entry in cache.get("hadis_collection", {}).items():
        if key in hadis_collection and not overwrite:
            stats["hc_skipped"] += 1
            continue
        hadis_collection[key] = entry
        stats["hc_added"] += 1

    logger.info(
        "Cache applied — QV added: %d, skipped: %d | HC added: %d, skipped: %d",
        stats["qv_added"], stats["qv_skipped"],
        stats["hc_added"], stats["hc_skipped"],
    )
    return stats


# Terapkan cache saat module di-import (aditif, tidak menimpa statis)
_cache_stats = _apply_cache()


# ── Integrity Check ───────────────────────────────────────────────────────────
def run_integrity_check(verbose: bool = True) -> dict:
    """
    Periksa:
      1. Cross-reference: setiap basis_quran dan basis_hadis di shafii_rules
         harus ada di quran_verses / hadis_collection.
      2. Entri stub (confidence="pending") masih outstanding.
      3. Duplikasi key (tidak mungkin di Python dict, tapi catat jika ada).

    Returns dict dengan status lengkap.
    """
    broken_quran: list = []
    broken_hadis: list = []

    for rule_key, rule in shafii_rules.items():
        for qref in rule.get("basis_quran", []):
            if qref not in quran_verses:
                broken_quran.append((rule_key, qref))
        for href in rule.get("basis_hadis", []):
            if href not in hadis_collection:
                broken_hadis.append((rule_key, href))

    pending_hadis = [
        k for k, v in hadis_collection.items()
        if v.get("status") == "stub"
    ]
    pending_quran = [
        k for k, v in quran_verses.items()
        if "PENDING" in v.get("arabic_text", "")
    ]

    status = "OK" if not (broken_quran or broken_hadis) else "WARNINGS"

    result = {
        "total_quran":    len(quran_verses),
        "total_hadis":    len(hadis_collection),
        "total_rules":    len(shafii_rules),
        "broken_quran":   broken_quran,
        "broken_hadis":   broken_hadis,
        "pending_quran":  pending_quran,
        "pending_hadis":  pending_hadis,
        "status":         status,
        "cache_stats":    _cache_stats,
    }

    if verbose:
        BAR = "=" * 60
        print(BAR)
        print("  IslamiAI v3.0 — LOADER INTEGRITY REPORT")
        print(BAR)
        print(f"  Quran verses     : {result['total_quran']}")
        print(f"  Hadis entries    : {result['total_hadis']}")
        print(f"  Shafi'i rules    : {result['total_rules']}")
        print(f"  Cache QV added   : {_cache_stats['qv_added']}")
        print(f"  Cache HC added   : {_cache_stats['hc_added']}")

        if pending_hadis:
            print(f"\n  ⏳ Pending hadis stubs ({len(pending_hadis)}):")
            for p in pending_hadis:
                ref = hadis_collection[p].get("reference", "?")
                print(f"     {p:<40} [{ref}]")

        if pending_quran:
            print(f"\n  ⏳ Pending quran stubs: {pending_quran}")

        if broken_quran:
            print(f"\n  ⚠  Broken Quran refs ({len(broken_quran)}):")
            for r, ref in broken_quran:
                print(f"     [{r}] → '{ref}'")
        else:
            print("\n  ✅ Quran cross-refs : all valid")

        if broken_hadis:
            print(f"  ⚠  Broken Hadis refs ({len(broken_hadis)}):")
            for r, ref in broken_hadis:
                print(f"     [{r}] → '{ref}'")
        else:
            print("  ✅ Hadis cross-refs : all valid")

        print(f"\n  OVERALL STATUS : {status}")
        print(BAR)

    return result


# ── Database Statistics ───────────────────────────────────────────────────────
def get_database_stats() -> dict:
    """
    Kembalikan distribusi tema dan autentisitas untuk monitoring.
    """
    return {
        "quran_by_theme":   dict(Counter(
            v.get("theme", "?") for v in quran_verses.values()
        )),
        "hadis_by_theme":   dict(Counter(
            v.get("theme", "?") for v in hadis_collection.values()
        )),
        "rules_by_madhab":  dict(Counter(
            v.get("madhab", "?") for v in shafii_rules.values()
        )),
        "hadis_by_auth":    dict(Counter(
            v.get("authenticity", "?") for v in hadis_collection.values()
        )),
        "rules_by_confidence": dict(Counter(
            v.get("confidence", "?") for v in shafii_rules.values()
        )),
        "pending_stubs": {
            "quran": [k for k, v in quran_verses.items()
                      if "PENDING" in v.get("arabic_text", "")],
            "hadis": [k for k, v in hadis_collection.items()
                      if v.get("status") == "stub"],
        },
    }


# ── Public API re-export ──────────────────────────────────────────────────────
# quran_verses, hadis_collection, shafii_rules sudah di-export di atas
# (module-level variables). Tidak ada lagi export dari sub-block.

__all__ = [
    "quran_verses",
    "hadis_collection",
    "shafii_rules",
    "run_integrity_check",
    "get_database_stats",
]


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    result = run_integrity_check(verbose=True)

    stats = get_database_stats()

    print("\n  DISTRIBUSI TEMA — QURAN:")
    for t, c in sorted(stats["quran_by_theme"].items()):
        print(f"    {t:<25}: {c}")

    print("\n  DISTRIBUSI TEMA — HADIS:")
    for t, c in sorted(stats["hadis_by_theme"].items()):
        print(f"    {t:<25}: {c}")

    print("\n  DISTRIBUSI MADHAB — RULES:")
    for m, c in sorted(stats["rules_by_madhab"].items()):
        print(f"    {m:<35}: {c}")

    if stats["pending_stubs"]["hadis"]:
        print("\n  STUB HADIS PENDING (isi teks Arab-nya):")
        for k in stats["pending_stubs"]["hadis"]:
            ref = hadis_collection[k].get("reference", "?")
            print(f"    {k:<45} → {ref}")
