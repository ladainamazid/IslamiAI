"""
app.py — IslamiAI Production Flask App (Phase B3 update)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase B3 additions vs Phase A.5:
  /api/ask  response JSON:
    + "source"             : "_source" dari retrieval_result
    + "kitab_citations"    : top-3 kitab hits (normalized)
    + "kitab_hits_count"   : dari EvidenceReport (Phase A.5 field)
    + "kitab_best_authority" : dari EvidenceReport (Phase A.5 field)
    + "disclaimer"         : kitab_corpus disclaimer otomatis digabung

  /api/health:
    + "db_status"          : cek ketersediaan islamiai.db + row count

  Semua additions backward-compatible (getattr default fallback).
"""

import logging
import os
import time
import uuid
from flask import Flask, render_template, request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config
from validators import validate_question, InputValidationError
from query_parser import parse_user_query
from retrieval import retrieve_ruling
from formatter import format_answer
from reasoning_validator import gate_answer

# ── Sentry (error monitoring) ─────────────────────────────────────────────────
_sentry_enabled = False
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FlaskIntegration()],
            send_default_pii=False,
            traces_sample_rate=0.10,
        )
        _sentry_enabled = True
    except ImportError:
        pass

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s [%(request_id)s]: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ]
)

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        try:
            from flask import g as flask_g
            record.request_id = getattr(flask_g, "request_id", "-")
        except RuntimeError:
            record.request_id = "-"
        return True

_request_id_filter = RequestIdFilter()
logging.getLogger().addFilter(_request_id_filter)
for _handler in logging.getLogger().handlers:
    _handler.addFilter(_request_id_filter)

logger = logging.getLogger("islamiai")


# ── Flask App ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["SESSION_COOKIE_SECURE"]   = config.SESSION_COOKIE_SECURE
app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE

_redis_url = os.getenv("REDIS_URL", "memory://")
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri=_redis_url,
    default_limits=[],
    strategy="fixed-window",
    headers_enabled=True,
)


# ── B3 Helpers ─────────────────────────────────────────────────────────────────

# Slug → display name (sinkron dengan chatbot.py _SLUG_TO_DISPLAY)
_SLUG_TO_NAME: dict[str, str] = {
    "al_umm":             "Al-Umm (الأم)",
    "al_risalah":         "Al-Risalah (الرسالة)",
    "mukhtasar_muzani":   "Mukhtasar Al-Muzani",
    "al_hawi_kabir":      "Al-Hawi Al-Kabir",
    "al_majmu":           "Al-Majmu'",
    "rawdhat_talibin":    "Rawdhat Al-Talibin",
    "minhaj_talibin":     "Minhaj Al-Talibin",
    "tuhfat_muhtaj":      "Tuhfat Al-Muhtaj",
    "nihayat_muhtaj":     "Nihayat Al-Muhtaj",
    "mughni_muhtaj":      "Mughni Al-Muhtaj",
    "asna_matalib":       "Asna Al-Matalib",
    "ianat_talibin":      "I'anat Al-Talibin",
    "irshad_faqih":       "Irshad Al-Faqih",
    "bughyat_mustarsyidin": "Bughyat Al-Mustarsyidin",
    "al_kiya_harrasi":    "Ahkam Al-Qur'an (Al-Kiya)",
    "al_qurtubi":         "Al-Jami' li Ahkam Al-Qur'an",
    "al_jassas":          "Ahkam Al-Qur'an (Al-Jassas)",
    "ibn_kathir_tafsir":  "Tafsir Ibn Kathir",
    "ibn_ashur":          "Al-Tahrir wa Al-Tanwir",
    "al_suyuthi_qawaid":  "Al-Asybah wa Al-Nazha'ir",
    "al_zarkasyi_qawaid": "Al-Manthur fi Al-Qawa'id",
    "izz_abd_salam":      "Qawa'id Al-Ahkam",
}

_AUTHORITY_LABEL: dict[int, str] = {
    1: "Qawl Imam",
    2: "Qawl Ashhab",
    3: "Mu'tamad",
    4: "Syarh Mu'tamad",
    5: "Tafsir / Qawa'id",
}

