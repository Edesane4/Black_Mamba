"""initial schema — 10 tables per §B.9.1.

Revision ID: 0001
Revises:
Create Date: 2026-04-25

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("station", sa.String(8), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("observed_temp_f", sa.Float(), nullable=True),
        sa.Column("raw_value", sa.String(64), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("polled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("qc_flags", sa.String(64), nullable=True),
        sa.Column("max_temp_today_so_far_f", sa.Float(), nullable=True),
        sa.Column("single_source", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_anomaly", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("anomaly_kind", sa.String(64), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=True),
    )
    op.create_index("ix_observations_station", "observations", ["station"])
    op.create_index("ix_observations_source", "observations", ["source"])
    op.create_index("ix_observations_observed_at", "observations", ["observed_at"])

    op.create_table(
        "order_book_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("market_ticker", sa.String(64), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trigger", sa.String(32), nullable=False),
        sa.Column("best_bid_yes_cents", sa.Integer(), nullable=True),
        sa.Column("best_ask_yes_cents", sa.Integer(), nullable=True),
        sa.Column("best_bid_no_cents", sa.Integer(), nullable=True),
        sa.Column("best_ask_no_cents", sa.Integer(), nullable=True),
        sa.Column("depth_yes_bid", sa.Integer(), nullable=True),
        sa.Column("depth_yes_ask", sa.Integer(), nullable=True),
        sa.Column("depth_no_bid", sa.Integer(), nullable=True),
        sa.Column("depth_no_ask", sa.Integer(), nullable=True),
        sa.Column("bids_json", sa.JSON(), nullable=True),
        sa.Column("asks_json", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_order_book_snapshots_market_ticker", "order_book_snapshots", ["market_ticker"]
    )
    op.create_index(
        "ix_order_book_snapshots_snapshot_at", "order_book_snapshots", ["snapshot_at"]
    )

    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("market_ticker", sa.String(64), nullable=False),
        sa.Column("city", sa.String(8), nullable=False),
        sa.Column("bucket_low_f", sa.Float(), nullable=True),
        sa.Column("bucket_high_f", sa.Float(), nullable=True),
        sa.Column("observed_temp_f", sa.Float(), nullable=True),
        sa.Column("observation_count_at_or_above_ceiling", sa.Integer(), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=True),
        sa.Column("best_no_ask_cents", sa.Integer(), nullable=True),
        sa.Column("depth_at_ask", sa.Integer(), nullable=True),
        sa.Column("forecast_high_f", sa.Float(), nullable=True),
        sa.Column("forecast_headroom_f", sa.Float(), nullable=True),
        sa.Column("time_local", sa.String(8), nullable=True),
        sa.Column("grading_station_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("no_active_circuit_breaker", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("no_observation_anomaly", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("market_status", sa.String(32), nullable=True),
        sa.Column("fired", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tier", sa.Integer(), nullable=True),
        sa.Column("reason_not_fired", sa.String(128), nullable=True),
        sa.Column("conditions_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_signals_evaluated_at", "signals", ["evaluated_at"])
    op.create_index("ix_signals_correlation_id", "signals", ["correlation_id"])
    op.create_index("ix_signals_market_ticker", "signals", ["market_ticker"])
    op.create_index("ix_signals_fired", "signals", ["fired"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("position_id", sa.Integer(), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("kalshi_order_id", sa.String(64), nullable=True),
        sa.Column("client_order_id", sa.String(64), nullable=False),
        sa.Column("market_ticker", sa.String(64), nullable=False),
        sa.Column("action", sa.String(8), nullable=False),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("tif", sa.String(8), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("response_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("filled_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_filled_price_cents", sa.Integer(), nullable=True),
        sa.Column("response_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_orders_position_id", "orders", ["position_id"])
    op.create_index("ix_orders_correlation_id", "orders", ["correlation_id"])
    op.create_index("ix_orders_kalshi_order_id", "orders", ["kalshi_order_id"])
    op.create_index("ix_orders_client_order_id", "orders", ["client_order_id"])
    op.create_index("ix_orders_status", "orders", ["status"])

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_id", sa.Integer(), sa.ForeignKey("signals.id"), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("market_ticker", sa.String(64), nullable=False),
        sa.Column("city", sa.String(8), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False),
        sa.Column("contracts", sa.Integer(), nullable=False),
        sa.Column("entry_price_cents", sa.Integer(), nullable=False),
        sa.Column("exit_price_cents", sa.Integer(), nullable=True),
        sa.Column("exit_type", sa.String(32), nullable=True),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pnl_cents", sa.Integer(), nullable=True),
        sa.Column("manual_reason", sa.String(256), nullable=True),
        sa.Column("entry_order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("exit_order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
    )
    op.create_index("ix_positions_signal_id", "positions", ["signal_id"])
    op.create_index("ix_positions_correlation_id", "positions", ["correlation_id"])
    op.create_index("ix_positions_market_ticker", "positions", ["market_ticker"])
    op.create_index("ix_positions_state", "positions", ["state"])
    op.create_index("ix_positions_opened_at", "positions", ["opened_at"])

    op.create_table(
        "manual_overrides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("position_id", sa.Integer(), sa.ForeignKey("positions.id"), nullable=True),
        sa.Column("command", sa.String(32), nullable=False),
        sa.Column("requested_price_cents", sa.Integer(), nullable=True),
        sa.Column("operator_reason", sa.String(256), nullable=True),
        sa.Column("telegram_user_id", sa.Integer(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.String(32), nullable=True),
    )
    op.create_index("ix_manual_overrides_position_id", "manual_overrides", ["position_id"])

    op.create_table(
        "settlements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("market_ticker", sa.String(64), nullable=False),
        sa.Column("event_ticker", sa.String(64), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("settlement_value", sa.String(8), nullable=False),
        sa.Column("payout_cents", sa.Integer(), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_settlements_market_ticker", "settlements", ["market_ticker"])
    op.create_index("ix_settlements_event_ticker", "settlements", ["event_ticker"])
    op.create_index("ix_settlements_settled_at", "settlements", ["settled_at"])

    op.create_table(
        "reconciliations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kalshi_balance_cents", sa.Integer(), nullable=True),
        sa.Column("local_balance_cents", sa.Integer(), nullable=True),
        sa.Column("discrepancy_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("positions_reconciled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("discrepancies_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_reconciliations_run_at", "reconciliations", ["run_at"])

    op.create_table(
        "circuit_breaker_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("breaker_name", sa.String(64), nullable=False),
        sa.Column("tripped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("context_json", sa.JSON(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_reason", sa.String(256), nullable=True),
    )
    op.create_index(
        "ix_circuit_breaker_events_breaker_name", "circuit_breaker_events", ["breaker_name"]
    )
    op.create_index(
        "ix_circuit_breaker_events_tripped_at", "circuit_breaker_events", ["tripped_at"]
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("city", sa.String(8), nullable=True),
        sa.Column("market_ticker", sa.String(64), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_reason", sa.String(256), nullable=True),
    )
    op.create_index("ix_incidents_kind", "incidents", ["kind"])
    op.create_index("ix_incidents_occurred_at", "incidents", ["occurred_at"])


def downgrade() -> None:
    op.drop_table("incidents")
    op.drop_table("circuit_breaker_events")
    op.drop_table("reconciliations")
    op.drop_table("settlements")
    op.drop_table("manual_overrides")
    op.drop_table("positions")
    op.drop_table("orders")
    op.drop_table("signals")
    op.drop_table("order_book_snapshots")
    op.drop_table("observations")
