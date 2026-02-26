"""
Application configuration via environment variables.
Sensitive values (API keys, DB credentials) are NEVER hardcoded.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Settings loaded from environment / .env file."""

    # ── Service ────────────────────────────────────────────
    SERVICE_NAME: str = "python-collector"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Internal API key (shared secret with Node.js gateway) ──
    INTERNAL_API_KEY: str = "changeme-internal-key"

    # ── Redis ──────────────────────────────────────────────
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    PRICE_HISTORY_TTL: int = 86400  # 24 h in seconds

    # ── External API keys (for real sources, optional) ─────
    RAPIDAPI_KEY: str = ""

    # ── Default currency for normalisation ─────────────────
    DEFAULT_CURRENCY: str = "MAD"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton so settings are read only once."""
    return Settings()
