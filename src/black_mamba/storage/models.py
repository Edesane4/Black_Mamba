"""SQLAlchemy ORM models — one class per table in §B.9.1.

Field names are snake_case. All datetimes are UTC-aware (§B.14).
JSON columns store raw payloads for postmortem analysis.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ---------- Data layer (§B.5) ----------

class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station: Mapped[str] = mapped_column(String(8), index=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    observed_temp_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    polled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    qc_flags: Mapped[str | None] = mapped_column(String(64), nullable=True)
    max_temp_today_so_far_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    single_source: Mapped[bool] = mapped_column(Boolean, default=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)
    anomaly_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


# ---------- Kalshi layer (§B.6) ----------

class OrderBookSnapshot(Base):
    __tablename__ = "order_book_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market_ticker: Mapped[str] = mapped_column(String(64), index=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    trigger: Mapped[str] = mapped_column(String(32))
    best_bid_yes_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_ask_yes_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_bid_no_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_ask_no_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth_yes_bid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth_yes_ask: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth_no_bid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth_no_ask: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bids_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    asks_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


# ---------- Strategy / Signals (§B.4) ----------

class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    market_ticker: Mapped[str] = mapped_column(String(64), index=True)
    city: Mapped[str] = mapped_column(String(8))
    bucket_low_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    bucket_high_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_temp_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    observation_count_at_or_above_ceiling: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    source_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_no_ask_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth_at_ask: Mapped[int | None] = mapped_column(Integer, nullable=True)
    forecast_high_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_headroom_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_local: Mapped[str | None] = mapped_column(String(8), nullable=True)
    grading_station_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    no_active_circuit_breaker: Mapped[bool] = mapped_column(Boolean, default=False)
    no_observation_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)
    market_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fired: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    tier: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason_not_fired: Mapped[str | None] = mapped_column(String(128), nullable=True)
    conditions_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


# ---------- Execution (§B.8) ----------

class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int | None] = mapped_column(
        ForeignKey("signals.id"), nullable=True, index=True
    )
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    market_ticker: Mapped[str] = mapped_column(String(64), index=True)
    city: Mapped[str] = mapped_column(String(8))
    tier: Mapped[int] = mapped_column(Integer)
    contracts: Mapped[int] = mapped_column(Integer)
    entry_price_cents: Mapped[int] = mapped_column(Integer)
    exit_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exit_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    state: Mapped[str] = mapped_column(String(32), index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    exited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pnl_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manual_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    entry_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id"), nullable=True
    )
    exit_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id"), nullable=True
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_id: Mapped[int | None] = mapped_column(
        ForeignKey("positions.id"), nullable=True, index=True
    )
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    kalshi_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    client_order_id: Mapped[str] = mapped_column(String(64), index=True)
    market_ticker: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(8))  # buy | sell
    side: Mapped[str] = mapped_column(String(4))  # yes | no
    type: Mapped[str] = mapped_column(String(16))  # limit (always)
    tif: Mapped[str] = mapped_column(String(8))  # IOC | GTC
    price_cents: Mapped[int] = mapped_column(Integer)
    count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    response_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    filled_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_filled_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class ManualOverride(Base):
    __tablename__ = "manual_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_id: Mapped[int | None] = mapped_column(
        ForeignKey("positions.id"), nullable=True, index=True
    )
    command: Mapped[str] = mapped_column(String(32))
    requested_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operator_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    telegram_user_id: Mapped[int] = mapped_column(Integer)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[str | None] = mapped_column(String(32), nullable=True)


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market_ticker: Mapped[str] = mapped_column(String(64), index=True)
    event_ticker: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    settled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    settlement_value: Mapped[str] = mapped_column(String(8))  # yes | no | void
    payout_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


# ---------- Risk + Operational (§B.7) ----------

class Reconciliation(Base):
    __tablename__ = "reconciliations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    kalshi_balance_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    local_balance_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discrepancy_cents: Mapped[int] = mapped_column(Integer, default=0)
    positions_reconciled: Mapped[int] = mapped_column(Integer, default=0)
    discrepancies_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class CircuitBreakerEvent(Base):
    __tablename__ = "circuit_breaker_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    breaker_name: Mapped[str] = mapped_column(String(64), index=True)
    tripped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    reason: Mapped[str] = mapped_column(Text)
    context_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    city: Mapped[str | None] = mapped_column(String(8), nullable=True)
    market_ticker: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
