# config.py
# IslamiAI - Environment Configuration
# Pattern: 12-factor app. Semua nilai sensitif dari environment variable.

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    # ── Server ────────────────────────────────────────────────
    HOST: str = os.getenv("ISLAMIAI_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("ISLAMIAI_PORT", "1928"))
    DEBUG: bool = os.getenv("ISLAMIAI_DEBUG", "false").lower() == "true"

    # ── Security ─────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("ISLAMIAI_SECRET_KEY", "dev-insecure-key-CHANGE-IN-PROD")
    SESSION_COOKIE_SECURE: bool = not DEBUG
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    WTF_CSRF_ENABLED: bool = True

    # ── Rate Limiting ─────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))

    # ── Input Validation ──────────────────────────────────────
    MAX_QUESTION_LENGTH: int = 500
    MIN_QUESTION_LENGTH: int = 3

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "islamiai.log")

    # ── Content ───────────────────────────────────────────────
    DEFAULT_MADHAB: str = "shafii"
    MIN_CONFIDENCE_SCORE: float = 0.5  # threshold untuk reasoning layer

    def validate(self):
        """Gagal keras jika konfigurasi production tidak aman."""
        if not self.DEBUG and self.SECRET_KEY == "dev-insecure-key-CHANGE-IN-PROD":
            raise EnvironmentError(
                "ISLAMIAI_SECRET_KEY harus diset di environment production. "
                "Jangan gunakan default key."
            )
        return self


config = Config()


if __name__ == "__main__":
    try:
        config.validate()
        print("✅ Config valid (DEBUG mode — production check dilewati)")
    except EnvironmentError as e:
        print(f"❌ Config error: {e}")

    print(f"   HOST      : {config.HOST}")
    print(f"   PORT      : {config.PORT}")
    print(f"   DEBUG     : {config.DEBUG}")
    print(f"   RATE LIMIT: {config.RATE_LIMIT_PER_MINUTE} req/min")
    print(f"   LOG LEVEL : {config.LOG_LEVEL}")
