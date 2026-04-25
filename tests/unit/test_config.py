"""Config loading + mode validation."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from black_mamba.config import RuntimeMode, Settings


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Wipe Black_Mamba env vars and point cwd at a tmp dir so .env doesn't leak in."""
    prefixes = (
        "KALSHI_", "BLACK_MAMBA_", "TELEGRAM_", "OBSIDIAN_", "NWS_", "SYNOPTIC_",
    )
    for key in list(os.environ):
        if key.startswith(prefixes):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.chdir(tmp_path)


def test_defaults_load() -> None:
    s = Settings()
    assert s.KALSHI_MODE == RuntimeMode.PAPER
    assert s.BLACK_MAMBA_MODE == RuntimeMode.PAPER
    assert s.MAX_TOTAL_EXPOSURE_PCT == 40.0
    assert s.DAILY_LOSS_CIRCUIT_BREAKER_PCT == 12.0
    assert s.MIN_TRADE_DOLLARS == 25.0
    assert s.DATABASE_URL.startswith("sqlite:")


def test_paper_mode_no_errors() -> None:
    s = Settings()
    assert s.validate_for_mode("paper") == []


def test_live_mode_reports_missing_credentials() -> None:
    s = Settings()
    errors = s.validate_for_mode("live")
    assert any("KALSHI_API_KEY_ID" in e for e in errors)
    assert any("KALSHI_PRIVATE_KEY_PATH" in e for e in errors)
    assert any("TELEGRAM_BOT_TOKEN" in e for e in errors)
    assert any("TELEGRAM_OPERATOR_CHAT_ID" in e for e in errors)
    assert any("OBSIDIAN_VAULT_PATH" in e for e in errors)


def test_mode_mismatch_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLACK_MAMBA_MODE", "live")
    monkeypatch.setenv("KALSHI_MODE", "paper")
    s = Settings()
    errors = s.validate_for_mode()
    assert any("Mode mismatch" in e for e in errors)
