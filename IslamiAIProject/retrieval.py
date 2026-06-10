"""
retrieval.py — 4-layer retrieval pipeline
─────────────────────────────────────────────────────────────────
Strategi lookup (empat lapis):
  1. shafii_rules dari islamic_data.py  → static, prioritas tertinggi
  2. keyword search di shafii_rules     → fallback jika topic key tidak match
  3. quran/hadis dari data_cache.json   → extended, medium confidence
  4. kitab_corpus FTS5 (db_retrieval)   → 28 kitab Shamela, aktif jika DB ada

Layer 4 graceful degradation: jika islamiai.db atau db_retrieval tidak
tersedia, pipeline tetap berfungsi dengan Layer 1-3.
Tidak ada network call di sini — network hanya di data_fetcher.py.
"""

import json
import logging
import os
from typing import Optional

from islamic_data import quran_verses, hadis_collection, shafii_rules

logger = logging.getLogger("islamiai.retrieval")

# ── Layer 4: db_retrieval (kitab corpus FTS5) — opsional ──────
# Graceful degradation: jika islamiai.db belum ada atau db_retrieval
# belum terinstall, Layer 4 dinonaktifkan tanpa merusak Layer 1-3.
try:
    from db_retrieval import search_kitab as _search_kitab
    _DB_RETRIEVAL_AVAILABLE = True
except (ImportError, Exception) as _import_err:
    _search_kitab = None
    _DB_RETRIEVAL_AVAILABLE = False
    logger.warning(
        "db_retrieval tidak tersedia — Layer 4 dinonaktifkan. (%s)", _import_err
    )

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
        quran_resolved = _resolve_quran_refs(
            rule.get("basis_quran", []),
            quran_verses
        )
        hadis_resolved = _resolve_hadis_refs(
            rule.get("basis_hadis", []),
            hadis_collection
        )

        if len(quran_resolved) < 2 or len(hadis_resolved) < 1:
            quran_ext, hadis_ext = _load_extended_data()
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
            "confidence": "medium",
            "reasoning": "",
            "keywords": [],
            "_source": "cache_extended",
            "_needs_review": True,
        }

    # ── Layer 4: Kitab Corpus FTS5 ─────────────────────────────
    if _DB_RETRIEVAL_AVAILABLE:
        try:
            kitab_hits = _search_kitab(topic_lower)
        except Exception as e:
            logger.warning("Layer 4 search gagal untuk '%s': %s", topic_lower, e)
            kitab_hits = []

        if kitab_hits:
            logger.info(
                "Topik '%s' ditemukan di kitab_corpus (%d hits).",
                topic_lower, len(kitab_hits)
            )
            return {
                "topic": topic_lower,
                "ruling": "",
                "madhab": madhab,
                "quran": [],
                "hadis": [],
                "confidence": "medium",
                "reasoning": "",
                "keywords": [],
                "_source": "kitab_corpus",
                "_kitab_hits": kitab_hits,
            }

    logger.info(
        "Topik '%s' tidak ditemukan di static, cache, maupun kitab_corpus.",
        topic_lower
    )
    return None


# ─── Helper functions ──────────────────────────────────────────

def _resolve_quran_refs(refs: list, data: dict) -> list:
    result = []
    for ref in refs:
        if ref in data:
            result.append(data[ref])
    return result


def _resolve_hadis_refs(refs: list, data: dict) -> list:
    result = []
    for ref in refs:
        if ref in data:
            result.append(data[ref])
    return result


def _search_by_keyword(topic: str, rules: dict) -> Optional[tuple]:
    for rule_key, rule in rules.items():
        keywords = rule.get("keywords", [])
        if any(topic in kw or kw in topic for kw in keywords):
            return rule_key, rule
    return None


def _search_theme_in_cache(topic: str, quran_ext: dict, hadis_ext: dict) -> Optional[dict]:
    matched_quran = [
        v for v in quran_ext.values()
        if v.get("theme", "").lower() == topic
        or topic in v.get("theme", "").lower()
    ]
    matched_hadis = []

    if matched_quran:
        return {"quran": matched_quran[:3], "hadis": matched_hadis}

    return None
