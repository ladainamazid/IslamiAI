"""
reasoning/layer1_perception_semantic.py
─────────────────────────────────────────────────────────────────
LAYER 1 — Perception + Semantic Fusion
[Menggantikan L01 + L02 dari versi 20-layer]

Tanggung jawab ganda yang koheren:
  A. Persepsi Input: deteksi bahasa, tipe, panjang, sinyal struktural
  B. Analisis Semantik: ekstrak token bermakna, scoring domain Islam

Alasan penggabungan L01+L02:
  Kedua layer memproses string yang SAMA dengan transformasi berurutan
  yang tidak membutuhkan decision point di antaranya. Memisahkannya
  hanya menambah overhead tanpa manfaat arsitektural.

Integrasi dengan IslamiAIProject:
  - Token domain Islam digunakan L2 untuk pemetaan topik
  - input_type digunakan L3 untuk routing (fatwa vs. ibadah vs. sejarah)
  - language digunakan L6 untuk memilih format response (Arabic/Latin)

Domain Islam yang dikenali (dari 12 topik IslamiAI):
  syahadat, shalat, zakat, puasa, haji, nikah, thaharah,
  aqidah, muamalah, jinayah, faraid, dan umum
"""

import re
from typing import Any, Dict, List, Tuple
from base_layer import BaseLayer

# ─── Deteksi Bahasa ────────────────────────────────────────────
_ID_MARKERS = {"yang", "ini", "adalah", "untuk", "dengan", "dan", "atau",
               "tidak", "dari", "pada", "dalam", "ke", "di", "bagaimana",
               "apa", "mengapa", "boleh", "hukum", "cara", "apakah"}
_EN_MARKERS = {"the", "is", "are", "and", "or", "for", "with", "not",
               "how", "what", "why", "islamic", "allowed", "haram", "halal"}
_AR_MARKERS = {"الله", "صلاة", "زكاة", "حج", "نكاح", "طهارة", "فقه"}

# ─── Lexikon Domain Islam (12 Topik IslamiAI) ──────────────────
_ISLAMIC_DOMAIN_LEXICON: Dict[str, List[str]] = {
    "syahadat":   ["syahadat", "shahada", "tauhid", "iman", "kalimat", "syahadah",
                   "la ilaha", "muallaf", "masuk islam", "murtad"],
    "shalat":     ["shalat", "salat", "solat", "wudhu", "wudu", "tayamum",
                   "qiblat", "azan", "iqamah", "rakaat", "sujud", "ruku",
                   "fardhu", "sunnah", "jamaah", "imam"],
    "zakat":      ["zakat", "fitrah", "maal", "nisab", "haul", "amil",
                   "infak", "sedekah", "wakaf", "mustahik"],
    "puasa":      ["puasa", "saum", "shaum", "ramadan", "ramadhan", "sahur",
                   "buka", "iftar", "fidyah", "kafarat", "itikaf"],
    "haji":       ["haji", "hajj", "umrah", "ihram", "tawaf", "sai",
                   "wukuf", "arafah", "mina", "muzdalifah", "mabit", "dam"],
    "nikah":      ["nikah", "pernikahan", "perkawinan", "mahar", "wali",
                   "saksi", "talak", "cerai", "rujuk", "iddah", "nafkah",
                   "poligami", "mahram", "khitbah"],
    "thaharah":   ["thaharah", "taharah", "najis", "suci", "bersuci", "mandi",
                   "wajib", "haid", "nifas", "junub", "hadats", "istinja"],
    "aqidah":     ["aqidah", "akidah", "iman", "tauhid", "rukun", "asmaul",
                   "husna", "sifat", "allah", "rasul", "nabi", "malaikat",
                   "kitab", "qada", "qadar", "akhirat", "surga", "neraka"],
    "muamalah":   ["muamalah", "jual", "beli", "riba", "hutang", "utang",
                   "gadai", "sewa", "ijarah", "mudharabah", "musyarakah",
                   "halal", "haram", "hukum", "bisnis", "investasi"],
    "jinayah":    ["jinayah", "hudud", "qisas", "diyat", "hukuman", "pidana",
                   "zina", "mencuri", "minum", "murtad", "qadzaf"],
    "faraid":     ["faraid", "waris", "warisan", "pewaris", "ahli waris",
                   "wasiat", "hibah", "pusaka", "hak waris"],
    "umum":       ["islam", "muslim", "muslimah", "doa", "dzikir", "tasbih",
                   "istighfar", "taubat", "akhlak", "adab", "sunnah"],
}

_STOPWORDS = {
    "yang", "ini", "itu", "adalah", "untuk", "dengan", "dan", "atau",
    "tidak", "dari", "pada", "dalam", "ke", "di", "ya", "bisa", "sudah",
    "saya", "apa", "bagaimana", "apakah", "mohon", "tolong", "jelaskan",
    "the", "is", "are", "and", "or", "for", "with", "not", "a", "an",
}


