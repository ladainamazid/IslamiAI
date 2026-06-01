from flask import Flask, request, jsonify
from functools import wraps
import secrets
from datetime import datetime, timedelta
import sys
import os

# === KONFIGURASI ISLAMI AI PROJECT ===
AI_PROJECT_NAME = "IslamiAIProject"
AI_PROJECT_PATH = os.path.expanduser("~/IslamiAIProject")

# Tambahkan path IslamiAIProject ke sys.path
if os.path.exists(AI_PROJECT_PATH):
    sys.path.insert(0, AI_PROJECT_PATH)

app = Flask(__name__)

# === KONFIGURASI KEAMANAN ===
API_KEY = "mUhAmmAdtAUfIqUrrOhmAn1928"
VALID_DURATION_HOURS = 24
valid_tokens = {}

# === MIDDLEWARE: Autentikasi API Key ===
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != API_KEY:
            return jsonify({"error": "Akses ditolak. API Key tidak valid."}), 401
        return f(*args, **kwargs)
    return decorated

# === MIDDLEWARE: Rate Limiting ===
request_log = {}
def rate_limit(max_requests=100, window_seconds=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr
            now = datetime.now()
            if client_ip not in request_log:
                request_log[client_ip] = []
            request_log[client_ip] = [
                t for t in request_log[client_ip]
                if (now - t).total_seconds() < window_seconds
            ]
            if len(request_log[client_ip]) >= max_requests:
                return jsonify({"error": "Terlalu banyak permintaan."}), 429
            request_log[client_ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

# === ENDPOINT: Home (Publik) ===
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": f"{AI_PROJECT_NAME} Server v1.0.0",
        "ai_project": AI_PROJECT_NAME,
        "ai_path": AI_PROJECT_PATH,
        "endpoints": {
            "GET /": "Public (Home)",
            "GET /health": "Public",
            "POST /auth/get-token": "Perlu API Key",
            "GET /api/data": "Perlu API Key + Token",
            "POST /api/chat": "Perlu API Key + Token (IslamiAI Chatbot)"
        },
        "ai_function": "chatbot.chat(question: str) -> dict"
    }), 200

# === ENDPOINT: Health Check (Publik) ===
@app.route("/health", methods=["GET"])
def health_check():
    ai_exists = os.path.exists(AI_PROJECT_PATH)
    chatbot_exists = os.path.exists(os.path.join(AI_PROJECT_PATH, "chatbot.py"))
    return jsonify({
        "status": "healthy" if (ai_exists and chatbot_exists) else "warning",
        "timestamp": datetime.now().isoformat(),
        "server": f"{AI_PROJECT_NAME} Server v1.0.0",
        "ai_project": AI_PROJECT_NAME,
        "ai_path": AI_PROJECT_PATH,
        "ai_found": ai_exists,
        "chatbot_found": chatbot_exists
    }), 200

# === ENDPOINT: Dapatkan Token ===
@app.route("/auth/get-token", methods=["POST"])
@require_api_key
def get_token():
    data = request.get_json() or {}
    username = data.get("username")
    if not username:
        return jsonify({"error": "Username diperlukan."}), 400
    
    token = secrets.token_urlsafe(32)
    expiry = datetime.now() + timedelta(hours=VALID_DURATION_HOURS)
    valid_tokens[token] = {"username": username, "expiry": expiry}
    
    return jsonify({
        "token": token,
        "expires_in_hours": VALID_DURATION_HOURS,
        "message": f"Token berhasil dibuat untuk {AI_PROJECT_NAME}."
    }), 200

# === ENDPOINT: Data (Perlu Token) ===
@app.route("/api/data", methods=["GET"])
@require_api_key
@rate_limit(max_requests=50, window_seconds=60)
def get_data():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token not in valid_tokens:
        return jsonify({"error": "Token tidak valid."}), 401
    
    token_data = valid_tokens[token]
    if datetime.now() > token_data["expiry"]:
        del valid_tokens[token]
        return jsonify({"error": "Token kadaluarsa."}), 401
    
    return jsonify({
        "message": f"Halo, {token_data['username']}!",
        "data": {
            "server": AI_PROJECT_NAME,
            "versi": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    }), 200

# === ENDPOINT: IslamiAI Chatbot (Perlu Token) ===
@app.route("/api/chat", methods=["POST"])
@require_api_key
@rate_limit(max_requests=30, window_seconds=60)
def chat():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token not in valid_tokens:
        return jsonify({"error": "Token tidak valid."}), 401
    
    token_data = valid_tokens[token]
    if datetime.now() > token_data["expiry"]:
        del valid_tokens[token]
        return jsonify({"error": "Token kadaluarsa."}), 401
    
    data = request.get_json() or {}
    user_question = data.get("question") or data.get("message")
    
    if not user_question:
        return jsonify({"error": "Pertanyaan diperlukan."}), 400
    
    try:
        # === INTEGRASI LANGSUNG DENGAN ISLAMI AI PROJECT ===
        # Import dan panggil chatbot.chat() dari IslamiAIProject
        import chatbot
        
        # Panggil function chat(question: str) -> dict
        result = chatbot.chat(user_question)
        
        # Return response dari IslamiAIProject
        return jsonify({
            "answer": result.get("answer", str(result)),
            "question": user_question,
            "user": token_data['username'],
            "timestamp": datetime.now().isoformat(),
            "ai_project": AI_PROJECT_NAME,
            "confidence": result.get("confidence", None),
            "is_answerable": result.get("is_answerable", None),
            "sources": result.get("sources", [])
        }), 200
        
    except ImportError as e:
        return jsonify({
            "error": f"Error importing IslamiAIProject: {str(e)}",
            "answer": f"Error: tidak dapat mengimport chatbot dari {AI_PROJECT_NAME}"
        }), 500
        
    except Exception as e:
        return jsonify({
            "error": f"Error executing chatbot: {str(e)}",
            "answer": f"Error: terjadi kesalahan saat memproses pertanyaan Anda"
        }), 500

# === JALANKAN SERVER ===
if __name__ == "__main__":
    ai_exists = os.path.exists(AI_PROJECT_PATH)
    chatbot_exists = os.path.exists(os.path.join(AI_PROJECT_PATH, "chatbot.py"))
    ai_status = "✅ Found" if (ai_exists and chatbot_exists) else "❌ Not Found"
    
    print("="*70)
    print(f"🚀 {AI_PROJECT_NAME} SERVER (Linux Mint)")
    print(f"🔑 API_KEY Anda: {API_KEY}")
    print(f"📁 {AI_PROJECT_NAME} Path: {AI_PROJECT_PATH} [{ai_status}]")
    print("💡 Simpan API_KEY ini dengan aman!")
    print("\n📌 Endpoint:")
    print("   GET  /                    → Public (Home)")
    print("   GET  /health              → Public")
    print("   POST /auth/get-token      → Perlu API Key")
    print("   GET  /api/data            → Perlu API Key + Token")
    print("   POST /api/chat            → Perlu API Key + Token (IslamiAI Chatbot)")
    print("\n🔗 Integrasi: chatbot.chat(question: str) -> dict")
    print("\n🔒 Keamanan: API Key + Token + Rate Limiting")
    print("="*70)
    
    app.run(host="127.0.0.1", port=8291, debug=False, threaded=True)
