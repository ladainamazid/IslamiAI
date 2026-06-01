# test_query_parser.py
# IslamiAI — Pytest suite untuk query_parser.py
#
# Menguji: parse_user_query(), parse_user_query_debug()
# Semua expected topic keys diverifikasi secara empiris terhadap
#   keyword data di islamic_data.shafii_rules.
#
# Prinsip:
#   1. Test harus deterministik — tidak bergantung pada urutan dict.
#   2. Test memverifikasi perilaku, bukan implementasi internal.
#   3. Tidak ada mock data palsu — query parser berjalan terhadap data nyata.
#
# Jalankan: pytest test_query_parser.py -v

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query_parser import parse_user_query, parse_user_query_debug
from islamic_data import shafii_rules


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 1 — Return type dan kontrak dasar
# ════════════════════════════════════════════════════════════════════════════════

class TestParseUserQueryContract:

    def test_returns_string_or_none(self):
        result = parse_user_query("syahadat")
        assert result is None or isinstance(result, str)

    def test_match_is_valid_topic_key(self):
        result = parse_user_query("syahadat")
        # Hasil harus ada di shafii_rules atau None
        assert result is None or result in shafii_rules

    def test_no_match_returns_none(self):
        # Catatan arsitektur: keyword matching berbasis word-overlap memiliki
        # keterbatasan — kata umum bisa menghasilkan false positive skor rendah.
        # Query yang benar-benar tidak ada tumpang-tindih keyword barulah None.
        # Known limitation — akan dievaluasi di Phase 2 (TF-IDF / embedding).
        result = parse_user_query("zzxqkjfhsdf lorem ipsum dolor")
        assert result is None

    def test_empty_string_returns_none(self):
        result = parse_user_query("")
        assert result is None

    def test_whitespace_only_returns_none(self):
        result = parse_user_query("   ")
        assert result is None

    def test_random_nonsense_returns_none(self):
        result = parse_user_query("zzxqkjfhsdf")
        assert result is None


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 2 — Topic matching: kasus positif (verified empirically)
# ════════════════════════════════════════════════════════════════════════════════

class TestTopicMatchingPositive:
    """
    Setiap test case diverifikasi dengan menjalankan parse_user_query()
    sebelum ditulis. Semua hasilnya ✅ valid.
    """

    def test_syahadat_direct_keyword(self):
        assert parse_user_query("syahadat") == "syahadat"

    def test_syahadat_in_question_form(self):
        assert parse_user_query("apa itu syahadat") == "syahadat"

    def test_wudhu_keyword(self):
        assert parse_user_query("apa itu wudhu") == "thaharah_wudhu"

    def test_wudhu_in_question(self):
        assert parse_user_query("bagaimana cara wudhu yang benar") == "thaharah_wudhu"

    def test_shalat_lima_waktu(self):
        assert parse_user_query("shalat lima waktu") == "shalat_lima_waktu"

    def test_shalat_fardhu(self):
        assert parse_user_query("hukum shalat fardhu") == "shalat_lima_waktu"

    def test_makanan_haram_babi(self):
        assert parse_user_query("hukum daging babi") == "makanan_haram_umum"

    def test_puasa_ramadhan(self):
        assert parse_user_query("puasa ramadhan") == "puasa_ramadhan"

    def test_zakat_fitrah(self):
        assert parse_user_query("zakat fitrah ramadhan") == "zakat_fitrah"

    def test_waris_beda_agama(self):
        assert parse_user_query("hukum warisan beda agama") == "waris_perbedaan_agama"

    def test_jenazah_memandikan(self):
        result = parse_user_query("cara memandikan jenazah")
        assert result == "jenazah_ghusl"

    def test_aurat_perempuan(self):
        result = parse_user_query("aurat perempuan dalam shalat")
        assert result in {"aurat_perempuan_shalat", "aurat_perempuan_di_luar_shalat"}

    def test_najis_berat(self):
        result = parse_user_query("najis berat")
        # Harus match salah satu kategori najis
        assert result in {"najis_berat", "najis_sedang", "najis_ringkan"}

    def test_mandi_wajib(self):
        result = parse_user_query("kapan mandi wajib")
        assert result == "thaharah_mandi_wajib"

    def test_zakat_harta(self):
        result = parse_user_query("zakat harta emas")
        assert result == "zakat_harta"

    def test_pernikahan_beda_agama(self):
        result = parse_user_query("hukum pernikahan dengan kafir")
        assert result in {
            "pernikahan_suami_islam_istri_kafir",
            "pernikahan_istri_islam_suami_kafir",
            "pernikahan_keduanya_islam",
        }


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 3 — Case insensitivity
# ════════════════════════════════════════════════════════════════════════════════

