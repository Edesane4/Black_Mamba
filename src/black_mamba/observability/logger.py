"""Structured JSON logging — §B.9.2.

- JSON output to ./logs/black_mamba.{YYYY-MM-DD}.log (daily-rotated).
- ISO 8601 timestamps with ms precision (UTC).
- Correlation IDs propagated via contextvars.
- 90-day retention; logs older than 7 days gzipped via `compress_aged_logs`.

The orchestrator calls `configure_logging(...)` once at startup, and
`compress_aged_logs(...)` from a scheduled job (wired in later phases).
"""

from __future__ import annotations

import gzip
import logging
import shutil
from datetime import UTC, datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, cast

import structlog
from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    merge_contextvars,
)
from structlog.types import EventDict, Processor


def _add_iso_ms_timestamp(_: object, __: str, event_dict: EventDict) -> EventDict:
    """Replace structlog's default timestamp with ISO 8601 / ms precision UTC."""
    now = datetime.now(UTC)
    event_dict["timestamp"] = (
        now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
    )
    return event_dict


def configure_logging(
    *,
    log_dir: Path | str = Path("./logs"),
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_stderr: bool = True,
    filename_stem: str = "black_mamba",
) -> None:
    """Install structlog + stdlib handlers. Idempotent — safe to call once
    at startup. Test code may set log_to_file=False to keep tmp dirs clean.
    """
    log_dir = Path(log_dir)
    if log_to_file:
        log_dir.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        merge_contextvars,
        structlog.processors.add_log_level,
        _add_iso_ms_timestamp,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.format_exc_info,
        structlog.processors.dict_tracebacks,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root = logging.getLogger()
    root.setLevel(numeric_level)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter("%(message)s")

    if log_to_stderr:
        stream = logging.StreamHandler()
        stream.setLevel(numeric_level)
        stream.setFormatter(formatter)
        root.addHandler(stream)

    if log_to_file:
        log_path = log_dir / f"{filename_stem}.log"
        file_handler = TimedRotatingFileHandler(
            filename=str(log_path),
            when="midnight",
            interval=1,
            backupCount=90,
            utc=True,
            encoding="utf-8",
        )
        # Daily rotation suffix: black_mamba.log.YYYY-MM-DD
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def bind_correlation_id(correlation_id: str, **extra: Any) -> None:
    """Bind a correlation ID (and any extra fields) to the current context.
    Every subsequent log call from this task/thread will carry these fields.
    """
    bind_contextvars(correlation_id=correlation_id, **extra)


def clear_correlation_context() -> None:
    """Clear all bound contextvars. Call at the end of a unit of work."""
    clear_contextvars()


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog bound logger. Pass __name__ for per-module loggers."""
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))


def compress_aged_logs(
    log_dir: Path | str = Path("./logs"),
    *,
    age_days: int = 7,
    now: datetime | None = None,
) -> list[Path]:
    """Gzip rotated log files older than `age_days`. Returns the list of
    files that were compressed. Idempotent — files already ending in .gz
    are skipped. Called by a scheduled job (later phases).
    """
    log_dir = Path(log_dir)
    if not log_dir.is_dir():
        return []

    cutoff = (now or datetime.now(UTC)) - timedelta(days=age_days)
    compressed: list[Path] = []
    for entry in log_dir.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix == ".gz":
            continue
        if entry.name == "black_mamba.log":  # active file
            continue
        # mtime is naive UTC seconds; tzinfo-aware comparison
        mtime = datetime.fromtimestamp(entry.stat().st_mtime, tz=UTC)
        if mtime > cutoff:
            continue
        gz_path = entry.with_suffix(entry.suffix + ".gz")
        with entry.open("rb") as src, gzip.open(gz_path, "wb") as dst:
            shutil.copyfileobj(src, dst)
        entry.unlink()
        compressed.append(gz_path)
    return compressed


__all__ = [
    "bind_correlation_id",
    "clear_correlation_context",
    "compress_aged_logs",
    "configure_logging",
    "get_logger",
]
