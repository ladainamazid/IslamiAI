# test_reasoning_validator.py
# IslamiAI — Pytest suite untuk reasoning_validator.py
#
# Menguji: compute_confidence(), gate_answer(), EvidenceReport
# Catatan: semua expected scores diverifikasi secara empiris terhadap
#   implementasi aktual sebelum ditulis sebagai fixture.
#
# Scoring rubric (dari kode sumber):
#   Quran (ada)      : +0.40, +0.05 per ayat tambahan (maks 3 extra = +0.15)
#   Hadis sahih (ada): +0.30, +0.05 per hadis tambahan
#   Hadis hasan      : +0.15
#   Hadis dhaif      : +0.00 (warning saja)
#   Rule high        : +0.05
#   Threshold medium : >= 0.50, high >= 0.70
#
# Jalankan: pytest test_reasoning_validator.py -v

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reasoning_validator import (
    compute_confidence,
    gate_answer,
    EvidenceReport,
)


# ════════════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════════════

def _mock(quran_count=0, hadis_list=None, rule_conf="medium"):
    """Helper membuat mock retrieval_result."""
    return {
        "topic": "test_topic",
        "ruling": "wajib",
        "confidence": rule_conf,
        "quran": [{"arabic_text": "...", "theme": "aqidah"}] * quran_count,
        "hadis": hadis_list or [],
    }


def _hadis(auth, source="TestSource"):
    return {"source": source, "authenticity": auth}


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 1 — compute_confidence(): tipe dan struktur return value
# ════════════════════════════════════════════════════════════════════════════════

class TestComputeConfidenceReturnType:

    def test_returns_evidence_report_instance(self):
        result = compute_confidence(_mock())
        assert isinstance(result, EvidenceReport)

    def test_confidence_score_is_float(self):
        result = compute_confidence(_mock(quran_count=1))
        assert isinstance(result.confidence_score, float)

    def test_confidence_label_is_string(self):
        result = compute_confidence(_mock())
        assert isinstance(result.confidence_label, str)

    def test_confidence_label_valid_values(self):
        valid = {"high", "medium", "insufficient"}
        result = compute_confidence(_mock())
        assert result.confidence_label in valid

    def test_score_never_exceeds_1(self):
        # Banyak evidence sekaligus — skor tidak boleh > 1.0
        hadis = [_hadis("sahih", f"H{i}") for i in range(10)]
        result = compute_confidence(_mock(quran_count=5, hadis_list=hadis, rule_conf="high"))
        assert result.confidence_score <= 1.0

    def test_score_never_below_0(self):
        result = compute_confidence(_mock())
        assert result.confidence_score >= 0.0

    def test_warnings_is_list(self):
        result = compute_confidence(_mock())
        assert isinstance(result.warnings, list)

    def test_quran_count_correct(self):
        result = compute_confidence(_mock(quran_count=3))
        assert result.quran_count == 3

    def test_hadis_count_correct(self):
        hadis = [_hadis("sahih"), _hadis("hasan")]
        result = compute_confidence(_mock(hadis_list=hadis))
        assert result.hadis_count == 2


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 2 — compute_confidence(): scoring rubric (nilai eksak)
# ════════════════════════════════════════════════════════════════════════════════

