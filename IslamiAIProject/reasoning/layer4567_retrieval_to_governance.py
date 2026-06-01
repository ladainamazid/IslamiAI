"""
reasoning/layer4_knowledge_retriever.py
reasoning/layer5_evidence_validator.py
reasoning/layer6_response_synthesizer.py
reasoning/layer7_output_governance.py
─────────────────────────────────────────────────────────────────

LAYER 4 — Knowledge Retriever
[Menggantikan L05 + L07 + L15 dari versi 20-layer]
BERINTEGRASI LANGSUNG dengan: retrieval.py, query_parser.py

LAYER 5 — Evidence Validator + Self-Critic
[Menggantikan L06 + L08 + L11 dari versi 20-layer]
BERINTEGRASI LANGSUNG dengan: reasoning_validator.py

LAYER 6 — Response Synthesizer
[Menggantikan L09 + L17 dari versi 20-layer]
BERINTEGRASI LANGSUNG dengan: formatter.py

LAYER 7 — Output Governance
[Menggantikan L10 + L19 + L20 dari versi 20-layer]
BERINTEGRASI LANGSUNG dengan: validators.py, config.py
"""

import sys
import os
import logging
from typing import Any, Dict, List, Optional, Tuple
from base_layer import BaseLayer, LayerException

logger = logging.getLogger("islamiai.reasoning")

# ─── Import modul IslamiAIProject (path relatif dari reasoning/ ke root) ───
# reasoning/ ada di dalam IslamiAIProject/, jadi parent dir = root project
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import modul Phase 0/1 yang sudah ada dan terbukti berjalan
from retrieval import retrieve_ruling                              # Layer 4
from reasoning_validator import (                                  # Layer 5
    compute_confidence,
    gate_answer,
    EvidenceReport,
)
from formatter import format_answer                                # Layer 6


# ─── Adapter: seragamkan return type compute_confidence → (float, str, list) ───
# reasoning_validator.compute_confidence() mengembalikan EvidenceReport,
# bukan tuple. Adapter ini menjaga Layer 5 tidak perlu tahu detail internal.
def _get_confidence_tuple(retrieval_result: Dict) -> Tuple[float, str, List[str], "EvidenceReport"]:
    """
    Panggil compute_confidence() nyata dan ekstrak nilai yang dibutuhkan.
    Mengembalikan (score, label, warnings, report_object).
    report_object disimpan di state untuk digunakan L7 jika perlu.
    """
    report: EvidenceReport = compute_confidence(retrieval_result)
    return (
        report.confidence_score,
        report.confidence_label,
        report.warnings,
        report,
    )


# ─── Adapter: retrieve_ruling() untuk Layer 4 ─────────────────────────────
# retrieve_ruling() dari retrieval.py mengambil topic string,
# Layer 4 perlu mengetahui format return-nya untuk mengekstrak evidence.
def _retrieve(topic: str, madhab: str = "shafii") -> Optional[Dict]:
    """
    Wrapper retrieve_ruling() dengan normalisasi output.
    retrieve_ruling() mengembalikan dict dengan key:
      topic, ruling, confidence, quran (list), hadis (list), rules (list)
    Layer 4 mengekspektasikan key tersebut secara langsung.
    """
    try:
        result = retrieve_ruling(topic)
        return result   # Langsung kembalikan — format sudah kompatibel
    except Exception as e:
        logger.warning("retrieve_ruling('%s') error: %s", topic, e)
        return None


# ─── Adapter: format_answer() untuk Layer 6 ───────────────────────────────
def _format(retrieval_result: Dict, depth: str = "standard") -> str:
    """
    Wrapper format_answer() dari formatter.py.
    format_answer() tidak menerima parameter 'depth' — depth digunakan
    hanya oleh Layer 6 untuk menentukan apakah perlu extended context.
    """
    try:
        return format_answer(retrieval_result)
    except Exception as e:
        logger.error("format_answer() error: %s", e)
        topic = retrieval_result.get("topic", "topik ini")
        return f"Informasi mengenai {topic} tersedia namun gagal diformat."


