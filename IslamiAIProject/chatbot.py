"""
chatbot.py — IslamiAI Chatbot Layer (Phase B3 update)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase B3 additions vs Phase A.5:
  - ChatResponse: +2 field (source, kitab_citations)
  - _build_kitab_citations(): normalisasi _kitab_hits → list siap kirim
  - Disclaimer kitab_corpus otomatis ditambahkan jika source == 'kitab_corpus'

Backward compatible: jika retrieval_result tidak punya _source / _kitab_hits
(query diselesaikan di Layer 1-3), field baru diisi default kosong.

Pipeline tidak berubah:
  user input
    → parse_user_query()      [query_parser.py]
    → retrieve_ruling()       [retrieval.py]
    → gate_answer()           [reasoning_validator.py]
    → format_answer()         [formatter.py]
    → ChatResponse dict
"""

import logging
from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

from query_parser import parse_user_query
from retrieval import retrieve_ruling
from reasoning_validator import gate_answer, EvidenceReport
from formatter import format_answer

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# Slug → display name untuk kitab_citations (26 kitab Phase A)
_SLUG_TO_DISPLAY: dict[str, str] = {
    "al_umm":             "Al-Umm (الأم) — Imam Al-Syafi'i",
    "al_risalah":         "Al-Risalah (الرسالة) — Imam Al-Syafi'i",
    "mukhtasar_muzani":   "Mukhtasar Al-Muzani (مختصر المزني)",
    "al_hawi_kabir":      "Al-Hawi Al-Kabir (الحاوي الكبير) — Al-Mawardi",
    "al_majmu":           "Al-Majmu' (المجموع) — Al-Nawawi",
    "rawdhat_talibin":    "Rawdhat Al-Talibin (روضة الطالبين) — Al-Nawawi",
    "minhaj_talibin":     "Minhaj Al-Talibin (منهاج الطالبين) — Al-Nawawi",
    "tuhfat_muhtaj":      "Tuhfat Al-Muhtaj (تحفة المحتاج) — Ibn Hajar Al-Haytami",
    "nihayat_muhtaj":     "Nihayat Al-Muhtaj (نهاية المحتاج) — Al-Ramli",
    "mughni_muhtaj":      "Mughni Al-Muhtaj (مغني المحتاج) — Al-Khatib Al-Syarbini",
    "asna_matalib":       "Asna Al-Matalib (أسنى المطالب) — Zakariyya Al-Anshari",
    "ianat_talibin":      "I'anat Al-Talibin (إعانة الطالبين) — Al-Bakri",
    "irshad_faqih":       "Irshad Al-Faqih (إرشاد الفقيه) — Ibn Kathir",
    "bughyat_mustarsyidin": "Bughyat Al-Mustarsyidin (بغية المسترشدين) — Ba'alawi",
    "al_kiya_harrasi":    "Ahkam Al-Qur'an (أحكام القرآن) — Al-Kiya Al-Harrasi",
    "al_qurtubi":         "Al-Jami' li Ahkam Al-Qur'an (الجامع) — Al-Qurtubi",
    "al_jassas":          "Ahkam Al-Qur'an (أحكام القرآن) — Al-Jassas",
    "ibn_kathir_tafsir":  "Tafsir Ibn Kathir (تفسير ابن كثير)",
    "ibn_ashur":          "Al-Tahrir wa Al-Tanwir — Ibn Ashur",
    "al_suyuthi_qawaid":  "Al-Asybah wa Al-Nazha'ir — Al-Suyuthi",
    "al_zarkasyi_qawaid": "Al-Manthur fi Al-Qawa'id — Al-Zarkasyi",
    "izz_abd_salam":      "Qawa'id Al-Ahkam — Al-'Izz ibn Abd Al-Salam",
}

_AUTHORITY_LABEL: dict[int, str] = {
    1: "Qawl Imam",
    2: "Qawl Ashhab",
    3: "Mu'tamad",
    4: "Syarh Mu'tamad",
    5: "Tafsir / Qawa'id",
}

# Disclaimer khusus untuk jawaban dari kitab_corpus (Layer 4)
_KITAB_CORPUS_DISCLAIMER = (
    "📚 Jawaban ini diambil dari korpus kitab klasik melalui pencarian teks penuh "
    "(full-text search). Kutipan ditampilkan sesuai relevansi teks Arab, bukan "
    "penilaian kontekstual seorang ulama. Pastikan memverifikasi dengan membaca "
    "kitab asli atau berkonsultasi dengan ulama yang berkompeten."
)