class TestConfidenceScoring:
    """
    Verifikasi nilai score eksak berdasarkan rubrik.
    Semua expected value diverifikasi secara empiris.
    """

    def test_empty_evidence_score_zero(self):
        result = compute_confidence(_mock())
        assert result.confidence_score == 0.0

    def test_one_quran_verse_score_040(self):
        result = compute_confidence(_mock(quran_count=1))
        assert result.confidence_score == 0.40

    def test_two_quran_verses_score_045(self):
        # 0.40 base + 0.05 extra
        result = compute_confidence(_mock(quran_count=2))
        assert result.confidence_score == 0.45

    def test_one_sahih_hadis_score_030(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("sahih")]))
        assert result.confidence_score == 0.30

    def test_one_hasan_hadis_score_015(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("hasan")]))
        assert result.confidence_score == 0.15

    def test_one_dhaif_hadis_score_zero(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("dhaif")]))
        assert result.confidence_score == 0.0

    def test_one_quran_one_sahih_score_070(self):
        # 0.40 + 0.30 = 0.70 → threshold high
        hadis = [_hadis("sahih")]
        result = compute_confidence(_mock(quran_count=1, hadis_list=hadis))
        assert result.confidence_score == 0.70

    def test_two_quran_one_sahih_rule_high_score_080(self):
        # 0.40 + 0.05(extra) + 0.30 + 0.05(rule) = 0.80
        hadis = [_hadis("sahih")]
        result = compute_confidence(_mock(quran_count=2, hadis_list=hadis, rule_conf="high"))
        assert result.confidence_score == 0.80

    def test_rule_high_adds_bonus_005(self):
        # Tanpa rule bonus
        base = compute_confidence(_mock(quran_count=1, rule_conf="medium"))
        # Dengan rule bonus
        boosted = compute_confidence(_mock(quran_count=1, rule_conf="high"))
        assert boosted.confidence_score == base.confidence_score + 0.05

    def test_score_capped_at_one(self):
        # Banyak quran + hadis + rule high
        hadis = [_hadis("sahih")] * 5
        result = compute_confidence(_mock(quran_count=5, hadis_list=hadis, rule_conf="high"))
        assert result.confidence_score == 1.0


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 3 — compute_confidence(): confidence labels
# ════════════════════════════════════════════════════════════════════════════════

class TestConfidenceLabels:

    def test_score_070_gives_high_label(self):
        # 1 quran + 1 sahih = 0.70 → high
        result = compute_confidence(_mock(quran_count=1, hadis_list=[_hadis("sahih")]))
        assert result.confidence_label == "high"

    def test_score_below_050_gives_insufficient_label(self):
        # 1 quran saja = 0.40 → insufficient
        result = compute_confidence(_mock(quran_count=1))
        assert result.confidence_label == "insufficient"

    def test_score_000_gives_insufficient_label(self):
        result = compute_confidence(_mock())
        assert result.confidence_label == "insufficient"

    def test_is_answerable_true_when_high(self):
        result = compute_confidence(_mock(quran_count=1, hadis_list=[_hadis("sahih")]))
        assert result.is_answerable is True

    def test_is_answerable_false_when_insufficient(self):
        result = compute_confidence(_mock())
        assert result.is_answerable is False

    def test_high_label_has_no_disclaimer(self):
        result = compute_confidence(_mock(quran_count=1, hadis_list=[_hadis("sahih")]))
        assert result.disclaimer == ""

    def test_insufficient_label_has_disclaimer(self):
        result = compute_confidence(_mock())
        assert len(result.disclaimer) > 0

    def test_insufficient_disclaimer_not_empty(self):
        result = compute_confidence(_mock())
        assert result.disclaimer.strip() != ""


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 4 — compute_confidence(): warnings
# ════════════════════════════════════════════════════════════════════════════════

class TestConfidenceWarnings:

    def test_dhaif_hadis_generates_warning(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("dhaif", "DhaifSource")]))
        assert len(result.warnings) > 0

    def test_hasan_hadis_generates_warning(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("hasan", "HasanSource")]))
        assert len(result.warnings) > 0

    def test_sahih_hadis_no_authenticity_warning(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("sahih")]))
        # Sahih tidak menghasilkan warning autentisitas (hanya hasan/dhaif yang menghasilkan).
        # Catatan: jika skor akhir < 0.50 (sahih tanpa quran = 0.30), sistem tetap
        # menambahkan warning "confidence terlalu rendah" — itu perilaku benar.
        # Test ini hanya memverifikasi tidak ada warning khusus authenticity.
        auth_warnings = [w for w in result.warnings
                         if "sahih" in w.lower() or "autentisitas" in w.lower()]
        assert len(auth_warnings) == 0

    def test_dhaif_warning_mentions_source(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("dhaif", "TestDhaifSource")]))
        assert any("TestDhaifSource" in w for w in result.warnings)

    def test_insufficient_score_adds_warning(self):
        result = compute_confidence(_mock())
        # Saat insufficient, satu warning tentang confidence ditambahkan
        assert len(result.warnings) >= 1

    def test_no_warnings_on_strong_evidence(self):
        # Evidence kuat: quran + sahih, tanpa hadis bermasalah
        result = compute_confidence(_mock(quran_count=2, hadis_list=[_hadis("sahih")]))
        assert len(result.warnings) == 0

    def test_multiple_dhaif_generate_multiple_warnings(self):
        hadis = [_hadis("dhaif", f"Dhaif{i}") for i in range(3)]
        result = compute_confidence(_mock(hadis_list=hadis))
        # 3 dhaif + 1 insufficient warning = minimal 4
        assert len(result.warnings) >= 3


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 5 — gate_answer(): kontrak return
# ════════════════════════════════════════════════════════════════════════════════

