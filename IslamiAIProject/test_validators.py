# test_validators.py
# IslamiAI — Pytest suite untuk validators.py
#
# Menguji: sanitize_text(), validate_question(), validate_madhab()
# Prinsip: setiap test hanya menguji satu invariant (single-assertion rule).
# Struktur: AAA — Arrange / Act / Assert.
#
# Jalankan: pytest test_validators.py -v

import sys
import os
import pytest

# Pastikan project root ada di path agar import bekerja
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validators import (
    sanitize_text,
    validate_question,
    validate_madhab,
    InputValidationError,
)


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 1 — sanitize_text()
# ════════════════════════════════════════════════════════════════════════════════

class TestSanitizeText:
    """Unit test untuk fungsi sanitize_text()."""

    def test_strips_leading_trailing_whitespace(self):
        result = sanitize_text("  syahadat  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_collapses_internal_whitespace(self):
        result = sanitize_text("apa   itu   wudhu")
        assert "  " not in result

    def test_normalizes_to_nfc_unicode(self):
        # NFD: karakter + combining mark terpisah
        nfd_text = "cafe\u0301"   # 'e' + combining acute accent (NFD)
        result = sanitize_text(nfd_text)
        # NFC: karakter precomposed (é)
        assert result == "caf\u00e9"

    def test_escapes_html_ampersand(self):
        result = sanitize_text("a & b")
        assert "&amp;" in result

    def test_escapes_html_less_than(self):
        result = sanitize_text("<div>")
        assert "&lt;" in result

    def test_escapes_html_greater_than(self):
        result = sanitize_text(">test")
        assert "&gt;" in result

    def test_escapes_html_quotes(self):
        result = sanitize_text('"quoted"')
        assert "&quot;" in result

    def test_raises_on_non_string_input(self):
        with pytest.raises(InputValidationError):
            sanitize_text(123)

    def test_raises_on_none_input(self):
        with pytest.raises(InputValidationError):
            sanitize_text(None)

    def test_arabic_text_preserved(self):
        arabic = "ما هو الشهادة"
        result = sanitize_text(arabic)
        # Karakter Arabic harus tetap ada setelah sanitasi
        assert "ما" in result

    def test_returns_string_type(self):
        result = sanitize_text("test")
        assert isinstance(result, str)


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 2 — validate_question(): kasus VALID (harus lolos)
# ════════════════════════════════════════════════════════════════════════════════

class TestValidateQuestionValid:
    """Pertanyaan yang harus lolos validasi."""

    def test_simple_valid_question(self):
        result = validate_question("syahadat itu apa?")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_valid_question_hukum_shalat(self):
        result = validate_question("hukum shalat")
        assert "hukum" in result.lower() or "shalat" in result.lower()

    def test_valid_with_extra_spaces(self):
        # Spasi berlebih harus di-collapse, bukan ditolak
        result = validate_question("  apa  itu  wudhu  ")
        assert "apa" in result.lower()

    def test_valid_question_at_min_length(self):
        # Tepat di minimum (3 karakter)
        result = validate_question("abc")
        assert len(result) >= 3

    def test_valid_question_at_max_length(self):
        # Tepat di maksimum (500 karakter)
        question = "a" * 500
        result = validate_question(question)
        assert len(result) <= 500

    def test_valid_question_with_arabic(self):
        result = validate_question("apa arti bismillah")
        assert isinstance(result, str)

    def test_valid_question_with_punctuation(self):
        result = validate_question("boleh tidak makan daging babi?")
        assert isinstance(result, str)

    def test_valid_question_returns_cleaned_string(self):
        raw = "  Apakah  wudhu  itu  wajib?  "
        result = validate_question(raw)
        # Double-space tidak boleh ada
        assert "  " not in result


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 3 — validate_question(): kasus INVALID (harus ditolak)
# ════════════════════════════════════════════════════════════════════════════════

class TestValidateQuestionInvalid:
    """Pertanyaan yang harus ditolak dengan InputValidationError."""

    def test_empty_string_rejected(self):
        with pytest.raises(InputValidationError):
            validate_question("")

    def test_whitespace_only_rejected(self):
        with pytest.raises(InputValidationError):
            validate_question("   ")

    def test_too_short_rejected(self):
        # 2 karakter — di bawah minimum 3
        with pytest.raises(InputValidationError):
            validate_question("ab")

    def test_too_long_rejected(self):
        # 501 karakter — di atas maksimum 500
        with pytest.raises(InputValidationError):
            validate_question("a" * 501)

    def test_html_script_tag_rejected(self):
        with pytest.raises(InputValidationError):
            validate_question("<script>alert(1)</script>")

    def test_html_img_tag_rejected(self):
        with pytest.raises(InputValidationError):
            validate_question("<img src=x onerror=alert(1)>")

    def test_javascript_protocol_rejected(self):
        with pytest.raises(InputValidationError):
            validate_question("javascript:alert(1)")

    def test_event_handler_rejected(self):
        with pytest.raises(InputValidationError):
            validate_question("onclick=doSomething()")

    def test_sql_drop_table_rejected(self):
        with pytest.raises(InputValidationError):
            validate_question("'; DROP TABLE users;--")

    def test_sql_select_injection_rejected(self):
        with pytest.raises(InputValidationError):
            validate_question("x'; SELECT * FROM users;--")

    def test_path_traversal_rejected(self):
        with pytest.raises(InputValidationError):
            validate_question("../../etc/passwd")

    def test_sql_comment_double_dash_rejected(self):
        with pytest.raises(InputValidationError):
            validate_question("hukum shalat --comment")

    def test_error_type_is_input_validation_error(self):
        # Pastikan exception class yang benar dilempar, bukan ValueError generik
        with pytest.raises(InputValidationError):
            validate_question("")

    def test_error_is_subclass_of_value_error(self):
        # InputValidationError harus subclass ValueError (kontrak API)
        with pytest.raises(ValueError):
            validate_question("")


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 4 — validate_question(): pesan error
# ════════════════════════════════════════════════════════════════════════════════

class TestValidateQuestionErrorMessages:
    """Pesan error harus informatif dan konsisten."""

    def test_empty_error_message_in_bahasa(self):
        with pytest.raises(InputValidationError) as exc_info:
            validate_question("")
        assert len(str(exc_info.value)) > 0

    def test_too_long_error_mentions_max_length(self):
        with pytest.raises(InputValidationError) as exc_info:
            validate_question("a" * 501)
        # Pesan harus menyebutkan batas maksimum
        assert "500" in str(exc_info.value)

    def test_too_short_error_mentions_min_length(self):
        with pytest.raises(InputValidationError) as exc_info:
            validate_question("ab")
        assert "3" in str(exc_info.value)


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 5 — validate_madhab()
# ════════════════════════════════════════════════════════════════════════════════

class TestValidateMadhab:
    """Unit test untuk validate_madhab()."""

    @pytest.mark.parametrize("madhab", ["shafii", "hanafi", "maliki", "hanbali"])
    def test_valid_madhabs_accepted(self, madhab):
        result = validate_madhab(madhab)
        assert result == madhab

    @pytest.mark.parametrize("madhab", ["Shafii", "HANAFI", "Maliki", "HANBALI"])
    def test_valid_madhabs_case_insensitive(self, madhab):
        result = validate_madhab(madhab)
        assert result == madhab.lower()

    def test_invalid_madhab_rejected(self):
        with pytest.raises(InputValidationError):
            validate_madhab("dzahiri")

    def test_empty_madhab_rejected(self):
        with pytest.raises(InputValidationError):
            validate_madhab("")

    def test_returns_lowercase(self):
        result = validate_madhab("SHAFII")
        assert result == result.lower()

    def test_invalid_madhab_error_message_contains_options(self):
        with pytest.raises(InputValidationError) as exc_info:
            validate_madhab("unknown")
        msg = str(exc_info.value)
        # Pesan harus menyebutkan madhab yang tersedia
        assert any(m in msg for m in ["shafii", "hanafi", "maliki", "hanbali"])


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 6 — Edge cases & boundary conditions
# ════════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Boundary conditions dan kasus sudut."""

    def test_exactly_3_chars_valid(self):
        # Tepat di batas minimum
        result = validate_question("abc")
        assert len(result) >= 3

    def test_exactly_500_chars_valid(self):
        # Tepat di batas maksimum — harus lolos
        result = validate_question("a" * 500)
        assert len(result) <= 500

    def test_501_chars_invalid(self):
        # Satu karakter melewati batas
        with pytest.raises(InputValidationError):
            validate_question("a" * 501)

    def test_question_with_newline_gets_collapsed(self):
        # Newline di-collapse menjadi spasi
        q = "hukum\nshalat"
        result = validate_question(q)
        assert "\n" not in result

    def test_unicode_arabic_question_valid(self):
        # Pertanyaan dalam bahasa Arab murni harus diterima
        q = "ما هو حكم الصلاة"
        result = validate_question(q)
        assert isinstance(result, str)
