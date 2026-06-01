# IslamiAI — Staging Deployment Guide (Phase 1)
# Target: Railway (primary) atau Render (alternatif)
# Kedua platform: free tier, HTTPS otomatis, zero-downtime deploy

---

## Opsi A: Railway (Recommended)

### Kenapa Railway?
- Deploy dari GitHub push (CI/CD otomatis)
- Redis add-on tersedia langsung di dashboard
- Healthcheck endpoint `/api/health` didukung native
- Free tier: 500 jam/bulan + $5 credit

### Langkah Deploy

1. **Push ke GitHub**
   ```bash
   cd ~/IslamiAIProject
   git init  # jika belum
   git add .
   git commit -m "Phase 1: frontend + dalil rendering"
   git remote add origin https://github.com/USERNAME/islamiai.git
   git push -u origin main
   ```

2. **Buat project di Railway**
   - Buka https://railway.app → New Project → Deploy from GitHub Repo
   - Pilih repo `islamiai`
   - Railway akan deteksi `Dockerfile` otomatis

3. **Tambah Redis**
   - Di dashboard project → Add Plugin → Redis
   - Railway akan inject `REDIS_URL` sebagai env var otomatis

4. **Set environment variables** (Settings → Variables)
   ```
   ISLAMIAI_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
   ISLAMIAI_DEBUG=false
   ISLAMIAI_HOST=0.0.0.0
   ISLAMIAI_PORT=8080
   RATE_LIMIT_PER_MIN=30
   LOG_LEVEL=INFO
   ```

5. **Healthcheck config** (Settings → Deploy)
   ```
   Healthcheck Path: /api/health
   Healthcheck Timeout: 10s
   ```

6. **Verify deploy**
   ```bash
   curl https://islamiai-production.up.railway.app/api/health
   # Expected: {"status":"ok","data":{"quran_verses":23,"hadis":14,"rules":29}}
   ```

---

## Opsi B: Render

### Langkah Deploy

1. **Buka** https://render.com → New → Web Service → Connect GitHub

2. **Config**:
   | Field         | Value              |
   |---------------|--------------------|
   | Name          | islamiai-staging   |
   | Environment   | Docker             |
   | Branch        | main               |
   | Health Check  | /api/health        |

3. **Tambah Redis**:
   - New → Redis → pilih Free tier
   - Copy Internal URL → set sebagai `REDIS_URL` di web service env vars

4. **Environment Variables** (sama seperti Railway di atas)

5. **Deploy** → klik "Create Web Service"

---

## Redis Rate Limiter — Konfigurasi app.py (Phase 1 Next Step)

Setelah Redis tersedia, ganti in-memory limiter di `app.py` dengan:

```python
# app.py — tambahkan di atas setelah imports
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "memory://"),
    default_limits=["30 per minute"],
)

# Hapus fungsi is_rate_limited() dan blok manual di /api/ask
# Ganti dengan decorator:
@app.route("/api/ask", methods=["POST"])
@limiter.limit("30 per minute")
def ask_question():
    ...
```

Keunggulan flask-limiter + Redis vs in-memory:
- Persist saat restart container
- Shared across multiple workers (Gunicorn --workers 2)
- Sliding window algorithm lebih akurat
- Rate limit headers otomatis (X-RateLimit-Remaining, dll.)

---

## Checklist Pre-Deploy

- [ ] `ISLAMIAI_SECRET_KEY` bukan default value
- [ ] `ISLAMIAI_DEBUG=false`
- [ ] `Dockerfile` entry point: `app:app` (bukan `app_v2:app`)
- [ ] `GET /api/health` mengembalikan 200 dari public URL
- [ ] `POST /api/ask` dengan `{"question":"syahadat"}` mengembalikan `found: true`
- [ ] Arabic text terrender benar di browser (font Scheherazade New loaded)
- [ ] RTL direction benar pada blok Arabic (text align kanan)
- [ ] Rate limit 429 tertest: kirim 31 request dalam 1 menit

---

## Troubleshooting

**Container tidak start:**
```bash
# Cek log di Railway/Render dashboard
# Penyebab umum: SECRET_KEY tidak diset, port tidak match
```

**Font Arabic tidak load:**
- Pastikan CSP di app.py include `fonts.googleapis.com` dan `fonts.gstatic.com`
- Sudah dikonfigurasi di `add_security_headers()` ✅

**Redis connection error:**
- Jika `REDIS_URL` tidak diset, flask-limiter fallback ke `memory://`
- Ini acceptable untuk staging; mandatory untuk production
