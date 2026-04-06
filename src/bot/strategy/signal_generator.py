"""Signal generation: CROSSOVER, PULLBACK, MOMENTUM, BREAKOUT."""

import logging
from typing import Literal

import pandas as pd

from src.bot.strategy.indicators import adx, atr, rsi, sma
from src.config.presets import StylePreset

logger = logging.getLogger(__name__)

SignalType = Literal["CROSSOVER", "PULLBACK", "MOMENTUM", "BREAKOUT", "NONE"]
Direction = Literal["LONG", "SHORT", "NONE"]
Trend = Literal["UP", "DOWN", "NEUTRAL"]

# Minimum ADX value required to take a PULLBACK signal.
# Below this threshold the market is ranging and pullback entries underperform.
_ADX_TREND_THRESHOLD = 20.0

# Volume must be at least this fraction of its rolling average for any signal.
# Protects against entries in illiquid/thin conditions.
_VOLUME_RATIO_MIN = 0.70


def get_htf_trend(df_htf: pd.DataFrame, preset: StylePreset) -> Trend:
    """Determine higher-timeframe trend direction using price vs trend SMA.

    Only price vs the trend SMA is used — requiring the fast SMA to also clear
    the trend SMA adds ~80 h of extra lag on the 4h timeframe, keeping the bot in
    NEUTRAL for the entire duration of a sharp rally or sell-off.
    """
    if len(df_htf) < preset.sma_trend:
        return "NEUTRAL"
    close = df_htf["close"]
    trend_val = sma(close, preset.sma_trend).iloc[-1]
    price = close.iloc[-1]
    if price > trend_val:
        return "UP"
    if price < trend_val:
        return "DOWN"
    return "NEUTRAL"


def _is_market_trending(df: pd.DataFrame) -> bool:
    """Return False if ATR is contracting vs its recent average — indicates ranging market.

    Compares the current 14-period ATR to the mean of the last 30 ATR values.
    If the current ATR is below 70% of that mean the market is likely choppy.
    PULLBACK is exempt from this filter because it already requires HTF trend alignment.
    """
    if len(df) < 60:
        return True  # insufficient history — don't suppress
    atr_series = atr(df, 14)
    current = atr_series.iloc[-1]
    avg = atr_series.iloc[-30:].mean()
    if pd.isna(current) or pd.isna(avg) or avg == 0:
        return True
    return current >= avg * 0.70


def _is_market_dead(df: pd.DataFrame, volatility_floor: float) -> bool:
    """Return True when ATR/price is below the per-preset volatility floor.

    Floor is derived per preset as 2 * fee_rate / atr_sl_multiplier so that
    1R always covers round-trip costs regardless of timeframe:
      scalping  (1m, mult=1.5) → 0.0013
      day_trade (1h, mult=2.0) → 0.0010
      swing     (1d, mult=3.0) → 0.0007
    A single hardcoded 0.0025 floor permanently blocked scalping on 1m bars
    where BTC's natural ATR/price is ~0.0008.
    """
    if len(df) < 15:
        return False  # insufficient history — allow through
    atr_series = atr(df, 14)
    current_atr = atr_series.iloc[-1]
    close = df["close"].iloc[-1]
    if pd.isna(current_atr) or close <= 0:
        return False
    return (current_atr / close) < volatility_floor


def _has_sufficient_volume(df: pd.DataFrame, periods: int = 20) -> bool:
    """Return False when current volume is below the minimum activity threshold.

    Prevents entries during illiquid windows (e.g. late-night thin market,
    exchange maintenance) where spreads are wide and slippage is elevated.
    Uses the last *completed* candle (iloc[-2]) — the live candle (iloc[-1]) is
    still forming and always shows artificially low volume mid-bar.
    """
    if len(df) < periods + 2:
        return True  # not enough history — allow through
    current_vol = df["volume"].iloc[-2]
    avg_vol = df["volume"].iloc[-periods - 2:-2].mean()
    if avg_vol == 0 or pd.isna(avg_vol):
        return True
    return (current_vol / avg_vol) >= _VOLUME_RATIO_MIN