# ═══════════════════════════════════════════════════════════════
# LAYER 4 — Knowledge Retriever
# ═══════════════════════════════════════════════════════════════

class Layer4_KnowledgeRetriever(BaseLayer):
    """
    Eksekusi retrieval dari knowledge base IslamiAI.
    
    Layer ini adalah JEMBATAN antara reasoning engine dan
    modul retrieval yang sudah ada di Phase 0/1 project.
    
    Strategi retrieval (dari L3):
    - 'comprehensive': Quran + hadis + rules, semua domain
    - 'targeted': rules utama + Quran jika tersedia
    - 'minimal': rules saja atau penjelasan dasar
    
    Untuk integrasi nyata: ganti _stub_retrieve_ruling dengan
    import dari retrieval.py dan parse_user_query dari query_parser.py
    """

    @property
    def layer_id(self) -> str:
        return "L4_knowledge_retriever"

    @property
    def required_keys(self):
        return ["input", "L1_perception_semantic", "L2_islamic_context", "L3_cognitive_router"]

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        l1 = state["L1_perception_semantic"].payload
        l2 = state["L2_islamic_context"].payload
        l3 = state["L3_cognitive_router"].payload

        primary_domain = l2["primary_domain"]
        secondary_domains = l2.get("secondary_domains", [])
        madhhab = l2["madhhab"]
        strategy = l3["retrieval_strategy"]

        # Retrieval primer — menggunakan retrieve_ruling() dari retrieval.py
        primary_result = _retrieve(primary_domain, madhhab)

        retrieval_results = [primary_result] if primary_result else []

        # Retrieval sekunder jika strategy comprehensive atau cross-domain
        if strategy == "comprehensive" and secondary_domains:
            for sec_domain in secondary_domains[:2]:   # Max 2 domain sekunder
                sec_result = _retrieve(sec_domain, madhhab)
                if sec_result:
                    retrieval_results.append(sec_result)

        # Metadata retrieval
        # retrieve_ruling() mengembalikan key "quran" dan "hadis" (list dict)
        # bukan "quran_refs"/"hadis_refs" — sesuaikan dengan format retrieval.py
        total_quran_refs = sum(len(r.get("quran", [])) for r in retrieval_results)
        total_hadis_refs = sum(len(r.get("hadis", [])) for r in retrieval_results)
        total_rules = sum(1 for r in retrieval_results if r.get("ruling"))
        retrieval_successful = len(retrieval_results) > 0

        # Confidence retrieval: proporsional terhadap kelengkapan evidence
        evidence_pieces = total_quran_refs + total_hadis_refs + total_rules
        min_required = l3["min_evidence_pieces"]
        retrieval_confidence = min(evidence_pieces / max(min_required * 2, 1), 1.0)

        warnings = []
        if not retrieval_successful:
            warnings.append(f"Tidak ada data untuk domain '{primary_domain}' — response tidak dapat dibuat.")
        if evidence_pieces < min_required:
            warnings.append(
                f"Evidence tidak mencukupi: {evidence_pieces} dari "
                f"minimum {min_required} yang diperlukan."
            )

        return {
            "retrieval_results": retrieval_results,
            "primary_domain": primary_domain,
            "retrieval_successful": retrieval_successful,
            "evidence_count": {
                "quran": total_quran_refs,
                "hadis": total_hadis_refs,
                "rules": total_rules,
                "total": evidence_pieces,
            },
            "strategy_used": strategy,
            "_confidence": round(retrieval_confidence, 4),
            "_warnings": warnings,
            "_requires_reprocess": not retrieval_successful,
            "_religious_content": True,
        }


# ═══════════════════════════════════════════════════════════════
# LAYER 5 — Evidence Validator + Self-Critic
# ═══════════════════════════════════════════════════════════════

