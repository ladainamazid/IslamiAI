# app.py
# IslamiAI — Production Flask App (Phase 1 + Phase 2)
# Security hardening: flask-limiter + Redis, request ID tracing, Sentry.
#
# Changelog:
#   Phase 1   — /api/ask, /api/health, rate limiter, Sentry, security headers
#   Phase 2   — /chat (chatbot.py), /status (debug endpoint)

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

# ── Phase 2: Chatbot orchestration ───────────────────────────────────────────
from chatbot import chat as chatbot_chat

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

# ── Rate Limiter ───────────────────────────────────────────────────────────────
_redis_url = os.getenv("REDIS_URL", "memory://")

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri=_redis_url,
    default_limits=[],
    strategy="fixed-window",
    headers_enabled=True,
)

# ── Request ID Middleware ──────────────────────────────────────────────────────
@app.before_request
def assign_request_id():
    g.request_id = uuid.uuid4().hex[:8]
    g.start_time = time.time()

# ── Security Headers ───────────────────────────────────────────────────────────
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

# ── Request Logging ────────────────────────────────────────────────────────────
@app.after_request
def log_request(response):
    if hasattr(g, "start_time"):
        duration_ms = round((time.time() - g.start_time) * 1000, 1)
        logger.info(
            "%s %s [%s] %sms ip=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            request.remote_addr,
        )
    return response

# ── Rate limit error handler ───────────────────────────────────────────────────
@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning("Rate limit hit: ip=%s", request.remote_addr)
    return jsonify({
        "error": "Terlalu banyak permintaan. Silakan tunggu sebentar.",
        "code": "RATE_LIMITED",
    }), 429


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    return render_template("index.html")


# ── /api/ask  (Phase 1 — backward compatible, respons kaya) ──────────────────
@app.route("/api/ask", methods=["POST"])
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE} per minute")
def ask_question():
    """
    Endpoint Phase 1. Tetap dipertahankan untuk backward compatibility.
    Mengembalikan respons lengkap (ruling, madhab, quran refs, hadis refs).
    Gunakan /chat untuk integrasi chatbot UI yang lebih sederhana.
    """
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

    topic             = parse_user_query(question)
    retrieval_result  = retrieve_ruling(topic) if topic else None
    can_answer, evidence_report, block_reason = gate_answer(retrieval_result)

    if not can_answer:
        return jsonify({
            "found":      False,
            "answer":     block_reason,
            "confidence": "insufficient",
            "topic":      topic,
            "code":       "NO_RELIABLE_EVIDENCE",
        })

    answer_text = format_answer(retrieval_result)

    return jsonify({
        "found":            True,
        "answer":           answer_text,
        "topic":            topic,
        "ruling":           retrieval_result["ruling"],
        "madhab":           retrieval_result["madhab"],
        "reasoning":        retrieval_result.get("reasoning", ""),
        "confidence":       evidence_report.confidence_label,
        "confidence_score": evidence_report.confidence_score,
        "quran":            retrieval_result.get("quran", []),
        "hadis":            retrieval_result.get("hadis", []),
        "evidence_summary": {
            "quran_count": evidence_report.quran_count,
            "hadis_count": evidence_report.hadis_count,
        },
        "warnings":    evidence_report.warnings,
        "disclaimer":  evidence_report.disclaimer,
        "request_id":  g.request_id,
    })


