# Operator Runbook

This document is the human-facing operator manual. Filled in across phases —
final form must be complete enough that a stranger could operate Black_Mamba.

## Phase 0 — what works today

- `uv run python -m black_mamba.main --version` prints version.
- `uv run alembic upgrade head` applies the schema to `./data/black_mamba.db`.
- `uv run pytest` passes; `uv run ruff check .` clean; `uv run mypy src tests`
  clean.

Trading, Telegram commands, Obsidian export, and circuit breakers are wired
up in later phases (§B.16). Until then this binary does not place orders.

## Daily operations (post Phase 5+)

TBD.

## Manual exit flow (post Phase 5+)

TBD — see `CLAUDE.md` §B.10.1 for the spec.

## Incident response

See `INCIDENT_LOG.md` for the running log; see `CLAUDE.md` §B.7 for circuit
breakers.

## Credentials rotation

See `CLAUDE.md` §B.20 for the credentials checklist.
