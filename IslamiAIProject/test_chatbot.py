"""
test_chatbot.py — Unit tests for chatbot.py (Phase 2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategi: mock semua Phase 1 functions (parse, retrieve, gate, format)
→ uji HANYA orchestration logic di chatbot.py.
"""

import pytest
from unittest.mock import patch, MagicMock
from chatbot import chat, is_answerable, get_confidence, ChatResponse, ChatRejection


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES — mock EvidenceReport
# ─────────────────────────────────────────────────────────────────────────────

def make_report(score=0.85, label="high", warnings=None, disclaimer="", answerable=True):
    """Helper buat mock EvidenceReport."""
    r = MagicMock()
    r.confidence_score = score
    r.confidence_label = label
    r.warnings = warnings or []
    r.disclaimer = disclaimer
    r.is_answerable = answerable
    return r


MOCK_RETRIEVAL = {
    "topic": "syahadat",
    "ruling": "wajib",
    "madhab": "Shafi'i",
    "quran": [{"arabic_text": "...", "transliteration": "...", "translation": "..."}],
    "hadis": [{"source": "Bukhari", "authenticity": "sahih", "translation": "..."}],
    "keywords": ["syahadat"],
    "reasoning": "Syahadat adalah rukun Islam pertama.",
}

MOCK_FORMATTED = "======\n🔖 HUKUM: WAJIB\n======"


# ─────────────────────────────────────────────────────────────────────────────
# HAPPY PATH
# ─────────────────────────────────────────────────────────────────────────────

