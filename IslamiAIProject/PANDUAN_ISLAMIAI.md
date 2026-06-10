# PANDUAN ISLAMIAI
## Cara Kerja Database, Perintah Git, dan Penggunaan di Termux

---

## BAGIAN 1: CARA KERJA DATABASE

### Mengapa jawaban masih dari islamic_data.py?

Saat ini sistem punya **dua sumber data** yang bekerja berlapis:

```
Pertanyaan user
       ↓
   Layer 1-3 ─── islamic_data.py (statis, ~60 ayat, ~38 hadis, 64 aturan Syafi'i)
       ↓ tidak ditemukan
   Layer 4   ─── islamiai.db    (dinamis, 89.109 passage dari 28 EPUB kitab)
       ↓ tidak ditemukan
   Tolak jawaban (kurang dalil)
```

**Layer 4 (islamiai.db) belum aktif** karena proses ingest EPUB belum dijalankan.
Itulah kenapa semua jawaban masih dari islamic_data.py.

---

### Arsitektur database islamiai.db

```
islamiai.db
├── kitab_books     ← metadata kitab (slug, nama, author, authority_level)
├── kitab_corpus    ← isi teks: 89.109 passage Arab dari 28 kitab
└── kitab_fts       ← FTS5 virtual table: index pencarian fulltext
```

**Alur data dari EPUB ke database:**

```
corpus/epub/al_umm.epub
       ↓ ebooklib: baca setiap halaman XHTML
       ↓ BeautifulSoup: ekstrak teks Arab
       ↓ filter: panjang ≥150 char, rasio Arab ≥35%
       ↓ _get_chapter_title(): cari heading Arab (bukan page anchor)
       ↓ _get_page_ref(): ambil nama file halaman
       ↓
INSERT INTO kitab_corpus (book_slug, authority_level, chapter_title, arabic_text, ...)
       ↓
INSERT INTO kitab_fts (rebuild) ← index FTS5 dibangun sekali di akhir
```

**Cara FTS5 bekerja saat ada pertanyaan:**

```python
# User tanya: "hukum wudhu"
query = "hukum wudhu"

# 1. detect domain → "tahara"
# 2. expand query → "وضوء OR الوضوء OR الطهارة OR ..."
# 3. FTS5 MATCH → ambil 20 kandidat (4× limit)
# 4. re-rank: 55% skor teks + 45% authority level
# 5. return top-5 passages dari kitab paling otoritatif
```

**Authority level mempengaruhi ranking:**
```
Level 1 (skor 1.00) — Al-Umm, Al-Risalah          ← Qawl Imam Syafi'i
Level 2 (skor 0.85) — Mukhtasar al-Muzani          ← Murid langsung
Level 3 (skor 0.70) — Al-Majmu', Rawdhat, Minhaj   ← Mu'tamad (Nawawi)
Level 4 (skor 0.55) — Tuhfat, Nihayat, Mughni      ← Syarh Mu'tamad
Level 5 (skor 0.40) — Tafsir Ibn Kathir, Qurtubi   ← Tafsir & Qawa'id
```

---

### Cara mengaktifkan Layer 4 (wajib dilakukan)

```bash
cd ~/IslamiAI/IslamiAIProject
source venv/bin/activate

# Langkah 1 — Test satu kitab dulu (dry run, tidak tulis ke DB)
python3 -W ignore::UserWarning ingest_corpus.py --book al_risalah --dry-run

# Langkah 2 — Ingest satu kitab dulu sebagai verifikasi
python3 -W ignore::UserWarning ingest_corpus.py --book al_risalah

# Langkah 3 — Cek hasilnya
python3 -c "from db_retrieval import get_corpus_stats; s=get_corpus_stats(); print(s)"

# Langkah 4 — Ingest semua (15–30 menit, jalankan di background)
nohup python3 -W ignore::UserWarning ingest_corpus.py > ingest_log.txt 2>&1 &
echo "PID: $! — pantau: tail -f ingest_log.txt"

# Langkah 5 — Cek selesai
tail -20 ingest_log.txt
python3 -c "from db_retrieval import get_corpus_stats; \
            s=get_corpus_stats(); print(s.get('passages','?'), 'passages')"
```

**Catatan penting:**
- `islamiai.db` ada di dalam `IslamiAIProject/` dan di-gitignore (tidak masuk repo)
- Setiap kali pindah mesin atau fresh clone, harus ingest ulang
- Setelah update `ingest_corpus.py`, jalankan ulang dengan `--reset-book <slug>` untuk kitab yang terpengaruh

---

## BAGIAN 2: UPDATE MONOREPO GITHUB

### Commit semua perubahan Phase B

```bash
cd ~/IslamiAI
source IslamiAIProject/venv/bin/activate

# Cek status file yang berubah
git status

# Tambahkan semua file yang berubah
git add IslamiAIProject/db_retrieval.py \
        IslamiAIProject/ingest_corpus.py \
        IslamiAIProject/chatbot.py \
        IslamiAIProject/app.py \
        IslamiAIProject/templates/index.html \
        IslamiAIProject/test_phase.py \
        IslamiAIProject/chapter_title_extractor.py

# Commit
git commit -m "Phase B: domain re-rank (B1), chapter title fix (B2), kitab citations frontend (B3), welcome screen + scroll fix (UI)"

# Push
git push origin main
```

### Jika ada konflik atau error saat push

```bash
# Cek remote
git remote -v

# Jika perlu pull dulu
git pull origin main --rebase
git push origin main
```