_KITAB_CORPUS_DISCLAIMER = (
    "📚 Jawaban ini diambil dari korpus kitab klasik melalui full-text search. "
    "Pastikan memverifikasi dengan membaca kitab asli atau berkonsultasi dengan ulama."
)


def _build_kitab_citations(kitab_hits: list[dict], max_hits: int = 3) -> list[dict]:
    """
    Normalisasi _kitab_hits untuk dikirim ke frontend.
    Menghilangkan field internal (fts_rank, combined_score tidak ditampilkan ke user).
    """
    result = []
    for hit in kitab_hits[:max_hits]:
        slug = hit.get("book_slug", "")
        arabic_text = hit.get("arabic_text", "")
        excerpt = arabic_text[:200].rstrip() + ("…" if len(arabic_text) > 200 else "")
        result.append({
            "book_name":       _SLUG_TO_NAME.get(slug, slug),
            "book_slug":       slug,
            "authority_label": _AUTHORITY_LABEL.get(hit.get("authority_level", 5), "—"),
            "authority_level": hit.get("authority_level", 5),
            "chapter_title":   hit.get("chapter_title", ""),
            "page_ref":        hit.get("page_ref", ""),
            "arabic_excerpt":  excerpt,
        })
    return result


def _build_combined_disclaimer(
    evidence_disclaimer: str,
    source: str,
) -> str:
    """Gabungkan evidence disclaimer + kitab_corpus disclaimer jika relevan."""
    parts = [p for p in [evidence_disclaimer, ""] if p]
    if source == "kitab_corpus":
        parts.append(_KITAB_CORPUS_DISCLAIMER)
    return "\n\n".join(p for p in parts if p)


# ── Middleware ─────────────────────────────────────────────────────────────────

@app.before_request
def assign_request_id():
    g.request_id = uuid.uuid4().hex[:8]
    g.start_time = time.time()


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"]  = "nosniff"
    response.headers["X-Frame-Options"]          = "DENY"
    response.headers["X-XSS-Protection"]         = "1; mode=block"
    response.headers["Referrer-Policy"]          = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"]  = (
        "default-src 'self'; "
        "font-src 'self' https://fonts.gstatic.com; "
        "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline';"
    )
    if not config.DEBUG:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    if hasattr(g, "request_id"):
        response.headers["X-Request-ID"] = g.request_id
    return response


@app.after_request
def log_request(response):
    if hasattr(g, "start_time"):
        duration_ms = round((time.time() - g.start_time) * 1000, 1)
        logger.info(
            "%s %s [%s] %sms ip=%s",
            request.method, request.path,
            response.status_code, duration_ms,
            request.remote_addr,
        )
    return response