# ── /chat  (Phase 2 — chatbot.py, respons terstruktur) ───────────────────────
@app.route("/chat", methods=["POST"])
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE} per minute")
def chat_endpoint():
    """
    Endpoint Phase 2. Menggunakan chatbot.py sebagai orchestration layer.

    Menerima:
        { "question": "..." }   atau   { "message": "..." }

    Mengembalikan ChatResponse / ChatRejection dict dengan field:
        status, answer/reason, topic, confidence_score,
        confidence_label, warnings, disclaimer, timestamp, request_id

    HTTP Status:
        200  — selalu (status chatbot ada di body: ok/no_match/rejected)
        400  — body bukan JSON
        422  — validasi input gagal
        429  — rate limited
        500  — error tidak terduga di luar pipeline chatbot
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body harus berupa JSON.", "code": "BAD_REQUEST"}), 400

    # Terima "question" atau "message" untuk fleksibilitas integrasi frontend
    raw_question = data.get("question", data.get("message", ""))

    try:
        question = validate_question(raw_question)
    except InputValidationError as e:
        logger.info("Chat validation failed: ip=%s error='%s'", request.remote_addr, e)
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422

    logger.info("Chat: ip=%s question='%s'", request.remote_addr, question[:60])

    # Seluruh pipeline (parse → retrieve → gate → format) ada di chatbot_chat()
    result = chatbot_chat(question)

    # Inject request_id untuk client-side tracing
    result["request_id"] = g.request_id

    # Error dalam pipeline dikembalikan sebagai 200 dengan status="error" di body,
    # kecuali jika chatbot_chat() sendiri raise (seharusnya tidak terjadi).
    return jsonify(result)


# ── /api/health  (Phase 1 — cloud uptime monitoring) ─────────────────────────
@app.route("/api/health")
def health():
    """Cloud health check endpoint. Tidak di-rate-limit."""
    from islamic_data import quran_verses, hadis_collection, shafii_rules
    return jsonify({
        "status": "ok",
        "data": {
            "quran_verses": len(quran_verses),
            "hadis":        len(hadis_collection),
            "rules":        len(shafii_rules),
        },
        "sentry":               _sentry_enabled,
        "rate_limiter_backend": "redis" if "redis" in _redis_url else "memory",
    })


# ── /status  (Phase 2 — chatbot pipeline status) ─────────────────────────────
@app.route("/status")
def status():
    """
    Debug endpoint Phase 2: verifikasi semua komponen pipeline siap.
    Berguna saat deployment untuk konfirmasi sistem berjalan end-to-end.
    Tidak di-rate-limit — akses internal/monitoring saja.
    """
    components = {}

    # Cek islamic_data
    try:
        from islamic_data import quran_verses, hadis_collection, shafii_rules
        components["islamic_data"] = {
            "status": "ready",
            "quran_verses": len(quran_verses),
            "hadis": len(hadis_collection),
            "rules": len(shafii_rules),
        }
    except Exception as e:
        components["islamic_data"] = {"status": "error", "detail": str(e)}

    # Cek query_parser
    try:
        from query_parser import parse_user_query
        test_result = parse_user_query("syahadat")
        components["query_parser"] = {
            "status": "ready",
            "test_parse": test_result or "no_match",
        }
    except Exception as e:
        components["query_parser"] = {"status": "error", "detail": str(e)}

    # Cek retrieval
    try:
        from retrieval import retrieve_ruling
        components["retrieval"] = {"status": "ready"}
    except Exception as e:
        components["retrieval"] = {"status": "error", "detail": str(e)}

    # Cek reasoning_validator
    try:
        from reasoning_validator import gate_answer
        components["reasoning_validator"] = {"status": "ready"}
    except Exception as e:
        components["reasoning_validator"] = {"status": "error", "detail": str(e)}

    # Cek formatter
    try:
        from formatter import format_answer
        components["response_formatter"] = {"status": "ready"}
    except Exception as e:
        components["response_formatter"] = {"status": "error", "detail": str(e)}

    # Cek chatbot
    try:
        from chatbot import chat
        components["chatbot"] = {"status": "ready"}
    except Exception as e:
        components["chatbot"] = {"status": "error", "detail": str(e)}

    # Overall status
    all_ready = all(c.get("status") == "ready" for c in components.values())
    overall   = "healthy" if all_ready else "degraded"

    return jsonify({
        "chatbot_status": overall,
        **{k: v["status"] for k, v in components.items()},
        "components": components,
        "request_id": g.request_id,
    }), 200 if all_ready else 503


# ── Error handlers ────────────────────────────────────────────────────────────
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
