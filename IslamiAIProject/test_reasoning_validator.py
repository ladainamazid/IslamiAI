"""
test_reasoning_validator.py
Bagian 1-6: test suite lama (57 test)
Bagian 7  : TestKitabCorpusScoring — path kitab_corpus (33 test baru)
Total     : 90 test
"""

import pytest
from reasoning_validator import EvidenceReport, compute_confidence, gate_answer


# ─── Helpers ──────────────────────────────────────────────────

def _hadis(auth: str, source: str = "Test Hadis") -> dict:
    return {"source": source, "authenticity": auth}


def _mock(
    quran_count: int = 0,
    hadis_list: list = None,
    ruling: str = "test_ruling",
    confidence: str = "medium",
    topic: str = "test_topic",
) -> dict:
    quran = [{"arabic_text": f"ayat_{i}", "surah_ayah": f"2:{i}"}
             for i in range(quran_count)]
    return {
        "topic": topic,
        "ruling": ruling,
        "madhab": "shafii",
        "quran": quran,
        "hadis": hadis_list or [],
        "confidence": confidence,
    }


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 1 — Return type & struktur dasar
# ════════════════════════════════════════════════════════════════════════════════

class TestComputeConfidenceReturnType:

    def test_returns_evidence_report_instance(self):
        result = compute_confidence(_mock())
        assert isinstance(result, EvidenceReport)

    def test_confidence_score_is_float(self):
        result = compute_confidence(_mock())
        assert isinstance(result.confidence_score, float)

    def test_confidence_label_is_string(self):
        result = compute_confidence(_mock())
        assert isinstance(result.confidence_label, str)

    def test_confidence_label_valid_values(self):
        result = compute_confidence(_mock())
        assert result.confidence_label in {"high", "medium", "insufficient"}

    def test_score_never_exceeds_1(self):
        hadis = [_hadis("sahih")] * 10
        result = compute_confidence(_mock(quran_count=5, hadis_list=hadis))
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
# BAGIAN 2 — Scoring rubrik
# ════════════════════════════════════════════════════════════════════════════════

class TestConfidenceScoring:

    def test_empty_evidence_score_zero(self):
        result = compute_confidence(_mock())
        assert result.confidence_score == 0.0

    def test_one_quran_verse_score_040(self):
        result = compute_confidence(_mock(quran_count=1))
        assert result.confidence_score == 0.40

    def test_two_quran_verses_score_045(self):
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
        result = compute_confidence(_mock(
            quran_count=1,
            hadis_list=[_hadis("sahih")]
        ))
        assert result.confidence_score == 0.70

    def test_two_quran_one_sahih_rule_high_score_080(self):
        result = compute_confidence(_mock(
            quran_count=2,
            hadis_list=[_hadis("sahih")],
            confidence="high"
        ))
        assert result.confidence_score == 0.80

    def test_rule_high_adds_bonus_005(self):
        base = compute_confidence(_mock(quran_count=1, confidence="medium"))
        high = compute_confidence(_mock(quran_count=1, confidence="high"))
        assert high.confidence_score - base.confidence_score == pytest.approx(0.05)

    def test_score_capped_at_one(self):
        hadis = [_hadis("sahih")] * 5
        result = compute_confidence(_mock(
            quran_count=5,
            hadis_list=hadis,
            confidence="high"
        ))
        assert result.confidence_score == 1.0


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 3 — Labels & is_answerable
# ════════════════════════════════════════════════════════════════════════════════

class TestConfidenceLabels:

    def test_score_070_gives_high_label(self):
        result = compute_confidence(_mock(
            quran_count=1,
            hadis_list=[_hadis("sahih")]
        ))
        assert result.confidence_label == "high"

    def test_score_below_050_gives_insufficient_label(self):
        result = compute_confidence(_mock(quran_count=1))
        assert result.confidence_label == "insufficient"

    def test_score_000_gives_insufficient_label(self):
        result = compute_confidence(_mock())
        assert result.confidence_label == "insufficient"

    def test_is_answerable_true_when_high(self):
        result = compute_confidence(_mock(
            quran_count=1,
            hadis_list=[_hadis("sahih")]
        ))
        assert result.is_answerable is True

    def test_is_answerable_false_when_insufficient(self):
        result = compute_confidence(_mock())
        assert result.is_answerable is False

    def test_high_label_has_no_disclaimer(self):
        result = compute_confidence(_mock(
            quran_count=1,
            hadis_list=[_hadis("sahih")]
        ))
        assert result.disclaimer == ""

    def test_insufficient_label_has_disclaimer(self):
        result = compute_confidence(_mock())
        assert len(result.disclaimer) > 0

    def test_insufficient_disclaimer_not_empty(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("dhaif")]))
        assert result.disclaimer != ""


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 4 — Warnings
# ════════════════════════════════════════════════════════════════════════════════