def _crossover(df: pd.DataFrame, preset: StylePreset, trend: Trend) -> Direction:
    """SMA fast/slow crossover in the trend direction with minimum gap filter.

    Requires the gap between fast and slow to be at least 0.05% of price after
    the cross — filters micro-crosses in flat/ranging markets.
    """
    if len(df) < preset.sma_slow + 2:
        return "NONE"
    fast = sma(df["close"], preset.sma_fast)
    slow = sma(df["close"], preset.sma_slow)
    crossed_up = fast.iloc[-2] <= slow.iloc[-2] and fast.iloc[-1] > slow.iloc[-1]
    crossed_dn = fast.iloc[-2] >= slow.iloc[-2] and fast.iloc[-1] < slow.iloc[-1]
    min_gap = slow.iloc[-1] * 0.0005  # 0.05% of price — filters noise crosses
    if crossed_up and trend == "UP" and fast.iloc[-1] - slow.iloc[-1] >= min_gap:
        return "LONG"
    if crossed_dn and trend == "DOWN" and slow.iloc[-1] - fast.iloc[-1] >= min_gap:
        return "SHORT"
    return "NONE"


def _pullback(
    df: pd.DataFrame,
    preset: StylePreset,
    trend: Trend,
    adx_val: float,
) -> Direction:
    """Price pulls back to fast SMA and bounces with RSI and ADX confirmation.

    ADX filter: requires adx_val >= _ADX_TREND_THRESHOLD (default 20) to avoid
    taking pullback entries in choppy/ranging regimes where the HTF trend may be
    stale or weak.
    """
    if adx_val < _ADX_TREND_THRESHOLD:
        return "NONE"
    if len(df) < preset.sma_slow + 2:
        return "NONE"
    close = df["close"]
    fast = sma(close, preset.sma_fast)
    slow = sma(close, preset.sma_slow)
    price = close.iloc[-1]
    prev = close.iloc[-2]
    fast_val = fast.iloc[-1]
    slow_val = slow.iloc[-1]
    tol = fast_val * 0.003  # 0.3% tolerance band around fast SMA
    rsi_val = rsi(close).iloc[-1]

    if trend == "UP" and fast_val > slow_val:
        if rsi_val >= 45 and prev <= fast_val + tol and price > prev:
            return "LONG"
    if trend == "DOWN" and fast_val < slow_val:
        if rsi_val <= 55 and prev >= fast_val - tol and price < prev:
            return "SHORT"
    return "NONE"


def _momentum(df: pd.DataFrame, preset: StylePreset, trend: Trend) -> Direction:
    """Fast SMA rising, price above both MAs, RSI 50-75."""
    if len(df) < preset.sma_slow + 15:
        return "NONE"
    close = df["close"]
    fast = sma(close, preset.sma_fast)
    slow = sma(close, preset.sma_slow)
    rsi_val = rsi(close).iloc[-1]
    price = close.iloc[-1]
    fast_val = fast.iloc[-1]
    slow_val = slow.iloc[-1]

    min_dist = fast_val * 0.0015  # price must be 0.15% beyond fast SMA — avoids entries near SMA
    if trend == "UP":
        fast_rising = fast.iloc[-1] > fast.iloc[-3]
        if fast_rising and price > fast_val + min_dist and fast_val > slow_val and 50 <= rsi_val <= 75:
            return "LONG"
    if trend == "DOWN":
        fast_falling = fast.iloc[-1] < fast.iloc[-3]
        if fast_falling and price < fast_val - min_dist and fast_val < slow_val and 25 <= rsi_val <= 50:
            return "SHORT"
    return "NONE"