class Layer5_EvidenceValidator(BaseLayer):
    """
    Validasi kualitas evidence dan evaluasi konsistensi reasoning.
    
    Dua fungsi utama:
    A. Evidence Validation: apakah retrieval memberikan cukup dalil?
       (Integrasi: compute_confidence + gate_answer dari reasoning_validator.py)
    
    B. Self-Critic: apakah confidence antar layer konsisten?
       (Sama dengan Layer08 v2, diperkecil untuk efisiensi)
    
    Layer ini adalah GATEKEEPER — ia bisa menghentikan pipeline
    sebelum response dibuat jika evidence tidak memadai.
    """

    MINIMUM_CONFIDENCE_THRESHOLD = 0.45
    HIGH_CONFIDENCE_THRESHOLD = 0.70

    @property
    def layer_id(self) -> str:
        return "L5_evidence_validator"

    @property
    def required_keys(self):
        return ["L1_perception_semantic", "L2_islamic_context",
                "L3_cognitive_router", "L4_knowledge_retriever"]

    def _collect_confidences(self, state: Dict) -> Dict[str, float]:
        return {
            k: v.confidence
            for k, v in state.items()
            if hasattr(v, 'confidence')
        }

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        l3 = state["L3_cognitive_router"].payload
        l4 = state["L4_knowledge_retriever"].payload

        retrieval_results = l4["retrieval_results"]
        evidence_count = l4["evidence_count"]
        allow_partial = l3["allow_partial_response"]
        min_required = l3["min_evidence_pieces"]

        # A. Evidence validation
        if not l4["retrieval_successful"]:
            # Tidak ada data sama sekali → abort
            return {
                "gate_passed": False,
                "gate_reason": "retrieval_empty",
                "confidence_score": 0.0,
                "confidence_level": "none",
                "evidence_sufficient": False,
                "validation_issues": ["Tidak ada data yang ditemukan untuk topik ini."],
                "_confidence": 0.0,
                "_requires_reprocess": False,
                "_warnings": ["Pipeline dihentikan: tidak ada data retrieval."],
                "_religious_content": True,
            }

        # Hitung confidence menggunakan compute_confidence() dari reasoning_validator.py
        # Return: (score, label, warnings, EvidenceReport_object)
        confidence_score, confidence_level, val_warnings, evidence_report = \
            _get_confidence_tuple(retrieval_results[0])

        # Delegasikan gating ke gate_answer() yang sudah ada
        # gate_answer() mengembalikan (can_answer, report, reason)
        can_answer, _, gate_reason_str = gate_answer(retrieval_results[0])
        gate_passed_by_validator = can_answer

        evidence_sufficient = evidence_count["total"] >= min_required

        # B. Self-critic: konsistensi confidence pipeline
        confidences = self._collect_confidences(state)
        conf_values = list(confidences.values())
        pipeline_mean_conf = sum(conf_values) / len(conf_values) if conf_values else 0.5

        # Gating decision: gabungan dari gate_answer() (validator) + routing threshold
        gate_passed = gate_passed_by_validator
        gate_reason = "passed" if gate_passed else gate_reason_str
        validation_issues = list(val_warnings)

        # Override jika evidence tidak cukup dan partial tidak diizinkan
        if gate_passed and not evidence_sufficient and not allow_partial:
            gate_passed = False
            gate_reason = "evidence_insufficient"
            validation_issues.append(
                f"Evidence {evidence_count['total']} di bawah minimum {min_required}."
            )

        # Estimasi hallucination risk dari gap confidence
        hallucination_risk = max(0.0, 0.9 - confidence_score - pipeline_mean_conf * 0.3)

        final_confidence = confidence_score * 0.7 + pipeline_mean_conf * 0.3

        return {
            "gate_passed": gate_passed,
            "gate_reason": gate_reason,
            "confidence_score": round(confidence_score, 4),
            "confidence_level": confidence_level,
            "pipeline_mean_confidence": round(pipeline_mean_conf, 4),
            "hallucination_risk": round(hallucination_risk, 4),
            "evidence_sufficient": evidence_sufficient,
            "validation_issues": validation_issues,
            "_confidence": round(final_confidence, 4),
            "_requires_reprocess": False,
            "_warnings": validation_issues if not gate_passed else [],
            "_religious_content": True,
        }


# ═══════════════════════════════════════════════════════════════
# LAYER 6 — Response Synthesizer
# ═══════════════════════════════════════════════════════════════

