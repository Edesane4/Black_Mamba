"""Configuration loading and validation.

Settings are loaded from environment variables (and the optional .env file).
Field names mirror the §B.20 credentials checklist exactly. Defaults match
§B.4.3 / §B.7 where the spec gives them.

Credential fields are Optional in Phase 0 so the package is importable on a
fresh checkout. Mode-specific completeness checks live in `validate_for_mode`,
which the orchestrator calls at startup before any trading-relevant work.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeMode(StrEnum):
    PAPER = "paper"
    LIVE = "live"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # --- Kalshi ---
    KALSHI_API_KEY_ID: str | None = None
    KALSHI_PRIVATE_KEY_PATH: Path | None = None
    KALSHI_API_BASE_URL: str = "https://api.elections.kalshi.com/trade-api/v2"
    KALSHI_WS_URL: str = "wss://api.elections.kalshi.com/trade-api/ws/v2"
    KALSHI_MODE: RuntimeMode = RuntimeMode.PAPER

    # --- Weather data sources ---
    NWS_USER_AGENT: str = "BlackMamba/1.0 (contact@example.com)"
    SYNOPTIC_API_TOKEN: SecretStr | None = None

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: SecretStr | None = None
    TELEGRAM_OPERATOR_CHAT_ID: int | None = None

    # --- Obsidian ---
    OBSIDIAN_VAULT_PATH: Path | None = None

    # --- Storage / runtime ---
    DATABASE_URL: str = "sqlite:///./data/black_mamba.db"
    LOG_LEVEL: LogLevel = LogLevel.INFO

    # --- Mode ---
    BLACK_MAMBA_MODE: RuntimeMode = RuntimeMode.PAPER
    BLACK_MAMBA_STARTING_BALANCE: float = Field(default=1000.0, ge=0)

    # --- Risk parameters (§B.4.3 / §B.7) ---
    DAILY_LOSS_CIRCUIT_BREAKER_PCT: float = Field(default=12.0, gt=0, le=100)
    MAX_TOTAL_EXPOSURE_PCT: float = Field(default=40.0, gt=0, le=100)
    MIN_TRADE_DOLLARS: float = Field(default=25.0, ge=0)

    def validate_for_mode(self, mode: Literal["paper", "live"] | None = None) -> list[str]:
        """Return a list of missing-field errors for the given mode.

        Called by the orchestrator at startup, not at Settings construction.
        Empty list = ready to run in that mode.
        """
        target = mode or self.BLACK_MAMBA_MODE.value
        errors: list[str] = []

        if self.BLACK_MAMBA_MODE != self.KALSHI_MODE:
            errors.append(
                f"Mode mismatch: BLACK_MAMBA_MODE={self.BLACK_MAMBA_MODE.value} "
                f"vs KALSHI_MODE={self.KALSHI_MODE.value}"
            )

        if target == "live":
            if not self.KALSHI_API_KEY_ID:
                errors.append("KALSHI_API_KEY_ID required for live mode")
            if not self.KALSHI_PRIVATE_KEY_PATH:
                errors.append("KALSHI_PRIVATE_KEY_PATH required for live mode")
            elif not self.KALSHI_PRIVATE_KEY_PATH.is_file():
                errors.append(
                    f"KALSHI_PRIVATE_KEY_PATH does not exist: {self.KALSHI_PRIVATE_KEY_PATH}"
                )
            if not self.TELEGRAM_BOT_TOKEN:
                errors.append("TELEGRAM_BOT_TOKEN required for live mode")
            if self.TELEGRAM_OPERATOR_CHAT_ID is None:
                errors.append("TELEGRAM_OPERATOR_CHAT_ID required for live mode")
            if not self.OBSIDIAN_VAULT_PATH:
                errors.append("OBSIDIAN_VAULT_PATH required for live mode")

        return errors


def load_settings() -> Settings:
    """Load settings from environment / .env. Construction does not validate
    completeness for the runtime mode — call `Settings.validate_for_mode` for
    that.
    """
    return Settings()