@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning("Rate limit hit: ip=%s", request.remote_addr)
    return jsonify({
        "error": "Terlalu banyak permintaan. Silakan tunggu sebentar.",
        "code": "RATE_LIMITED",
    }), 429


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/ask", methods=["POST"])
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE} per minute")
def ask_question():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body harus berupa JSON.", "code": "BAD_REQUEST"}), 400

    raw_question = data.get("question", "")

    try:
        question = validate_question(raw_question)
    except InputValidationError as e:
        logger.info("Validation failed: ip=%s error='%s'", request.remote_addr, e)
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422

    logger.info("Query: ip=%s question='%s'", request.remote_addr, question[:60])

    # ── Pipeline: parse → retrieve → gate → format ─────────────────────────
    topic            = parse_user_query(question)
    retrieval_result = retrieve_ruling(topic) if topic else None
    can_answer, evidence_report, block_reason = gate_answer(retrieval_result)

    # ── B3: Ekstrak metadata sumber ────────────────────────────────────────
    source = (retrieval_result or {}).get("_source", "unknown")

    if not can_answer:
        return jsonify({
            "found":      False,
            "answer":     block_reason,
            "confidence": "insufficient",
            "topic":      topic,
            "source":     source,       # B3
            "code":       "NO_RELIABLE_EVIDENCE",
        })

    answer_text = format_answer(retrieval_result)

    # ── B3: Kitab corpus metadata ──────────────────────────────────────────
    kitab_hits_raw    = (retrieval_result or {}).get("_kitab_hits", [])
    kitab_citations   = _build_kitab_citations(kitab_hits_raw)

    # getattr dengan default untuk backward compat dengan pre-Phase A.5 EvidenceReport
    kitab_hits_count     = getattr(evidence_report, "kitab_hits_count", len(kitab_hits_raw))
    kitab_best_authority = getattr(evidence_report, "kitab_best_authority", None)

    combined_disclaimer = _build_combined_disclaimer(
        evidence_report.disclaimer, source
    )

    return jsonify({
        # ── Core response (tidak berubah dari Phase A.5) ───────────────────
        "found":            True,
        "answer":           answer_text,
        "topic":            topic,
        "ruling":           (retrieval_result or {}).get("ruling", ""),
        "madhab":           (retrieval_result or {}).get("madhab", ""),
        "reasoning":        (retrieval_result or {}).get("reasoning", ""),
        "confidence":       evidence_report.confidence_label,
        "confidence_score": evidence_report.confidence_score,
        "quran":            (retrieval_result or {}).get("quran", []),
        "hadis":            (retrieval_result or {}).get("hadis", []),
        "evidence_summary": {
            "quran_count": evidence_report.quran_count,
            "hadis_count": evidence_report.hadis_count,
        },
        "warnings":         evidence_report.warnings,
        "disclaimer":       combined_disclaimer,     # B3: gabungan
        # ── B3: Tambahan metadata sumber ──────────────────────────────────
        "source":                source,
        "kitab_citations":       kitab_citations,
        "kitab_hits_count":      kitab_hits_count,
        "kitab_best_authority":  kitab_best_authority,
        # ── Meta ──────────────────────────────────────────────────────────
        "request_id":       g.request_id,
    })


@app.route("/api/health")
def health():
    """Health check endpoint dengan DB status."""
    from islamic_data import quran_verses, hadis_collection, shafii_rules

    # ── B3: DB health check ───────────────────────────────────────────────
    db_status: dict = {"available": False, "kitab_corpus_count": 0}
    try:
        _db_path = os.path.join(os.path.dirname(__file__), "islamiai.db")
        if os.path.exists(_db_path):
            import sqlite3
            conn = sqlite3.connect(_db_path)
            row = conn.execute(
                "SELECT COUNT(*) FROM kitab_corpus"
            ).fetchone()
            conn.close()
            db_status = {
                "available": True,
                "kitab_corpus_count": row[0] if row else 0,
            }
    except Exception as e:
        db_status["error"] = str(e)

    return jsonify({
        "status": "ok",
        "data": {
            "quran_verses": len(quran_verses),
            "hadis":        len(hadis_collection),
            "rules":        len(shafii_rules),
        },
        "db": db_status,        # B3
        "sentry": _sentry_enabled,
        "rate_limiter_backend": "redis" if "redis" in _redis_url else "memory",
    })


@app.route("/api/topics")
def get_topics():
    """
    Kembalikan list topic yang tersedia di static rules.
    Dipakai sidebar frontend untuk topic suggestions.
    """
    from islamic_data import shafii_rules
    topics = [
        {
            "key":      k,
            "ruling":   v.get("ruling", ""),
            "keywords": v.get("keywords", [])[:3],
        }
        for k, v in shafii_rules.items()
    ]
    return jsonify({"topics": topics, "count": len(topics)})


# ── Error handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint tidak ditemukan.", "code": "NOT_FOUND"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method tidak diizinkan.", "code": "METHOD_NOT_ALLOWED"}), 405

@app.errorhandler(500)
def internal_error(e):
    logger.error("Internal error: %s", e)
    return jsonify({
        "error": "Terjadi kesalahan internal. Tim teknis telah dinotifikasi.",
        "code":  "INTERNAL_ERROR",
    }), 500


if __name__ == "__main__":
    logger.info(
        "Starting IslamiAI on %s:%s | DEBUG=%s | Sentry=%s | RateLimit=%s",
        config.HOST, config.PORT, config.DEBUG, _sentry_enabled, _redis_url[:20],
    )
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
