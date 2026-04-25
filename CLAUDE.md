# CLAUDE.md

> **You (Claude Code) are the senior engineer building Black_Mamba.** This document has two parts: behavioral guidelines (Part A) that govern *how* you work, and the project contract (Part B) that defines *what* you build. Read both fully before writing any code.

---

# PART A — Behavioral Guidelines

Behavioral guidelines to reduce common LLM coding mistakes.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## A.1 Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them. Don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## A.2 Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## A.3 Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it. Don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

## A.4 Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## A.5 Project-Specific Discipline (Black_Mamba)

In addition to the above, these rules apply to this project specifically:

- **No silent deviation from Part B.** If the spec is wrong or unclear, stop and propose a change to this document via PR. Don't quietly do it differently.
- **No ML, no probabilistic forecasting.** This is a deterministic system. If you find yourself wanting to add a model that "predicts" something, stop — the answer is wrong.
- **No financial-style cleverness.** Don't add hedges, baskets, or "improvements" to the trading logic. The strategy is exactly what's specified in §B.4. Nothing more.
- **Conservative on ambiguity.** When two interpretations exist for a risk parameter, choose the one that risks less capital. Document the choice.
- **Stop at phase boundaries.** Build order in §B.16 has 8 phases. After each, stop and report. Do not start the next phase until told.

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

# PART B — Project Contract: Black_Mamba

## B.1 Mission

Black_Mamba is an autonomous trading agent that exploits a structural latency arbitrage in Kalshi's daily high-temperature markets across **Los Angeles (KLAX), San Francisco (KSFO), and Phoenix (KPHX)**. The edge: NWS publishes live observations on a 5-15 minute lag, while Kalshi order books are populated by retail traders watching forecast products (weather.com, AccuWeather) rather than live obs. When observed temperature has already crossed into a bucket that the order book is still pricing as "live," Black_Mamba buys NO contracts on the dead bucket at ≤97¢ and immediately posts an exit limit at 99¢.

**The agent does not forecast weather.** It compares two numbers: (a) the most recent confirmed observed temperature at the Kalshi-graded station, and (b) the implied probability of each bucket in Kalshi's order book. When (a) makes a bucket deterministically dead and (b) hasn't repriced, Black_Mamba acts.

**The agent has no discretion.** Every trade decision is a deterministic function of inputs. There is no "model says 87% confident" — there is "observation crossed bucket ceiling for ≥2 consecutive intervals AND forecast headroom present AND order book mispriced AND time-of-day in window AND no platform anomalies." All conditions must be true. If any condition is false or ambiguous, the agent does not trade.

**The agent always exits at 99¢ automatically.** The operator (human-in-the-loop project manager) is the only party who manually exits a winning position below 99¢. Manual exits are first-class supported via Telegram commands (see §B.10) and are recorded distinctly from automated exits in the learning system (see §B.11).

## B.2 Core Principles (Non-Negotiable)

1. **Determinism over inference.** No ML, no probabilistic model output drives a trade. Every fire is a boolean expression of measured facts.
2. **Verify before you trade. Reconcile after.** Every position has a verification step pre-trade and a reconciliation step post-settlement.
3. **Bound the worst case, not the average case.** Sizing, exposure caps, and circuit breakers are designed to survive the worst day, not optimize the median day.
4. **Multiple data sources for any fact that drives a trade.** Single-source data is a single point of failure. Use redundancy with explicit reconciliation.
5. **Log everything, immutably.** Every API call, every observation, every order book snapshot, every fill, every settlement, every rejection — timestamped to millisecond, stored append-only.
6. **Paper trade before live trade.** No live trading until 14 consecutive days of paper trading show the system performs as specified with zero unhandled exceptions.
7. **Fail closed, not open.** Any unrecognized state, any data inconsistency, any heartbeat miss, any unparseable response — close all open positions, halt new trades, alert the operator.
8. **Automated exits at 99¢; manual exits below.** The agent never sells a winning position below 99¢ on its own. Only the operator does that, via explicit Telegram command.

## B.3 Repository Structure