class TestChatHappyPath:

    @patch("chatbot.format_answer", return_value=MOCK_FORMATTED)
    @patch("chatbot.gate_answer", return_value=(True, make_report(), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_returns_ok_status(self, mock_parse, mock_retrieve, mock_gate, mock_format):
        result = chat("apa itu syahadat")
        assert result["status"] == "ok"

    @patch("chatbot.format_answer", return_value=MOCK_FORMATTED)
    @patch("chatbot.gate_answer", return_value=(True, make_report(score=0.92), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_answer_is_formatted_output(self, mock_parse, mock_retrieve, mock_gate, mock_format):
        result = chat("apa itu syahadat")
        assert result["answer"] == MOCK_FORMATTED

    @patch("chatbot.format_answer", return_value=MOCK_FORMATTED)
    @patch("chatbot.gate_answer", return_value=(True, make_report(score=0.92, label="high"), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_confidence_score_preserved(self, mock_parse, mock_retrieve, mock_gate, mock_format):
        result = chat("apa itu syahadat")
        assert result["confidence_score"] == 0.92
        assert result["confidence_label"] == "high"

    @patch("chatbot.format_answer", return_value=MOCK_FORMATTED)
    @patch("chatbot.gate_answer", return_value=(True, make_report(), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_topic_preserved(self, mock_parse, mock_retrieve, mock_gate, mock_format):
        result = chat("apa itu syahadat")
        assert result["topic"] == "syahadat"

    @patch("chatbot.format_answer", return_value=MOCK_FORMATTED)
    @patch("chatbot.gate_answer", return_value=(True, make_report(), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_timestamp_present(self, mock_parse, mock_retrieve, mock_gate, mock_format):
        result = chat("apa itu syahadat")
        assert "timestamp" in result
        assert result["timestamp"] != ""

    @patch("chatbot.format_answer", return_value=MOCK_FORMATTED)
    @patch("chatbot.gate_answer", return_value=(True, make_report(warnings=["hadis dhaif"]), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_warnings_forwarded(self, mock_parse, mock_retrieve, mock_gate, mock_format):
        result = chat("apa itu syahadat")
        assert "hadis dhaif" in result["warnings"]


# ─────────────────────────────────────────────────────────────────────────────
# NO MATCH (parse returns None)
# ─────────────────────────────────────────────────────────────────────────────

class TestChatNoMatch:

    @patch("chatbot.gate_answer", return_value=(False, None, "Topik tidak ditemukan."))
    @patch("chatbot.retrieve_ruling", return_value=None)
    @patch("chatbot.parse_user_query", return_value=None)
    def test_no_match_status(self, mock_parse, mock_retrieve, mock_gate):
        result = chat("cuaca hari ini bagaimana")
        assert result["status"] == "no_match"

    @patch("chatbot.gate_answer", return_value=(False, None, "Topik tidak ditemukan."))
    @patch("chatbot.retrieve_ruling", return_value=None)
    @patch("chatbot.parse_user_query", return_value=None)
    def test_no_match_reason_forwarded(self, mock_parse, mock_retrieve, mock_gate):
        result = chat("cuaca hari ini bagaimana")
        assert result["reason"] == "Topik tidak ditemukan."

    @patch("chatbot.gate_answer", return_value=(False, None, "Tidak ada dalil."))
    @patch("chatbot.retrieve_ruling", return_value=None)
    @patch("chatbot.parse_user_query", return_value=None)
    def test_no_match_topic_is_none(self, mock_parse, mock_retrieve, mock_gate):
        result = chat("sesuatu yang tidak ada")
        assert result["topic"] is None

    @patch("chatbot.gate_answer", return_value=(False, None, "Tidak ada dalil."))
    @patch("chatbot.retrieve_ruling", return_value=None)
    @patch("chatbot.parse_user_query", return_value=None)
    def test_retrieve_not_called_when_no_topic(self, mock_parse, mock_retrieve, mock_gate):
        chat("sesuatu yang tidak ada")
        mock_retrieve.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# REJECTED (topic found, but confidence too low)
# ─────────────────────────────────────────────────────────────────────────────

class TestChatRejected:

    @patch("chatbot.gate_answer", return_value=(
        False,
        make_report(score=0.30, label="insufficient", answerable=False),
        "❌ Confidence terlalu rendah."
    ))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="zakat_muallaf")
    def test_rejected_status(self, mock_parse, mock_retrieve, mock_gate):
        result = chat("hukum zakat muallaf")
        assert result["status"] == "rejected"

    @patch("chatbot.gate_answer", return_value=(
        False,
        make_report(score=0.30, label="insufficient", answerable=False),
        "❌ Confidence terlalu rendah."
    ))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="zakat_muallaf")
    def test_rejected_confidence_score_preserved(self, mock_parse, mock_retrieve, mock_gate):
        result = chat("hukum zakat muallaf")
        assert result["confidence_score"] == 0.30
        assert result["confidence_label"] == "insufficient"

    @patch("chatbot.gate_answer", return_value=(
        False,
        make_report(score=0.30, label="insufficient", answerable=False),
        "❌ Confidence terlalu rendah."
    ))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="zakat_muallaf")
    def test_rejected_topic_still_returned(self, mock_parse, mock_retrieve, mock_gate):
        result = chat("hukum zakat muallaf")
        assert result["topic"] == "zakat_muallaf"

    @patch("chatbot.gate_answer", return_value=(
        False,
        make_report(score=0.30, label="insufficient"),
        "Tanya ulama."
    ))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="zakat_muallaf")
    def test_format_not_called_when_rejected(self, mock_parse, mock_retrieve, mock_gate):
        with patch("chatbot.format_answer") as mock_format:
            chat("hukum zakat muallaf")
            mock_format.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# ERROR HANDLING
# ─────────────────────────────────────────────────────────────────────────────

class TestChatErrorHandling:

    @patch("chatbot.parse_user_query", side_effect=Exception("DB error"))
    def test_exception_returns_error_status(self, mock_parse):
        result = chat("pertanyaan apapun")
        assert result["status"] == "error"

    @patch("chatbot.parse_user_query", side_effect=Exception("DB error"))
    def test_exception_returns_friendly_reason(self, mock_parse):
        result = chat("pertanyaan apapun")
        assert "kesalahan internal" in result["reason"].lower()

    @patch("chatbot.parse_user_query", side_effect=Exception("DB error"))
    def test_exception_confidence_zero(self, mock_parse):
        result = chat("pertanyaan apapun")
        assert result["confidence_score"] == 0.0

    @patch("chatbot.retrieve_ruling", side_effect=RuntimeError("retrieval crash"))
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_retrieve_exception_caught(self, mock_parse, mock_retrieve):
        result = chat("syahadat")
        assert result["status"] == "error"

    @patch("chatbot.format_answer", side_effect=ValueError("format crash"))
    @patch("chatbot.gate_answer", return_value=(True, make_report(), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_format_exception_caught(self, mock_parse, mock_retrieve, mock_gate, mock_format):
        result = chat("syahadat")
        assert result["status"] == "error"


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE CALL ORDER
# ─────────────────────────────────────────────────────────────────────────────

class TestPipelineOrder:

    @patch("chatbot.format_answer", return_value=MOCK_FORMATTED)
    @patch("chatbot.gate_answer", return_value=(True, make_report(), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_parse_called_with_original_question(self, mock_parse, *_):
        chat("apa hukum syahadat?")
        mock_parse.assert_called_once_with("apa hukum syahadat?")

    @patch("chatbot.format_answer", return_value=MOCK_FORMATTED)
    @patch("chatbot.gate_answer", return_value=(True, make_report(), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_retrieve_called_with_topic(self, mock_parse, mock_retrieve, *_):
        chat("apa hukum syahadat?")
        mock_retrieve.assert_called_once_with("syahadat")

    @patch("chatbot.format_answer", return_value=MOCK_FORMATTED)
    @patch("chatbot.gate_answer", return_value=(True, make_report(), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_gate_called_with_retrieval_result(self, mock_parse, mock_retrieve, mock_gate, *_):
        chat("apa hukum syahadat?")
        mock_gate.assert_called_once_with(MOCK_RETRIEVAL)

    @patch("chatbot.format_answer", return_value=MOCK_FORMATTED)
    @patch("chatbot.gate_answer", return_value=(True, make_report(), ""))
    @patch("chatbot.retrieve_ruling", return_value=MOCK_RETRIEVAL)
    @patch("chatbot.parse_user_query", return_value="syahadat")
    def test_format_called_with_retrieval_result(self, mock_parse, mock_retrieve, mock_gate, mock_format):
        chat("apa hukum syahadat?")
        mock_format.assert_called_once_with(MOCK_RETRIEVAL)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

class TestHelpers:

    @patch("chatbot.chat", return_value={"status": "ok", "confidence_score": 0.9})
    def test_is_answerable_true(self, mock_chat):
        assert is_answerable("syahadat") is True

    @patch("chatbot.chat", return_value={"status": "rejected", "confidence_score": 0.3})
    def test_is_answerable_false(self, mock_chat):
        assert is_answerable("sesuatu tidak jelas") is False

    @patch("chatbot.chat", return_value={"status": "ok", "confidence_score": 0.87})
    def test_get_confidence_ok(self, mock_chat):
        assert get_confidence("syahadat") == 0.87

    @patch("chatbot.chat", return_value={"status": "error", "confidence_score": 0.0})
    def test_get_confidence_error(self, mock_chat):
        assert get_confidence("error") == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

class TestDataStructures:

    def test_chat_response_to_dict(self):
        r = ChatResponse(
            status="ok", answer="test", topic="syahadat",
            confidence_score=0.9, confidence_label="high",
            warnings=[], disclaimer=""
        )
        d = r.to_dict()
        assert d["status"] == "ok"
        assert d["confidence_score"] == 0.9
        assert "timestamp" in d

    def test_chat_rejection_to_dict(self):
        r = ChatRejection(
            status="rejected", reason="low confidence",
            topic="syahadat", confidence_score=0.3,
            confidence_label="insufficient", warnings=[]
        )
        d = r.to_dict()
        assert d["status"] == "rejected"
        assert d["topic"] == "syahadat"
        assert "timestamp" in d

    def test_chat_response_timestamp_auto_filled(self):
        r = ChatResponse(
            status="ok", answer="x", topic="y",
            confidence_score=1.0, confidence_label="high",
            warnings=[], disclaimer=""
        )
        assert r.timestamp != ""

    def test_chat_rejection_topic_can_be_none(self):
        r = ChatRejection(
            status="no_match", reason="not found",
            topic=None, confidence_score=0.0,
            confidence_label="insufficient", warnings=[]
        )
        assert r.topic is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
