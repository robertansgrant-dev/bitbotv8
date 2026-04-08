"""Frozen dataclass presets for each trading style."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class StylePreset:
    """Immutable trading style configuration."""

    name: str
    position_size_pct: float
    stop_loss_pct: float
    risk_reward: float
    max_daily_trades: int
    sma_fast: int
    sma_slow: int
    sma_trend: int
    ltf_timeframe: str
    htf_timeframe: str
    trailing_stop: bool
    max_hold_minutes: int
    # Risk-per-trade sizing: size position so that hitting SL costs this % of capital
    risk_per_trade_pct: float = 0.5
    # ATR multiplier for stop loss distance (ATR * multiplier = SL offset in price)
    # When ATR data is available this overrides the fixed stop_loss_pct
    atr_sl_multiplier: float = 1.5
    # Minimum ATR/price ratio for a signal to fire — below this 1R barely covers fees.
    # Formula: 2 * fee_rate / atr_sl_multiplier (fee_rate=0.001, so each style differs).
    # Scalping 1m bars have naturally small ATR; a shared 0.0025 floor would block all trades.
    volatility_floor: float = 0.0013


SCALPING = StylePreset(
    name="scalping",
    position_size_pct=20.0,
    stop_loss_pct=0.4,
    risk_reward=1.5,
    max_daily_trades=100,
    sma_fast=8,
    sma_slow=21,
    sma_trend=200,
    ltf_timeframe="1m",
    htf_timeframe="5m",
    trailing_stop=False,
    max_hold_minutes=30,
    risk_per_trade_pct=1.0,
    atr_sl_multiplier=1.0,
    volatility_floor=0.0005,
)

DAY_TRADING = StylePreset(
    name="day_trading",
    position_size_pct=60.0,
    stop_loss_pct=1.5,
    risk_reward=2.0,
    max_daily_trades=8,
    sma_fast=9,
    sma_slow=21,
    sma_trend=50,
    ltf_timeframe="15m",
    htf_timeframe="1h",
    trailing_stop=True,
    max_hold_minutes=480,
    risk_per_trade_pct=1.0,
    atr_sl_multiplier=1.5,
    volatility_floor=0.0010,
)

SWING_TRADING = StylePreset(
    name="swing_trading",
    position_size_pct=90.0,
    stop_loss_pct=3.5,
    risk_reward=3.0,
    max_daily_trades=3,
    sma_fast=21,
    sma_slow=55,
    sma_trend=200,
    ltf_timeframe="1h",
    htf_timeframe="1d",
    trailing_stop=True,
    max_hold_minutes=1440,
    risk_per_trade_pct=1.5,
    atr_sl_multiplier=2.0,
    volatility_floor=0.0007,
)

PRESETS: dict[str, StylePreset] = {
    "scalping": SCALPING,
    "day_trading": DAY_TRADING,
    "swing_trading": SWING_TRADING,
}


def get_preset(style: Literal["scalping", "day_trading", "swing_trading"]) -> StylePreset:
    """Return the preset for the given trading style."""
    return PRESETS[style]
