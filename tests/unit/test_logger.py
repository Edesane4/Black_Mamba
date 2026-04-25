"""Logging infrastructure smoke."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import structlog

from black_mamba.observability.logger import (
    bind_correlation_id,
    clear_correlation_context,
    compress_aged_logs,
    configure_logging,
    get_logger,
)


def test_configure_no_file(tmp_path: Path) -> None:
    configure_logging(log_dir=tmp_path, log_to_file=False, log_to_stderr=False)
    log = get_logger("test")
    assert isinstance(log, structlog.stdlib.BoundLogger) or log is not None


def test_configure_writes_file(tmp_path: Path) -> None:
    configure_logging(log_dir=tmp_path, log_to_file=True, log_to_stderr=False)
    log = get_logger("test")
    log.info("phase0_smoke", k="v")
    files = list(tmp_path.glob("black_mamba.log*"))
    assert files, "expected at least one rotated log file"


def test_correlation_id_roundtrip(tmp_path: Path) -> None:
    configure_logging(log_dir=tmp_path, log_to_file=False, log_to_stderr=False)
    bind_correlation_id("abc123", phase="0")
    log = get_logger("test")
    log.info("event")
    clear_correlation_context()


def test_compress_aged_logs_empty_dir(tmp_path: Path) -> None:
    assert compress_aged_logs(tmp_path) == []


def test_compress_aged_logs_compresses_old_files(tmp_path: Path) -> None:
    old = tmp_path / "black_mamba.log.2024-01-01"
    old.write_text("old line\n")
    fresh = tmp_path / "black_mamba.log.2099-01-01"
    fresh.write_text("fresh line\n")
    active = tmp_path / "black_mamba.log"
    active.write_text("active line\n")

    fake_now = datetime.now(UTC) + timedelta(days=365 * 10)
    compressed = compress_aged_logs(tmp_path, age_days=7, now=fake_now)

    assert any(p.name.endswith(".gz") for p in compressed)
    assert not old.exists()
    assert active.exists()  # active file never compressed