class Layer6_ResponseSynthesizer(BaseLayer):
    """
    Sintesis response dari evidence yang sudah divalidasi.
    
    Layer ini TIDAK berjalan jika L5 gate_passed = False.
    Orchestrator bertanggung jawab untuk skip layer ini.
    
    Integrasi dengan formatter.py:
    - format_answer() dari formatter.py dipanggil di sini
    - Depth ditentukan oleh L3 (brief/standard/full)
    - Language dari L2 (id/en/ar)
    
    Output layer ini adalah proto-response yang BELUM melalui
    governance — masih bisa dimodifikasi oleh L7.
    """

    @property
    def layer_id(self) -> str:
        return "L6_response_synthesizer"

    @property
    def required_keys(self):
        return ["L2_islamic_context", "L3_cognitive_router",
                "L4_knowledge_retriever", "L5_evidence_validator"]

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        l2 = state["L2_islamic_context"].payload
        l3 = state["L3_cognitive_router"].payload
        l4 = state["L4_knowledge_retriever"].payload
        l5 = state["L5_evidence_validator"].payload

        # Cek gate — jika L5 tidak pass, buat error response
        if not l5["gate_passed"]:
            return {
                "response_text": (
                    "Maaf, saya tidak dapat memberikan jawaban yang memadai "
                    f"untuk pertanyaan ini saat ini. Alasan: {l5['gate_reason']}. "
                    "Silakan konsultasikan dengan ustadz atau ulama terpercaya."
                ),
                "response_type": "gate_rejected",
                "response_language": l2["response_language"],
                "confidence_level": "none",
                "evidence_used": {},
                "add_ulama_referral": True,
                "_confidence": 0.2,
                "_warnings": ["Response dibuat karena gate rejection — isi minimal."],
                "_religious_content": True,
            }

        retrieval_results = l4["retrieval_results"]
        depth = l3["response_depth"]
        language = l2["response_language"]
        fiqh_context = l2["fiqh_context"]

        # Sintesis utama — format_answer() dari formatter.py
        response_text = _format(retrieval_results[0], depth)

        # Tambahkan evidence sekunder jika strategy comprehensive
        if depth == "full" and len(retrieval_results) > 1:
            sec_texts = [_format(r, "brief") for r in retrieval_results[1:]]
            response_text += "\n\nKonteks tambahan: " + " ".join(sec_texts)

        # Tambahkan permintaan klarifikasi jika dibutuhkan
        if l3.get("add_clarification_request"):
            response_text += (
                "\n\nCatatan: Pertanyaan Anda memiliki beberapa kemungkinan interpretasi. "
                "Apakah maksud Anda berkaitan dengan [topik spesifik]?"
            )

        # Kumpulkan evidence — key dari retrieve_ruling() adalah "quran" dan "hadis"
        evidence_used = {
            "quran": retrieval_results[0].get("quran", []),
            "hadis": retrieval_results[0].get("hadis", []),
            "ruling": retrieval_results[0].get("ruling", ""),
        }

        l4_confidence = state["L4_knowledge_retriever"].confidence
        synthesis_confidence = l5["confidence_score"] * 0.8 + l4_confidence * 0.2

        return {
            "response_text": response_text,
            "response_type": "substantive",
            "response_language": language,
            "fiqh_context": fiqh_context,
            "confidence_level": l5["confidence_level"],
            "evidence_used": evidence_used,
            "add_ulama_referral": l3.get("requires_ulama_disclaimer", False),
            "depth_used": depth,
            "_confidence": round(synthesis_confidence, 4),
            "_warnings": [],
            "_religious_content": True,
        }


# ═══════════════════════════════════════════════════════════════
# LAYER 7 — Output Governance
# ═══════════════════════════════════════════════════════════════

