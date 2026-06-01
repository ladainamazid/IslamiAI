# IslamiAI — Monorepo

Repositori tunggal yang berisi dua komponen utama proyek IslamiAI.

## 📁 Struktur Proyek

```
IslamiAI/
├── IslamiAIProject/        ← Core AI (chatbot, retrieval, validator)
└── MiniServerPrototype/    ← Flask REST API Server
```

---

## 🧠 IslamiAIProject

Sistem Knowledge Retrieval berbasis AI untuk pertanyaan keislaman.

**Komponen utama:**
- `chatbot.py` — Antarmuka utama chatbot
- `retrieval.py` — Engine pencarian knowledge
- `validators.py` / `reasoning_validator.py` — Validasi jawaban
- `query_parser.py` — Parsing pertanyaan pengguna
- `islamic_data.py` — Dataset Islam
- `data_fetcher.py` — Fetcher data eksternal

**Menjalankan:**
```bash
cd IslamiAIProject
cp .env.example .env
pip install -r requirements.txt
python3 main.py
```

---

## 🌐 MiniServerPrototype

Flask REST API server sebagai gateway ke IslamiAIProject.

**Auth flow:** `API Key → Bearer Token → Akses endpoint`

| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/` | Publik |
| GET | `/health` | Publik |
| POST | `/auth/get-token` | API Key |
| GET | `/api/data` | API Key + Token |
| POST | `/api/chat` | API Key + Token |

**Menjalankan:**
```bash
cd MiniServerPrototype
cp .env.example .env
nano .env   # Set API_KEY
pip install -r requirements.txt
python3 server.py
```

---

## ⚙️ Setup Awal

```bash
git clone https://github.com/USERNAME/IslamiAI.git
cd IslamiAI

# Setup AI Project
cd IslamiAIProject && cp .env.example .env && cd ..

# Setup Server
cd MiniServerPrototype && cp .env.example .env && cd ..
```

---

## 🔒 Keamanan

- Jangan pernah commit file `.env`
- API Key disimpan di `.env`, bukan di kode
- File `.env.example` disediakan sebagai template

---

*IslamiAI Project — v1.0.0*
