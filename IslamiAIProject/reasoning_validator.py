# reasoning_validator.py
# IslamiAI - Reasoning & Confidence Layer
#
# DESAIN FILOSOFIS:
# Ini bukan "AI reasoning" dalam arti LLM. Ini adalah rule-based
# evidence chain validator: setiap jawaban harus memiliki backing
# yang terverifikasi sebelum dikirim ke user.
#
# Analoginya: hakim tidak memutus tanpa bukti; sistem ini tidak
# menjawab tanpa dalil yang terkonfirmasi.

from dataclasses import dataclass, field
from typing import Optional
from config import config


@dataclass
class EvidenceReport:
    """Laporan validitas evidence untuk satu jawaban."""
    topic: str
    ruling: str
    confidence_score: float          # 0.0 – 1.0
    confidence_label: str            # "high" | "medium" | "insufficient"
    has_quran_evidence: bool
    has_hadis_evidence: bool
    quran_count: int
    hadis_count: int
    hadis_authenticity: list         # list status tiap hadis
    warnings: list = field(default_factory=list)
    is_answerable: bool = True
    disclaimer: str = ""
    # Layer 4 — kitab corpus fields (default untuk backward compatibility)
    kitab_hits_count: int = 0
    kitab_best_authority: Optional[int] = None  # level 1-5, None jika bukan kitab_corpus


def _compute_confidence_kitab(retrieval_result: dict) -> EvidenceReport:
    """
    Scoring khusus untuk _source='kitab_corpus'.

    Score ditentukan dari authority_level TERBAIK (minimum) di _kitab_hits,
    karena satu nukilan sahih dari Al-Umm sudah cukup sebagai dasar hukum.

    Rubrik authority_level:
      <= 2  (Qawl Imam / Qawl Ashhab)       -> 0.60  medium
      <= 4  (Mu'tamad / Syarh Mu'tamad)     -> 0.52  medium
        5   (Tafsir Ahkam / Qawa'id)         -> 0.50  medium (batas bawah)
      tidak ada hits                         -> 0.00  insufficient
    """
    kitab_hits = retrieval_result.get("_kitab_hits", [])
    warnings = []

    if not kitab_hits:
        score = 0.0
        best_level = None
    else:
        best_level = min(h.get("authority_level", 5) for h in kitab_hits)
        if best_level <= 2:
            score = 0.60
        elif best_level <= 4:
            score = 0.52
        else:                        # level 5: Tafsir & Qawa'id
            score = 0.50
        warnings.append(
            "Jawaban bersumber dari teks kitab korpus; "
            "dalil Quran/hadis belum dipetakan secara eksplisit dalam database."
        )

    if score >= 0.70:
        label = "high"
        disclaimer = ""
        is_answerable = True
    elif score >= config.MIN_CONFIDENCE_SCORE:
        label = "medium"
        disclaimer = (
            "⚠️  Catatan: Jawaban ini merujuk pada teks kitab klasik dalam korpus. "
            "Untuk kepastian hukum, konsultasikan dengan ulama atau ustaz terpercaya."
        )
        is_answerable = True
    else:
        label = "insufficient"
        disclaimer = (
            "❌  Database tidak memiliki cukup dalil untuk menjawab pertanyaan ini dengan "
            "keyakinan yang memadai. Mohon tanyakan langsung kepada ulama atau ustaz."
        )
        is_answerable = False
        warnings.append("Confidence terlalu rendah untuk dijawab secara otomatis.")

    return EvidenceReport(
        topic=retrieval_result.get("topic", "unknown"),
        ruling=retrieval_result.get("ruling", ""),
        confidence_score=score,
        confidence_label=label,
        has_quran_evidence=False,
        has_hadis_evidence=False,
        quran_count=0,
        hadis_count=0,
        hadis_authenticity=[],
        warnings=warnings,
        is_answerable=is_answerable,
        disclaimer=disclaimer,
        kitab_hits_count=len(kitab_hits),
        kitab_best_authority=best_level,
    )


