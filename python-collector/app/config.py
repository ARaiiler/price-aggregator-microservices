"""
Application configuration.

All settings are loaded exclusively from environment variables so that
no secrets or environment-specific values are ever hardcoded.

Redis URL resolution
--------------------
Two notations are supported, checked in priority order:

1. ``REDIS_URL`` (full URL, e.g. ``redis://:secret@redis:6379/0``) —
   takes precedence when set.
2. ``REDIS_HOST`` + ``REDIS_PORT`` + ``REDIS_PASSWORD`` —
   assembled automatically when ``REDIS_URL`` is absent.  This is the
   preferred notation for Docker Compose and Kubernetes environments
   where each credential lives in its own variable.
"""
from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ------------------------------------------------------------------ #
    # Service metadata
    # ------------------------------------------------------------------ #
    service_name: str = Field(default="python-collector", alias="SERVICE_NAME")
    service_version: str = Field(default="1.0.0", alias="SERVICE_VERSION")
    environment: str = Field(default="production", alias="ENVIRONMENT")

    # ------------------------------------------------------------------ #
    # Server
    # ------------------------------------------------------------------ #
    host: str = Field(default="0.0.0.0", alias="HOST")
    # Accepts SERVICE_PORT (preferred in Docker) or PORT (generic fallback).
    port: int = Field(
        default=8000,
        validation_alias=AliasChoices("SERVICE_PORT", "PORT"),
    )
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    # ------------------------------------------------------------------ #
    # Redis — individual parts (preferred)
    # ------------------------------------------------------------------ #
    # REDIS_HOST and REDIS_PORT are the canonical way to configure Redis in
    # this service.  They are assembled into redis_url by the validator
    # below unless REDIS_URL is supplied directly.
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    # Optional password — leave blank when Redis runs without auth (dev only).
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")

    # ------------------------------------------------------------------ #
    # Redis — full URL (optional override)
    # ------------------------------------------------------------------ #
    # When REDIS_URL is set it takes precedence over the individual parts
    # above.  Leave unset to let the validator build it automatically.
    redis_url: str = Field(default="", alias="REDIS_URL")

    # Default TTL for cached search results (seconds)
    cache_ttl_seconds: int = Field(default=3600, alias="CACHE_TTL_SECONDS")
    # TTL for latest_price:{name} keys — 10 minutes
    latest_price_ttl_seconds: int = Field(default=600, alias="LATEST_PRICE_TTL_SECONDS")

    # ------------------------------------------------------------------ #
    # Scraper behaviour
    # ------------------------------------------------------------------ #
    # Maximum time (seconds) to wait for a single source scrape
    scraper_timeout_seconds: float = Field(
        default=10.0, alias="SCRAPER_TIMEOUT_SECONDS"
    )
    # Minimum number of sources that must respond before returning a result
    min_sources_required: int = Field(default=2, alias="MIN_SOURCES_REQUIRED")

    model_config = {"env_file": ".env", "extra": "ignore", "populate_by_name": True}

    # ------------------------------------------------------------------ #
    # Computed fields
    # ------------------------------------------------------------------ #

    @model_validator(mode="after")
    def build_redis_url(self) -> "Settings":
        """
        If ``REDIS_URL`` was not supplied, assemble it from
        ``REDIS_HOST``, ``REDIS_PORT``, and optionally ``REDIS_PASSWORD``.

        This runs after all individual fields have been validated so
        redis_url is always populated before the first cache connection
        is attempted.
        """
        if not self.redis_url:
            if self.redis_password:
                self.redis_url = (
                    f"redis://:{self.redis_password}"
                    f"@{self.redis_host}:{self.redis_port}/0"
                )
            else:
                self.redis_url = (
                    f"redis://{self.redis_host}:{self.redis_port}/0"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using @lru_cache means the .env file is parsed exactly once per
    interpreter lifecycle, which is safe for production usage.
    """
    return Settings()