```
black_mamba/
├── CLAUDE.md                          # This file — the contract
├── README.md                          # Operator-facing docs
├── pyproject.toml                     # Python project config (uv)
├── .env.example                       # Template for credentials (real .env is gitignored)
├── .gitignore
├── docker-compose.yml                 # Optional: redis + postgres if used
│
├── src/black_mamba/
│   ├── __init__.py
│   ├── main.py                        # Entrypoint, orchestrator
│   ├── config.py                      # Pydantic settings, loads .env
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── cities.py                  # Day-one trading universe (LAX/SFO/PHX): station, tz, source priority
│   │   ├── nws_api.py                 # api.weather.gov client
│   │   ├── metar_direct.py            # tgftp.nws.noaa.gov direct METAR fetch
│   │   ├── synoptic.py                # Synoptic Data PBC fallback (MesoWest)
│   │   ├── hires_asos.py              # weather.gov/psr/HiResASOS scraper for KPHX
│   │   ├── observation.py             # Unified Observation dataclass + reconciler
│   │   └── poller.py                  # Async poller, runs N sources concurrently
│   │
│   ├── kalshi/
│   │   ├── __init__.py
│   │   ├── auth.py                    # RSA-PSS request signing
│   │   ├── rest_client.py             # REST wrapper for non-time-critical ops
│   │   ├── ws_client.py               # WebSocket client for live order books
│   │   ├── markets.py                 # Market discovery, series resolution
│   │   ├── rules_scraper.py           # Pulls market rules daily, verifies grading station
│   │   ├── orders.py                  # Order placement / cancellation / modification
│   │   ├── portfolio.py               # Balance, positions, fills
│   │   └── models.py                  # Pydantic models for Kalshi objects
│   │
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── bucket_analyzer.py         # Computes dead/live status per bucket per market
│   │   ├── signal.py                  # Signal generation: dead bucket + mispriced + window
│   │   ├── tier_classifier.py         # Classifies signals into Tier 1/2/3
│   │   └── settlement_scalper.py      # Secondary module — late-day theta scalp
│   │
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── sizer.py                   # Tiered sizing logic
│   │   ├── exposure.py                # Portfolio exposure tracking
│   │   ├── circuit_breakers.py        # Daily loss, position count, anomaly halts
│   │   └── kelly.py                   # Fractional Kelly calculator
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── state_machine.py           # Position state machine (see §B.8)
│   │   ├── executor.py                # Order placement + immediate exit limit posting
│   │   ├── manual_exit.py             # Operator-driven exit handler
│   │   ├── slippage_model.py          # Learns realized slippage per market/time
│   │   └── reconciler.py              # Post-settlement P&L reconciliation
│   │
│   ├── learning/
│   │   ├── __init__.py
│   │   ├── feedback.py                # The three feedback loops (§B.11)
│   │   ├── retracement_stats.py       # Per-station retracement base rates
│   │   ├── reprice_latency.py         # How long after NWS print does Kalshi book move
│   │   └── fill_quality.py            # Realized vs expected entry price
│   │
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── logger.py                  # Structured JSON logging
│   │   ├── telegram.py                # Bot — alerts AND command interface
│   │   ├── obsidian.py                # Daily journal export to vault
│   │   ├── heartbeat.py               # Dead-man's switch
│   │   └── dashboard.py               # Optional: simple FastAPI status endpoint
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── db.py                      # SQLAlchemy + SQLite (default) or Postgres
│   │   ├── models.py                  # ORM models
│   │   └── migrations/                # Alembic migrations
│   │
│   └── backtest/
│       ├── __init__.py
│       ├── replay.py                  # Replay historical NWS + Kalshi snapshots
│       └── analyzer.py                # Performance analysis of replayed trades
│
├── tests/
│   ├── unit/                          # Per-module unit tests
│   ├── integration/                   # End-to-end with mocked Kalshi + NWS
│   ├── fixtures/                      # Sample API responses, historical data
│   └── scenarios/                     # Specific historical days to validate against
│
├── scripts/
│   ├── paper_trade.py                 # Run in paper mode
│   ├── backtest.py                    # Run backtest over date range
│   ├── verify_grading_sources.py      # Daily check of Kalshi rules
│   ├── watchdog.py                    # Heartbeat watchdog (separate process)
│   └── reconcile.py                   # Manual reconciliation tool
│
└── docs/
    ├── DECISIONS.md                   # Architectural decisions log
    ├── RUNBOOK.md                     # Operator runbook
    ├── INCIDENT_LOG.md                # Operator-maintained incident log
    └── KALSHI_API_NOTES.md            # Quirks, rate limits, edge cases
```

## B.4 Strategy Specification (Exact Trading Logic)

### B.4.1 Markets in scope

Day-one cities, as confirmed by Kalshi's published grading stations:

| City | Series Ticker (verify on launch) | Graded Station | Data Source Priority |
|---|---|---|---|
| Los Angeles | `KXHIGHLAX` | KLAX | NWS API → METAR direct → Synoptic |
| San Francisco | `KXHIGHSF` (verify exact ticker via `series` endpoint) | KSFO | NWS API → METAR direct → Synoptic |
| Phoenix | `KXHIGHPHX` | KPHX | **High-Res ASOS first (weather.gov/psr/HiResASOS) → NWS API → METAR direct** |

**Phoenix-specific rule:** Standard 5-min ASOS reports in whole degrees Celsius, then converts to F, producing rounding artifacts. KPHX **must** be primarily polled from the high-resolution ASOS feed which reports rolling 5-min averages directly in whole F. NWS API and METAR direct are confirmation sources, not primary.

### B.4.2 The trade