def compute_confidence(retrieval_result: dict) -> EvidenceReport:
    """
    Hitung confidence score berdasarkan kualitas dan kuantitas evidence.

    Untuk _source='kitab_corpus', scoring didelegasikan ke
    _compute_confidence_kitab() karena dalil tidak hadir sebagai
    quran[]/hadis[] melainkan sebagai _kitab_hits[].

    Scoring rubric (Layer 1-3):
    - Quran evidence     : +0.40 (ada) + 0.05 per ayat tambahan (max 0.55)
    - Hadis sahih        : +0.30 (ada) + 0.05 per hadis tambahan (max 0.40)
    - Hadis hasan        : +0.15 per hadis
    - Hadis dhaif        : +0.00 (tidak menambah score, hanya warning)
    - Rule confidence    : +0.05 jika rule sendiri ditandai "high"

    Threshold:
    - >= 0.70 -> high (aman dijawab)
    - >= 0.50 -> medium (dijawab dengan disclaimer)
    - <  0.50 -> insufficient (tolak, arahkan ke ulama)
    """
    # ── Dispatch ke kitab_corpus scorer ───────────────────────
    if retrieval_result.get("_source") == "kitab_corpus":
        return _compute_confidence_kitab(retrieval_result)

    # ── Scoring normal (Layer 1-3) ─────────────────────────────
    warnings = []
    score = 0.0

    quran_refs = retrieval_result.get("quran", [])
    hadis_refs = retrieval_result.get("hadis", [])

    # Quran score
    has_quran = len(quran_refs) > 0
    if has_quran:
        score += 0.40
        extra = min(len(quran_refs) - 1, 3) * 0.05
        score += extra

    # Hadis score
    authenticity_list = []
    has_sahih = False
    for h in hadis_refs:
        auth = h.get("authenticity", "").lower()
        authenticity_list.append(auth)
        if auth == "sahih":
            if not has_sahih:
                score += 0.30
                has_sahih = True
            else:
                score += min(0.05, 0.40 - 0.30)
        elif auth == "hasan":
            score += 0.15
            warnings.append(f"Hadis '{h.get('source', '')}' berstatus hasan, bukan sahih.")
        elif auth == "dhaif":
            warnings.append(f"Hadis '{h.get('source', '')}' berstatus dhaif dan tidak menambah confidence.")

    has_hadis = has_sahih or any(a == "hasan" for a in authenticity_list)

    # Rule-level confidence bonus
    rule_confidence = retrieval_result.get("confidence", "medium")
    if rule_confidence == "high":
        score += 0.05

    # Layer 1 override: rule yang dikurasi manual dengan confidence "high"
    # dipercaya sebagai minimum medium meskipun dalil eksplisit terbatas.
    # Jawab dengan disclaimer — jangan tolak sepenuhnya.
    source = retrieval_result.get("_source", "")
    if source == "static_rules" and rule_confidence == "high":
        score = max(score, 0.55)

    # Cap di 1.0
    score = min(score, 1.0)
    score = round(score, 2)

    # Label
    if score >= 0.70:
        label = "high"
        disclaimer = ""
        is_answerable = True
    elif score >= config.MIN_CONFIDENCE_SCORE:
        label = "medium"
        disclaimer = (
            "⚠️  Catatan: Hukum ini berdasarkan dalil yang tersedia dalam database. "
            "Untuk kepastian, konsultasikan dengan ulama atau ustaz terpercaya."
        )
        is_answerable = True
    else:
        label = "insufficient"
        disclaimer = (
            "❌  Database tidak memiliki cukup dalil untuk menjawab pertanyaan ini dengan "
            "keyakinan yang memadai. Mohon tanyakan langsung kepada ulama atau ustaz."
        )
        is_answerable = False
        warnings.append("Confidence terlalu rendah untuk dijawab secara otomatis.")

    return EvidenceReport(
        topic=retrieval_result.get("topic", "unknown"),
        ruling=retrieval_result.get("ruling", ""),
        confidence_score=score,
        confidence_label=label,
        has_quran_evidence=has_quran,
        has_hadis_evidence=has_hadis,
        quran_count=len(quran_refs),
        hadis_count=len(hadis_refs),
        hadis_authenticity=authenticity_list,
        warnings=warnings,
        is_answerable=is_answerable,
        disclaimer=disclaimer,
    )


def gate_answer(retrieval_result: Optional[dict]) -> tuple[bool, EvidenceReport | None, str]:
    """
    Gate function: apakah sistem boleh menjawab?

    Returns:
        (can_answer: bool, report: EvidenceReport | None, reason: str)
    """
    if retrieval_result is None:
        return False, None, (
            "Pertanyaan tidak cocok dengan topik yang ada dalam database. "
            "Silakan tanyakan kepada ulama setempat."
        )

    report = compute_confidence(retrieval_result)

    if not report.is_answerable:
        return False, report, report.disclaimer

    return True, report, ""


if __name__ == "__main__":
    mock_result_strong = {
        "topic": "syahadat",
        "ruling": "wajib",
        "confidence": "high",
        "quran": [{"arabic_text": "...", "authenticity": ""}],
        "hadis": [
            {"source": "Bukhari no. 8", "authenticity": "sahih"},
            {"source": "Muslim no. 16", "authenticity": "sahih"},
        ]
    }

    mock_result_kitab = {
        "topic": "wudhu",
        "ruling": "",
        "confidence": "medium",
        "quran": [],
        "hadis": [],
        "_source": "kitab_corpus",
        "_kitab_hits": [
            {"book_slug": "al_umm", "authority_level": 1,
             "chapter_title": "كِتَابُ الطَّهَارَةِ", "arabic_text": "نَصٌّ"},
        ]
    }

    print("=== Reasoning Validator Test ===\n")
    for label, result in [
        ("STRONG (syahadat)", mock_result_strong),
        ("KITAB CORPUS (wudhu)", mock_result_kitab),
        ("NONE", None),
    ]:
        can_answer, report, reason = gate_answer(result)
        print(f"Case: {label}")
        print(f"  Can answer  : {can_answer}")
        if report:
            print(f"  Score       : {report.confidence_score}")
            print(f"  Label       : {report.confidence_label}")
            print(f"  KitabLevel  : {report.kitab_best_authority}")
        if reason:
            print(f"  Reason      : {reason[:80]}")
        print()
