"""
test_phase_b.py
════════════════════════════════════════════════════════════════════════════════
Test suite untuk Phase B1 dan B2.
Tidak membutuhkan islamiai.db atau EPUB files (semua mock-based).

Jalankan: pytest test_phase_b.py -v
════════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import pytest

# Tambah path ke phase_b1 dan chapter_title_extractor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── B1 imports ────────────────────────────────────────────────────────────────
# Karena phase_b1_db_retrieval_additions.py bukan modul standalone (ada reference ke
# ARABIC_TOPIC_MAP dan _DB_PATH dari db_retrieval.py), kita import fungsi yang
# bisa ditest secara independen.
from db_retrieval import (
    DOMAIN_QUERY_PROFILES,
    _AUTHORITY_SCORE,
    _DOMAIN_PREFERENCE_BOOST,
    _detect_domain,
    _rerank_by_authority,
)

# ── B2 imports ────────────────────────────────────────────────────────────────
from chapter_title_extractor import (
    HTMLPageParser,
    is_page_anchor_text,
    contains_arabic,
    is_valid_chapter_title,
    extract_page_ref_from_element,
)
from bs4 import BeautifulSoup


# ════════════════════════════════════════════════════════════════════════════════
# B1 — DOMAIN_QUERY_PROFILES structure
# ════════════════════════════════════════════════════════════════════════════════

class TestDomainProfilesStructure:

    def test_general_domain_exists(self):
        assert "general" in DOMAIN_QUERY_PROFILES

    def test_all_required_domains_exist(self):
        required = {"tahara", "salat", "zakat", "sawm", "hajj",
                    "muamalat", "munakahah", "aqidah", "general"}
        assert required.issubset(DOMAIN_QUERY_PROFILES.keys())

    def test_each_domain_has_required_keys(self):
        for domain, profile in DOMAIN_QUERY_PROFILES.items():
            assert "arabic_terms" in profile,       f"{domain}: missing arabic_terms"
            assert "authority_preference" in profile, f"{domain}: missing authority_preference"
            assert "topic_keywords" in profile,     f"{domain}: missing topic_keywords"

    def test_arabic_terms_are_strings(self):
        for domain, profile in DOMAIN_QUERY_PROFILES.items():
            for term in profile["arabic_terms"]:
                assert isinstance(term, str), f"{domain}: non-string arabic_term {term!r}"

    def test_authority_preference_values_in_range(self):
        for domain, profile in DOMAIN_QUERY_PROFILES.items():
            for level in profile["authority_preference"]:
                assert 1 <= level <= 5, \
                    f"{domain}: authority_preference value {level} out of range"

    def test_general_domain_accepts_all_levels(self):
        pref = set(DOMAIN_QUERY_PROFILES["general"]["authority_preference"])
        assert pref == {1, 2, 3, 4, 5}

    def test_authority_score_covers_all_levels(self):
        assert set(_AUTHORITY_SCORE.keys()) == {1, 2, 3, 4, 5}

    def test_authority_scores_descending(self):
        # Level 1 harus lebih tinggi dari level 5
        assert _AUTHORITY_SCORE[1] > _AUTHORITY_SCORE[5]
        assert _AUTHORITY_SCORE[1] > _AUTHORITY_SCORE[2] > _AUTHORITY_SCORE[3] \
               > _AUTHORITY_SCORE[4] > _AUTHORITY_SCORE[5]

    def test_authority_scores_in_valid_range(self):
        for level, score in _AUTHORITY_SCORE.items():
            assert 0.0 <= score <= 1.0, f"Level {level} score {score} out of [0,1]"


# ════════════════════════════════════════════════════════════════════════════════
# B1 — _detect_domain()
# ════════════════════════════════════════════════════════════════════════════════

class TestDetectDomain:

    def test_wudhu_detected_as_tahara(self):
        assert _detect_domain("wudhu") == "tahara"

    def test_shalat_detected_as_salat(self):
        assert _detect_domain("shalat") == "salat"

    def test_zakat_detected(self):
        assert _detect_domain("zakat mal") == "zakat"

    def test_puasa_detected_as_sawm(self):
        assert _detect_domain("puasa ramadhan") == "sawm"

    def test_haji_detected(self):
        assert _detect_domain("haji umrah") == "hajj"

    def test_nikah_detected_as_munakahah(self):
        assert _detect_domain("hukum nikah") == "munakahah"

    def test_jual_beli_detected_as_muamalat(self):
        assert _detect_domain("jual beli riba") == "muamalat"

    def test_iman_detected_as_aqidah(self):
        assert _detect_domain("iman tauhid") == "aqidah"

    def test_unknown_query_returns_general(self):
        assert _detect_domain("cuaca hari ini") == "general"

    def test_empty_query_returns_general(self):
        assert _detect_domain("") == "general"

    def test_returns_string(self):
        result = _detect_domain("wudhu shalat")
        assert isinstance(result, str)

    def test_returns_valid_domain_key(self):
        result = _detect_domain("wudhu")
        assert result in DOMAIN_QUERY_PROFILES

    def test_case_insensitive(self):
        assert _detect_domain("WUDHU") == _detect_domain("wudhu")

    def test_partial_keyword_match(self):
        # "solat" (Malaysian spelling) should still map to salat
        assert _detect_domain("solat fardhu") == "salat"

    def test_compound_topic_picks_dominant_domain(self):
        # "puasa zakat" — zakat has 1 hit, sawm has 1 hit
        # result should be one of the two (non-general)
        result = _detect_domain("puasa zakat")
        assert result in ("sawm", "zakat")


# ════════════════════════════════════════════════════════════════════════════════
# B1 — _rerank_by_authority()
# ════════════════════════════════════════════════════════════════════════════════

def _make_hits(specs: list[tuple[float, int]]) -> list[dict]:
    """Helper: buat mock hits dari list (fts_rank, authority_level)."""
    return [
        {"fts_rank": rank, "authority_level": level, "book_slug": f"book_{i}"}
        for i, (rank, level) in enumerate(specs)
    ]


class TestRerankByAuthority:

    def test_returns_list(self):
        hits = _make_hits([(-5.0, 3), (-3.0, 1)])
        result = _rerank_by_authority(hits)
        assert isinstance(result, list)

    def test_empty_input_returns_empty(self):
        assert _rerank_by_authority([]) == []

    def test_single_hit_returned_unchanged_structure(self):
        hits = _make_hits([(-5.0, 1)])
        result = _rerank_by_authority(hits)
        assert len(result) == 1
        assert "combined_score" in result[0]

    def test_all_hits_have_combined_score(self):
        hits = _make_hits([(-10.0, 1), (-5.0, 3), (-2.0, 5)])
        result = _rerank_by_authority(hits)
        for h in result:
            assert "combined_score" in h

    def test_combined_score_in_range_0_1(self):
        hits = _make_hits([(-10.0, 1), (-5.0, 3), (-2.0, 5)])
        result = _rerank_by_authority(hits)
        for h in result:
            assert 0.0 <= h["combined_score"] <= 1.0

    def test_sorted_descending_by_combined_score(self):
        hits = _make_hits([(-10.0, 1), (-5.0, 3), (-2.0, 5)])
        result = _rerank_by_authority(hits)
        scores = [h["combined_score"] for h in result]
        assert scores == sorted(scores, reverse=True)

    def test_high_authority_wins_over_slightly_better_text(self):
        """
        Level 1 dengan BM25 sedikit lebih buruk harus menang atas level 5
        dengan BM25 sedikit lebih baik, karena authority weight.
        alpha=0.55 → 45% weight untuk authority.

        Butuh ≥3 hits agar normalisasi menghasilkan skor tengah (bukan ekstrem
        {0.0, 1.0}). Dengan 2 hits saja, level-5 selalu mendapat text_score=1.0
        dan level-1 mendapat 0.0 — gap yang tidak dapat diatasi authority weight.

        Skenario: 3 hits dengan range BM25 = 4.0
          level-5  rank=-10.0 → text=1.0,    auth=0.40 → combined=0.730
          level-1  rank=-9.5  → text=0.875,  auth=1.00 → combined=0.931  ← menang
          level-3  rank=-6.0  → text=0.0,    auth=0.85 → combined=0.383
        (tahara domain: level-1,2,3 preferred; level-1 auth_score = min(1.0, 1.0+0.15) = 1.0)
        """
        # level-5: best BM25 (-10.0), worst authority
        # level-1: slightly worse BM25 (-9.5, diff 0.5 dari range 4.0 = 12.5%), best authority
        # level-3: poorest BM25 (-6.0), as range anchor
        hits = _make_hits([(-10.0, 5), (-9.5, 1), (-6.0, 3)])
        result = _rerank_by_authority(hits, domain="tahara", alpha=0.55)
        # level-1 harus di posisi pertama karena authority + domain preference boost
        assert result[0]["authority_level"] == 1

    def test_domain_preferred_levels_get_boost(self):
        """Level yang ada di authority_preference domain mendapat boost +0.15."""
        # tahara domain: authority_preference = [1, 2, 3]
        # level-1 dan level-4 dengan BM25 identik
        hits = _make_hits([(-5.0, 1), (-5.0, 4)])
        result_tahara  = _rerank_by_authority(hits, domain="tahara")
        result_general = _rerank_by_authority(hits, domain="general")

        # Di tahara domain, level-1 (preferred) harus dapat score lebih tinggi
        # Daripada level-4 (non-preferred)
        scores_tahara = {h["authority_level"]: h["combined_score"] for h in result_tahara}
        assert scores_tahara[1] > scores_tahara[4]

        # Di general domain (semua level preferred), score level-1 tetap lebih tinggi
        # karena base _AUTHORITY_SCORE[1] > _AUTHORITY_SCORE[4]
        scores_general = {h["authority_level"]: h["combined_score"] for h in result_general}
        assert scores_general[1] > scores_general[4]

    def test_alpha_zero_ranks_purely_by_authority(self):
        """alpha=0 → 100% authority weight, text score tidak berpengaruh."""
        # level-5 dengan BM25 jauh lebih baik dari level-1
        hits = _make_hits([(-100.0, 5), (-1.0, 1)])
        result = _rerank_by_authority(hits, domain="general", alpha=0.0)
        # Dengan alpha=0, authority saja yang menentukan → level-1 harus menang
        assert result[0]["authority_level"] == 1

    def test_alpha_one_ranks_purely_by_text(self):
        """alpha=1 → 100% text relevance, authority tidak berpengaruh."""
        # level-5 dengan BM25 lebih baik dari level-1
        hits = _make_hits([(-100.0, 5), (-1.0, 1)])
        result = _rerank_by_authority(hits, domain="general", alpha=1.0)
        # Dengan alpha=1, text rank saja yang menentukan → rank -100 (level-5) menang
        assert result[0]["authority_level"] == 5

    def test_identical_ranks_and_levels_return_stable_order(self):
        hits = _make_hits([(-5.0, 3), (-5.0, 3), (-5.0, 3)])
        result = _rerank_by_authority(hits)
        assert len(result) == 3
        # Tidak error
        scores = [h["combined_score"] for h in result]
        assert len(set(scores)) == 1  # semua score sama

    def test_does_not_mutate_input_order(self):
        """Input list tidak boleh di-sort in-place sebelum normalisasi selesai."""
        original = _make_hits([(-2.0, 5), (-10.0, 1)])
        original_copy = [dict(h) for h in original]
        _rerank_by_authority(original)
        # combined_score ditambahkan tapi urutan asli tidak berubah
        for orig, copy in zip(original, original_copy):
            assert orig["authority_level"] == copy["authority_level"]
            assert orig["fts_rank"] == copy["fts_rank"]

    def test_missing_authority_level_defaults_to_5(self):
        hits = [{"fts_rank": -5.0, "book_slug": "unknown_book"}]  # no authority_level
        result = _rerank_by_authority(hits)
        assert len(result) == 1
        assert result[0]["combined_score"] > 0.0


# ════════════════════════════════════════════════════════════════════════════════
# B2 — Helper functions
# ════════════════════════════════════════════════════════════════════════════════

class TestHelperFunctions:

    # is_page_anchor_text
    def test_page_anchor_detected(self):
        assert is_page_anchor_text("page_1_0265") is True

    def test_page_anchor_detected_vol2(self):
        assert is_page_anchor_text("page_2_0001") is True

    def test_arabic_text_not_anchor(self):
        assert is_page_anchor_text("كتاب الطهارة") is False

    def test_empty_string_not_anchor(self):
        assert is_page_anchor_text("") is False

    def test_partial_anchor_not_detected(self):
        assert is_page_anchor_text("page_1") is False

    # contains_arabic
    def test_arabic_string_detected(self):
        assert contains_arabic("الوضوء") is True

    def test_latin_string_not_arabic(self):
        assert contains_arabic("wudhu") is False

    def test_mixed_string_detected(self):
        assert contains_arabic("hukum الوضوء") is True

    def test_empty_string_not_arabic(self):
        assert contains_arabic("") is False

    # is_valid_chapter_title
    def test_arabic_title_is_valid(self):
        assert is_valid_chapter_title("كتاب الطهارة") is True

    def test_page_anchor_is_invalid(self):
        assert is_valid_chapter_title("page_1_0265") is False

    def test_empty_string_is_invalid(self):
        assert is_valid_chapter_title("") is False

    def test_latin_only_is_invalid(self):
        assert is_valid_chapter_title("Chapter 1") is False

    def test_short_arabic_is_invalid(self):
        # Kurang dari 4 karakter Arab
        assert is_valid_chapter_title("ب") is False

    def test_long_arabic_title_is_valid(self):
        title = "فصل في أحكام المياه وأقسامها وما يطهر به وما لا يطهر"
        assert is_valid_chapter_title(title) is True

    # extract_page_ref_from_element
    def test_extract_from_heading_id(self):
        soup = BeautifulSoup('<h2 id="page_1_0045">text</h2>', "html.parser")
        el = soup.find("h2")
        assert extract_page_ref_from_element(el) == "page_1_0045"

    def test_extract_from_nested_anchor(self):
        soup = BeautifulSoup('<h2><a id="page_1_0046"></a>text</h2>', "html.parser")
        el = soup.find("h2")
        assert extract_page_ref_from_element(el) == "page_1_0046"

    def test_no_anchor_returns_none(self):
        soup = BeautifulSoup('<h2>كتاب الطهارة</h2>', "html.parser")
        el = soup.find("h2")
        assert extract_page_ref_from_element(el) is None

    def test_non_anchor_id_returns_none(self):
        soup = BeautifulSoup('<h2 id="intro">text</h2>', "html.parser")
        el = soup.find("h2")
        assert extract_page_ref_from_element(el) is None


# ════════════════════════════════════════════════════════════════════════════════
# B2 — HTMLPageParser
# ════════════════════════════════════════════════════════════════════════════════

# HTML fixtures yang mereproduksi pola umum shamela2epub

HTML_BASIC = """
<html><body>
  <h2 id="page_1_0044"><a id="pg44"></a></h2>
  <p>هذا نص قصير.</p>
  <h2 id="page_1_0045"><a id="pg45"></a></h2>
  <h3>كتاب الطهارة</h3>
  <p>قال الشافعي: الطهارة واجبة للصلاة وللطواف بالبيت.</p>
  <p>وتنقسم الطهارة إلى قسمين: طهارة الحدث وطهارة الخبث.</p>