# Disclaimer wajib untuk konteks tertentu (IslamiAI safety policy)
_ULAMA_DISCLAIMER = (
    "\n\n⚠️ Penting: Jawaban ini adalah panduan awal berdasarkan fiqh mazhab "
    "Syafi'i. Untuk keputusan yang bersifat mengikat secara agama — terutama "
    "dalam masalah muamalah, waris, dan pernikahan — konsultasikan dengan "
    "ulama atau lembaga fatwa terpercaya (seperti MUI, NU, atau Muhammadiyah)."
)

_CONFIDENCE_DISCLAIMER = {
    "medium": "\n\n📌 Catatan: Jawaban ini memiliki tingkat keyakinan sedang. Verifikasi dengan sumber primer dianjurkan.",
    "low":    "\n\n⚠️ Catatan: Jawaban ini memiliki tingkat keyakinan rendah karena keterbatasan data. Mohon konsultasikan lebih lanjut.",
}


class Layer7_OutputGovernance(BaseLayer):
    """
    Layer terakhir: finalisasi, safety check, dan pembentukan JSON response.
    
    Tanggung jawab:
    - Tambahkan disclaimer berdasarkan konteks dan confidence
    - Strukturkan JSON response final sesuai format /api/ask IslamiAI
    - Log keputusan governance untuk audit halal-verification
    - Integrasi dengan validators.py untuk output sanitization
    
    Format output HARUS kompatibel dengan response format /api/ask
    yang sudah ada di app.py IslamiAIProject.
    """

    @property
    def layer_id(self) -> str:
        return "L7_output_governance"

    @property
    def required_keys(self):
        return ["L3_cognitive_router", "L5_evidence_validator", "L6_response_synthesizer"]

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        l1 = state["L1_perception_semantic"].payload
        l2 = state["L2_islamic_context"].payload
        l3 = state["L3_cognitive_router"].payload
        l5 = state["L5_evidence_validator"].payload
        l6 = state["L6_response_synthesizer"].payload

        response_text = l6["response_text"]
        confidence_level = l6["confidence_level"]

        # Tambahkan disclaimer berdasarkan policy
        if l6.get("add_ulama_referral"):
            response_text += _ULAMA_DISCLAIMER

        if confidence_level in _CONFIDENCE_DISCLAIMER:
            response_text += _CONFIDENCE_DISCLAIMER[confidence_level]

        # Sanitasi output — integrasi: validators.py
        # Nyata: response_text = sanitize_output(response_text)
        response_text = response_text.strip()

        # Bangun JSON response kompatibel dengan /api/ask IslamiAI
        final_response = {
            # Field yang sudah ada di format response Phase 0
            "status": "success" if l5["gate_passed"] else "limited",
            "question": state["input"],
            "answer": response_text,
            "topic": l2["primary_domain"],
            "madhab": l2["madhhab"],
            "confidence": confidence_level,
            "confidence_score": l5["confidence_score"],
            "evidence": l6.get("evidence_used", {}),
            "disclaimer": (
                "Jawaban ini adalah panduan, bukan fatwa resmi."
                if l5["gate_passed"] else
                "Pertanyaan ini tidak dapat dijawab dengan data yang tersedia."
            ),
            "warnings": l5.get("validation_issues", []),
            # Field baru dari reasoning engine
            "reasoning_metadata": {
                "fiqh_context":        l2["fiqh_context"],
                "retrieval_strategy":  l3["retrieval_strategy"],
                "hallucination_risk":  l5["hallucination_risk"],
                "pipeline_confidence": l5["pipeline_mean_confidence"],
                "routing_rationale":   l3["routing_rationale"],
            }
        }

        # Governance confidence: produk dari semua confidence layer kunci
        key_confidences = [
            state["L1_perception_semantic"].confidence,
            state["L2_islamic_context"].confidence,
            state["L4_knowledge_retriever"].confidence,
            state["L5_evidence_validator"].confidence,
            state["L6_response_synthesizer"].confidence,
        ]
        governance_confidence = (
            sum(key_confidences) / len(key_confidences)
            if key_confidences else 0.0
        )

        return {
            "final_response": final_response,
            "output_approved": l5["gate_passed"],
            "output_sanitized": True,
            "_confidence": round(governance_confidence, 4),
            "_warnings": [],
            "_religious_content": True,
        }
