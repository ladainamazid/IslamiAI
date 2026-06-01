# Mini Server Pro - Production Ready Server

Server mini profesional dengan keamanan menengah-ke-atas, modular, dan siap production.

## ✨ Fitur

- 🔐 **API Key + Token Authentication**
- 🔒 **Rate Limiting** (50 req/menit/IP)
- 💾 **SQLite Database** dengan SQLAlchemy ORM
- 🔐 **HTTPS** dengan self-signed certificate
- 🧪 **Unit Tests** dengan unittest
- 📝 **Validation** input otomatis
- 🔄 **Systemd Service** untuk auto-start
- 📊 **System Monitor** (CPU, Memory)

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env  # Edit API_KEY

# Inisialisasi database
python3 migrations/init_db.py

# Jalankan server
python3 run.py
```

## 📌 Endpoints

| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/health` | Pubik |
| POST | `/auth/get-token` | API Key |
| GET | `/api/data` | API Key + Token |
| GET | `/api/users` | API Key + Token |

## 🧪 Testing

```bash
python3 -m pytest tests/
```

## 📄 License

MIT License - Mini Server Pro v2.0.0
