# Black_Mamba

Autonomous trading agent that exploits a structural latency arbitrage in
Kalshi's daily high-temperature markets for **Los Angeles (KLAX)**,
**San Francisco (KSFO)**, and **Phoenix (KPHX)**.

The strategy, risk rules, and operator responsibilities are defined in
[`CLAUDE.md`](./CLAUDE.md). That document is the contract; this README is a
quick start.

## Status

**Phase 0 — Foundation.** Skeleton, config, DB schema, logging, CI in place.
Trading logic is not yet implemented. See §B.16 in `CLAUDE.md` for the
full build order.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`pip install uv` or
  `curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Setup

```bash
uv sync --extra dev
cp .env.example .env  # fill in credentials when ready
```

## Operator commands

```bash
# Verify install
uv run python -m black_mamba.main --version

# Apply DB migrations
uv run alembic upgrade head

# Lint, typecheck, tests
uv run ruff check .
uv run mypy src tests
uv run pytest
```

Live trading and Telegram operator commands are wired up in later phases —
see `CLAUDE.md` §B.10 and §B.16.
