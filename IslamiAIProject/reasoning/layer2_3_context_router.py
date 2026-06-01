"""
reasoning/layer2_islamic_context.py
reasoning/layer3_cognitive_router.py
─────────────────────────────────────────────────────────────────

LAYER 2 — Islamic Context Mapper
[Menggantikan L03 + L16 + L17 dari versi 20-layer]

Tanggung jawab:
  - Map domain Islam ke konteks fiqh yang lebih spesifik
  - Identifikasi madhab yang relevan (fokus: Shafi'i sesuai IslamiAI)
  - Tentukan apakah pertanyaan memerlukan dalil (Quran/hadis)
    atau cukup penjelasan prosedural
  - Integrasi dengan query_parser.py (parse_user_query) yang sudah ada

LAYER 3 — Cognitive Router
[Menggantikan L04 + L12 + L13 + L14 dari versi 20-layer]

Tanggung jawab:
  - Tentukan strategy retrieval: exact match vs. fuzzy vs. combined
  - Putuskan apakah perlu multi-source (Quran + hadis + rules)
  - Set complexity yang diperlukan untuk response
  - Hasilkan skip_layers jika path sederhana
  - INTEGRASIKAN dengan retrieval.py untuk memberi hint retrieval

Alasan pemisahan L2 dan L3 (tidak digabung):
  L2 adalah *interpretasi* (apa artinya pertanyaan ini secara fiqh?).
  L3 adalah *eksekusi* (bagaimana pipeline harus merespons?).
  Keduanya memiliki decision point yang berbeda dan perlu diaudit
  secara terpisah untuk keperluan halal-verification.
"""

from typing import Any, Dict, List, Optional, Tuple
from base_layer import BaseLayer


# ═══════════════════════════════════════════════════════════════
# LAYER 2 — Islamic Context Mapper
# ═══════════════════════════════════════════════════════════════

# Mapping: (domain, input_type) → konteks fiqh spesifik
# Format: (fiqh_context, dalil_required, madhhab_primary, urgency_level)
_FIQH_CONTEXT_MAP: Dict[Tuple[str, str], Tuple[str, bool, str, str]] = {
    # Syahadat
    ("syahadat", "permintaan_fatwa"):      ("masuk_islam_prosedur", True,  "shafii", "high"),
    ("syahadat", "pertanyaan"):            ("aqidah_tauhid",         True,  "shafii", "medium"),
    # Shalat
    ("shalat",   "permintaan_fatwa"):      ("shalat_hukum",          True,  "shafii", "high"),
    ("shalat",   "permintaan_prosedur"):   ("shalat_tata_cara",      False, "shafii", "medium"),
    ("shalat",   "pertanyaan"):            ("shalat_umum",           True,  "shafii", "medium"),
    # Zakat
    ("zakat",    "permintaan_fatwa"):      ("zakat_hukum",           True,  "shafii", "high"),
    ("zakat",    "pertanyaan"):            ("zakat_ketentuan",       True,  "shafii", "medium"),
    # Puasa
    ("puasa",    "permintaan_fatwa"):      ("puasa_hukum",           True,  "shafii", "high"),
    ("puasa",    "permintaan_prosedur"):   ("puasa_pelaksanaan",     False, "shafii", "medium"),
    ("puasa",    "pertanyaan"):            ("puasa_umum",            True,  "shafii", "medium"),
    # Haji
    ("haji",     "permintaan_prosedur"):   ("haji_manasik",          True,  "shafii", "high"),
    ("haji",     "pertanyaan"):            ("haji_umum",             True,  "shafii", "medium"),
    # Nikah
    ("nikah",    "permintaan_fatwa"):      ("nikah_hukum",           True,  "shafii", "high"),
    ("nikah",    "pertanyaan"):            ("nikah_ketentuan",       True,  "shafii", "medium"),
    # Muamalah
    ("muamalah", "permintaan_fatwa"):      ("muamalah_hukum",        True,  "shafii", "high"),
    ("muamalah", "pertanyaan"):            ("muamalah_umum",         True,  "shafii", "medium"),
    # Thaharah
    ("thaharah", "permintaan_prosedur"):   ("thaharah_tata_cara",    False, "shafii", "medium"),
    ("thaharah", "permintaan_fatwa"):      ("thaharah_hukum",        True,  "shafii", "medium"),
    # Aqidah
    ("aqidah",   "pertanyaan"):            ("aqidah_penjelasan",     True,  "shafii", "medium"),
    ("aqidah",   "permintaan_penjelasan"): ("aqidah_detail",         True,  "shafii", "high"),
}

_DEFAULT_CONTEXT = ("umum_islam", True, "shafii", "low")


