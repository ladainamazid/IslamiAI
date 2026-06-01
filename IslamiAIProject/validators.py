# validators.py
# IslamiAI - Input Sanitization & Validation
# Prinsip: sanitize dulu, validate kemudian, tolak yang ambigu

import re
import html
import unicodedata
from config import config


class InputValidationError(ValueError):
    """Raised ketika input tidak lolos validasi."""
    pass


# Karakter yang diizinkan: huruf (termasuk Arabic Unicode), angka, spasi, tanda baca umum
_ALLOWED_PATTERN = re.compile(
    r"^[\w\s\u0600-\u06FF\u200c\u200d"
    r".,;:?!\-'\"()\[\]/@#&*%+=/\\<>{}|~`^]+$",
    re.UNICODE
)

# Pola yang patut dicurigai (injeksi, XSS dasar)
_SUSPICIOUS_PATTERNS = [
    re.compile(r"<[^>]+>"),           # HTML tags
    re.compile(r"javascript\s*:", re.I),
    re.compile(r"on\w+\s*=", re.I),   # event handlers
    re.compile(r"--"),                  # SQL comment
    re.compile(r";\s*(drop|insert|update|delete|select)", re.I),  # SQL injection
    re.compile(r"\.\./"),              # path traversal
]


def sanitize_text(raw: str) -> str:
    """
    Bersihkan input teks dari karakter berbahaya.
    1. Normalize Unicode (NFC)
    2. Escape HTML entities
    3. Strip leading/trailing whitespace
    4. Collapse multiple spaces
    """
    if not isinstance(raw, str):
        raise InputValidationError("Input harus berupa teks.")

    # Normalize Unicode
    text = unicodedata.normalize("NFC", raw)

    # Escape HTML entities (pertahanan terhadap XSS)
    text = html.escape(text, quote=True)

    # Strip dan collapse whitespace
    text = " ".join(text.split())

    return text


def validate_question(raw: str) -> str:
    """
    Validasi dan sanitasi pertanyaan pengguna.
    Returns: teks yang sudah bersih
    Raises: InputValidationError jika tidak valid
    """
    if not raw or not raw.strip():
        raise InputValidationError("Pertanyaan tidak boleh kosong.")

    cleaned = sanitize_text(raw)

    # Panjang minimum
    if len(cleaned) < config.MIN_QUESTION_LENGTH:
        raise InputValidationError(
            f"Pertanyaan terlalu pendek (minimum {config.MIN_QUESTION_LENGTH} karakter)."
        )

    # Panjang maksimum
    if len(cleaned) > config.MAX_QUESTION_LENGTH:
        raise InputValidationError(
            f"Pertanyaan terlalu panjang (maksimum {config.MAX_QUESTION_LENGTH} karakter). "
            f"Anda memasukkan {len(cleaned)} karakter."
        )

    # Cek pola mencurigakan (pre-escape, jadi cek di raw juga)
    for pattern in _SUSPICIOUS_PATTERNS:
        if pattern.search(raw):
            raise InputValidationError(
                "Input mengandung karakter atau pola yang tidak diizinkan."
            )

    return cleaned


def validate_madhab(madhab: str) -> str:
    """Validasi madhab yang diizinkan."""
    allowed = {"shafii", "hanafi", "maliki", "hanbali"}
    m = madhab.lower().strip()
    if m not in allowed:
        raise InputValidationError(
            f"Madhab '{madhab}' tidak dikenali. Pilihan: {', '.join(sorted(allowed))}."
        )
    return m


if __name__ == "__main__":
    test_cases = [
        ("syahadat itu apa?", True),
        ("hukum shalat", True),
        ("  apa  itu  wudhu  ", True),
        ("", False),
        ("ab", False),
        ("<script>alert(1)</script>", False),
        ("'; DROP TABLE users;--", False),
        ("../../etc/passwd", False),
        ("a" * 501, False),
    ]

    print("=== Validator Test ===\n")
    for text, should_pass in test_cases:
        try:
            result = validate_question(text)
            status = "✅ PASS" if should_pass else "❌ SEHARUSNYA GAGAL"
            print(f"{status}: '{text[:40]}' → '{result[:40]}'")
        except InputValidationError as e:
            status = "✅ BLOCKED" if not should_pass else "❌ SEHARUSNYA LOLOS"
            print(f"{status}: '{text[:40]}' → {e}")
