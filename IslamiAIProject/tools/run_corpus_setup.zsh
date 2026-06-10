#!/usr/bin/env zsh
# ══════════════════════════════════════════════════════════════════
# run_corpus_setup.zsh — IslamiAI Shamela Corpus Setup
# ══════════════════════════════════════════════════════════════════
#
# CARA PAKAI:
#   cd /home/muhammad/IslamiAI/IslamiAIProject
#   chmod +x tools/run_corpus_setup.zsh
#   ./tools/run_corpus_setup.zsh
#
# Script ini menjalankan tiga langkah secara berurutan:
#   1. Download 29 kitab dari shamela.ws → corpus/epub/
#   2. Konversi EPUB → SQLite            → corpus/shamela_corpus.db
#   3. Integrasi dengan IslamiAI         → corpus_retrieval.py
#
# Jika gagal di langkah tertentu, bisa dilanjut dari sana:
#   ./tools/run_corpus_setup.zsh --from 2
# ══════════════════════════════════════════════════════════════════

set -e  # exit on error
setopt NULL_GLOB 2>/dev/null || true  # zsh: no error jika glob kosong

# ── Warna terminal ──────────────────────────────────────────────────────────────
RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[0;33m'
BLU='\033[0;34m'
BLD='\033[1m'
RST='\033[0m'

# ── Konfigurasi ─────────────────────────────────────────────────────────────────
SCRIPT_DIR="${0:A:h}"           # direktori tools/
PROJECT_DIR="${SCRIPT_DIR:h}"   # direktori project root
TOOLS_DIR="$SCRIPT_DIR"
CORPUS_DIR="$PROJECT_DIR/corpus"
LOG_FILE="$CORPUS_DIR/setup.log"

# Mulai dari langkah berapa (default 1)
START_FROM=${2:-1}
if [[ "$1" == "--from" ]]; then
    START_FROM=${2:-1}
fi

# ── Fungsi Helper ────────────────────────────────────────────────────────────────
log_header() {
    echo ""
    echo "${BLU}${BLD}══════════════════════════════════════════════════════════════${RST}"
    echo "${BLU}${BLD}  $1${RST}"
    echo "${BLU}${BLD}══════════════════════════════════════════════════════════════${RST}"
    echo ""
}

log_ok()   { echo "${GRN}✅ $1${RST}"; }
log_warn() { echo "${YLW}⚠️  $1${RST}"; }
log_err()  { echo "${RED}❌ $1${RST}"; }
log_info() { echo "   $1"; }

# ── Header ───────────────────────────────────────────────────────────────────────
clear
echo ""
echo "${BLD}╔══════════════════════════════════════════════════════════════╗${RST}"
echo "${BLD}║   IslamiAI — Shamela Corpus Setup                           ║${RST}"
echo "${BLD}║   Mendownload & mengintegrasikan 29 kitab klasik Islam       ║${RST}"
echo "${BLD}╚══════════════════════════════════════════════════════════════╝${RST}"
echo ""
echo "   Project  : $PROJECT_DIR"
echo "   Corpus   : $CORPUS_DIR"
echo "   Log      : $LOG_FILE"
echo "   Mulai di : Langkah $START_FROM"
echo ""

# ── Persiapan ────────────────────────────────────────────────────────────────────
mkdir -p "$CORPUS_DIR" "$CORPUS_DIR/epub" "$CORPUS_DIR/db"
touch "$LOG_FILE"

# Cek Python
if ! command -v python3 &>/dev/null; then
    log_err "Python3 tidak ditemukan. Install Python 3.10+ terlebih dahulu."
    exit 1
fi
PYTHON_VER=$(python3 --version 2>&1)
log_ok "Python: $PYTHON_VER"

# Cek dan install dependensi Python
log_header "Persiapan: Cek Dependensi"

check_and_install() {
    local pkg="$1"
    local import_name="${2:-$1}"
    if python3 -c "import $import_name" 2>/dev/null; then
        log_ok "$pkg sudah terinstall"
    else
        log_info "Menginstall $pkg..."
        pip install "$pkg" --break-system-packages -q
        if python3 -c "import $import_name" 2>/dev/null; then
            log_ok "$pkg berhasil diinstall"
        else
            log_err "Gagal install $pkg"
            exit 1
        fi
    fi
}

check_and_install "shamela2epub" "shamela2epub"
check_and_install "ebooklib"     "ebooklib"
check_and_install "beautifulsoup4" "bs4"
check_and_install "lxml"         "lxml"
check_and_install "requests"     "requests"

# Pastikan script tools ada
for script in "01_download.py" "02_build_db.py" "03_integrate.py"; do
    if [[ ! -f "$TOOLS_DIR/$script" ]]; then
        log_err "$script tidak ditemukan di $TOOLS_DIR"
        log_err "Pastikan semua file tools/ ada."
        exit 1
    fi
done

# ── Langkah 1: Download ──────────────────────────────────────────────────────────
if [[ $START_FROM -le 1 ]]; then
    log_header "LANGKAH 1/3: Download 29 Kitab dari Shamela"
    echo "   ${YLW}Proses ini memerlukan koneksi internet dan mungkin${RST}"
    echo "   ${YLW}memakan waktu 30–90 menit tergantung ukuran kitab.${RST}"
    echo ""
    echo "   Anda bisa memantau progress di file lain:"
    echo "   ${BLD}tail -f $CORPUS_DIR/download.log${RST}"
    echo ""

    read -q "REPLY?Lanjutkan download? [y/N] " || true
    echo ""

    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
        python3 "$TOOLS_DIR/01_download.py" 2>&1 | tee -a "$LOG_FILE"
        EPUB_COUNT=$(ls "$CORPUS_DIR/epub/"*.epub 2>/dev/null | wc -l | tr -d ' ')
        log_ok "Download selesai: $EPUB_COUNT file EPUB tersedia"
    else
        log_warn "Download dilewati oleh user."
        EPUB_COUNT=$(ls "$CORPUS_DIR/epub/"*.epub 2>/dev/null | wc -l | tr -d ' ')
        if [[ $EPUB_COUNT -eq 0 ]]; then
            log_err "Tidak ada file EPUB. Langkah 2 dan 3 tidak bisa dijalankan."
            exit 1
        fi
        log_info "Menggunakan $EPUB_COUNT EPUB yang sudah ada."
    fi
else
    log_info "Skip langkah 1 (--from $START_FROM)"
    EPUB_COUNT=$(ls "$CORPUS_DIR/epub/"*.epub 2>/dev/null | wc -l | tr -d ' ')
    log_info "EPUB yang tersedia: $EPUB_COUNT"
fi

# ── Langkah 2: Build Database ────────────────────────────────────────────────────
if [[ $START_FROM -le 2 ]]; then
    log_header "LANGKAH 2/3: Membangun Database SQLite"
    echo "   Mengkonversi $EPUB_COUNT EPUB ke SQLite dengan FTS5..."
    echo ""

    python3 "$TOOLS_DIR/02_build_db.py" 2>&1 | tee -a "$LOG_FILE"

    if [[ -f "$CORPUS_DIR/shamela_corpus.db" ]]; then
        DB_SIZE=$(du -sh "$CORPUS_DIR/shamela_corpus.db" | cut -f1)
        log_ok "Database berhasil dibuat: shamela_corpus.db ($DB_SIZE)"
    else
        log_err "shamela_corpus.db tidak dibuat. Periksa log."
        exit 1
    fi

    # Hitung individual .db files
    DB_COUNT=$(ls "$CORPUS_DIR/db/"*.db 2>/dev/null | wc -l | tr -d ' ')
    log_ok "$DB_COUNT individual .db file tersedia di corpus/db/"
else
    log_info "Skip langkah 2 (--from $START_FROM)"
fi

# ── Langkah 3: Integrasi ─────────────────────────────────────────────────────────
if [[ $START_FROM -le 3 ]]; then
    log_header "LANGKAH 3/3: Integrasi dengan IslamiAI"

    python3 "$TOOLS_DIR/03_integrate.py" 2>&1 | tee -a "$LOG_FILE"

    if [[ -f "$PROJECT_DIR/corpus_retrieval.py" ]]; then
        log_ok "corpus_retrieval.py berhasil dipasang"
    else
        log_warn "corpus_retrieval.py tidak terpasang otomatis"
        log_info "Salin manual: cp $TOOLS_DIR/../corpus_retrieval.py $PROJECT_DIR/"
    fi
fi

# ── Ringkasan Final ───────────────────────────────────────────────────────────────
log_header "SELESAI — Ringkasan"

echo "   File yang dibuat:"
[[ -d "$CORPUS_DIR/epub" ]]   && log_ok "corpus/epub/          ($(ls "$CORPUS_DIR/epub/"*.epub 2>/dev/null | wc -l | tr -d ' ') EPUB)"
[[ -f "$CORPUS_DIR/shamela_corpus.db" ]] && log_ok "corpus/shamela_corpus.db ($(du -sh "$CORPUS_DIR/shamela_corpus.db" | cut -f1))"
[[ -d "$CORPUS_DIR/db" ]]     && log_ok "corpus/db/            ($(ls "$CORPUS_DIR/db/"*.db 2>/dev/null | wc -l | tr -d ' ') individual .db)"
[[ -f "$PROJECT_DIR/corpus_retrieval.py" ]] && log_ok "corpus_retrieval.py   (modul integrasi)"
[[ -f "$PROJECT_DIR/retrieval.py.bak" ]]    && log_ok "retrieval.py.bak      (backup original)"

echo ""
echo "   ${BLD}Langkah selanjutnya:${RST}"
echo "   1. Test retrieval: ${BLD}python3 corpus_retrieval.py${RST}"
echo "   2. Jalankan server: ${BLD}python3 app.py${RST}"
echo "   3. Tanya tentang: thaharah, wudhu, zakat, nikah, waris"
echo ""
echo "   ${YLW}Penting: Jawaban dari corpus (29 kitab) akan ditandai${RST}"
echo "   ${YLW}_needs_review=True. Validasi dengan ustaz sebelum publik.${RST}"
echo ""
