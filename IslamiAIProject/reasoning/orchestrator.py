"""
reasoning/orchestrator.py
─────────────────────────────────────────────────────────────────
Entry point reasoning engine untuk IslamiAIProject.

Ini yang dipanggil oleh chatbot.py:
  from reasoning.orchestrator import ReasoningOrchestrator
  self.reasoner = ReasoningOrchestrator()
  reasoning_state, report = self.reasoner.run(user_input)
  return reasoning_state["L7_output_governance"].payload["final_response"]

Control flow:
  L1 → L2 → L3 → L4 → L5 ─┬─ [gate passed]  → L6 → L7
                             └─ [gate failed]  → L6(rejected) → L7

Feedback loop: jika L5 meminta reprocess, ulangi dari L4 dengan
parameter yang diperketat (max 1x retry untuk mencegah infinite loop).
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from base_layer import BaseLayer, LayerException, LayerResult
from layer1_perception_semantic import Layer1_PerceptionSemantic
from layer2_3_context_router import Layer2_IslamicContext, Layer3_CognitiveRouter
from layer4567_retrieval_to_governance import (
    Layer4_KnowledgeRetriever,
    Layer5_EvidenceValidator,
    Layer6_ResponseSynthesizer,
    Layer7_OutputGovernance,
)

logger = logging.getLogger("islamiai.orchestrator")


@dataclass
class ReasoningReport:
    """Laporan eksekusi untuk monitoring dan debugging."""
    layers_executed: List[str] = field(default_factory=list)
    layers_skipped: List[str] = field(default_factory=list)
    reprocess_count: int = 0
    final_status: str = "pending"
    total_time_ms: float = 0.0
    all_warnings: List[str] = field(default_factory=list)


class ReasoningOrchestrator:
    """
    Orchestrator 7-layer untuk IslamiAI reasoning engine.

    Penggunaan di chatbot.py:
    ─────────────────────────
    class IslamicKnowledgeChatbot:
        def __init__(self):
            self.reasoner = ReasoningOrchestrator()

        def chat(self, user_input: str) -> dict:
            state, report = self.reasoner.run(user_input)
            l7 = state.get("L7_output_governance")
            if l7 and l7.payload.get("output_approved"):
                return l7.payload["final_response"]
            else:
                return {
                    "status": "error",
                    "answer": "Terjadi kesalahan internal.",
                    "warnings": report.all_warnings,
                }
    """

    MAX_REPROCESS = 1   # Cukup 1 retry — lebih dari ini jarang membantu

    def __init__(self):
        # Layer urutan eksekusi tetap
        self.layers: List[BaseLayer] = [
            Layer1_PerceptionSemantic(),
            Layer2_IslamicContext(),
            Layer3_CognitiveRouter(),
            Layer4_KnowledgeRetriever(),
            Layer5_EvidenceValidator(),
            Layer6_ResponseSynthesizer(),
            Layer7_OutputGovernance(),
        ]

    def _run_layer(
        self,
        layer: BaseLayer,
        state: Dict,
        report: ReasoningReport,
        skip_set: set
    ) -> Dict:
        if layer.layer_id in skip_set:
            logger.info("SKIP | %s", layer.layer_id)
            report.layers_skipped.append(layer.layer_id)
            return state

        try:
            state = layer.execute(state)
            result: LayerResult = state[layer.layer_id]
            report.layers_executed.append(layer.layer_id)
            report.total_time_ms += result.execution_time_ms
            if result.warnings:
                report.all_warnings.extend(result.warnings)
            logger.info(
                "OK   | %-40s | conf=%.3f | %.1fms",
                layer.layer_id, result.confidence, result.execution_time_ms
            )
        except LayerException as e:
            report.layers_failed = getattr(report, 'layers_failed', [])
            report.layers_failed.append(layer.layer_id)
            logger.error("FAIL | %s | %s | recoverable=%s",
                         layer.layer_id, e.reason, e.recoverable)
            if not e.recoverable:
                report.final_status = "aborted"
                raise

        return state

    def run(self, user_input: str) -> Tuple[Dict[str, Any], ReasoningReport]:
        state: Dict[str, Any] = {"input": user_input.strip()}
        report = ReasoningReport()

        reprocess_count = 0
        while reprocess_count <= self.MAX_REPROCESS:
            # Tentukan skip set dari L3 (jika sudah berjalan)
            skip_set = set()
            l3_result = state.get("L3_cognitive_router")
            if l3_result:
                skip_set = set(l3_result.payload.get("skip_layers", []))

            for layer in self.layers:
                try:
                    state = self._run_layer(layer, state, report, skip_set)
                except LayerException:
                    report.final_status = "aborted"
                    return state, report

                # Cek setelah L5 apakah perlu reprocess
                if layer.layer_id == "L5_evidence_validator":
                    l5_result = state.get("L5_evidence_validator")
                    if (l5_result and l5_result.requires_reprocess
                            and reprocess_count < self.MAX_REPROCESS):
                        reprocess_count += 1
                        report.reprocess_count = reprocess_count
                        logger.warning(
                            "L5 meminta reprocess (attempt %d/%d)",
                            reprocess_count, self.MAX_REPROCESS
                        )
                        # Hapus L4 dan L5 dari state untuk diulang
                        state.pop("L4_knowledge_retriever", None)
                        state.pop("L5_evidence_validator", None)
                        break   # Keluar dari inner for-loop, ulangi while

            else:
                # Inner loop selesai tanpa break — tidak ada reprocess
                break

        report.final_status = "success"
        logger.info(
            "Pipeline selesai | status=%s | layers=%d | reprocess=%d | %.1fms",
            report.final_status,
            len(report.layers_executed),
            report.reprocess_count,
            report.total_time_ms,
        )
        return state, report


# ─── Test mandiri ───────────────────────────────────────────────
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)-8s | %(name)s | %(message)s")

    test_queries = [
        "apa hukum meninggalkan shalat?",
        "bagaimana cara berwudhu yang benar?",
        "apakah bunga bank termasuk riba?",
        "apa itu syahadat dan bagaimana cara mengucapkannya?",
    ]

    orchestrator = ReasoningOrchestrator()

    for q in test_queries:
        print(f"\n{'─'*60}")
        print(f"QUERY: {q}")
        print('─'*60)
        final_state, exec_report = orchestrator.run(q)

        l7 = final_state.get("L7_output_governance")
        if l7:
            resp = l7.payload.get("final_response", {})
            print(f"STATUS   : {resp.get('status')}")
            print(f"TOPIC    : {resp.get('topic')}")
            print(f"CONFIDENCE: {resp.get('confidence')} ({resp.get('confidence_score', 0):.3f})")
            print(f"ANSWER   : {resp.get('answer', '')[:200]}...")
            if resp.get('warnings'):
                print(f"WARNINGS : {resp['warnings']}")

        print(f"\nEXEC REPORT: {exec_report.layers_executed} | {exec_report.total_time_ms:.1f}ms")