class TestConfidenceWarnings:

    def test_dhaif_hadis_generates_warning(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("dhaif", "HR. X")]))
        assert len(result.warnings) >= 1

    def test_hasan_hadis_generates_warning(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("hasan", "HR. Y")]))
        assert len(result.warnings) >= 1

    def test_sahih_hadis_no_authenticity_warning(self):
        # Sahih tidak menghasilkan warning autentisitas (berbeda dengan dhaif/hasan).
        # Catatan: score 0.30 < threshold -> bisa ada warning "confidence rendah",
        # tapi itu bukan warning autentisitas — tidak boleh ada "berstatus" di dalamnya.
        result = compute_confidence(_mock(hadis_list=[_hadis("sahih")]))
        assert not any("berstatus" in w for w in result.warnings)

    def test_dhaif_warning_mentions_source(self):
        result = compute_confidence(_mock(hadis_list=[_hadis("dhaif", "HR. TestSource")]))
        assert any("TestSource" in w for w in result.warnings)

    def test_insufficient_score_adds_warning(self):
        result = compute_confidence(_mock())
        assert any("rendah" in w.lower() for w in result.warnings)

    def test_no_warnings_on_strong_evidence(self):
        result = compute_confidence(_mock(
            quran_count=2,
            hadis_list=[_hadis("sahih"), _hadis("sahih")],
            confidence="high"
        ))
        assert result.warnings == []

    def test_multiple_dhaif_generate_multiple_warnings(self):
        hadis = [_hadis("dhaif", f"HR.{i}") for i in range(3)]
        result = compute_confidence(_mock(hadis_list=hadis))
        dhaif_warnings = [w for w in result.warnings if "dhaif" in w.lower()]
        assert len(dhaif_warnings) == 3


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 5 — gate_answer()
# ════════════════════════════════════════════════════════════════════════════════

class TestGateAnswer:

    def test_returns_tuple_of_three(self):
        result = gate_answer(_mock())
        assert len(result) == 3

    def test_returns_bool_as_first_element(self):
        can_answer, _, _ = gate_answer(_mock())
        assert isinstance(can_answer, bool)

    def test_none_input_returns_false(self):
        can_answer, _, _ = gate_answer(None)
        assert can_answer is False

    def test_none_input_returns_none_report(self):
        _, report, _ = gate_answer(None)
        assert report is None

    def test_none_input_returns_nonempty_reason(self):
        _, _, reason = gate_answer(None)
        assert len(reason) > 0

    def test_strong_evidence_can_answer_true(self):
        can_answer, _, _ = gate_answer(_mock(
            quran_count=1,
            hadis_list=[_hadis("sahih")]
        ))
        assert can_answer is True

    def test_strong_evidence_report_not_none(self):
        _, report, _ = gate_answer(_mock(
            quran_count=1,
            hadis_list=[_hadis("sahih")]
        ))
        assert report is not None

    def test_strong_evidence_reason_empty(self):
        _, _, reason = gate_answer(_mock(
            quran_count=1,
            hadis_list=[_hadis("sahih")]
        ))
        assert reason == ""

    def test_empty_evidence_can_answer_false(self):
        can_answer, _, _ = gate_answer(_mock())
        assert can_answer is False

    def test_empty_evidence_reason_not_empty(self):
        _, _, reason = gate_answer(_mock())
        assert len(reason) > 0

    def test_dhaif_only_cannot_answer(self):
        can_answer, _, _ = gate_answer(_mock(hadis_list=[_hadis("dhaif")]))
        assert can_answer is False

    def test_hasan_only_cannot_answer(self):
        can_answer, _, _ = gate_answer(_mock(hadis_list=[_hadis("hasan")]))
        assert can_answer is False

    def test_report_topic_matches_input(self):
        _, report, _ = gate_answer(_mock(topic="shalat"))
        assert report.topic == "shalat"

    def test_report_ruling_matches_input(self):
        _, report, _ = gate_answer(_mock(ruling="wajib"))
        assert report.ruling == "wajib"


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 6 — Evidence flags
# ════════════════════════════════════════════════════════════════════════════════

