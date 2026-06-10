"""
chapter_title_extractor.py  ─── Phase B2
════════════════════════════════════════════════════════════════════════════════
Modul ekstraksi judul bab dari HTML output shamela2epub.

MASALAH (Phase A known issue):
  ingest_corpus.py saat ini menyimpan chapter_title = page anchor ID
  seperti "page_1_0265", bukan judul bab Arab yang sebenarnya.
  Ini adalah artefak dari shamela2epub yang membungkus nomor halaman
  dalam tag heading (<h1 id="page_1_0265">).

SOLUSI:
  Modul ini menyediakan HTMLPageParser yang:
  1. Mempertahankan state "judul bab aktif" saat menelusuri elemen HTML
  2. Update chapter_title hanya jika heading mengandung teks Arab nyata
  3. Update page_ref dari page anchor ID (terpisah dari chapter_title)
  4. Fallback ke kita_slug + page_ref jika tidak ada judul bab ditemukan

CARA INTEGRASI KE ingest_corpus.py:
  Cari fungsi yang mem-parse HTML di ingest_corpus.py. Kemungkinan besar
  terlihat seperti salah satu pola berikut:

  POLA A — parse langsung di loop:
    for item in epub.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.content, 'html.parser')
        for p in soup.find_all('p'):
            heading = soup.find('h1') or soup.find('h2')
            chapter_title = heading.get('id', '') if heading else ''  ← MASALAH INI
            ...

  POLA B — fungsi helper terpisah:
    def _parse_html_page(html_content, book_slug, authority_level):
        ...
        chapter_title = heading['id']  ← MASALAH INI

  LANGKAH INTEGRASI:
    1. from chapter_title_extractor import HTMLPageParser
    2. Ganti loop parse HTML dengan HTMLPageParser().parse(html_content)
    3. Jalankan re-ingest (lihat perintah di bawah)

PERINTAH RE-INGEST:
  cd ~/IslamiAI/IslamiAIProject
  python ingest_corpus.py --rebuild
  # Estimasi: ~15-30 menit untuk 89,109 passages
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import re
import logging
from typing import Optional

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger("islamiai.chapter_title_extractor")

# ── Regex / konstanta ─────────────────────────────────────────────────────────

# Page anchor pattern: "page_1_0265", "page_2_0001", dst.
_PAGE_ANCHOR_RE = re.compile(r"^page_\d+_\d+$")

# Judul bab klasik Islam: "كتاب الطهارة", "باب الصلاة", "فصل في ...", "مسألة"
_CHAPTER_OPENER_RE = re.compile(
    r"^(كتاب|باب|فصل|مسألة|فروع|تنبيه|خاتمة|مقدمة|قاعدة)\b"
)

# Deteksi karakter Arab (U+0600–U+06FF)
_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")

# Panjang minimum teks Arab untuk dianggap chapter title (bukan noise)
_MIN_TITLE_LENGTH = 4
# Panjang maksimum chapter title yang disimpan ke DB
_MAX_TITLE_LENGTH = 200


# ── Fungsi helper (bisa dipakai standalone) ───────────────────────────────────

def is_page_anchor_text(text: str) -> bool:
    """
    True jika teks hanyalah page anchor pattern.
    Contoh: "page_1_0265" → True
             "باب الطهارة" → False
    """
    return bool(_PAGE_ANCHOR_RE.match(text.strip()))


def contains_arabic(text: str) -> bool:
    """True jika string mengandung setidaknya satu karakter Arab."""
    return bool(_ARABIC_RE.search(text))


def is_valid_chapter_title(text: str) -> bool:
    """
    True jika teks layak dijadikan chapter_title:
      - Mengandung karakter Arab
      - Bukan pure page anchor
      - Panjang minimal _MIN_TITLE_LENGTH karakter Arab
    """
    if not text or is_page_anchor_text(text):
        return False
    arabic_chars = [c for c in text if _ARABIC_RE.match(c)]
    return len(arabic_chars) >= _MIN_TITLE_LENGTH


def extract_page_ref_from_element(el: Tag) -> Optional[str]:
    """
    Cari page anchor ID dari element dan descendant-nya.
    Shamela2epub biasanya menyimpan ini sebagai:
      <h2 id="page_1_0265"> atau
      <h2><a id="page_1_0265"></a>...</h2>

    Returns:
        "page_1_0265" jika ditemukan, None jika tidak.
    """
    # Cek id di element itu sendiri
    el_id = el.get("id", "")
    if el_id and _PAGE_ANCHOR_RE.match(el_id):
        return el_id

    # Cek nested <a> dengan id
    anchor = el.find("a", id=_PAGE_ANCHOR_RE)
    if anchor:
        return anchor.get("id", "")

    return None


# ── Kelas utama ───────────────────────────────────────────────────────────────

class HTMLPageParser:
    """
    Parser HTML untuk satu EPUB item dari shamela2epub.

    Mempertahankan state:
      current_chapter_title : judul bab Arab terakhir yang valid
      current_page_ref      : page anchor ID terakhir

    Penggunaan:
        parser = HTMLPageParser(book_slug="al_umm", authority_level=1)
        passages = parser.parse(html_bytes_or_string)
        # passages: list[dict] siap dimasukkan ke kitab_corpus

    Tiap passage dict berisi:
        book_slug, authority_level, chapter_title, page_ref, arabic_text
    """

    def __init__(self, book_slug: str, authority_level: int) -> None:
        self.book_slug = book_slug
        self.authority_level = authority_level
        self.current_chapter_title: str = ""
        self.current_page_ref: str = ""
        self._passages: list[dict] = []

    def parse(self, html_content: bytes | str) -> list[dict]:
        """
        Parse satu HTML page, return list passage dicts.

        Traversal linear melalui semua elemen; heading memperbarui state,
        paragraph menghasilkan passage.
        """
        if isinstance(html_content, bytes):
            html_content = html_content.decode("utf-8", errors="replace")

        soup = BeautifulSoup(html_content, "html.parser")
        self._passages = []

        # Traversal sesuai urutan dokumen
        for el in soup.descendants:
            if not isinstance(el, Tag):
                continue

            # Heading elements: update state chapter_title dan/atau page_ref
            if el.name in ("h1", "h2", "h3", "h4"):
                self._process_heading(el)

            # Paragraph / div: hasilkan passage jika ada teks Arab
            elif el.name in ("p", "div") and not el.find(["p", "div"]):
                # Skip nested containers (hanya proses leaf nodes)
                self._process_paragraph(el)

        return list(self._passages)

    # ── Private methods ────────────────────────────────────────────────────

    def _process_heading(self, el: Tag) -> None:
        """
        Update state berdasarkan heading element.

        Kasus yang ditangani:
          A. Heading id = page anchor, teks kosong:
             → update page_ref saja
          B. Heading id = page anchor, teks berisi Arab:
             → update page_ref, juga update chapter_title
          C. Heading tidak punya page anchor, teks berisi Arab:
             → update chapter_title saja
          D. Nested <a id="page_X"> di dalam heading:
             → update page_ref, cek teks heading untuk chapter_title
        """
        # Cari page anchor
        page_ref = extract_page_ref_from_element(el)
        if page_ref:
            self.current_page_ref = page_ref

        # Ambil teks bersih dari heading
        raw_text = el.get_text(strip=True)

        # Jika teks itu sendiri hanya page anchor, skip chapter_title update
        if is_page_anchor_text(raw_text):
            return

        # Jika teks valid sebagai chapter title, update
        if is_valid_chapter_title(raw_text):
            self.current_chapter_title = raw_text[:_MAX_TITLE_LENGTH]
            logger.debug(
                "chapter_title updated: '%s' (book=%s page=%s)",
                self.current_chapter_title[:60],
                self.book_slug,
                self.current_page_ref,
            )

    def _process_paragraph(self, el: Tag) -> None:
        """
        Hasilkan passage dict dari paragraph element jika mengandung teks Arab.

        Juga deteksi "inline chapter marker" — paragraf yang diawali با/فصل/كتاب
        seringkali adalah judul bab yang ditulis sebagai <p> bukan <h>.
        """
        text = el.get_text(strip=True)

        if not text or not contains_arabic(text):
            return

        # Deteksi inline chapter markers (shamela kadang pakai <p> untuk bab)
        if _CHAPTER_OPENER_RE.match(text) and len(text) < 120:
            self.current_chapter_title = text[:_MAX_TITLE_LENGTH]
            logger.debug(
                "Inline chapter marker: '%s'", text[:60]
            )
            # Jangan return — teks ini sendiri mungkin juga konten, tapi
            # untuk kitab klasik biasanya bab header tidak dihitung sebagai passage.
            # Keputusan: SKIP sebagai passage (hanya update state).
            return

        # Filter teks terlalu pendek (noise, footnote marker, dll)
        arabic_chars_count = sum(1 for c in text if _ARABIC_RE.match(c))
        if arabic_chars_count < 15:
            return

        self._passages.append({
            "book_slug": self.book_slug,
            "authority_level": self.authority_level,
            "chapter_title": self.current_chapter_title,
            "page_ref": self.current_page_ref,
            "arabic_text": text,
        })


# ── Diagnostic helper ─────────────────────────────────────────────────────────

def diagnose_epub_html_structure(html_content: bytes | str, max_elements: int = 40) -> None:
    """
    Print struktur heading/paragraph dari HTML page untuk debugging.
    Berguna sebelum integrasi untuk memahami pola konkret tiap kitab.

    Penggunaan:
        import ebooklib
        from ebooklib import epub
        from chapter_title_extractor import diagnose_epub_html_structure

        book = epub.read_epub("corpus/epub/al_umm_shafii.epub")
        for item in list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))[:3]:
            print(f"\\n=== {item.get_name()} ===")
            diagnose_epub_html_structure(item.content)
    """
    if isinstance(html_content, bytes):
        html_content = html_content.decode("utf-8", errors="replace")

    soup = BeautifulSoup(html_content, "html.parser")
    count = 0
    for el in soup.descendants:
        if not isinstance(el, Tag):
            continue
        if el.name not in ("h1", "h2", "h3", "h4", "p"):
            continue
        text = el.get_text(strip=True)[:80]
        el_id = el.get("id", "")
        anchor = el.find("a", id=True)
        anchor_id = anchor.get("id", "") if anchor else ""
        print(
            f"<{el.name}> id={el_id!r:20s} anchor_id={anchor_id!r:20s} "
            f"text={text!r}"
        )
        count += 1
        if count >= max_elements:
            print(f"... (truncated at {max_elements} elements)")
            break


# ── Smoke test / standalone run ───────────────────────────────────────────────

if __name__ == "__main__":
    # Test dengan HTML sintetis yang mereproduksi pola shamela2epub
    TEST_HTML = """
    <html><body>
      <h2 id="page_1_0044"><a id="pg44"></a></h2>
      <p dir="rtl">هذا مقدمة قصيرة للكتاب.</p>

      <h2 id="page_1_0045"><a id="pg45"></a></h2>
      <h3>كتاب الطهارة</h3>
      <p dir="rtl">قال الشافعي رحمه الله: الطهارة واجبة للصلاة وللطواف.</p>
      <p dir="rtl">وتنقسم الطهارة إلى طهارة حدث وطهارة خبث.</p>

      <h2 id="page_1_0046"><a id="pg46"></a></h2>
      <p dir="rtl">باب الوضوء وأركانه وشروطه وسننه.</p>
      <p dir="rtl">الوضوء فريضة على من أراد الصلاة وكان محدثا.</p>

      <h2 id="page_1_0047"><a id="pg47"></a></h2>
      <p dir="rtl">فصل في النية وشروطها في الوضوء.</p>
      <p dir="rtl">لا يصح الوضوء إلا بنية صحيحة عند غسل الوجه.</p>
    </body></html>
    """

    print("=== HTMLPageParser Test ===\n")
    parser = HTMLPageParser(book_slug="al_umm", authority_level=1)
    passages = parser.parse(TEST_HTML)

    for i, p in enumerate(passages, 1):
        print(f"[{i}] chapter_title : {p['chapter_title']!r}")
        print(f"    page_ref     : {p['page_ref']!r}")
        print(f"    arabic_text  : {p['arabic_text'][:60]!r}")
        print()

    print(f"Total passages: {len(passages)}")
    assert len(passages) >= 4, "Expected at least 4 passages"
    assert passages[0]["chapter_title"] == "", \
        "First passage before any heading should have empty title"
    assert "الطهارة" in passages[1]["chapter_title"], \
        "Second passage should have 'كتاب الطهارة' as chapter title"
    assert passages[1]["page_ref"] == "page_1_0045", \
        "page_ref should be the page anchor, not the chapter title"
    print("\n✅ All assertions passed.")

    print("\n=== Diagnosis helper demo ===\n")
    diagnose_epub_html_structure(TEST_HTML, max_elements=20)
