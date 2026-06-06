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


# ══════════════════════════════════════════════════════════════════════════════
# TOPIC METADATA — sumber kebenaran untuk sidebar frontend
# Semua key harus sesuai persis dengan key di shafii_rules (islamic_data.py)
# ══════════════════════════════════════════════════════════════════════════════

_TOPIC_META = {
    # ── AQIDAH ────────────────────────────────────────────────────────────────
    'syahadat':                         ('☪️',  'Syahadat & Masuk Islam',               'apa itu syahadat dan bagaimana cara masuk islam'),
    # ── THAHARAH ──────────────────────────────────────────────────────────────
    'thaharah_wudhu':                   ('💧',  'Cara Wudhu yang Benar',                'bagaimana cara wudhu yang benar menurut syafii'),
    'thaharah_mandi_wajib':             ('🚿',  'Mandi Wajib (Ghusl)',                  'bagaimana cara mandi wajib junub yang benar'),
    'thaharah_tayammum':                ('🏜️',  'Tayammum',                             'kapan boleh tayammum dan bagaimana caranya'),
    'najis_ringkan':                    ('🧹',  'Najis Ringan (Mukhaffafah)',            'apa itu najis ringan dan cara menyucikannya'),
    'najis_sedang':                     ('🧼',  'Najis Sedang (Mutawassithah)',          'apa itu najis sedang dan cara menyucikannya'),
    'najis_berat':                      ('⚠️',  'Najis Berat — Anjing & Babi',          'bagaimana cara menyucikan najis anjing menurut syafii'),
    # ── SHALAT ────────────────────────────────────────────────────────────────
    'shalat_lima_waktu':                ('🕌',  'Shalat Lima Waktu',                    'hukum dan tata cara shalat lima waktu'),
    'shalat_jama_qashar_safar':         ('✈️',  'Shalat Jama & Qashar (Safar)',         'bolehkah shalat jama dan qashar saat bepergian'),
    'shalat_jumat_kewajiban':           ('📢',  'Kewajiban Shalat Jumat',               'siapa saja yang wajib shalat jumat'),
    'shalat_sunnah_rawatib':            ('⭐',  'Shalat Sunnah Rawatib',                'apa saja shalat sunnah rawatib dan keutamaannya'),
    # ── PUASA ─────────────────────────────────────────────────────────────────
    'puasa_ramadhan':                   ('🌙',  'Puasa Ramadhan',                       'hukum puasa ramadhan dan syaratnya'),
    'puasa_muallaf_tengah_ramadhan':    ('🆕',  'Puasa Muallaf Tengah Ramadhan',        'saya baru masuk islam di tengah ramadhan apakah wajib puasa'),
    'puasa_qadha':                      ('📅',  'Qadha (Ganti) Puasa',                  'bagaimana cara qadha puasa yang terlewat'),
    'puasa_fidyah':                     ('🌾',  'Fidyah Puasa',                         'siapa yang boleh membayar fidyah dan berapa banyaknya'),
    'puasa_digital_konteks_ibadah':     ('📴',  'Puasa Digital',                        'apakah puasa dari media sosial bernilai ibadah'),
    # ── ZAKAT ─────────────────────────────────────────────────────────────────
    'zakat_fitrah':                     ('🎁',  'Zakat Fitrah',                         'hukum dan cara menunaikan zakat fitrah'),
    'zakat_harta':                      ('💰',  'Zakat Harta (Maal)',                   'bagaimana cara menghitung zakat harta'),
    'zakat_muallaf':                    ('🤝',  'Zakat untuk Muallaf',                  'apakah muallaf berhak menerima zakat'),
    'zakat_nishab_emas_perak':          ('🥇',  'Nishab Emas & Perak',                  'berapa nishab zakat emas dan perak'),
    'zakat_profesi_kontemporer':        ('💼',  'Zakat Profesi & Gaji',                 'bagaimana hukum dan cara menghitung zakat gaji'),
    'zakat_delapan_asnaf':              ('👥',  '8 Asnaf Penerima Zakat',               'siapa saja 8 golongan yang berhak menerima zakat'),
    # ── HAJI & UMRAH ──────────────────────────────────────────────────────────
    'haji_syarat_wajib':                ('🕋',  'Syarat Wajib Haji',                    'apa saja syarat wajib haji dalam islam'),
    'haji_rukun':                       ('🏃',  'Rukun Haji',                           'apa saja rukun haji yang wajib dipenuhi'),
    'haji_wajib':                       ('✅',  'Wajib Haji',                           'apa perbedaan rukun haji dan wajib haji'),
    'umrah_hukum':                      ('🕋',  'Hukum Umrah',                          'apakah umrah hukumnya wajib atau sunnah'),
    # ── NIKAH & KELUARGA ──────────────────────────────────────────────────────
    'nikah_syarat_rukun':               ('💒',  'Syarat & Rukun Nikah',                 'syarat dan rukun nikah menurut mazhab syafii'),
    'nikah_mahar':                      ('💍',  'Mahar (Mas Kawin)',                    'apa itu mahar dan berapa batas minimalnya'),
    'pernikahan_suami_islam_istri_kafir':('👫', 'Suami Islam, Istri Non-Muslim',         'bolehkah laki-laki muslim menikahi wanita non muslim'),
    'pernikahan_istri_islam_suami_kafir':('👫', 'Istri Islam, Suami Non-Muslim',         'bagaimana hukum wanita muslimah menikah dengan pria kafir'),
    'pernikahan_keduanya_islam':        ('👫',  'Keduanya Masuk Islam Bersama',          'jika suami dan istri masuk islam bersama apakah perlu akad ulang'),
    'talak_jenis':                      ('📄',  'Jenis-Jenis Talak',                    'apa saja jenis talak dalam islam dan perbedaannya'),
    'khuluk':                           ('⚖️',  'Khuluk (Gugat Cerai Istri)',            'apa itu khuluk dan bagaimana prosesnya'),
    # ── WARIS & JENAZAH ───────────────────────────────────────────────────────
    'waris_perbedaan_agama':            ('📜',  'Waris Beda Agama',                     'apakah muslim bisa mewarisi dari keluarga non muslim'),
    'waris_muallaf_keluarga_non_muslim':('📜',  'Waris Muallaf',                        'bagaimana hak waris muallaf dari keluarga non muslim'),
    'waris_hijab':                      ('📜',  'Hijab (Penghalang) Waris',             'apa yang dimaksud hijab dalam hukum waris islam'),
    'jenazah_ghusl':                    ('🕯️',  'Memandikan Jenazah',                   'bagaimana cara memandikan jenazah muslim'),
    'jenazah_takfin':                   ('🕯️',  'Mengkafani Jenazah',                   'bagaimana cara mengkafani jenazah yang benar'),
    'jenazah_shalat':                   ('🕯️',  'Shalat Jenazah',                       'bagaimana tata cara shalat jenazah'),
    'jenazah_dafan':                    ('⚰️',  'Menguburkan Jenazah',                  'bagaimana cara menguburkan jenazah yang sesuai syariat'),
    'jenazah_keluarga_non_muslim':      ('🕯️',  'Jenazah Keluarga Non-Muslim',          'bolehkah muslim mengurus jenazah keluarga non muslim'),
    # ── MUAMALAH & KEUANGAN ───────────────────────────────────────────────────
    'jual_beli_syarat':                 ('🛒',  'Syarat Jual Beli yang Sah',            'apa syarat jual beli yang sah dalam islam'),
    'riba_jenis':                       ('🏦',  'Jenis-Jenis Riba',                     'apa saja jenis riba yang diharamkan dalam islam'),
    'bank_konvensional_hukum':          ('🏦',  'Hukum Bank Konvensional',              'hukum bunga bank konvensional dalam islam'),
    'hutang_piutang':                   ('💸',  'Hutang Piutang (Qardh)',               'apa hukum dan adab hutang piutang dalam islam'),
    'asuransi_konvensional':            ('📋',  'Hukum Asuransi Konvensional',          'apakah asuransi konvensional haram dalam islam'),
    'pinjol_fintech':                   ('📲',  'Pinjol & Fintech Lending',             'bagaimana hukum pinjaman online berbunga'),
    'kripto_investasi':                 ('💎',  'Hukum Kripto & Investasi',             'apakah investasi kripto seperti bitcoin halal'),
    # ── AKHLAK & SOSIAL ───────────────────────────────────────────────────────
    'keluarga_non_muslim_hubungan':     ('👨‍👩‍👧', 'Hubungan dengan Keluarga Non-Muslim', 'bagaimana hukum berbuat baik kepada keluarga non muslim'),
    'aurat_laki_laki':                  ('👔',  'Aurat Laki-Laki',                      'apa batas aurat laki-laki menurut syafii'),
    'aurat_perempuan_shalat':           ('🧕',  'Aurat Perempuan dalam Shalat',         'apa batas aurat perempuan saat shalat'),
    'aurat_perempuan_di_luar_shalat':   ('🧕',  'Aurat Perempuan di Luar Shalat',       'apa batas aurat perempuan di hadapan pria ajnabi'),
    'medsos_ghibah_online':             ('📱',  'Ghibah di Media Sosial',               'hukum ghibah dan gosip di media sosial'),
    'medsos_hoaks_tabayyun':            ('📰',  'Hoaks & Tabayyun',                     'hukum menyebarkan berita tanpa tabayyun'),
    'musik_hukum':                      ('🎵',  'Hukum Musik & Lagu',                   'bagaimana hukum mendengarkan musik dalam islam'),
    'gambar_foto_video':                ('📷',  'Hukum Foto & Video Makhluk Hidup',     'apakah foto dan video makhluk hidup haram'),
    'kerja_perusahaan_non_halal':       ('💼',  'Kerja di Perusahaan Non-Halal',        'bagaimana hukum bekerja di bank atau pabrik rokok'),
    'pacaran_sebelum_nikah':            ('❤️',  'Hukum Pacaran',                        'hukum pacaran dan khalwat dalam islam'),
    'operasi_plastik_kecantikan':       ('💉',  'Operasi Plastik & Kecantikan',         'bagaimana hukum operasi plastik dalam islam'),
    'lingkungan_hidup_islami':          ('🌿',  'Lingkungan Hidup dalam Islam',         'apa pandangan islam tentang menjaga lingkungan'),
    'kesehatan_mental_islam':           ('🧠',  'Kesehatan Mental dalam Islam',         'bagaimana islam memandang depresi dan kesehatan mental'),
    # ── MAKANAN & MINUMAN ─────────────────────────────────────────────────────
    'makanan_haram_umum':               ('🍖',  'Makanan Haram',                        'makanan apa saja yang haram dalam islam'),
    'makanan_haram_minuman':            ('🚫',  'Minuman Haram (Khamar)',               'apa saja minuman yang diharamkan dalam islam'),
    'makanan_halal_penyembelihan':      ('🥩',  'Cara Penyembelihan Halal',             'bagaimana syarat penyembelihan hewan yang halal'),
}