A signal fires when **all** of the following are true for a given bucket B in market M:

```
SIGNAL_CONDITIONS = (
    observed_temp_confirmed >= bucket_ceiling(B)
    AND observation_count_at_or_above_ceiling >= 2 (consecutive 5-min intervals)
    AND most_recent_observation_age_seconds <= 900
    AND bucket_no_ask_price <= 97  (cents)
    AND bucket_no_ask_price >= 50  (cents — sanity floor; if below 50¢ something is wrong)
    AND order_book_depth_at_ask >= position_size_contracts
    AND time_local IN [11:00, 15:00] (city-local time, configurable per city)
    AND forecast_high_for_today >= bucket_ceiling(B) + 2  (degrees F)
    AND grading_station_verified_today == True
    AND no_active_circuit_breaker == True
    AND no_observation_anomaly_flag == True
    AND market_status == "active"
    AND no_kalshi_halt_or_warning == True
)
```

When the conjunction is true, fire **immediately** (target ≤500ms from signal evaluation to order submission). Place a limit buy on NO contracts at the current best ask (capped at 97¢). Immediately upon fill confirmation, place a limit sell at 99¢ for the full position.

**The agent always posts the exit at 99¢. Never lower.** If the operator wants to exit below 99¢, they do it manually via Telegram (§B.10.1).

### B.4.3 Tier classification (drives sizing)

Tiers are evaluated at signal time and never upgraded after entry.

**Tier 1 — Standard (8% of portfolio):**
- Observation ≥ bucket ceiling for 2 consecutive intervals
- Forecast headroom ≥ 2°F
- Time of day in window
- Order book depth adequate
- All anomaly flags clear

**Tier 2 — High Confidence (12% of portfolio):**
- All Tier 1 conditions
- Observation ≥ bucket ceiling for 3 consecutive intervals
- Forecast headroom ≥ 3°F
- Time of day in 11:00–14:00 (peak retail-asleep window)
- Cross-source observation agreement (≥2 of 3 sources confirm)

**Tier 3 — Locked (18% of portfolio):**
- All Tier 2 conditions
- Observed temperature ≥ bucket_ceiling + 2°F
- NWS reported `max_temp_today_so_far` field already shows ≥ bucket_ceiling
- All 3 data sources agree to within 1°F
- Station status nominal (no QC flags, no recent gaps)
- Forecast headroom ≥ 4°F

