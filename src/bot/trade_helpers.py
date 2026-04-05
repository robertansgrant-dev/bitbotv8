"""Shared trade lifecycle helpers used by bot_runner and portfolio_routes.

Extracted from V7 to eliminate ~150 lines of duplication between the bot loop
and the manual position API endpoints.
"""

import logging
import uuid
from datetime import datetime, timezone

import pandas as pd

from src.bot.risk.risk_manager import RiskManager, TradeState
from src.config.presets import StylePreset
from src.config.settings import Settings
from src.data.models.position import Position
from src.data.models.trade import Trade

logger = logging.getLogger(__name__)

_REQUIRED_OHLCV_COLS = {"open", "high", "low", "close", "volume"}


def validate_ohlcv(df: pd.DataFrame, min_rows: int = 50) -> None:
    """Raise ValueError if the DataFrame is missing columns or has too few rows."""
    missing = _REQUIRED_OHLCV_COLS - set(df.columns)
    if missing:
        raise ValueError(f"OHLCV DataFrame missing columns: {missing}")
    if len(df) < min_rows:
        raise ValueError(f"OHLCV DataFrame has {len(df)} rows; need at least {min_rows}")


def sync_rm_from_preset(rm: RiskManager, preset: StylePreset, settings: Settings) -> None:
    """Sync RiskManager config fields from the active style preset and settings.

    Called in _seek_entry before every entry attempt so RM always reflects the
    current style — covers runtime style switches mid-session.
    """
    rm.cfg.sl_atr_mult = preset.atr_sl_multiplier
    rm.cfg.tp_atr_mult = preset.atr_sl_multiplier * preset.risk_reward
    rm.cfg.risk_per_trade_pct = preset.risk_per_trade_pct / 100
    rm.cfg.time_exit_minutes = preset.max_hold_minutes
    rm.cfg.max_hold_extension_minutes = 5 if preset.name == "scalping" else 15
    rm.cfg.fee_rate = settings.fee_rate


def build_closed_trade_state(pos: Position, price: float, reason: str) -> TradeState:
    """Build a completed TradeState from a Position, for use with calculate_trade_metrics."""
    ts = TradeState(
        id=str(uuid.uuid4())[:8],
        side=pos.side,
        entry_price=pos.entry_price,
        entry_time=pos.open_time,
        qty=pos.quantity,
        sl=pos.stop_loss,
        tp=pos.take_profit,
        signal_type=pos.signal_type or "",
        exit_price=price,
        exit_reason=reason,
    )
    ts.max_price_seen = pos.max_price_seen
    ts.min_price_seen = pos.min_price_seen
    return ts


def build_trade_record(
    pos: Position,
    closed_ts: TradeState,
    metrics: dict,
    mode: str,
    style: str,
) -> tuple[Trade, float, float, float]:
    """Build a Trade record from a closed position and its RM metrics.

    Returns (trade, gross_pnl, fees, net_pnl).
    """
    pnl = pos.unrealized_pnl
    fees = metrics.get("fees_paid", 0.0)
    net = metrics.get("net_pnl", pnl)
    trade = Trade(
        trade_id=closed_ts.id,
        symbol=pos.symbol,
        side=pos.side,
        entry_price=pos.entry_price,
        exit_price=closed_ts.exit_price or 0.0,
        quantity=pos.quantity,
        timestamp=datetime.now(timezone.utc),
        pnl=pnl,
        fees=fees,
        entry_time=pos.open_time,
        mode=mode,
        style=style,
        signal_type=pos.signal_type,
        exit_reason=closed_ts.exit_reason,
    )
    return trade, pnl, fees, net