class TestCaseInsensitivity:

    def test_uppercase_query_matches(self):
        lower = parse_user_query("syahadat")
        upper = parse_user_query("SYAHADAT")
        assert lower == upper

    def test_mixed_case_query_matches(self):
        lower = parse_user_query("wudhu")
        mixed = parse_user_query("Wudhu")
        assert lower == mixed

    def test_all_caps_shalat(self):
        lower = parse_user_query("shalat")
        caps  = parse_user_query("SHALAT")
        assert lower == caps


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 4 — Best match (skor tertinggi menang)
# ════════════════════════════════════════════════════════════════════════════════

class TestBestMatchSelection:

    def test_more_specific_query_wins(self):
        # "zakat fitrah" lebih spesifik dari "zakat" saja
        result = parse_user_query("zakat fitrah")
        assert result == "zakat_fitrah"

    def test_multiple_matching_keywords_raises_score(self):
        # Query dengan banyak keyword matching harus dapat skor tinggi
        result = parse_user_query("shalat lima waktu fardhu")
        assert result == "shalat_lima_waktu"

    def test_exact_keyword_match_beats_partial(self):
        # "syahadat" exact match harus menang atas partial word overlap
        result = parse_user_query("makna syahadat dalam islam")
        assert result == "syahadat"

    def test_single_keyword_match_consistent(self):
        # Query yang sama selalu mengembalikan hasil yang sama (deterministik)
        r1 = parse_user_query("puasa")
        r2 = parse_user_query("puasa")
        assert r1 == r2


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 5 — parse_user_query_debug(): kontrak dan struktur
# ════════════════════════════════════════════════════════════════════════════════

class TestParseUserQueryDebug:

    def test_returns_list(self):
        result = parse_user_query_debug("syahadat")
        assert isinstance(result, list)

    def test_empty_query_returns_empty_list(self):
        result = parse_user_query_debug("zzxqhhhh")
        assert result == []

    def test_each_item_is_tuple(self):
        result = parse_user_query_debug("syahadat")
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_first_element_of_tuple_is_topic_key(self):
        result = parse_user_query_debug("syahadat")
        assert len(result) > 0
        topic_key = result[0][0]
        assert topic_key in shafii_rules

    def test_second_element_contains_score(self):
        result = parse_user_query_debug("syahadat")
        assert len(result) > 0
        data = result[0][1]
        assert "score" in data

    def test_second_element_contains_keywords(self):
        result = parse_user_query_debug("syahadat")
        assert len(result) > 0
        data = result[0][1]
        assert "keywords" in data

    def test_sorted_descending_by_score(self):
        result = parse_user_query_debug("syahadat wudhu shalat puasa zakat")
        scores = [item[1]["score"] for item in result]
        assert scores == sorted(scores, reverse=True)

    def test_top_result_matches_parse_user_query(self):
        # Debug top result harus konsisten dengan non-debug
        query = "wudhu sebelum shalat"
        debug_top = parse_user_query_debug(query)[0][0]
        normal = parse_user_query(query)
        assert debug_top == normal

    def test_all_scores_positive(self):
        result = parse_user_query_debug("shalat lima waktu wajib")
        for _, data in result:
            assert data["score"] > 0

    def test_no_duplicate_topic_keys(self):
        result = parse_user_query_debug("shalat wudhu syahadat puasa zakat jenazah")
        keys = [item[0] for item in result]
        assert len(keys) == len(set(keys))


# ════════════════════════════════════════════════════════════════════════════════
# BAGIAN 6 — Robustness: input tidak biasa
# ════════════════════════════════════════════════════════════════════════════════

class TestRobustness:

    def test_very_long_query_does_not_crash(self):
        long_query = "syahadat " * 100
        result = parse_user_query(long_query)
        assert result is None or result in shafii_rules

    def test_query_with_numbers_does_not_crash(self):
        result = parse_user_query("shalat 5 waktu sehari")
        assert result is None or result in shafii_rules

    def test_query_with_special_chars_does_not_crash(self):
        # Pertanyaan yang sudah di-escape oleh validators
        result = parse_user_query("hukum shalat &amp; puasa")
        assert result is None or result in shafii_rules

    def test_single_word_query_does_not_crash(self):
        result = parse_user_query("zakat")
        assert result is None or result in shafii_rules

    def test_arabic_text_does_not_crash(self):
        result = parse_user_query("ما هو الشهادة")
        assert result is None or result in shafii_rules

    def test_repeated_calls_are_idempotent(self):
        # Panggil 5 kali berurutan — harus sama
        results = [parse_user_query("syahadat") for _ in range(5)]
        assert len(set(results)) == 1