_TOPIC_CATEGORIES = [
    ('aqidah',       '☪️ Aqidah & Masuk Islam',    ['syahadat']),
    ('thaharah',     '💧 Thaharah & Bersuci',       ['thaharah_wudhu','thaharah_mandi_wajib','thaharah_tayammum','najis_ringkan','najis_sedang','najis_berat']),
    ('shalat',       '🕌 Shalat',                   ['shalat_lima_waktu','shalat_jama_qashar_safar','shalat_jumat_kewajiban','shalat_sunnah_rawatib']),
    ('puasa',        '🌙 Puasa',                    ['puasa_ramadhan','puasa_muallaf_tengah_ramadhan','puasa_qadha','puasa_fidyah','puasa_digital_konteks_ibadah']),
    ('zakat',        '💰 Zakat',                    ['zakat_fitrah','zakat_harta','zakat_muallaf','zakat_nishab_emas_perak','zakat_profesi_kontemporer','zakat_delapan_asnaf']),
    ('haji',         '🕋 Haji & Umrah',             ['haji_syarat_wajib','haji_rukun','haji_wajib','umrah_hukum']),
    ('nikah',        '💒 Nikah & Keluarga',         ['nikah_syarat_rukun','nikah_mahar','pernikahan_suami_islam_istri_kafir','pernikahan_istri_islam_suami_kafir','pernikahan_keduanya_islam','talak_jenis','khuluk']),
    ('waris',        '📜 Waris & Jenazah',          ['waris_perbedaan_agama','waris_muallaf_keluarga_non_muslim','waris_hijab','jenazah_ghusl','jenazah_takfin','jenazah_shalat','jenazah_dafan','jenazah_keluarga_non_muslim']),
    ('muamalah',     '🏦 Muamalah & Keuangan',     ['jual_beli_syarat','riba_jenis','bank_konvensional_hukum','hutang_piutang','asuransi_konvensional','pinjol_fintech','kripto_investasi']),
    ('akhlak',       '🤲 Akhlak & Sosial',          ['keluarga_non_muslim_hubungan','aurat_laki_laki','aurat_perempuan_shalat','aurat_perempuan_di_luar_shalat','medsos_ghibah_online','medsos_hoaks_tabayyun','musik_hukum','gambar_foto_video','kerja_perusahaan_non_halal','pacaran_sebelum_nikah','operasi_plastik_kecantikan','lingkungan_hidup_islami','kesehatan_mental_islam']),
    ('makanan',      '🍖 Makanan & Minuman',        ['makanan_haram_umum','makanan_haram_minuman','makanan_halal_penyembelihan']),
]


# ── /api/topics ───────────────────────────────────────────────────────────────
@app.route("/api/topics")
def get_topics():
    """
    Kembalikan semua topik dari shafii_rules, dikelompokkan per kategori.
    Hanya topik yang ada di database (shafii_rules) yang dikembalikan.
    Frontend menggunakan endpoint ini untuk membangun sidebar dinamis.
    """
    from islamic_data import shafii_rules

    categories = []
    for cat_id, cat_label, keys in _TOPIC_CATEGORIES:
        topics = []
        for key in keys:
            if key in shafii_rules and key in _TOPIC_META:
                icon, label, query = _TOPIC_META[key]
                topics.append({"key": key, "icon": icon, "label": label, "query": query})
        if topics:
            categories.append({"id": cat_id, "label": cat_label, "topics": topics})

    return jsonify({"categories": categories, "total": sum(len(c["topics"]) for c in categories)})