def _detect_language(text: str) -> str:
    # Cek karakter Arabic Unicode
    if re.search(r'[\u0600-\u06FF]', text):
        return "ar"
    tokens = set(re.findall(r'\b\w+\b', text.lower()))
    id_score = len(tokens & _ID_MARKERS)
    en_score = len(tokens & _EN_MARKERS)
    if id_score == 0 and en_score == 0:
        return "id"   # Default bahasa Indonesia untuk IslamiAI
    return "id" if id_score >= en_score else "en"


def _compute_semantic_density(text: str) -> float:
    tokens = re.findall(r'\b\w+\b', text.lower())
    if not tokens:
        return 0.0
    return round(len(set(tokens)) / len(tokens), 4)


def _classify_input_type(text: str) -> str:
    """Klasifikasi berdasarkan struktur permintaan."""
    stripped = text.strip().lower()
    if stripped.endswith("?") or stripped.startswith(("apa", "bagaimana", "apakah",
                                                       "mengapa", "kapan", "siapa",
                                                       "what", "how", "why", "is ", "are ")):
        return "pertanyaan"
    if any(stripped.startswith(k) for k in ("jelaskan", "ceritakan", "uraikan",
                                              "explain", "describe", "tell me")):
        return "permintaan_penjelasan"
    if any(w in stripped for w in ("hukum", "boleh", "halal", "haram", "mubah",
                                    "wajib", "sunnah", "makruh", "allowed", "permitted")):
        return "permintaan_fatwa"
    if any(w in stripped for w in ("cara", "langkah", "bagaimana cara",
                                    "how to", "steps", "tutorial")):
        return "permintaan_prosedur"
    return "pernyataan"


def _score_domains(content_tokens: List[str]) -> Dict[str, float]:
    """
    Hitung relevansi tiap domain Islam dari token content.
    Return dict terurut dari skor tertinggi.
    """
    token_set = set(t.lower() for t in content_tokens)
    raw_scores: Dict[str, int] = {}

    for domain, keywords in _ISLAMIC_DOMAIN_LEXICON.items():
        hits = sum(1 for kw in keywords
                   if any(kw in t or t in kw for t in token_set))
        if hits > 0:
            raw_scores[domain] = hits

    if not raw_scores:
        return {"umum": 1.0}

    total = sum(raw_scores.values())
    return {
        d: round(s / total, 4)
        for d, s in sorted(raw_scores.items(), key=lambda x: -x[1])
    }


class Layer1_PerceptionSemantic(BaseLayer):
    """
    Layer terluar: transformasi raw string → representasi semantik bermakna.
    Output layer ini adalah fondasi untuk semua layer berikutnya.
    """

    @property
    def layer_id(self) -> str:
        return "L1_perception_semantic"

    @property
    def required_keys(self):
        return ["input"]

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raw = state["input"]

        # A. Persepsi
        language = _detect_language(raw)
        token_count = len(re.findall(r'\b\w+\b', raw))
        semantic_density = _compute_semantic_density(raw)
        input_type = _classify_input_type(raw)

        # B. Semantik
        all_tokens = re.findall(r'\b\w+\b', raw.lower())
        content_tokens = [t for t in all_tokens if t not in _STOPWORDS and len(t) > 2]
        domain_scores = _score_domains(content_tokens)
        primary_domain = next(iter(domain_scores))   # Tertinggi pertama
        secondary_domains = list(domain_scores.keys())[1:3]  # Max 2 domain sekunder

        # Confidence: fungsi dari kejelasan sinyal
        domain_confidence = domain_scores.get(primary_domain, 0)
        length_factor = min(token_count / 15, 1.0)
        confidence = round(domain_confidence * 0.6 + semantic_density * 0.2 + length_factor * 0.2, 4)

        warnings = []
        if token_count < 4:
            warnings.append("Input terlalu pendek — ambiguitas tinggi, jawaban mungkin tidak akurat.")
        if primary_domain == "umum" and domain_scores.get("umum", 0) < 0.5:
            warnings.append("Domain Islam tidak teridentifikasi jelas — akan diperlakukan sebagai pertanyaan umum.")

        return {
            # Persepsi
            "raw_input": raw,
            "language": language,
            "input_type": input_type,
            "token_count": token_count,
            "semantic_density": semantic_density,
            # Semantik
            "content_tokens": content_tokens[:15],
            "domain_scores": domain_scores,
            "primary_domain": primary_domain,
            "secondary_domains": secondary_domains,
            # Meta
            "_confidence": confidence,
            "_warnings": warnings,
            "_religious_content": True,  # Selalu True di IslamiAI
        }
