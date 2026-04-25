# Kalshi API Notes

Quirks, rate limits, and edge cases discovered during development. Filled in
during Phase 2.

## Endpoints in use

- REST base: `https://api.elections.kalshi.com/trade-api/v2`
- WS base: `wss://api.elections.kalshi.com/trade-api/ws/v2`

## Auth

RSA-PSS request signing — see `src/black_mamba/kalshi/auth.py` (Phase 2).

## Rate limits

TBD — track per-endpoint and document throttling thresholds (§B.6.5).

## Quirks

TBD.