class TestEvidenceFlags:

    def test_has_quran_evidence_true_when_present(self):
        result = compute_confidence(_mock(quran_count=1))
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


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 7 — kitab_corpus path: _compute_confidence_kitab()
#
# Rubrik (dari implementasi):
#   authority_level <= 2  -> 0.60  medium
#   authority_level <= 4  -> 0.52  medium
#   authority_level  = 5  -> 0.50  medium (batas bawah)
#   _kitab_hits kosong    -> 0.00  insufficient
#
# Dispatch: compute_confidence() mendelegasikan ke _compute_confidence_kitab()
# jika dan hanya jika _source == "kitab_corpus".
# ════════════════════════════════════════════════════════════════════════════════

def _mock_kitab(authority_levels=None):
    """
    Helper membuat mock retrieval_result untuk _source='kitab_corpus'.
    authority_levels: list of int, satu entry per hit.
    Kosong/None -> _kitab_hits = [].
    """
    hits = [
        {"book_slug": f"kitab_{lvl}", "authority_level": lvl,
         "chapter_title": "بَابٌ", "arabic_text": "نَصٌّ", "page_ref": "1"}
        for lvl in (authority_levels or [])
    ]
    return {
        "topic": "test_kitab_topic",
        "ruling": "",
        "madhab": "shafii",
        "quran": [],
        "hadis": [],
        "confidence": "medium",
        "_source": "kitab_corpus",
        "_kitab_hits": hits,
    }