def _breakout(df: pd.DataFrame, trend: Trend) -> Direction:
    """Price exceeds 20-bar high/low with volume and momentum confirmation."""
    if len(df) < 50:
        return "NONE"
    prev_high = df["high"].iloc[-21:-1].max()
    prev_low = df["low"].iloc[-21:-1].min()
    price = df["close"].iloc[-1]
    volume = df["volume"].iloc[-1]
    avg_volume = df["volume"].iloc[-21:-1].mean()

    if volume < avg_volume * 1.5:
        return "NONE"

    body = abs(df["close"].iloc[-1] - df["open"].iloc[-1])
    candle_range = df["high"].iloc[-1] - df["low"].iloc[-1]
    if candle_range == 0 or body / candle_range < 0.6:
        return "NONE"

    if trend == "UP" and price > prev_high:
        return "LONG"
    if trend == "DOWN" and price < prev_low:
        return "SHORT"
    return "NONE"


def get_signal(
    df: pd.DataFrame,
    df_htf: pd.DataFrame,
    preset: StylePreset,
) -> tuple[SignalType, Direction]:
    """Return (signal_type, direction) for the current market state.

    Filter order (cheapest / most restrictive first):
    1. HTF trend must be UP or DOWN (NEUTRAL → no trade)
    2. Volume must meet minimum activity threshold (thin market → no trade)
    3. ATR regime filter: CROSSOVER, MOMENTUM, BREAKOUT suppressed in ranging markets
    4. ADX filter: PULLBACK requires ADX ≥ 20 on the LTF
    5. Individual signal checks in priority order
    """
    trend = get_htf_trend(df_htf, preset)
    if trend == "NEUTRAL":
        logger.info("Signal skip: weak_trend (HTF SMA trend=NEUTRAL)")
        return "NONE", "NONE"

    # Volume gate — applies to all signal types
    if not _has_sufficient_volume(df):
        current_vol = df["volume"].iloc[-2] if len(df) > 1 else 0
        avg_vol = df["volume"].iloc[-22:-2].mean() if len(df) > 22 else 0
        logger.info(
            "Signal skip: low_vol (vol=%.0f < %.0f%% of SMA=%.0f)",
            current_vol, _VOLUME_RATIO_MIN * 100, avg_vol,
        )
        return "NONE", "NONE"

    # Hard volatility floor — overrides PULLBACK exemption in dead/grind markets
    if _is_market_dead(df, preset.volatility_floor):
        close = df["close"].iloc[-1]
        current_atr = atr(df, 14).iloc[-1]
        logger.info(
            "Signal skip: dead_market (ATR/price=%.4f < floor=%.4f  ATR=%.2f)",
            current_atr / close if close > 0 else 0, preset.volatility_floor, current_atr,
        )
        return "NONE", "NONE"

    trending = _is_market_trending(df)

    # ADX for PULLBACK gate — compute once, reuse below
    adx_series = adx(df, 14)
    adx_val = adx_series.iloc[-1] if not adx_series.empty else 0.0
    if pd.isna(adx_val):
        adx_val = 0.0

    checks: list[tuple[Direction, SignalType]] = [
        (_crossover(df, preset, trend) if trending else "NONE", "CROSSOVER"),
        (_pullback(df, preset, trend, adx_val), "PULLBACK"),
        (_momentum(df, preset, trend) if trending else "NONE", "MOMENTUM"),
        (_breakout(df, trend) if trending else "NONE", "BREAKOUT"),
    ]
    for direction, name in checks:
        if direction != "NONE":
            logger.info(
                "Signal: %s %s (HTF trend=%s trending=%s adx=%.1f)",
                name, direction, trend, trending, adx_val,
            )
            return name, direction  # type: ignore[return-value]

    # Log why no signal fired — helps diagnose over-filtering
    if not trending:
        logger.info(
            "Signal skip: chop (ATR below 70%% of 30-bar avg; HTF=%s adx=%.1f)",
            trend, adx_val,
        )
    elif adx_val < _ADX_TREND_THRESHOLD:
        logger.info(
            "Signal skip: weak_trend (ADX=%.1f < %.1f; HTF=%s)",
            adx_val, _ADX_TREND_THRESHOLD, trend,
        )

    return "NONE", "NONE"
