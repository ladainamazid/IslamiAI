"""
retrieval.py — UPDATE MINIMAL untuk integrasi data_cache.json
─────────────────────────────────────────────────────────────────
PERUBAHAN dari versi sebelumnya:
  HANYA satu fungsi baru ditambahkan: _load_extended_data()
  Fungsi retrieve_ruling() TIDAK berubah signature-nya.

Strategi lookup (tiga lapis):
  1. shafii_rules dari islamic_data.py  → paling dipercaya, prioritas utama
  2. quran/hadis dari islamic_data.py   → static, verified
  3. quran/hadis dari data_cache.json   → extended, medium confidence

Jika cache tidak ada atau gagal dimuat → fallback ke static saja.
Tidak ada network call di sini — network hanya di data_fetcher.py.
"""

import json
import logging
import os
from typing import Optional

from islamic_data import quran_verses, hadis_collection, shafii_rules

logger = logging.getLogger("islamiai.retrieval")

_CACHE_FILE = os.path.join(os.path.dirname(__file__), "data_cache.json")


def _load_extended_data() -> tuple[dict, dict]:
    """
    Muat data dari cache tanpa network call.
    Return (quran_extended, hadis_extended) — dict kosong jika cache tidak ada.
    """
    if not os.path.exists(_CACHE_FILE):
        return {}, {}
    try:
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
        quran_ext  = cache.get("quran_verses", {})
        hadis_ext  = cache.get("hadis_collection", {})
        logger.debug("Cache dimuat: %d ayat, %d hadis tambahan",
                     len(quran_ext), len(hadis_ext))
        return quran_ext, hadis_ext
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Gagal muat cache: %s — menggunakan data statis saja.", e)
        return {}, {}


def retrieve_ruling(topic: str, madhab: str = "shafii") -> Optional[dict]:
    """
    Fungsi utama retrieval. Signature TIDAK berubah.

    Args:
        topic: Topic key dari parse_user_query() atau L2_IslamicContext
        madhab: Default "shafii"

    Returns:
        dict dengan key: topic, ruling, madhab, quran, hadis, confidence
        None jika tidak ditemukan sama sekali
    """
    if not topic:
        return None

    topic_lower = topic.lower().strip()

    # ── Layer 1: Shafi'i rules (static, prioritas tertinggi) ──
    rule = shafii_rules.get(topic_lower)
    if rule:
        # Resolve referensi Quran dari static data
        quran_resolved = _resolve_quran_refs(
            rule.get("basis_quran", []),
            quran_verses
        )
        # Resolve referensi hadis dari static data
        hadis_resolved = _resolve_hadis_refs(
            rule.get("basis_hadis", []),
            hadis_collection
        )

        # Jika static tidak cukup, coba tambah dari cache
        if len(quran_resolved) < 2 or len(hadis_resolved) < 1:
            quran_ext, hadis_ext = _load_extended_data()
            # Tambah dari cache hanya jika belum ada di static
            for ref in rule.get("basis_quran", []):
                if ref not in quran_verses and ref in quran_ext:
                    quran_resolved.append(quran_ext[ref])
            for ref in rule.get("basis_hadis", []):
                if ref not in hadis_collection and ref in hadis_ext:
                    hadis_resolved.append(hadis_ext[ref])

        return {
            "topic": topic_lower,
            "ruling": rule.get("ruling", ""),
            "madhab": rule.get("madhab", madhab),
            "quran": quran_resolved,
            "hadis": hadis_resolved,
            "confidence": rule.get("confidence", "medium"),
            "reasoning": rule.get("reasoning", ""),
            "keywords": rule.get("keywords", []),
            "_source": "static_rules",
        }

    # ── Layer 2: Keyword search di static data ─────────────────
    # Beberapa pertanyaan tidak match topic key langsung
    rule_by_keyword = _search_by_keyword(topic_lower, shafii_rules)
    if rule_by_keyword:
        rule_key, rule = rule_by_keyword
        quran_resolved = _resolve_quran_refs(rule.get("basis_quran", []), quran_verses)
        hadis_resolved = _resolve_hadis_refs(rule.get("basis_hadis", []), hadis_collection)
        return {
            "topic": rule_key,
            "ruling": rule.get("ruling", ""),
            "madhab": rule.get("madhab", madhab),
            "quran": quran_resolved,
            "hadis": hadis_resolved,
            "confidence": rule.get("confidence", "medium"),
            "reasoning": rule.get("reasoning", ""),
            "keywords": rule.get("keywords", []),
            "_source": "keyword_search",
        }

    # ── Layer 3: Search di cache (extended data) ───────────────
    quran_ext, hadis_ext = _load_extended_data()
    theme_match = _search_theme_in_cache(topic_lower, quran_ext, hadis_ext)
    if theme_match:
        logger.info("Topik '%s' ditemukan di cache (extended data)", topic_lower)
        return {
            "topic": topic_lower,
            "ruling": "Lihat referensi Quran dan hadis terkait.",
            "madhab": madhab,
            "quran": theme_match["quran"],
            "hadis": theme_match["hadis"],
            "confidence": "medium",      # Cache belum terverifikasi manual
            "reasoning": "",
            "keywords": [],
            "_source": "cache_extended",
            "_needs_review": True,
        }

    logger.info("Topik '%s' tidak ditemukan di static maupun cache.", topic_lower)
    return None


# ─── Helper functions ──────────────────────────────────────────

def _resolve_quran_refs(refs: list, data: dict) -> list:
    """Resolve list ref key → list dict ayat yang lengkap."""
    result = []
    for ref in refs:
        if ref in data:
            result.append(data[ref])
    return result


def _resolve_hadis_refs(refs: list, data: dict) -> list:
    """Resolve list ref key → list dict hadis yang lengkap."""
    result = []
    for ref in refs:
        if ref in data:
            result.append(data[ref])
    return result


def _search_by_keyword(topic: str, rules: dict) -> Optional[tuple]:
    """
    Cari rule yang keyword-nya mengandung topic string.
    Return (rule_key, rule_dict) atau None.
    """
    for rule_key, rule in rules.items():
        keywords = rule.get("keywords", [])
        if any(topic in kw or kw in topic for kw in keywords):
            return rule_key, rule
    return None


def _search_theme_in_cache(topic: str, quran_ext: dict, hadis_ext: dict) -> Optional[dict]:
    """
    Cari di cache berdasarkan theme yang cocok dengan topic.
    Return dict dengan 'quran' dan 'hadis' atau None.
    """
    matched_quran = [
        v for v in quran_ext.values()
        if v.get("theme", "").lower() == topic
        or topic in v.get("theme", "").lower()
    ]
    matched_hadis = []   # Hadis di cache tidak punya theme, skip untuk sekarang

    if matched_quran:
        return {"quran": matched_quran[:3], "hadis": matched_hadis}

    return None
