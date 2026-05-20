"""
Application settings loaded from environment / .env file.

Uses Pydantic ``BaseSettings`` for automatic validation, type coercion,
and environment-variable loading with sensible defaults for testnet usage.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# .env lives at project root (two levels above this file)
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Immutable application configuration."""

    # ── Binance credentials ──────────────────────────────────────────
    binance_api_key: str = Field(
        ...,
        description="Binance Futures Testnet API key.",
    )
    binance_api_secret: str = Field(
        ...,
        description="Binance Futures Testnet API secret.",
    )

    # ── Endpoint ─────────────────────────────────────────────────────
    base_url: str = Field(
        default="https://testnet.binancefuture.com",
        description="Binance Futures API base URL.",
    )

    # ── Operational defaults ─────────────────────────────────────────
    default_recv_window: int = Field(
        default=5000,
        ge=1000,
        le=60000,
        description="Maximum milliseconds the request is valid after timestamp.",
    )
    retry_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of retry attempts for transient failures.",
    )
    retry_base_wait: float = Field(
        default=1.0,
        ge=0.1,
        le=30.0,
        description="Base wait time (seconds) for exponential backoff.",
    )
    log_level: str = Field(
        default="INFO",
        description="Application log level.",
    )

    model_config = {
        "env_file": str(_ENV_FILE),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @field_validator("binance_api_key", "binance_api_secret")
    @classmethod
    def _must_not_be_blank(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must not be blank")
        return v.strip()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached, validated :class:`Settings` instance.

    Raises :class:`pydantic.ValidationError` if required env vars are missing.
    """
    return Settings()  # type: ignore[call-arg]