</body></html>
"""

# Fixture khusus: paragraph panjang (≥15 char Arab) SEBELUM heading apapun,
# diikuti heading dan konten. Digunakan untuk test chapter_title == "" pre-heading.
# HTML_BASIC tidak cocok karena paragraf pertamanya hanya 9 char Arab → difilter.
HTML_PRE_HEADING = """
<html><body>
  <h2 id="page_1_0020"><a id="pg20"></a></h2>
  <p>النص الأول قبل أي عنوان للباب وهو نص عربي طويل كافٍ لتجاوز الفلتر.</p>
  <h2 id="page_1_0021"><a id="pg21"></a></h2>
  <h3>كتاب الطهارة</h3>
  <p>قال الشافعي: الطهارة واجبة للصلاة.</p>
</body></html>
"""

HTML_WITH_INLINE_BAB = """
<html><body>
  <h2 id="page_1_0050"><a id="pg50"></a></h2>
  <p>باب الوضوء وأركانه وشروطه وسننه.</p>
  <p>الوضوء فريضة على كل مسلم أراد الصلاة وكان محدثاً.</p>
  <h2 id="page_1_0051"><a id="pg51"></a></h2>
  <p>فصل في النية وشروطها.</p>
  <p>تجب النية عند ابتداء الوضوء.</p>
