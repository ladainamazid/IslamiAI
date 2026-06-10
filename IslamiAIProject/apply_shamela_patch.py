#!/usr/bin/env python3
"""
apply_shamela_patch.py — Patch shamela2epub v1.4.x
───────────────────────────────────────────────────
Perbaikan yang diterapkan:

  misc/http.py:
    • multiplexed=False  ← root cause Retry(total=9) tidak turun (HTTP/2 stream
                            membuat Retry object baru tiap attempt)
    • MAX_RETRIES = 3    ← retry selesai dalam <3 menit (bukan loop selamanya)
    • backoff_factor=2.0 ← jeda eksponensial: 2s, 4s, 8s

  main.py:
    • Cache HTML tiap halaman ke ~/.cache/shamela2epub/book_{id}/page_NNNNNN.html
    • Resume otomatis: halaman di cache tidak diunduh ulang
    • Per-page retry (3×) dengan fresh session setiap gagal
    • Halaman yang gagal semua percobaan di-skip (log warning), bukan crash/loop

Cara pakai:
  python3 apply_shamela_patch.py

Untuk restore ke versi asli:
  python3 apply_shamela_patch.py --restore
"""

import sys
import shutil
import shamela2epub
import os
from pathlib import Path

PKG = Path(os.path.dirname(shamela2epub.__file__))
HTTP_PY  = PKG / "misc" / "http.py"
MAIN_PY  = PKG / "main.py"
HTTP_BAK = PKG / "misc" / "http.py.orig"
MAIN_BAK = PKG / "main.py.orig"


# ═══════════════════════════════════════════════════════════════════════════════
# FILE 1: misc/http.py
# ═══════════════════════════════════════════════════════════════════════════════
PATCHED_HTTP = '''\
from niquests import Session
from urllib3 import Retry

TIME_OUT   = 60
MAX_RETRIES = 3   # Dikurangi dari 10; per-page retry ditangani di main.py

# backoff_factor=2.0: jeda 2s, 4s, 8s antar retry urllib3
# read=MAX_RETRIES: batasi retry untuk ReadTimeoutError secara eksplisit
retry_strategy = Retry(
    total=MAX_RETRIES,
    read=MAX_RETRIES,
    connect=MAX_RETRIES,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    backoff_factor=2.0,
)


def get_session(connections: int) -> Session:
    return Session(
        multiplexed=False,   # HTTP/2 multiplexed mode menyebabkan Retry counter
                             # tidak berkurang (dibuat ulang tiap stream) → infinite loop.
                             # Gunakan HTTP/1.1 dengan DNS sistem (tidak perlu resolver khusus).
        retries=retry_strategy,
        pool_maxsize=connections * 3,
    )
'''


