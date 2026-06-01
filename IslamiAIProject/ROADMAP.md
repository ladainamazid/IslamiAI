# IslamiAI — Project Roadmap & Mentoring Tracker

## Status: Phase 0 — Foundation (CURRENT)

---

## PHASE 0 — Foundation (Selesai)

### Files yang delivered
| File | Status | Keterangan |
|------|--------|------------|
| `islamic_data_complete.py` | ✅ Done | 23 ayat + 14 hadis, 0 placeholder, integrity check built-in |
| `validators.py` | ✅ Done | Input sanitization, XSS/SQLi blocking |
| `config.py` | ✅ Done | 12-factor app, env-based config |
| `reasoning_validator.py` | ✅ Done | Evidence chain, confidence scoring |
| `app_v2.py` | ✅ Done | Rate limiting, security headers, structured JSON |
| `retrieval.py` | ✅ Existing | Compatible, tidak perlu ganti |
| `query_parser.py` | ✅ Existing | Compatible, tidak perlu ganti |
| `formatter.py` | ✅ Existing | Compatible, tidak perlu ganti |
| `requirements.txt` | ✅ Done | — |
| `Dockerfile` | ✅ Done | Non-root, gunicorn |
| `.env.example` | ✅ Done | Template env vars |

### Apa yang BELUM ada (sengaja ditunda ke Phase 1)
- [ ] `templates/index_v2.html` — Arabic font (Google Noto Nastaliq Urdu / Scheherazade)
- [ ] Redis-backed rate limiter (saat ini in-memory, tidak persist restart)
- [ ] Persistent logging ke file rotasi
- [ ] Unit test suite

---

## PHASE 1 — Staging & Hardening (Target: Minggu 1)

### Deployment
- [ ] Deploy ke Railway / Render / Fly.io (free tier staging)
- [ ] Setup HTTPS (otomatis di platform tersebut)
- [ ] Set semua env vars di dashboard platform
- [ ] Test `/api/health` endpoint dari public URL

### UI
- [ ] Buat `templates/index_v2.html` dengan:
  - Google Fonts: `Scheherazade New` untuk Arabic
  - RTL rendering yang benar untuk teks Arab
  - XSS protection di JavaScript (escape sebelum innerHTML)

### Security Hardening
- [ ] Ganti in-memory rate limiter dengan `flask-limiter` + Redis
- [ ] Tambah request ID untuk tracing
- [ ] Setup Sentry (error monitoring gratis untuk hobby tier)

### Testing
- [ ] Tulis `test_validators.py` dengan pytest
- [ ] Tulis `test_reasoning_validator.py`
- [ ] Tulis `test_query_parser.py`

---

## PHASE 2 — Production Stability (Target: Bulan 1)

### Content
- [ ] Lengkapi Arabic text untuk semua 29 rules yang masih perlu hadis non-standard
- [ ] Review transliterasi oleh native speaker atau ustaz
- [ ] Tambah topik Phase 2: shalat jama & qashar, tayammum, shalat musafir

### Monitoring
- [ ] Uptime monitoring (UptimeRobot free tier)
- [ ] Log aggregation (Logtail atau Papertrail free tier)
- [ ] Weekly review: pertanyaan apa yang paling banyak tidak ditemukan (no-match analytics)

### Architecture Decision Points
- [ ] Evaluasi apakah keyword matching cukup atau perlu TF-IDF / embedding sederhana
- [ ] Decision: apakah data tetap di Python dict atau migrasi ke SQLite
- [ ] Decision: apakah perlu user session untuk history pertanyaan

---

## PHASE 3 — Scale & Trust (Target: Bulan 2-3)

### Trust Layer
- [ ] Setiap jawaban ditampilkan dengan badge confidence
- [ ] Link ke sumber eksternal (Quran.com, HadithCollection.com) untuk verifikasi mandiri
- [ ] Review konten oleh ustaz / ahli fiqh untuk QA validation

### Scale
- [ ] Migrasi ke SQLite + FTS (Full Text Search) jika data > 500 rules
- [ ] CDN untuk static assets
- [ ] Horizontal scaling jika traffic > 1000 req/hari

---

## Architectural Decisions & Rationale (Log)

| Tanggal | Keputusan | Alasan |
|---------|-----------|--------|
| 2026-05-27 | Data sebagai Python dict, bukan database | Simplicity untuk Phase 0; data kecil (< 100 entries) |
| 2026-05-27 | Keyword matching, bukan embeddings | Kontrol penuh atas matching; tidak perlu GPU; deterministic |
| 2026-05-27 | Confidence gating sebelum answer | Mencegah jawaban tanpa dalil; critical untuk domain agama |
| 2026-05-27 | In-memory rate limiter | Cukup untuk Phase 0; akan migrasi ke Redis di Phase 1 |
| 2026-05-27 | Hanya Shafi'i | Scope muallaf di Indonesia; extensible untuk madhab lain |

---

## Pertanyaan Terbuka (Untuk Diskusi Mentoring)

1. **Scope expansion**: Kapan project ini siap menerima pertanyaan di luar 12 topik muallaf?
2. **Disclaimer standar**: Apakah perlu fatwa dari lembaga (MUI/Rabithah) sebelum public launch?
3. **User feedback**: Bagaimana mekanisme user melaporkan jawaban yang salah?
4. **Data update cycle**: Siapa yang bertanggung jawab review konten jika ada koreksi ulama?