class Layer2_IslamicContext(BaseLayer):
    """
    Menentukan konteks fiqh dari pertanyaan untuk mengarahkan retrieval.
    Output langsung digunakan oleh retrieval.py di Layer 4.
    """

    @property
    def layer_id(self) -> str:
        return "L2_islamic_context"

    @property
    def required_keys(self):
        return ["input", "L1_perception_semantic"]

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        l1 = state["L1_perception_semantic"].payload
        primary_domain = l1["primary_domain"]
        input_type = l1["input_type"]
        secondary_domains = l1.get("secondary_domains", [])
        language = l1["language"]

        # Lookup konteks fiqh
        fiqh_context, dalil_required, madhhab, urgency = _FIQH_CONTEXT_MAP.get(
            (primary_domain, input_type),
            _DEFAULT_CONTEXT
        )

        # Tentukan scope dalil yang diperlukan
        evidence_scope = []
        if dalil_required:
            evidence_scope = ["quran", "hadis", "shafii_rules"]
        else:
            evidence_scope = ["shafii_rules"]   # Prosedural cukup rules

        # Apakah pertanyaan menyentuh domain lintas-topik?
        cross_domain = len([d for d in secondary_domains if d != "umum"]) > 0

        confidence = 0.9 if (primary_domain, input_type) in _FIQH_CONTEXT_MAP else 0.45

        warnings = []
        if confidence < 0.5:
            warnings.append(
                f"Konteks fiqh tidak terpetakan untuk "
                f"domain='{primary_domain}', type='{input_type}'. "
                "Menggunakan fallback 'umum_islam'."
            )
        if cross_domain:
            warnings.append(
                f"Pertanyaan mencakup domain sekunder: {secondary_domains}. "
                "Retrieval akan diperluas."
            )

        return {
            "fiqh_context": fiqh_context,
            "primary_domain": primary_domain,
            "secondary_domains": secondary_domains,
            "madhhab": madhhab,
            "dalil_required": dalil_required,
            "evidence_scope": evidence_scope,
            "urgency": urgency,
            "cross_domain": cross_domain,
            "response_language": language,
            "_confidence": round(confidence, 4),
            "_warnings": warnings,
            "_religious_content": True,
        }


# ═══════════════════════════════════════════════════════════════
# LAYER 3 — Cognitive Router
# ═══════════════════════════════════════════════════════════════

# Strategy retrieval berdasarkan urgency + dalil_required
_RETRIEVAL_STRATEGIES = {
    "high":   {
        "strategy": "comprehensive",       # Quran + hadis + rules, semua dicari
        "min_evidence_pieces": 3,
        "allow_partial_response": False,   # Harus ada dalil, tidak boleh skip
        "response_depth": "full",
    },
    "medium": {
        "strategy": "targeted",            # Prioritaskan rules, tambah Quran jika ada
        "min_evidence_pieces": 2,
        "allow_partial_response": True,
        "response_depth": "standard",
    },
    "low": {
        "strategy": "minimal",             # Cukup rules atau penjelasan singkat
        "min_evidence_pieces": 1,
        "allow_partial_response": True,
        "response_depth": "brief",
    },
}


class Layer3_CognitiveRouter(BaseLayer):
    """
    Mengatur strategi eksekusi pipeline berdasarkan konteks fiqh.
    Hasilkan routing_plan yang dibaca oleh Layer 4 dan Layer 7.
    
    PENTING: Layer ini yang memutuskan apakah jawaban BOLEH diberikan
    bahkan sebelum retrieval dilakukan — early rejection untuk topik
    yang berada di luar scope IslamiAI (jinayah berat, dll).
    """

    # Topik yang memerlukan perhatian khusus / referral ke ulama
    _SENSITIVE_CONTEXTS = {
        "jinayah_hukum",     # Hukum pidana Islam — rujuk ulama
        "faraid",            # Waris — memerlukan kalkulasi spesifik
        "muamalah_hukum",    # Fatwa bisnis kompleks
    }

    @property
    def layer_id(self) -> str:
        return "L3_cognitive_router"

    @property
    def required_keys(self):
        return ["L1_perception_semantic", "L2_islamic_context"]

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        l1 = state["L1_perception_semantic"].payload
        l2 = state["L2_islamic_context"].payload

        fiqh_context = l2["fiqh_context"]
        urgency = l2["urgency"]
        dalil_required = l2["dalil_required"]
        cross_domain = l2["cross_domain"]
        l1_confidence = state["L1_perception_semantic"].confidence

        routing = _RETRIEVAL_STRATEGIES[urgency].copy()

        # Penyesuaian berdasarkan kondisi aktual
        if cross_domain:
            routing["strategy"] = "comprehensive"
            routing["min_evidence_pieces"] = max(routing["min_evidence_pieces"], 3)

        if l1_confidence < 0.4:
            # Input ambigu → kurangi kedalaman, tambahkan disclaimer
            routing["response_depth"] = "brief"
            routing["add_clarification_request"] = True
        else:
            routing["add_clarification_request"] = False

        # Cek konteks sensitif → wajibkan disclaimer rujuk ulama
        requires_ulama_disclaimer = fiqh_context in self._SENSITIVE_CONTEXTS

        # Skip layers yang tidak relevan (dibaca orchestrator)
        skip_layers = []
        if urgency == "low" and not dalil_required:
            skip_layers.append("multi_source_quran_hadis")

        # Routing confidence: gunakan .confidence dari LayerResult (sudah di-pop dari payload)
        l2_confidence = state["L2_islamic_context"].confidence
        routing_confidence = l2_confidence * 0.7 + l1_confidence * 0.3

        rationale = (
            f"domain={l2['primary_domain']} | context={fiqh_context} | "
            f"urgency={urgency} | strategy={routing['strategy']} | "
            f"depth={routing['response_depth']} | "
            f"ulama_ref={requires_ulama_disclaimer}"
        )

        return {
            "retrieval_strategy": routing["strategy"],
            "min_evidence_pieces": routing["min_evidence_pieces"],
            "allow_partial_response": routing["allow_partial_response"],
            "response_depth": routing["response_depth"],
            "add_clarification_request": routing.get("add_clarification_request", False),
            "requires_ulama_disclaimer": requires_ulama_disclaimer,
            "skip_layers": skip_layers,
            "routing_rationale": rationale,
            "_confidence": round(routing_confidence, 4),
            "_warnings": (
                [f"Konteks '{fiqh_context}' memerlukan referral ke ulama — "
                 "disclaimer wajib ditambahkan."]
                if requires_ulama_disclaimer else []
            ),
            "_religious_content": True,
        }