# ═══════════════════════════════════════════════════════════════════════════════
# FILE 2: main.py
# ═══════════════════════════════════════════════════════════════════════════════
PATCHED_MAIN = '''\
"""shamela2epub main — patched: resume via disk cache + per-page retry."""

import logging
import os
import time
from collections.abc import Callable
from pathlib import Path

from tqdm import tqdm
from urllib3.exceptions import HTTPError

from shamela2epub import OUT_DIR
from shamela2epub.misc.http import MAX_RETRIES, TIME_OUT, get_session
from shamela2epub.misc.utils import get_book_first_page_url, get_book_info_page_url, is_valid_url
from shamela2epub.models.book_html_page import BookHTMLPage
from shamela2epub.models.book_info_html_page import BookInfoHTMLPage
from shamela2epub.models.epub_book import EPUBBook


# Percobaan per halaman di level aplikasi (di atas retry urllib3 di http.py)
MAX_PAGE_ATTEMPTS = 3

# Direktori cache: $SHAMELA_CACHE_DIR atau ~/.cache/shamela2epub/
# Override contoh: export SHAMELA_CACHE_DIR=~/IslamiAI/IslamiAIProject/corpus/cache
_CACHE_BASE = Path(
    os.environ.get("SHAMELA_CACHE_DIR", Path.home() / ".cache" / "shamela2epub")
)


def _cache_dir(book_id: str) -> Path:
    """Buat dan kembalikan direktori cache per kitab."""
    d = _CACHE_BASE / f"book_{book_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _page_file(cache: Path, n: int) -> Path:
    return cache / f"page_{n:06d}.html"


class BookDownloader:
    book_info_page: BookInfoHTMLPage

    def __init__(self, url: str, connections: int) -> None:
        """Book Downloader constructor."""
        self.url = url
        self.valid = is_valid_url(self.url)
        self.epub_book = EPUBBook()
        self._session = get_session(connections)
        self._chunk_size = connections * 2
        self._progress_bar: tqdm | None = None
        self._skipped_pages: list[int] = []

    def create_info_page(self) -> None:
        url = get_book_info_page_url(self.url)
        self.book_info_page = BookInfoHTMLPage(
            url, self._session.get(url, timeout=TIME_OUT).text
        )
        self.epub_book.init()
        self.epub_book.create_info_page(self.book_info_page)

    def create_first_page(self) -> None:
        url = get_book_first_page_url(self.url)
        book_html_page = BookHTMLPage(url, self._session.get(url, timeout=TIME_OUT).text)
        self.epub_book.set_page_count(book_html_page.last_page)
        self.epub_book.set_parts_map(book_html_page.parts_map)
        self.epub_book.set_toc(book_html_page.toc)
        self.epub_book.add_page(book_html_page)
        if self._progress_bar is not None:
            self._progress_bar.total = self.epub_book.pages_count
            self._progress_bar.update(1)

    def _download(self, progress_callback: Callable[[str | int], None]) -> None:
        # ID kitab: "https://shamela.ws/book/9851" → "9851"
        book_id = self.url.rstrip("/").split("/")[-1]
        cache = _cache_dir(book_id)

        self.create_first_page()
        total = self.epub_book.pages_count

        # ── Statistik cache untuk info resume ─────────────────────────────────
        cached_count = sum(
            1 for pn in range(2, total + 1)
            if _page_file(cache, pn).exists() and _page_file(cache, pn).stat().st_size > 0
        )
        if cached_count > 0:
            pct = cached_count / (total - 1) * 100
            logging.info(
                "Resume: %d/%d halaman di cache (%.1f%%) — %d halaman tersisa",
                cached_count, total - 1, pct, total - 1 - cached_count,
            )
        else:
            logging.info("Cache kosong — unduh dari awal (cache: %s)", cache)

        # ── Download per halaman ───────────────────────────────────────────────
        for page_number in range(2, total + 1):
            page_url = f"{self.url}/{page_number}"
            cf = _page_file(cache, page_number)

            # ── Dari cache ────────────────────────────────────────────────────
            if cf.exists() and cf.stat().st_size > 0:
                try:
                    html = cf.read_text(encoding="utf-8")
                    self.epub_book.add_page(BookHTMLPage(page_url, html))
                    progress_callback(str(page_number))
                    continue
                except Exception as e:
                    logging.warning("Cache rusak halaman %d: %s — download ulang", page_number, e)
                    cf.unlink(missing_ok=True)

            # ── Unduh dari server ─────────────────────────────────────────────
            for attempt in range(1, MAX_PAGE_ATTEMPTS + 1):
                try:
                    response = self._session.get(page_url, timeout=TIME_OUT)
                    if response.status_code == 200:
                        html = response.text
                        # Simpan ke cache sebelum proses ke EPUB
                        cf.write_text(html, encoding="utf-8")
                        self.epub_book.add_page(BookHTMLPage(page_url, html))
                        progress_callback(str(page_number))
                        break
                    else:
                        logging.warning(
                            "Halaman %d: HTTP %d (percobaan %d/%d)",
                            page_number, response.status_code, attempt, MAX_PAGE_ATTEMPTS,
                        )
                        if attempt < MAX_PAGE_ATTEMPTS:
                            time.sleep(15 * attempt)

                except Exception as e:
                    if attempt < MAX_PAGE_ATTEMPTS:
                        wait = 15 * attempt  # 15s → 30s
                        logging.warning(
                            "Halaman %d percobaan %d/%d: %s — retry dalam %ds...",
                            page_number, attempt, MAX_PAGE_ATTEMPTS, type(e).__name__, wait,
                        )
                        time.sleep(wait)
                        # Buat sesi baru untuk reset state koneksi yang stuck
                        self._session = get_session(1)
                    else:
                        logging.error(
                            "Halaman %d: DILEWATI setelah %d percobaan gagal (%s).",
                            page_number, MAX_PAGE_ATTEMPTS, type(e).__name__,
                        )
                        self._skipped_pages.append(page_number)

    def download(self) -> None:
        self._progress_bar = tqdm(
            desc="Downloading", colour="white", unit=" page", dynamic_ncols=True
        )
        self._download(lambda _: self._progress_bar.update(1))  # type: ignore[union-attr]
        if self._skipped_pages:
            logging.warning(
                "Total halaman dilewati: %d → nomor: %s",
                len(self._skipped_pages), self._skipped_pages,
            )

    def save_book(self, output: str) -> Path:
        self.epub_book.generate_toc()
        book_name = f"{self.book_info_page.title} - {self.book_info_page.author}.epub"
        if output:
            output_book = output if output.endswith(".epub") else f"{output}/{book_name}"
        else:
            output_book = f"{OUT_DIR}/{book_name}"
        self.epub_book.save_book(output_book)
        if self._progress_bar is not None:
            self._progress_bar.close()

        book_id = self.url.rstrip("/").split("/")[-1]
        cache = _cache_dir(book_id)
        cache_files = list(cache.glob("*.html"))
        size_mb = sum(f.stat().st_size for f in cache_files) / 1e6
        logging.info(
            "Cache tersimpan: %s (%d file, %.0f MB)",
            cache, len(cache_files), size_mb,
        )
        logging.info("Hapus cache jika tidak dibutuhkan lagi: rm -rf %s", cache)

        return Path(output_book)
'''