# Jumlah kitab citations yang dikirim ke frontend (max)
_MAX_KITAB_CITATIONS = 3


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _build_kitab_citations(kitab_hits: list[dict]) -> list[dict]:
    """
    Normalisasi _kitab_hits dari retrieval_result menjadi list citation
    yang siap dikirim ke frontend.

    Input (dari retrieval.py Layer 4):
        [{'book_slug': 'al_umm', 'authority_level': 1,
          'chapter_title': 'كتاب الطهارة', 'page_ref': 'page_1_0045',
          'arabic_text': 'قال الشافعي...', 'combined_score': 0.82}, ...]

    Output (untuk frontend):
        [{'book_name': 'Al-Umm (الأم) — Imam Al-Syafi'i',
          'authority_label': 'Qawl Imam',
          'authority_level': 1,
          'chapter_title': 'كتاب الطهارة',
          'page_ref': 'page_1_0045',
          'arabic_excerpt': 'قال الشافعي رحمه الله...',   ← max 200 chars
          'combined_score': 0.82}, ...]
    """
    citations = []
    for hit in kitab_hits[:_MAX_KITAB_CITATIONS]:
        slug = hit.get("book_slug", "")
        arabic_text = hit.get("arabic_text", "")
        # Truncate untuk display (full text ada di hit aslinya jika dibutuhkan)
        excerpt = arabic_text[:200].rstrip() + ("…" if len(arabic_text) > 200 else "")

        citations.append({
            "book_name":       _SLUG_TO_DISPLAY.get(slug, slug),
            "book_slug":       slug,
            "authority_label": _AUTHORITY_LABEL.get(hit.get("authority_level", 5), "—"),
            "authority_level": hit.get("authority_level", 5),
            "chapter_title":   hit.get("chapter_title", ""),
            "page_ref":        hit.get("page_ref", ""),
            "arabic_excerpt":  excerpt,
            "combined_score":  hit.get("combined_score", 0.0),
        })
    return citations


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
    confidence_label: str           # "high" | "medium" | "insufficient"
    warnings: list
    disclaimer: str
    source: str = "unknown"         # B3: _source dari retrieval_result
    kitab_citations: list = field(default_factory=list)  # B3: top kitab hits
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChatRejection:
    """Response ketika pipeline menolak menjawab."""
    status: str                     # "rejected" | "no_match" | "error"
    reason: str
    topic: Optional[str]
    confidence_score: float
    confidence_label: str
    warnings: list
    source: str = "unknown"         # B3: tambahkan agar interface seragam
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

    NEVER RAISES: semua exception ditangkap sebagai ChatRejection status="error".
    """
    logger.info("[chat] question='%s'", question[:80])

    try:
        # ── STEP 1: Parse ────────────────────────────────────────────────────
        topic = parse_user_query(question)
        logger.debug("[chat] topic resolved → %s", topic)

        # ── STEP 2: Retrieve ─────────────────────────────────────────────────
        retrieval_result = retrieve_ruling(topic) if topic else None

        # ── STEP 3: Gate ─────────────────────────────────────────────────────
        can_answer, report, reason = gate_answer(retrieval_result)

        # Metadata sumber (backward-compatible)
        source = (retrieval_result or {}).get("_source", "unknown")

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
                source=source,
            ).to_dict()

        # ── STEP 4b: Format & kembalikan ─────────────────────────────────────
        formatted = format_answer(retrieval_result)

        # Build kitab citations jika source adalah kitab_corpus
        kitab_citations: list = []
        combined_disclaimer = report.disclaimer

        if source == "kitab_corpus":
            raw_hits = (retrieval_result or {}).get("_kitab_hits", [])
            kitab_citations = _build_kitab_citations(raw_hits)
            # Gabungkan disclaimer evidence dengan disclaimer kitab_corpus
            if combined_disclaimer:
                combined_disclaimer = combined_disclaimer + "\n\n" + _KITAB_CORPUS_DISCLAIMER
            else:
                combined_disclaimer = _KITAB_CORPUS_DISCLAIMER

        return ChatResponse(
            status="ok",
            answer=formatted,
            topic=topic or "",
            confidence_score=report.confidence_score,
            confidence_label=report.confidence_label,
            warnings=report.warnings,
            disclaimer=combined_disclaimer,
            source=source,
            kitab_citations=kitab_citations,
        ).to_dict()

    except Exception as exc:
        logger.exception("[chat] unexpected error: %s", exc)
        return ChatRejection(
            status="error",
            reason="Terjadi kesalahan internal. Silakan coba lagi.",
            topic=None,
            confidence_score=0.0,
            confidence_label="insufficient",
            warnings=[str(exc)],
            source="error",
        ).to_dict()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS (opsional, dipakai app.py / tests)
# ─────────────────────────────────────────────────────────────────────────────

def is_answerable(question: str) -> bool:
    """True jika pertanyaan menghasilkan ChatResponse (status='ok')."""
    result = chat(question)
    return result.get("status") == "ok"


def get_confidence(question: str) -> float:
    """Shortcut: kembalikan confidence_score saja."""
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
        print(f"Source    : {result.get('source', 'n/a')}")
        if result['status'] == 'ok':
            print(f"Topic     : {result['topic']}")
            print(f"Confidence: {result['confidence_score']} ({result['confidence_label']})")
            cites = result.get('kitab_citations', [])
            if cites:
                print(f"Citations : {len(cites)} kitab hits")
                for c in cites:
                    print(f"  - {c['book_name']} | {c['authority_label']}")
        else:
            print(f"Reason    : {result['reason']}")
