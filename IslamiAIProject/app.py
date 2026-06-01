# app.py
# IslamiAI — Production Flask App (Phase 1)
# Security hardening: flask-limiter + Redis, request ID tracing, Sentry.

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
# Aktif hanya jika SENTRY_DSN diset di environment.
# Tidak perlu install sentry-sdk jika belum diperlukan — gagal gracefully.
_sentry_enabled = False
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FlaskIntegration()],
            # Jangan kirim data request body ke Sentry (privacy)
            send_default_pii=False,
            # Sample 100% errors, 10% performance traces
            traces_sample_rate=0.10,
        )
        _sentry_enabled = True
    except ImportError:
        pass  # sentry-sdk belum diinstall — tidak crash

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    # Format diperluas dengan request_id untuk tracing
    format="%(asctime)s [%(levelname)s] %(name)s [%(request_id)s]: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ]
)

class RequestIdFilter(logging.Filter):
    """Inject request_id ke setiap log record dalam konteks request."""
    def filter(self, record):
        # g tidak tersedia di luar request context (startup logs)
        try:
            from flask import g as flask_g
            record.request_id = getattr(flask_g, "request_id", "-")
        except RuntimeError:
            record.request_id = "-"
        return True

_request_id_filter = RequestIdFilter()
logging.getLogger().addFilter(_request_id_filter)

# ── TAMBAHKAN INI ───────────────────────────────────────────
# Filter pada logger hanya berlaku untuk record dari logger itu sendiri.
# Werkzeug/Flask propagate ke root handlers langsung, bypass filter logger.
# Solusi: pasang filter juga ke setiap handler.
for _handler in logging.getLogger().handlers:
    _handler.addFilter(_request_id_filter)
# ────────────────────────────────────────────────────────────

logger = logging.getLogger("islamiai")

# ── Flask App ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["SESSION_COOKIE_SECURE"]  = config.SESSION_COOKIE_SECURE
app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE

# ── Rate Limiter (flask-limiter + Redis) ───────────────────────────────────────
# storage_uri:
#   - Jika REDIS_URL diset (production/staging): gunakan Redis → persist restart,
#     akurat di multi-worker Gunicorn.
#   - Fallback "memory://" jika tidak diset (dev lokal): sama seperti Phase 0.
#
# Key function: IP address dari request.
# Default limit: 30 req/menit (sesuai config.RATE_LIMIT_PER_MINUTE).
# Burst allowance (RATE_LIMIT_BURST) diimplementasi via dua limit tier.

_redis_url = os.getenv("REDIS_URL", "memory://")

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri=_redis_url,
    default_limits=[],          # Tidak ada default global — dikontrol per-route
    strategy="fixed-window",    # Konsisten, predictable, cocok untuk API publik
    headers_enabled=True,       # Kirim X-RateLimit-* headers ke client
)

# ── Request ID Middleware ──────────────────────────────────────────────────────
@app.before_request
def assign_request_id():
    """
    Generate UUID unik per request dan simpan di g.request_id.
    Dipakai untuk: log tracing, Sentry breadcrumbs, X-Request-ID header.
    Format: 8 karakter hex pendek (cukup untuk tracing dalam satu session).
    """
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
    # Propagate request ID ke response header untuk client-side debugging
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

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/ask", methods=["POST"])
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE} per minute")
def ask_question():
    # Parse request body
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body harus berupa JSON.", "code": "BAD_REQUEST"}), 400

    raw_question = data.get("question", "")

    # Input validation
    try:
        question = validate_question(raw_question)
    except InputValidationError as e:
        logger.info("Validation failed: ip=%s error='%s'", request.remote_addr, e)
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422

    logger.info("Query: ip=%s question='%s'", request.remote_addr, question[:60])

    # Pipeline: parse → retrieve → gate → format
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
        "request_id":  g.request_id,   # memudahkan tracing di client
    })


@app.route("/api/health")
def health():
    """Cloud health check + uptime monitoring endpoint."""
    from islamic_data import quran_verses, hadis_collection, shafii_rules
    return jsonify({
        "status": "ok",
        "data": {
            "quran_verses": len(quran_verses),
            "hadis":        len(hadis_collection),
            "rules":        len(shafii_rules),
        },
        "sentry": _sentry_enabled,
        "rate_limiter_backend": "redis" if "redis" in _redis_url else "memory",
    })


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