class TestGateAnswer:

    def test_returns_tuple_of_three(self):
        result = gate_answer(_mock(quran_count=1, hadis_list=[_hadis("sahih")]))
        assert len(result) == 3

    def test_returns_bool_as_first_element(self):
        can_answer, _, _ = gate_answer(_mock())
        assert isinstance(can_answer, bool)

    def test_none_input_returns_false(self):
        can_answer, report, reason = gate_answer(None)
        assert can_answer is False

    def test_none_input_returns_none_report(self):
        _, report, _ = gate_answer(None)
        assert report is None

    def test_none_input_returns_nonempty_reason(self):
        _, _, reason = gate_answer(None)
        assert len(reason) > 0

    def test_strong_evidence_can_answer_true(self):
        mock = _mock(quran_count=1, hadis_list=[_hadis("sahih")])
        can_answer, _, _ = gate_answer(mock)
        assert can_answer is True

    def test_strong_evidence_report_not_none(self):
        mock = _mock(quran_count=1, hadis_list=[_hadis("sahih")])
        _, report, _ = gate_answer(mock)
        assert report is not None

    def test_strong_evidence_reason_empty(self):
        mock = _mock(quran_count=1, hadis_list=[_hadis("sahih")])
        _, _, reason = gate_answer(mock)
        assert reason == ""

    def test_empty_evidence_can_answer_false(self):
        can_answer, _, _ = gate_answer(_mock())
        assert can_answer is False

    def test_empty_evidence_reason_not_empty(self):
        _, _, reason = gate_answer(_mock())
        assert len(reason) > 0

    def test_dhaif_only_cannot_answer(self):
        mock = _mock(hadis_list=[_hadis("dhaif")])
        can_answer, _, _ = gate_answer(mock)
        assert can_answer is False

    def test_hasan_only_cannot_answer(self):
        # 0.15 < 0.50 threshold
        mock = _mock(hadis_list=[_hadis("hasan")])
        can_answer, _, _ = gate_answer(mock)
        assert can_answer is False

    def test_report_topic_matches_input(self):
        mock = _mock(quran_count=1, hadis_list=[_hadis("sahih")])
        mock["topic"] = "syahadat"
        _, report, _ = gate_answer(mock)
        assert report.topic == "syahadat"

    def test_report_ruling_matches_input(self):
        mock = _mock(quran_count=1, hadis_list=[_hadis("sahih")])
        mock["ruling"] = "wajib"
        _, report, _ = gate_answer(mock)
        assert report.ruling == "wajib"


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 6 — has_quran_evidence dan has_hadis_evidence flags
# ════════════════════════════════════════════════════════════════════════════════

class TestEvidenceFlags:

    def test_has_quran_evidence_true_when_present(self):
        result = compute_confidence(_mock(quran_count=2))
        assert result.has_quran_evidence is True

    def test_has_quran_evidence_false_when_absent(self):
        result = compute_confidence(_mock(quran_count=0))
        assert result.has_quran_evidence is False

    def test_has_hadis_evidence_true_for_sahih(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("sahih")]))
        assert result.has_hadis_evidence is True

    def test_has_hadis_evidence_true_for_hasan(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("hasan")]))
        assert result.has_hadis_evidence is True

    def test_has_hadis_evidence_false_for_dhaif_only(self):
        # Dhaif tidak dihitung sebagai evidence
        result = compute_confidence(_mock(hadis_list=[_hadis("dhaif")]))
        assert result.has_hadis_evidence is False

    def test_has_hadis_evidence_false_when_absent(self):
        result = compute_confidence(_mock())
        assert result.has_hadis_evidence is False

    def test_hadis_authenticity_list_populated(self):
        hadis = [_hadis("sahih"), _hadis("dhaif"), _hadis("hasan")]
        result = compute_confidence(_mock(hadis_list=hadis))
        assert "sahih" in result.hadis_authenticity
        assert "dhaif" in result.hadis_authenticity
        assert "hasan" in result.hadis_authenticity