class TestKitabCorpusScoring:
    """
    Verifikasi _compute_confidence_kitab() via dispatch di compute_confidence().
    Semua mock menyertakan _source='kitab_corpus' untuk memicu dispatch.
    """

    # ── Return type ──────────────────────────────────────────────

    def test_returns_evidence_report(self):
        result = compute_confidence(_mock_kitab([1]))
        assert isinstance(result, EvidenceReport)

    # ── Score eksak per authority_level ─────────────────────────

    def test_level_1_score_060(self):
        result = compute_confidence(_mock_kitab([1]))
        assert result.confidence_score == 0.60

    def test_level_2_score_060(self):
        result = compute_confidence(_mock_kitab([2]))
        assert result.confidence_score == 0.60

    def test_level_3_score_052(self):
        result = compute_confidence(_mock_kitab([3]))
        assert result.confidence_score == 0.52

    def test_level_4_score_052(self):
        result = compute_confidence(_mock_kitab([4]))
        assert result.confidence_score == 0.52

    def test_level_5_score_050(self):
        result = compute_confidence(_mock_kitab([5]))
        assert result.confidence_score == 0.50

    def test_empty_hits_score_zero(self):
        result = compute_confidence(_mock_kitab([]))
        assert result.confidence_score == 0.0

    # ── min() strategy: best (lowest) level menang ───────────────

    def test_mixed_levels_uses_min(self):
        result = compute_confidence(_mock_kitab([1, 5]))
        assert result.confidence_score == 0.60

    def test_mixed_level_3_and_5_uses_min(self):
        result = compute_confidence(_mock_kitab([3, 5]))
        assert result.confidence_score == 0.52

    # ── Labels ───────────────────────────────────────────────────

    def test_level_1_label_medium(self):
        result = compute_confidence(_mock_kitab([1]))
        assert result.confidence_label == "medium"

    def test_level_5_label_medium(self):
        result = compute_confidence(_mock_kitab([5]))
        assert result.confidence_label == "medium"

    def test_empty_hits_label_insufficient(self):
        result = compute_confidence(_mock_kitab([]))
        assert result.confidence_label == "insufficient"

    # ── is_answerable ────────────────────────────────────────────

    def test_level_1_is_answerable(self):
        result = compute_confidence(_mock_kitab([1]))
        assert result.is_answerable is True

    def test_level_5_is_answerable(self):
        result = compute_confidence(_mock_kitab([5]))
        assert result.is_answerable is True

    def test_empty_hits_not_answerable(self):
        result = compute_confidence(_mock_kitab([]))
        assert result.is_answerable is False

    # ── kitab-specific fields di EvidenceReport ─────────────────

    def test_kitab_hits_count_correct(self):
        result = compute_confidence(_mock_kitab([1, 3, 5]))
        assert result.kitab_hits_count == 3

    def test_kitab_hits_count_zero_when_empty(self):
        result = compute_confidence(_mock_kitab([]))
        assert result.kitab_hits_count == 0

    def test_kitab_best_authority_correct(self):
        result = compute_confidence(_mock_kitab([3, 1, 4]))
        assert result.kitab_best_authority == 1

    def test_kitab_best_authority_none_when_empty(self):
        result = compute_confidence(_mock_kitab([]))
        assert result.kitab_best_authority is None

    # ── Field-field yang harus nol di path kitab_corpus ─────────

    def test_has_quran_evidence_false(self):
        result = compute_confidence(_mock_kitab([1]))
        assert result.has_quran_evidence is False

    def test_has_hadis_evidence_false(self):
        result = compute_confidence(_mock_kitab([1]))
        assert result.has_hadis_evidence is False

    def test_quran_count_zero(self):
        result = compute_confidence(_mock_kitab([2]))
        assert result.quran_count == 0

    def test_hadis_count_zero(self):
        result = compute_confidence(_mock_kitab([2]))
        assert result.hadis_count == 0

    def test_hadis_authenticity_empty(self):
        result = compute_confidence(_mock_kitab([1]))
        assert result.hadis_authenticity == []

    # ── Warnings ─────────────────────────────────────────────────

    def test_warning_present_when_hits_exist(self):
        result = compute_confidence(_mock_kitab([1]))
        assert len(result.warnings) == 1

    def test_warning_mentions_korpus(self):
        result = compute_confidence(_mock_kitab([3]))
        assert any("korpus" in w.lower() for w in result.warnings)

    def test_empty_hits_has_insufficient_warning(self):
        result = compute_confidence(_mock_kitab([]))
        assert any("rendah" in w.lower() for w in result.warnings)

    # ── Disclaimer ───────────────────────────────────────────────

    def test_medium_disclaimer_not_empty(self):
        result = compute_confidence(_mock_kitab([1]))
        assert len(result.disclaimer) > 0

    def test_medium_disclaimer_mentions_kitab(self):
        result = compute_confidence(_mock_kitab([4]))
        assert "kitab" in result.disclaimer.lower()

    def test_empty_hits_disclaimer_not_empty(self):
        result = compute_confidence(_mock_kitab([]))
        assert len(result.disclaimer) > 0

    # ── gate_answer integration ──────────────────────────────────

    def test_gate_level_1_can_answer(self):
        can_answer, _, _ = gate_answer(_mock_kitab([1]))
        assert can_answer is True

    def test_gate_level_5_can_answer(self):
        can_answer, _, _ = gate_answer(_mock_kitab([5]))
        assert can_answer is True

    def test_gate_empty_hits_cannot_answer(self):
        can_answer, _, _ = gate_answer(_mock_kitab([]))
        assert can_answer is False

    def test_gate_report_has_kitab_fields(self):
        _, report, _ = gate_answer(_mock_kitab([2, 4]))
        assert report.kitab_hits_count == 2
        assert report.kitab_best_authority == 2

    # ── Regresi: dispatch tidak memengaruhi path Layer 1-3 ───────

    def test_non_kitab_source_unaffected(self):
        regular = _mock(quran_count=1, hadis_list=[_hadis("sahih")])
        result = compute_confidence(regular)
        assert result.confidence_score == 0.70
        assert result.kitab_hits_count == 0
        assert result.kitab_best_authority is None