---

## BAGIAN 3: PANDUAN PENGGUNAAN DI TERMUX

### Prasyarat (install sekali)

```bash
# Di Termux — install paket sistem
pkg update && pkg upgrade
pkg install python git openssh

# Clone repo (jika belum ada)
git clone https://github.com/ladainamazid/IslamiAI.git
cd IslamiAI/IslamiAIProject

# Buat virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install ebooklib beautifulsoup4 lxml
```

---

### Cara menjalankan server (setiap kali pakai)

```bash
cd ~/IslamiAI/IslamiAIProject
source venv/bin/activate
python3 app.py
```

Buka browser Termux (atau browser lain di HP) → `http://127.0.0.1:1928`

---

### Cara ingest EPUB (lakukan sekali, atau setelah update corpus)

```bash
cd ~/IslamiAI/IslamiAIProject
source venv/bin/activate

# Pastikan EPUB ada di tempat yang benar
ls corpus/epub/ | head -10

# Ingest semua (jalankan saat HP tidak dipakai, ~15-30 menit)
nohup python3 -W ignore::UserWarning ingest_corpus.py > ingest_log.txt 2>&1 &

# Pantau progress
tail -f ingest_log.txt
# (Ctrl+C untuk stop pantau, proses ingest tetap jalan)

# Cek selesai
python3 -c "from db_retrieval import get_corpus_stats; \
import json; print(json.dumps(get_corpus_stats(), indent=2, default=str))"
```

---

### Cara update kode dari GitHub (pull terbaru)

```bash
cd ~/IslamiAI
git pull origin main
cd IslamiAIProject
source venv/bin/activate
# Restart server jika sedang berjalan
pkill -f "python3 app.py"
python3 app.py
```

---

### Cara menjalankan test suite

```bash
cd ~/IslamiAI/IslamiAIProject
source venv/bin/activate
python3 -m pytest test_phase.py test_reasoning_validator.py -v
```

---

### Referensi cepat — perintah harian

| Tujuan | Perintah |
|--------|----------|
| Aktifkan venv | `source venv/bin/activate` |
| Jalankan server | `python3 app.py` |
| Buka di browser | `http://127.0.0.1:1928` |
| Cek DB tersedia | `python3 -c "from db_retrieval import is_db_available; print(is_db_available())"` |
| Cek jumlah passage | `python3 -c "from db_retrieval import get_corpus_stats; print(get_corpus_stats().get('passages'))"` |
| Jalankan ingest | `python3 -W ignore::UserWarning ingest_corpus.py` |
| Ingest satu kitab | `python3 ingest_corpus.py --book al_umm` |
| Reset satu kitab | `python3 ingest_corpus.py --reset-book al_umm` |
| Lihat daftar kitab | `python3 ingest_corpus.py --list-books` |
| Jalankan test | `python3 -m pytest test_phase.py -v` |
| Pull dari GitHub | `git pull origin main` |
| Push ke GitHub | `git add -A && git commit -m "..." && git push origin main` |
| Matikan server | `pkill -f "python3 app.py"` |

---

### Struktur direktori penting

```
IslamiAI/
├── .git/                        ← git repository
└── IslamiAIProject/
    ├── venv/                    ← virtual environment (jangan di-commit)
    ├── corpus/
    │   └── epub/                ← 28 file .epub kitab (jangan di-commit)
    ├── islamiai.db              ← database SQLite (jangan di-commit, di-gitignore)
    ├── app.py                   ← Flask server
    ├── chatbot.py               ← pipeline orchestration
    ├── retrieval.py             ← Layer 1-3 retrieval
    ├── db_retrieval.py          ← Layer 4 FTS5 search (Phase B1)
    ├── ingest_corpus.py         ← EPUB → database (Phase B2)
    ├── chapter_title_extractor.py ← ekstrak judul bab dari EPUB
    ├── reasoning_validator.py   ← confidence scoring
    ├── formatter.py             ← format output
    ├── islamic_data.py          ← data statis terverifikasi
    ├── templates/
    │   └── index.html           ← UI chatbot
    └── test_phase.py            ← test suite Phase B
```

---

### Troubleshooting umum

**Server tidak bisa diakses dari browser HP:**
```bash
# Jalankan di semua interface (bukan hanya localhost)
python3 app.py --host 0.0.0.0
# Akses dari browser: http://<IP-lokal>:1928
# Cek IP: ip addr show | grep "inet "
```

**venv tidak aktif (error ModuleNotFoundError):**
```bash
source ~/IslamiAI/IslamiAIProject/venv/bin/activate
# Cek aktif: prompt berubah jadi (venv)
```

**Database tidak tersedia (jawaban selalu dari islamic_data.py):**
```bash
ls -lh ~/IslamiAI/IslamiAIProject/islamiai.db
# Jika tidak ada → jalankan ingest_corpus.py
```

**Ingest terhenti di tengah:**
```bash
# Lihat kitab yang sudah masuk
python3 ingest_corpus.py --list-books
python3 -c "from db_retrieval import get_corpus_stats; print(get_corpus_stats())"
# Lanjut ingest — kitab yang sudah ada akan di-skip otomatis
python3 -W ignore::UserWarning ingest_corpus.py
```

**Welcome screen muncul terus:**
```bash
# Buka browser → F12 (DevTools) → Console → ketik:
# localStorage.removeItem('islamiai_welcomed')
# Atau: buka tab Incognito/Private
```
