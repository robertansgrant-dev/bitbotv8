"""Unit tests for signal generation filter chain and individual signal types.

Run from the project root:
    python -m pytest tests/test_signal_generator.py -v
or:
    python -m tests.test_signal_generator
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import pandas as pd
import numpy as np

from src.bot.strategy.signal_generator import (
    get_signal,
    get_htf_trend,
    _is_market_dead,
    _is_market_trending,
    _has_sufficient_volume,
)
from src.config.presets import get_preset

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if condition:
        print(f"  {PASS}  {name}")
    else:
        print(f"  {FAIL}  {name}")
        _failures.append(name)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def make_trending_df(
    n: int = 200,
    price_start: float = 85000.0,
    trend: str = "up",
    atr_pct: float = 0.006,
    volume_base: float = 100.0,
) -> pd.DataFrame:
    """Synthetic OHLCV DataFrame with a clear trend and decent volatility."""
    prices = []
    p = price_start
    step = price_start * 0.001 * (1 if trend == "up" else -1)
    for _ in range(n):
        p += step + np.random.uniform(-step * 0.3, step * 0.3)
        prices.append(p)

    closes = np.array(prices)
    atr_abs = closes * atr_pct
    highs = closes + atr_abs * 0.6
    lows = closes - atr_abs * 0.6
    opens = closes - atr_abs * 0.1
    volumes = np.random.uniform(volume_base * 0.8, volume_base * 1.2, n)

    return pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })


def make_flat_df(n: int = 200, price: float = 85000.0, atr_pct: float = 0.0002) -> pd.DataFrame:
    """Flat, dead-market DataFrame — price barely moves."""
    closes = np.full(n, price) + np.random.uniform(-price * 0.0001, price * 0.0001, n)
    atr_abs = closes * atr_pct
    return pd.DataFrame({
        "open": closes - atr_abs * 0.1,
        "high": closes + atr_abs * 0.5,
        "low": closes - atr_abs * 0.5,
        "close": closes,
        "volume": np.full(n, 50.0),
    })


SCALPING = get_preset("scalping")
DAY_TRADING = get_preset("day_trading")


# ─────────────────────────────────────────────────────────────
# Test: dead market detection
# ─────────────────────────────────────────────────────────────

def test_dead_market_filter() -> None:
    print("\n[_is_market_dead]")
    flat = make_flat_df(atr_pct=0.0002)
    check("Flat market detected as dead (ATR/price < 0.0025)", _is_market_dead(flat))

    live = make_trending_df(atr_pct=0.006)
    check("Trending market not detected as dead", not _is_market_dead(live))

    short_df = make_flat_df(n=10)
    check("Insufficient rows returns False (not dead)", not _is_market_dead(short_df))


# ─────────────────────────────────────────────────────────────
# Test: market trending
# ─────────────────────────────────────────────────────────────

def test_market_trending_filter() -> None:
    print("\n[_is_market_trending]")
    trending = make_trending_df(n=200, atr_pct=0.008)
    check("Trending market passes ATR regime check", _is_market_trending(trending))

    # Create clearly choppy market: first 170 bars have normal ATR, last 30 collapse to ~10%
    # This makes current ATR << 70% of the 30-bar mean
    n = 200
    prices = np.full(n, 85000.0)
    normal_atr = prices * 0.005  # 0.5% ATR first 170 bars
    tiny_atr = prices * 0.0002   # 0.02% ATR last 30 bars (collapsed)
    highs = np.concatenate([prices[:170] + normal_atr[:170] * 0.5, prices[170:] + tiny_atr[170:] * 0.5])
    lows  = np.concatenate([prices[:170] - normal_atr[:170] * 0.5, prices[170:] - tiny_atr[170:] * 0.5])
    choppy = pd.DataFrame({
        "open": prices,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": np.full(n, 50.0),
    })
    check("Choppy (collapsed ATR) market fails regime check", not _is_market_trending(choppy))

    short_df = make_trending_df(n=30)
    check("Insufficient rows (<60) passes through (no suppression)", _is_market_trending(short_df))


# ─────────────────────────────────────────────────────────────
# Test: volume filter
# ─────────────────────────────────────────────────────────────

def test_volume_filter() -> None:
    print("\n[_has_sufficient_volume]")
    df = make_trending_df(volume_base=100.0)
    check("Normal volume (80-120% of avg) passes", _has_sufficient_volume(df))

    # Last bar has very low volume
    df_low = df.copy()
    df_low.iloc[-1, df_low.columns.get_loc("volume")] = 5.0  # << 70% of ~100 avg
    check("Very low last-bar volume blocked", not _has_sufficient_volume(df_low))

    short_df = make_trending_df(n=10)
    check("Insufficient history returns True (allow through)", _has_sufficient_volume(short_df))


# ─────────────────────────────────────────────────────────────
# Test: HTF trend detection
# ─────────────────────────────────────────────────────────────

def test_htf_trend() -> None:
    print("\n[get_htf_trend]")
    up_df = make_trending_df(n=300, trend="up")
    trend = get_htf_trend(up_df, SCALPING)
    check("Uptrend HTF detected as UP or NEUTRAL (not DOWN)", trend != "DOWN")

    down_df = make_trending_df(n=300, trend="down")
    trend_down = get_htf_trend(down_df, SCALPING)
    check("Downtrend HTF detected as DOWN or NEUTRAL (not UP)", trend_down != "UP")

    short_df = make_trending_df(n=10)
    trend_short = get_htf_trend(short_df, SCALPING)
    check("Insufficient HTF rows returns NEUTRAL", trend_short == "NEUTRAL")


# ─────────────────────────────────────────────────────────────
# Test: get_signal returns NONE on dead market
# ─────────────────────────────────────────────────────────────

def test_get_signal_dead_market() -> None:
    print("\n[get_signal: dead market blocks all signals]")
    flat = make_flat_df(n=200, atr_pct=0.0002)
    sig, direction = get_signal(flat, flat, SCALPING)
    check("Dead market returns NONE signal", sig == "NONE")
    check("Dead market returns NONE direction", direction == "NONE")


# ─────────────────────────────────────────────────────────────
# Test: get_signal returns NONE with no volume
# ─────────────────────────────────────────────────────────────

def test_get_signal_low_volume() -> None:
    print("\n[get_signal: low volume blocks signals]")
    df = make_trending_df(n=200, atr_pct=0.008, volume_base=100.0)
    df_htf = make_trending_df(n=300, atr_pct=0.008, trend="up")
    # Collapse last bar volume to near-zero
    df.iloc[-1, df.columns.get_loc("volume")] = 0.01
    sig, direction = get_signal(df, df_htf, SCALPING)
    check("Low volume returns NONE direction", direction == "NONE")


# ─────────────────────────────────────────────────────────────
# Test: get_signal returns NONE on neutral HTF trend
# ─────────────────────────────────────────────────────────────

def test_get_signal_neutral_htf() -> None:
    print("\n[get_signal: neutral HTF trend blocks all signals]")
    # Sideways HTF: price oscillates around trend SMA
    df_htf = pd.DataFrame({
        "open": np.full(300, 85000.0),
        "high": np.full(300, 85100.0),
        "low": np.full(300, 84900.0),
        "close": np.full(300, 85000.0),
        "volume": np.full(300, 100.0),
    })
    df = make_trending_df(n=200, atr_pct=0.008)
    sig, direction = get_signal(df, df_htf, SCALPING)
    check("Neutral HTF trend returns NONE direction", direction == "NONE")


# ─────────────────────────────────────────────────────────────
# Test: validate_ohlcv raises on bad data
# ─────────────────────────────────────────────────────────────

def test_validate_ohlcv() -> None:
    print("\n[validate_ohlcv: input validation]")
    from src.bot.trade_helpers import validate_ohlcv

    good = make_trending_df(n=100)
    try:
        validate_ohlcv(good, min_rows=50)
        check("Valid OHLCV passes validation", True)
    except ValueError:
        check("Valid OHLCV passes validation", False)

    bad_cols = pd.DataFrame({"price": [1, 2, 3], "vol": [1, 2, 3]})
    try:
        validate_ohlcv(bad_cols)
        check("Missing columns raises ValueError", False)
    except ValueError:
        check("Missing columns raises ValueError", True)

    short_df = make_trending_df(n=10)
    try:
        validate_ohlcv(short_df, min_rows=50)
        check("Too-short DataFrame raises ValueError", False)
    except ValueError:
        check("Too-short DataFrame raises ValueError", True)


# ─────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    np.random.seed(42)
    test_dead_market_filter()
    test_market_trending_filter()
    test_volume_filter()
    test_htf_trend()
    test_get_signal_dead_market()
    test_get_signal_low_volume()
    test_get_signal_neutral_htf()
    test_validate_ohlcv()

    print()
    if _failures:
        print(f"\033[31m{len(_failures)} test(s) failed:\033[0m")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\033[32mAll tests passed.\033[0m")
