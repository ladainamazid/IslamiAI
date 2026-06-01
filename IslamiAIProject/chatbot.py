"""
chatbot.py — IslamiAI Chatbot Layer (Phase 2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pipeline:
  user input
    → parse_user_query()      [query_parser.py]
    → retrieve_ruling()       [retrieval.py]
    → gate_answer()           [reasoning_validator.py]
    → format_answer()         [formatter.py]
    → ChatResponse dict

Tidak ada class baru. Tidak ada abstraction baru.
Hanya orchestration tipis di atas fungsi Phase 1.
"""

import logging
from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from query_parser import parse_user_query
from retrieval import retrieve_ruling
from reasoning_validator import gate_answer, EvidenceReport
from formatter import format_answer

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# RESPONSE STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ChatResponse:
    """Response sukses dari pipeline."""
    status: str                     # "ok"
    answer: str                     # formatted output dari format_answer()
    topic: str                      # topic key yg ditemukan
    confidence_score: float         # 0.0 – 1.0
    confidence_label: str           # "high" | "medium" | "low" | "insufficient"
    warnings: list
    disclaimer: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChatRejection:
    """Response ketika pipeline menolak menjawab."""
    status: str                     # "rejected" | "no_match"
    reason: str                     # penjelasan ke user
    topic: Optional[str]            # topic key jika ditemukan, else None
    confidence_score: float
    confidence_label: str
    warnings: list
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CHAT FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def chat(question: str) -> dict:
    """
    Satu-satunya fungsi publik chatbot.

    ARGS:
        question (str): Pertanyaan dari user, teks bebas.

    RETURNS:
        dict: ChatResponse.to_dict()  jika bisa dijawab
              ChatRejection.to_dict() jika ditolak

    FLOW:
        1. parse_user_query()  → topic key
        2. retrieve_ruling()   → retrieval_result dict
        3. gate_answer()       → (can_answer, report, reason)
        4. format_answer()     → formatted string

    NEVER RAISES: semua exception ditangkap dan dikembalikan
    sebagai ChatRejection dengan status "error".
    """

    logger.info(f"[chat] question='{question[:80]}'")

    try:
        # ── STEP 1: Parse ────────────────────────────────────────────────────
        topic = parse_user_query(question)
        logger.debug(f"[chat] topic resolved → {topic}")

        # ── STEP 2: Retrieve ─────────────────────────────────────────────────
        retrieval_result = retrieve_ruling(topic) if topic else None

        # ── STEP 3: Gate ─────────────────────────────────────────────────────
        can_answer, report, reason = gate_answer(retrieval_result)

        # ── STEP 4a: Ditolak ─────────────────────────────────────────────────
        if not can_answer:
            status = "no_match" if topic is None else "rejected"
            return ChatRejection(
                status=status,
                reason=reason,
                topic=topic,
                confidence_score=report.confidence_score if report else 0.0,
                confidence_label=report.confidence_label if report else "insufficient",
                warnings=report.warnings if report else [],
            ).to_dict()

        # ── STEP 4b: Format & kembalikan ─────────────────────────────────────
        formatted = format_answer(retrieval_result)

        return ChatResponse(
            status="ok",
            answer=formatted,
            topic=topic,
            confidence_score=report.confidence_score,
            confidence_label=report.confidence_label,
            warnings=report.warnings,
            disclaimer=report.disclaimer,
        ).to_dict()

    except Exception as exc:
        logger.exception(f"[chat] unexpected error: {exc}")
        return ChatRejection(
            status="error",
            reason="Terjadi kesalahan internal. Silakan coba lagi.",
            topic=None,
            confidence_score=0.0,
            confidence_label="insufficient",
            warnings=[str(exc)],
        ).to_dict()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS (opsional, dipakai app.py / tests)
# ─────────────────────────────────────────────────────────────────────────────

def is_answerable(question: str) -> bool:
    """True jika pertanyaan ini akan menghasilkan ChatResponse (status='ok')."""
    result = chat(question)
    return result.get("status") == "ok"


def get_confidence(question: str) -> float:
    """Shortcut: kembalikan confidence_score saja (0.0 jika ditolak)."""
    result = chat(question)
    return result.get("confidence_score", 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)

    test_questions = [
        "apa itu syahadat",
        "boleh tidak shalat tanpa wudhu",
        "hukum daging babi",
        "pertanyaan tidak relevan tentang cuaca",
    ]

    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        result = chat(q)
        print(f"Status    : {result['status']}")
        if result['status'] == 'ok':
            print(f"Topic     : {result['topic']}")
            print(f"Confidence: {result['confidence_score']} ({result['confidence_label']})")
            print(f"Answer    :\n{result['answer']}")
        else:
            print(f"Reason    : {result['reason']}")