**Hard caps (override all sizing):**
- Maximum simultaneous deployment across all open positions: **40% of portfolio**
- Maximum positions per single market (event): **1**
- Maximum positions per city per day: **3** (one per dead-bucket as temp climbs)
- Daily realized loss circuit breaker: **12%** → halt all new entries until next trading day + operator review
- Per-trade dollar floor: **$25** (don't fire if 8% sizing produces less)

### B.4.4 Settlement scalper (secondary module)

After the primary window, deploy unused capital in the last 60–90 minutes before NWS daily high is effectively locked:

- Bucket NO ask available at ≤97¢
- Bucket is dead per current observed temp
- Time within 90 minutes of typical daily-high lock for that city
- Sizing: Tier 1 only (8%)
- Skip if total exposure cap (40%) reached

### B.4.5 Forbidden trades

Black_Mamba must **never** without an explicit code change reviewed by the operator:

- Buy YES contracts (the inverse latency arb is held in reserve per §B.15)
- Trade markets outside LAX, SF, PHX in v1
- Trade non-temperature markets
- Average down on a losing position
- Hold a position past its market's settlement
- Trade during a known platform halt or after a circuit-breaker trip
- Submit market orders (always limit orders)
- **Sell a winning position below 99¢ automatically.** Only the operator does that, manually.

### B.4.6 Note on CLI vs METAR settlement

Kalshi grades on the NWS Daily Climate Report (CLI), not the 5-min METAR feed Black_Mamba polls. They have a clause allowing voiding/delay when METAR and CLI disagree.

**For this strategy, this is a tail-of-tail risk.** Black_Mamba only trades buckets that are 3-4°F below the current observed temperature, meaning a CLI revision would have to disagree with METAR by 3-4°F to flip the trade — a major QC event, not a routine adjustment. The existing source agreement and retracement circuit breakers cover the realistic failure modes. No additional logic required for this edge case beyond the existing breakers.

## B.5 Data Layer

### B.5.1 Source hierarchy

For each city, all sources are queried concurrently. The "confirmed observation" is computed as follows:

1. Pull all sources concurrently with 3-second timeout each.
2. Drop sources that returned errors or stale data (>15 min old).
3. If ≥2 sources agree within 1°F → confirmed = median.
4. If only 1 source available → confirmed = that value, but flag `single_source=True` (disqualifies Tier 2/3).
5. If sources disagree by >1°F → flag `source_disagreement=True`, do not fire any new trades for that city until next reconciliation.

### B.5.2 Polling cadence

- **Default:** every 60 seconds during a city's active window (11am–3pm local).
- **Aggressive mode:** every 30 seconds during 12pm–2pm local (peak edge window).
- **Idle:** every 5 minutes outside active window (for settlement scalper freshness).

Use `httpx.AsyncClient` with connection pooling. Set `User-Agent` per NWS terms.

### B.5.3 Anomaly detection on observations

Reject any observation that:
- Differs from the previous observation by >5°F in 5 minutes.
- Carries any NWS QC flag.
- Has timestamp >15 minutes stale.
- Disagrees with sibling sources by >2°F.

When anomaly detected: flag the city as `observation_anomaly=True` for one polling cycle. Re-test on next cycle. If anomaly persists for 3 consecutive cycles, alert operator and disable city until manual reset.

### B.5.4 Kalshi grading source verification

Every morning at 06:00 UTC, `rules_scraper.py` runs:

1. Pull market rules for each active market in scope.
2. Parse rules text for grading station identifier.
3. Compare to expected: KLAX, KSFO, KPHX.
4. If mismatch: disable that city for the day, alert operator, log incident.
5. If match: log success, set `grading_station_verified_today=True`.

The agent will not fire any trade in a city where verification has not succeeded that calendar day.

## B.6 Kalshi Integration

### B.6.1 Authentication

Kalshi uses RSA-PSS signed requests. Key handling in `kalshi/auth.py`. Private key loaded from `.env` (path to PEM). Never log the key. Never include the key in any artifact uploaded to Obsidian.

### B.6.2 REST + WebSocket hybrid

- **REST** for: market discovery, balance, positions, order placement, order cancellation, order modification, market rules.
- **WebSocket** for: live order book updates on every market in scope.

WS gives sub-second order book state, which is what enables ≤500ms signal-to-fire latency.

### B.6.3 Order placement

Entry:
```python
order_id = kalshi.place_order(
    ticker=market.ticker,
    side="no",
    action="buy",
    type="limit",
    price_cents=ask_price,
    count=position_size_contracts,
    client_order_id=uuid(),
    time_in_force="IOC"
)
```

Exit (immediate post on fill confirmation):
```python
exit_id = kalshi.place_order(
    ticker=market.ticker,
    side="no",
    action="sell",
    type="limit",
    price_cents=99,
    count=filled_count,
    client_order_id=uuid(),
    time_in_force="GTC"
)
```

If entry partial-fills, exit sized to actual filled count. Unfilled portion logged but not retried in same cycle.

### B.6.4 Order modification (for manual exits)

When operator triggers a manual exit (§B.10.1), the executor:

1. Cancels the existing 99¢ exit limit via `kalshi.cancel_order(exit_id)`.
2. Places a new limit sell at the operator-specified price.
3. Updates position state to `MANUAL_EXIT_POSTED`.
4. Logs the override with operator-provided reason (if given).

Cancel failures are escalated to operator immediately — never silently retry, never assume the cancel succeeded.

### B.6.5 Rate limit handling

- Exponential backoff on 429.
- Track per-endpoint rate, throttle proactively at 80% of documented limit.
- Sustained rate-limiting → alert operator and reduce polling cadence.

## B.7 Risk Management

### B.7.1 Position sizing

```python
def size_position(tier: Tier, portfolio: Portfolio, ask_price_cents: int) -> int:
    pct_map = {Tier.ONE: 0.08, Tier.TWO: 0.12, Tier.THREE: 0.18}
    pct = pct_map[tier]

    available_pct = min(pct, MAX_TOTAL_EXPOSURE - portfolio.deployed_pct)
    if available_pct <= 0:
        return 0

    capital_at_risk = portfolio.cash_balance * available_pct
    if capital_at_risk < MIN_TRADE_DOLLARS:
        return 0

    contracts = int(capital_at_risk * 100 / ask_price_cents)
    contracts = min(contracts, available_book_depth_at_ask)
    return contracts
```

### B.7.2 Circuit breakers

Each is checked before every signal fire and on every fill.

| Breaker | Trigger | Action |
|---|---|---|
| Daily loss | Realized + unrealized P&L for day ≤ -12% of starting balance | Halt new entries, hold existing to settlement, alert |
| Per-trade loss | Single position closed at -100% of premium | Increment counter; if ≥2 in one day, halt new entries |
| Total exposure | Sum of (open positions × premium paid) > 40% of portfolio | Block new signals until exposure decreases |
| Source disagreement | >2°F divergence between data sources for one city | Halt that city's new entries until next reconciliation |
| Grading mismatch | Daily verification fails | Halt that city for the calendar day |
| Heartbeat | No data poll completed in 5 minutes | Halt new entries; if 15 min, cancel all open orders |
| Anomaly streak | 3 consecutive anomalous obs in one city | Halt that city until manual reset |
| API error rate | >10% Kalshi API errors in last 5 min | Halt new entries, alert |

### B.7.3 Daily reconciliation

At 23:00 local NYC time, run `reconciler.py`:

1. Fetch Kalshi reported balance and recent settlements.
2. Compare to local position ledger.
3. Any discrepancy ≥ $0.50 → flag, alert, write to `INCIDENT_LOG.md`.
4. Compute realized P&L for the day.
5. Update learning loops (§B.11).
6. Generate Obsidian journal entry (§B.10.2).

## B.8 Execution: Position State Machine

Every position progresses through explicit states. The state machine is the source of truth.

```
SIGNALED → ORDER_PLACED → FILLED → EXIT_POSTED ──→ EXITED → SETTLED → RECONCILED
                ↓             ↓          ↓                     │
            REJECTED      CANCELLED   FAILED                   │
                                         ↓                     │
                                     ESCALATED                 │
                                                               │
            ┌──────────────────────────────────────────────────┘
            │
            ▼  (operator command via Telegram)
   MANUAL_EXIT_POSTED → MANUAL_EXITED → RECONCILED
```

State transitions are persisted to the database immediately. The orchestrator is restartable: on restart, it loads all non-terminal positions and resumes management.

States:
- **SIGNALED**: Signal evaluated, sizing computed, about to place order
- **ORDER_PLACED**: Entry order submitted, awaiting fill
- **FILLED**: Entry fill confirmed, about to post exit
- **EXIT_POSTED**: Automated 99¢ exit limit live on order book
- **EXITED**: 99¢ exit filled (automated profit)
- **MANUAL_EXIT_POSTED**: Operator-triggered exit limit (below 99¢) live
- **MANUAL_EXITED**: Manual exit filled (operator-driven profit)
- **SETTLED**: Market settled with NO graded YES — paid out at 100¢ (held to settlement)
- **RECONCILED**: Local ledger matches Kalshi reported settlement
- **REJECTED**: Order rejected by Kalshi
- **CANCELLED**: We cancelled before fill
- **FAILED**: NO graded NO (bucket settled YES against us)
- **ESCALATED**: Anomaly requires human review

**Important:** any winning P&L outcome that closes below 99¢ implies a MANUAL_EXITED state. The agent never produces sub-99¢ winning closes through automated logic.

## B.9 Storage & Logging

### B.9.1 Database

**Default:** SQLite at `./data/black_mamba.db`. **Production option:** PostgreSQL via env flag.

Tables:
- `observations` — all weather observations, all sources, all timestamps
- `order_book_snapshots` — periodic and event-driven snapshots
- `signals` — every signal evaluation, including non-fires (with reason)
- `positions` — full lifecycle of every position
- `orders` — every order submitted, with response and outcome
- `manual_overrides` — every operator-driven action with reason
- `settlements` — Kalshi-reported settlements
- `reconciliations` — daily reconciliation results
- `circuit_breaker_events` — every breaker trip
- `incidents` — anomalies, source disagreements, manual interventions

Use Alembic migrations. Never alter schema without a migration.

### B.9.2 Logging

- Structured JSON logs to `./logs/black_mamba.{YYYY-MM-DD}.log`
- INFO default; DEBUG via env flag
- Every line: timestamp (ISO 8601 ms), module, level, event_type, correlation_id, payload
- Correlation IDs propagate signal → order → fill → exit → settlement
- Rotate: keep 90 days, gzip after 7

## B.10 Observability: Telegram + Obsidian + Heartbeat

### B.10.1 Telegram (alerts AND command interface)

**Outbound alerts** (severity-tagged):

- 🟢 Trade fired — ticker, tier, size, ask, expected exit at 99¢
- 🟢 Trade exited at 99¢ — ticker, P&L
- 🟢 Manual exit confirmed — ticker, exit price, P&L, operator reason
- 🟡 Tier 3 signal evaluated but not fired — reason
- 🟡 Position settled at 100¢ instead of exited (held to settlement)
- 🔴 Circuit breaker tripped — which one, reason
- 🔴 Anomaly detected — which city, what kind
- 🔴 Reconciliation discrepancy — amount, position
- 🔴 Manual exit cancel failed — escalate to operator immediately
- 🔴 Heartbeat lost
- 📊 End-of-day summary — trades, P&L (auto vs manual), win rate, balance

**Inbound commands** (operator → bot):

- `/status` — current portfolio, deployed capital, open positions
- `/positions` — list all open positions with tier and current P&L
- `/positions detail` — open positions with current bid/ask, time-in-position, recommended exit indicator
- `/exit <ticker> <price_cents> [reason]` — manually exit a position at a specified price below 99¢. Bot replies with confirmation request showing current bid/ask and position details. Operator must reply `confirm` within 30 seconds or the command is dropped.
- `/exit_all <price_cents> [reason]` — manual exit all open positions at specified prices (or "best_bid" to use current bid). Confirmation required.
- `/pause` — halt new entries; existing positions managed normally (auto exits at 99¢ stay live)
- `/resume` — resume new entries
- `/kill` — emergency: cancel all open orders, halt everything. Confirmation required.
- `/reconcile` — force reconciliation run
- `/balance` — current Kalshi balance
- `/today` — today's P&L (split by auto vs manual exits) and trade count
- `/last 10` — last 10 signals (fired or not, with reasons)

Implementation: `python-telegram-bot` v21+. Lock command access to single allowed user ID configured in `.env`. All commands that move money or cancel orders require explicit confirmation (reply `confirm` within 30s).

**Manual exit flow detail:**
1. Operator sends `/exit KXHIGHLAX-26APR25-T71 95 marine_layer_risk`
2. Bot replies: "Confirm exit of KXHIGHLAX-26APR25-T71 (NO, 50 contracts) at 95¢? Current bid: 96¢, current ask: 98¢. Reply `confirm` within 30s. Reason logged: marine_layer_risk"
3. Operator replies `confirm`
4. Bot triggers `manual_exit.py`: cancels existing 99¢ limit, posts new 95¢ limit, transitions state to MANUAL_EXIT_POSTED
5. Bot confirms: "Manual exit limit posted at 95¢. Will alert on fill."
6. On fill: state → MANUAL_EXITED; bot alerts P&L; learning system records as manual outcome

### B.10.2 Obsidian vault export

Daily at 23:30 local NYC time, write to:

```
{vault_path}/Black_Mamba/Daily/{YYYY-MM-DD}.md
```

Contents (YAML frontmatter + sections):
- Frontmatter: date, balance_open, balance_close, pnl_total, pnl_auto, pnl_manual, trades_total, trades_auto_exit, trades_manual_exit, win_rate
- Summary
- Per-city: signals evaluated, signals fired, P&L, observations vs forecast
- Per-trade: ticker, tier, entry, exit_price, exit_type (auto/manual), P&L, time-in-position, retracement-after-entry, operator_reason (if manual)
- Anomalies and incidents
- Manual interventions (separate section)
- Tomorrow's notes (forecast highs, expected windows)

Also maintain:
- `{vault_path}/Black_Mamba/Strategies.md` — current tier definitions, sizing, breakers (auto-updated when config changes)
- `{vault_path}/Black_Mamba/Incidents.md` — append-only incident log
- `{vault_path}/Black_Mamba/Manual_Exits.md` — append-only log of every manual operator override with full context
- `{vault_path}/Black_Mamba/Learnings/` — auto-generated weekly summary of feedback loops (auto vs manual segmented)

Use Obsidian wikilinks `[[...]]` for cross-references.

### B.10.3 Heartbeat / dead-man's switch

Heartbeat task runs every 30 seconds. Writes `{timestamp, status, last_obs_age_per_city, open_positions_count, deployed_pct}` to `./data/heartbeat.json`.

Separate watchdog process (`scripts/watchdog.py`) monitors:
- **2 minutes stale**: warn via Telegram
- **5 minutes stale**: halt new entries
- **15 minutes stale**: cancel all open orders via direct REST, alert with full system dump

Watchdog is OS-level separate process; a hung main process can't suppress its own death.

## B.11 Learning System

Three explicit, bounded feedback loops. No ML beyond these.

### B.11.1 Per-station retracement statistics

After each trading day, for every signal fire, record:
- Was the bucket actually dead at fire time? (ground truth from settlement)
- Did temperature retrace below the bucket ceiling at any point after fire?

Compute rolling 30-day per-station base rates: `P(retracement | hour_of_day, month, station)`.

If rolling base rate for retracement at this hour-of-day in this station exceeds 0.5%, Tier 3 is automatically downgraded to Tier 2 for that hour. (Consumed read-only — never fired silently.)

### B.11.2 Order book reprice latency

For every signal fire, measure `Δt = time_kalshi_book_repriced_to_99c - time_observation_crossed_threshold`.

- Consistent <60s for a city/time → increase polling cadence to 30s in that window.
- Consistent >300s → slacken to 90s.

### B.11.3 Fill quality / slippage

For every fill, measure `expected_entry - realized_entry`. Per-city, per-time-of-day.

- Realized slippage consistently 1¢ above ask → place limit at quoted_ask + 1¢ (still ≤97¢ cap).
- Zero slippage → place at quoted_ask.

### B.11.4 Auto vs manual outcome separation

**Critical for measurement integrity:** the three feedback loops above measure *automated* performance only. Positions closed via manual operator exit (`MANUAL_EXITED` state) are excluded from automated win rate, automated P&L, and automated slippage calculations.

Manual exits are tracked separately in:
- `manual_overrides` table
- `pnl_manual` aggregates (daily/weekly/monthly)
- `Manual_Exits.md` Obsidian log

This keeps the agent's performance evaluation honest. Manual saves are valuable but they're operator skill, not agent skill. Mixing the two would obscure whether the underlying automation is working.

### B.11.5 Weekly review export

Monday 06:00, generate `{vault_path}/Black_Mamba/Learnings/weekly_{YYYY-MM-DD}.md`:
- Per-city win rate (auto only), avg P&L per trade (auto and manual segmented), total P&L
- Retracement base rate trends
- Reprice latency trends
- Slippage trends
- Manual override patterns (when does operator override most? what reasons?)
- Suggested config changes — proposed only, never auto-applied

## B.12 Backtesting

`scripts/backtest.py` replays a date range:
1. Loads historical NWS observations (NCEI or stored snapshots)
2. Loads historical Kalshi market snapshots if available; else uses settlement data + order-book reconstruction model
3. Runs full signal evaluation at every simulated polling tick
4. Records every "would have fired" trade
5. Computes simulated P&L assuming fills at ask + slippage_model

Output: `backtest_{start}_{end}.md` in `./reports/`.

**Required before going live:** ≥90 days of backtest data, positive P&L, no single-day loss exceeding daily circuit breaker.

## B.13 Paper Trading Mode

Single env flag `BLACK_MAMBA_MODE={paper,live}`.

In paper mode:
- All Kalshi auth happens (use separate paper API key if Kalshi supports demo; else simulate)
- Order placement intercepted: logged and "filled" at current ask
- All other logic identical (state machine, exit posting, manual exit support, reconciliation)
- Separate paper ledger tracks paper P&L

Required before going live: 14 consecutive operating days in paper mode with:
- Zero unhandled exceptions
- Reconciliation discrepancies = 0
- All circuit breakers tested at least once (manually trip them in paper)
- Manual exit flow tested via Telegram at least 3 times
- Telegram + Obsidian outputs verified

After 14 days, operator manually flips `BLACK_MAMBA_MODE=live` in `.env` and restarts. Agent logs startup banner indicating live mode and waits 60 seconds before resuming.

## B.14 Tech Stack (Decisions)

- **Language:** Python 3.12+
- **Async runtime:** asyncio + httpx + websockets
- **Config:** pydantic-settings
- **DB:** SQLAlchemy 2.x + Alembic; SQLite default, Postgres via env
- **Logging:** structlog with JSON output
- **Telegram:** python-telegram-bot v21+
- **Process supervision:** systemd (production) or tmux/screen (dev). Provide both.
- **Time handling:** all internal times `datetime` with `tzinfo=UTC`. Display in local tz at boundaries only.
- **Testing:** pytest + pytest-asyncio + respx
- **Linting:** ruff + mypy in strict mode
- **Package manager:** `uv`

No additional dependencies without justification in `DECISIONS.md`.

## B.15 Out of Scope for v1

Build only after v1 has 60+ days of clean live trading:

1. YES-side latency arb
2. Additional cities (any beyond LAX, SFO, PHX)
3. Polymarket cross-arbitrage
4. Volatility-based sizing adjustments
5. Options-style basket trades
6. Auto-config tuning (learning outputs stay advisory)

## B.16 Build Order

Build in this exact order. Stop and report after each phase.

**Phase 0 — Foundation (1–2 days)**
- Repo skeleton, pyproject.toml, .env.example, CI lint+typecheck
- DB schema + migrations
- Logging infrastructure
- Config loading and validation
- DoD: `python -m black_mamba.main --version` runs clean

**Phase 1 — Data layer (2–3 days)**
- NWS API client, METAR direct, Synoptic fallback, High-Res ASOS for KPHX
- Observation reconciler, async poller
- DoD: poller runs 1 hour against all 3 cities, 0 errors, observations stored

**Phase 2 — Kalshi integration (2–3 days)**
- RSA-PSS auth, REST client, WebSocket client
- Rules scraper + grading verification
- DoD: pull market state, balance, live order books for all 3 cities; rules scraper runs daily

**Phase 3 — Strategy + Risk (2–3 days)**
- Bucket analyzer, signal evaluator, tier classifier
- Sizer, circuit breakers
- DoD: full signal pipeline runs in dry-run, generates and logs would-be trades, no orders placed

**Phase 4 — Execution + State Machine (2 days)**
- State machine, order executor (paper mode first), manual exit handler, reconciler
- DoD: paper mode runs end-to-end for one full trading day, manual exit flow tested, reconciliation passes

**Phase 5 — Observability (1–2 days)**
- Telegram bot (all alerts + all commands including manual exit confirmation flow)
- Obsidian export
- Heartbeat + watchdog
- DoD: all alerts fire, all commands work (including `/exit` and `/exit_all`), heartbeat watchdog test-killed and confirmed

**Phase 6 — Learning + Backtest (2–3 days)**
- Three feedback loops with auto/manual separation
- Backtest replay engine
- Weekly review generator
- DoD: 90-day backtest produces report; learning loops update DB after each test day; auto vs manual segmentation verified

**Phase 7 — Paper trading (14 days minimum)**
- System runs in paper mode
- Operator reviews daily
- Any unhandled exception or reconciliation miss resets the 14-day clock
- DoD: 14 consecutive clean days, manual exit flow exercised ≥3 times

**Phase 8 — Go live**
- Operator flips mode to live
- First 5 days at half sizing (multiply tier % by 0.5)
- Full sizing after 5 clean live days

## B.17 Definition of Done (Project-Level)

- [ ] All 8 phases completed
- [ ] 14 consecutive clean paper days
- [ ] 5 clean live days at half sizing
- [ ] Telegram command interface fully functional including manual exit flow
- [ ] Obsidian vault populated with daily journals + weekly reviews + manual exits log
- [ ] Backtest report shows >90 days positive expectancy
- [ ] All circuit breakers tested live
- [ ] Reconciliation has run with 0 discrepancies for 5+ days
- [ ] RUNBOOK.md complete enough that a stranger could operate
- [ ] DECISIONS.md documents every non-obvious choice
- [ ] All tests pass; mypy strict zero errors; ruff clean

## B.18 Operator Responsibilities (Things Black_Mamba Cannot Do)

- Fund the Kalshi account
- Generate and securely store Kalshi RSA private key
- Set up Telegram bot, provide token
- Configure Obsidian vault path
- Review daily Telegram summaries and Obsidian journals
- Review weekly Obsidian reports
- **Make manual exit decisions on open positions when conditions warrant** (this is the operator's PM role)
- Manually approve any tier configuration changes proposed by learning system
- Investigate and resolve escalated incidents within 24 hours
- Maintain `.env`, rotate credentials as needed

## B.19 Things You (Claude Code) Should Push Back On

If the operator asks during build, push back, cite this document, require explicit acknowledgement before proceeding:

- Increase per-trade sizing beyond Tier 3's 18% cap
- Disable the daily loss circuit breaker
- Skip paper trading and go straight to live
- Trade markets outside scope without formal scope addition
- Trade YES contracts
- Remove grading station verification
- Use single-source observations for Tier 2/3 trades
- Auto-apply learning system suggestions without operator review
- Add automated sub-99¢ exits (these stay manual-only)

You are not being unhelpful by pushing back. You are doing your job.

## B.20 Credentials Checklist (End of Build)

After implementation complete, present this to the operator:

```
[ ] KALSHI_API_KEY_ID                    (from Kalshi account → API)
[ ] KALSHI_PRIVATE_KEY_PATH              (path to PEM file with RSA private key)
[ ] KALSHI_API_BASE_URL                  (default: https://api.elections.kalshi.com/trade-api/v2)
[ ] KALSHI_WS_URL                        (default: wss://api.elections.kalshi.com/trade-api/ws/v2)
[ ] KALSHI_MODE                          (paper | live)
[ ] NWS_USER_AGENT                       ("BlackMamba/1.0 (contact@example.com)")
[ ] SYNOPTIC_API_TOKEN                   (optional fallback — synopticdata.com)
[ ] TELEGRAM_BOT_TOKEN                   (from @BotFather)
[ ] TELEGRAM_OPERATOR_CHAT_ID            (your chat ID — only allowed user)
[ ] OBSIDIAN_VAULT_PATH                  (absolute path to vault root)
[ ] DATABASE_URL                         (default: sqlite:///./data/black_mamba.db)
[ ] LOG_LEVEL                            (INFO | DEBUG)
[ ] BLACK_MAMBA_MODE                     (paper | live — must match KALSHI_MODE)
[ ] BLACK_MAMBA_STARTING_BALANCE         (paper mode only; live reads from Kalshi)
[ ] DAILY_LOSS_CIRCUIT_BREAKER_PCT       (default: 12)
[ ] MAX_TOTAL_EXPOSURE_PCT               (default: 40)
[ ] MIN_TRADE_DOLLARS                    (default: 25)
```

## B.21 Final Notes

- The operator (Eddie) has stated and demonstrated discipline issues with manual trading. **Black_Mamba's primary product is discipline.** The operator's manual exit role is intentional and bounded — it operates only on winning positions to lock in profit below 99¢ when conditions warrant. The operator does NOT manually open positions, average down, or override the entry logic. That separation is what makes the human-in-the-loop role safe.
- When facing ambiguous spec choices, prefer the more conservative option. Document.
- Build for restartability: every process killable and resumable from persistent state.
- Don't add features. Build what's specified.
- Stop at phase boundaries. Request review.
- Final integration test: full simulated trading day with all components running, verified by hand against logs, including at least one manual exit flow.

This document is the contract. Refer back to it. Propose changes via PRs to this file. Do not deviate silently.

— End of CLAUDE.md —