</body></html>
"""

HTML_NO_HEADINGS = """
<html><body>
  <p>نص بدون عناوين.</p>
  <p>ومزيد من النصوص العربية هنا في هذا الكتاب.</p>
</body></html>
"""

HTML_EMPTY = "<html><body></body></html>"

HTML_LATIN_ONLY = """
<html><body>
  <h2 id="page_1_0001"></h2>
  <p>This is English text only, no Arabic content here.</p>
</body></html>
"""


class TestHTMLPageParserBasic:

    def _parser(self):
        return HTMLPageParser(book_slug="al_umm", authority_level=1)

    def test_returns_list(self):
        result = self._parser().parse(HTML_BASIC)
        assert isinstance(result, list)

    def test_empty_html_returns_empty_list(self):
        result = self._parser().parse(HTML_EMPTY)
        assert result == []

    def test_latin_only_returns_empty_list(self):
        result = self._parser().parse(HTML_LATIN_ONLY)
        assert result == []

    def test_arabic_paragraphs_are_extracted(self):
        result = self._parser().parse(HTML_BASIC)
        assert len(result) >= 2

    def test_each_passage_has_required_keys(self):
        result = self._parser().parse(HTML_BASIC)
        for passage in result:
            assert "book_slug" in passage
            assert "authority_level" in passage
            assert "chapter_title" in passage
            assert "page_ref" in passage
            assert "arabic_text" in passage

    def test_book_slug_preserved(self):
        result = self._parser().parse(HTML_BASIC)
        for passage in result:
            assert passage["book_slug"] == "al_umm"

    def test_authority_level_preserved(self):
        result = self._parser().parse(HTML_BASIC)
        for passage in result:
            assert passage["authority_level"] == 1

    def test_arabic_text_contains_arabic_chars(self):
        result = self._parser().parse(HTML_BASIC)
        for passage in result:
            assert contains_arabic(passage["arabic_text"]), \
                f"Non-Arabic passage found: {passage['arabic_text']!r}"


class TestHTMLPageParserChapterTitle:

    def _parser(self):
        return HTMLPageParser(book_slug="al_majmu", authority_level=3)

    def test_chapter_title_before_any_heading_is_empty(self):
        """
        Passage sebelum heading Arab apapun → chapter_title = ''.

        Menggunakan HTML_PRE_HEADING (bukan HTML_BASIC) karena HTML_BASIC
        memiliki paragraf pertama 'هذا نص قصير.' yang hanya 9 char Arab,
        di bawah threshold 15 → difilter → result[0] sudah melewati heading.
        HTML_PRE_HEADING memiliki paragraf pertama ≥15 char Arab sehingga
        lolos filter dan benar-benar merepresentasikan passage pre-heading.
        """
        result = self._parser().parse(HTML_PRE_HEADING)
        assert len(result) >= 1, "Harus ada minimal 1 passage"
        assert result[0]["chapter_title"] == "", (
            f"Passage pertama seharusnya chapter_title='', "
            f"bukan {result[0]['chapter_title']!r}"
        )

    def test_chapter_title_updated_after_heading(self):
        """Passage setelah كتاب الطهارة heading → chapter_title terisi."""
        result = self._parser().parse(HTML_BASIC)
        later = [p for p in result if p["page_ref"] == "page_1_0045"]
        assert later, "Tidak ada passage dengan page_ref page_1_0045"
        assert "الطهارة" in later[0]["chapter_title"]

    def test_page_anchor_not_stored_as_chapter_title(self):
        """page_1_XXXX tidak boleh muncul sebagai chapter_title."""
        result = self._parser().parse(HTML_BASIC)
        for passage in result:
            assert not is_page_anchor_text(passage["chapter_title"]), \
                f"Page anchor stored as chapter_title: {passage['chapter_title']!r}"

    def test_inline_bab_detected_as_chapter_title(self):
        """Paragraf yang diawali 'باب' dideteksi sebagai chapter marker, tidak dijadikan passage."""
        result = self._parser().parse(HTML_WITH_INLINE_BAB)
        # Pastikan paragraf "باب الوضوء..." TIDAK ada sebagai arabic_text passage
        bab_passages = [p for p in result if p["arabic_text"].startswith("باب الوضوء")]
        assert len(bab_passages) == 0, "باب paragraph should not become a passage"

    def test_inline_bab_updates_chapter_title_for_next_passage(self):
        """Setelah 'باب الوضوء' terdeteksi, passage berikutnya menggunakan title itu."""
        result = self._parser().parse(HTML_WITH_INLINE_BAB)
        # Passage setelah بابالوضوء harus punya chapter_title yang sesuai
        wudhu_passages = [p for p in result if "الوضوء فريضة" in p["arabic_text"]]
        assert wudhu_passages, "Passage 'الوضوء فريضة' not found"
        assert "الوضوء" in wudhu_passages[0]["chapter_title"]

    def test_chapter_title_persists_across_pages(self):
        """chapter_title dari page-1 tetap berlaku di page-2 jika tidak ada heading baru."""
        result = self._parser().parse(HTML_BASIC)
        # page_1_0045 dan page_1_0045 (multi-paragraph) harus sama chapter_title
        page45 = [p for p in result if p["page_ref"] == "page_1_0045"]
        if len(page45) > 1:
            titles = [p["chapter_title"] for p in page45]
            assert len(set(titles)) == 1, "chapter_title inconsistent within same page"

    def test_no_headings_all_passages_have_empty_title(self):
        result = self._parser().parse(HTML_NO_HEADINGS)
        for passage in result:
            assert passage["chapter_title"] == ""


class TestHTMLPageParserPageRef:

    def _parser(self):
        return HTMLPageParser(book_slug="tuhfat_muhtaj", authority_level=4)

    def test_page_ref_updated_from_anchor_id(self):
        result = self._parser().parse(HTML_BASIC)
        page_refs = {p["page_ref"] for p in result if p["page_ref"]}
        assert "page_1_0044" in page_refs or "page_1_0045" in page_refs

    def test_page_ref_format_matches_pattern(self):
        import re
        result = self._parser().parse(HTML_BASIC)
        for passage in result:
            if passage["page_ref"]:
                assert re.match(r"^page_\d+_\d+$", passage["page_ref"]), \
                    f"Unexpected page_ref format: {passage['page_ref']!r}"

    def test_page_ref_distinct_from_chapter_title(self):
        result = self._parser().parse(HTML_BASIC)
        for passage in result:
            assert passage["page_ref"] != passage["chapter_title"] or \
                   (not passage["page_ref"] and not passage["chapter_title"])

    def test_accepts_bytes_input(self):
        """HTMLPageParser harus bisa menerima bytes (dari ebooklib item.content)."""
        result = self._parser().parse(HTML_BASIC.encode("utf-8"))
        assert isinstance(result, list)
        assert len(result) > 0


# ════════════════════════════════════════════════════════════════════════════════
# B3 — _build_kitab_citations() (unit test tanpa Flask)
# ════════════════════════════════════════════════════════════════════════════════

class TestBuildKitabCitations:
    """Test fungsi normalisasi kitab hits untuk frontend."""

    def _make_hit(self, slug="al_umm", level=1, chapter="باب الطهارة",
                  page="page_1_0045", text="نص عربي " * 20, score=0.82):
        return {
            "book_slug": slug,
            "authority_level": level,
            "chapter_title": chapter,
            "page_ref": page,
            "arabic_text": text,
            "combined_score": score,
        }

    def _build(self, hits):
        # Import dari chatbot_b3.py jika tersedia, else skip
        try:
            from chatbot import _build_kitab_citations
            return _build_kitab_citations(hits)
        except ImportError:
            pytest.skip("chatbot_b3 not importable (dependency missing)")

    def test_empty_hits_returns_empty(self):
        result = self._build([])
        assert result == []

    def test_max_3_citations_returned(self):
        hits = [self._make_hit(slug=f"book_{i}") for i in range(10)]
        result = self._build(hits)
        assert len(result) <= 3

    def test_citation_has_required_fields(self):
        result = self._build([self._make_hit()])
        assert len(result) == 1
        cite = result[0]
        for key in ("book_name", "book_slug", "authority_label",
                    "authority_level", "chapter_title", "page_ref", "arabic_excerpt"):
            assert key in cite, f"Missing field: {key}"

    def test_arabic_excerpt_truncated_at_200_chars(self):
        long_text = "الطهارة " * 50  # > 200 chars
        result = self._build([self._make_hit(text=long_text)])
        assert len(result[0]["arabic_excerpt"]) <= 205  # 200 + "…"

    def test_known_slug_gets_display_name(self):
        result = self._build([self._make_hit(slug="al_umm")])
        assert "Al-Umm" in result[0]["book_name"]

    def test_unknown_slug_falls_back_to_slug(self):
        result = self._build([self._make_hit(slug="unknown_kitab_xyz")])
        assert result[0]["book_name"] == "unknown_kitab_xyz"

    def test_authority_label_correct_for_level_1(self):
        result = self._build([self._make_hit(level=1)])
        assert result[0]["authority_label"] == "Qawl Imam"

    def test_authority_label_correct_for_level_5(self):
        result = self._build([self._make_hit(level=5)])
        assert result[0]["authority_label"] == "Tafsir / Qawa'id"


# ════════════════════════════════════════════════════════════════════════════════
# Entry point
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