# ═══════════════════════════════════════════════════════════════════════════════
# Eksekusi patch / restore
# ═══════════════════════════════════════════════════════════════════════════════

def do_patch():
    print(f"Package  : {PKG}")
    print(f"http.py  : {HTTP_PY}")
    print(f"main.py  : {MAIN_PY}")
    print()

    # Backup
    for src, bak in [(HTTP_PY, HTTP_BAK), (MAIN_PY, MAIN_BAK)]:
        if not bak.exists():
            shutil.copy2(src, bak)
            print(f"✅ Backup : {bak.name}")
        else:
            print(f"ℹ  Backup sudah ada: {bak.name} (tidak ditimpa)")

    # Tulis file patched
    HTTP_PY.write_text(PATCHED_HTTP, encoding="utf-8")
    print(f"✅ Patched: misc/http.py")

    MAIN_PY.write_text(PATCHED_MAIN, encoding="utf-8")
    print(f"✅ Patched: main.py")

    # Hapus .pyc agar Python pakai source baru
    for pyc in PKG.rglob("*.pyc"):
        pyc.unlink(missing_ok=True)
    print("✅ Cache .pyc dihapus")

    print()
    print("Patch berhasil diterapkan.")
    print()
    print("Cache halaman akan disimpan di:")
    print(f"  ~/.cache/shamela2epub/book_{{id}}/")
    print()
    print("Override lokasi cache (opsional):")
    print("  export SHAMELA_CACHE_DIR=~/IslamiAI/IslamiAIProject/corpus/cache")
    print()
    print("Verifikasi patch:")
    print("  python3 -c \"from shamela2epub.misc.http import get_session; print('OK')\"")


def do_restore():
    restored = False
    for bak, dst in [(HTTP_BAK, HTTP_PY), (MAIN_BAK, MAIN_PY)]:
        if bak.exists():
            shutil.copy2(bak, dst)
            print(f"✅ Restored: {dst.name}")
            restored = True
        else:
            print(f"⚠  Backup tidak ditemukan: {bak.name}")
    if restored:
        for pyc in PKG.rglob("*.pyc"):
            pyc.unlink(missing_ok=True)
        print("✅ Cache .pyc dihapus")
        print("Restore selesai.")
    else:
        print("Tidak ada backup yang ditemukan.")


if __name__ == "__main__":
    if "--restore" in sys.argv:
        do_restore()
    else:
        do_patch()
