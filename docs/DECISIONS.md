# Architectural Decisions Log

Append-only record of non-obvious design choices. Each entry: date, decision,
rationale, alternatives considered.

---

## 2026-04-25 — Phase 0 scaffold

### Package layout: `src/`

Package lives at `src/black_mamba/` (PEP 517 / hatchling src layout). Matches the
file tree in `CLAUDE.md` §B.3 and prevents the common pitfall of importing the
in-repo package instead of the installed one during tests.

### Phase 0 dependencies are minimal

`pyproject.toml` declares only what Phase 0 needs (pydantic-settings,
sqlalchemy, alembic, structlog) plus dev tooling (pytest, ruff, mypy). Per
behavioral guideline §A.2, later phases will add their own deps as they are
built — no speculative inclusion of httpx, websockets, python-telegram-bot, etc.

### Settings credentials are Optional in v1

Per §B.20, several credentials are required to trade live. Making the
`Settings` class enforce them at construction time would prevent the package
from importing on a fresh checkout (and break `--version`). Instead, fields are
typed `T | None` and a `validate_for_mode("paper" | "live")` method returns the
list of missing fields; the orchestrator calls it at startup before any
trading-relevant work. This keeps construction cheap and validation explicit.

### Log rotation strategy

`TimedRotatingFileHandler` rotates daily at UTC midnight, keeping 90 days
(`backupCount=90`). Per §B.9.2, files older than 7 days should be gzipped.
Rather than a custom `rotator` callable that compresses immediately at
rollover, we provide a separate `compress_aged_logs()` function to be called
on a scheduled job. Reason: this preserves the "uncompressed for 7 days, then
gzipped" semantics literally. The scheduled job is wired up in Phase 5
(observability) when the orchestrator gets its scheduling loop.

### Initial migration is a single revision

All 10 tables from §B.9.1 created in `0001_initial_schema.py`. Subsequent
schema changes get their own revisions. ORM column names match the spec
language; field details (e.g., `*_cents` for prices, JSON for raw payloads)
are conservative defaults.

### CI uses uv

`astral-sh/setup-uv@v3` is the path of least resistance for the `uv`-based
local dev workflow. No fallback `pip install` path — the spec says uv (§B.14).
