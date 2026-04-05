"""Session detection and market analysis utilities."""

import logging
from datetime import datetime, timezone
from typing import Literal

import pandas as pd

from src.bot.strategy.indicators import atr

logger = logging.getLogger(__name__)

SessionName = Literal["Asian", "EU", "US", "Off"]

# UTC hour ranges (inclusive start, exclusive end)
_SESSION_HOURS: dict[str, tuple[int, int]] = {
    "US": (13, 22),
    "EU": (7, 16),
    "Asian": (0, 8),
}


def get_current_session() -> SessionName:
    """Return the active trading session based on UTC time."""
    hour = datetime.now(timezone.utc).hour
    for name, (start, end) in _SESSION_HOURS.items():
        if start <= hour < end:
            return name  # type: ignore[return-value]
    return "Off"


def calculate_atr_value(df: pd.DataFrame, period: int = 14) -> float:
    """Return the latest ATR value, or 0.0 if insufficient data."""
    if len(df) < period + 1:
        return 0.0
    series = atr(df, period)
    val = series.iloc[-1]
    return float(val) if not pd.isna(val) else 0.0


def calculate_volume_ratio(df: pd.DataFrame, period: int = 20) -> float:
    """Return current volume divided by the rolling average volume."""
    if len(df) < period + 1:
        return 1.0
    avg = df["volume"].iloc[-period - 1: -1].mean()
    current = df["volume"].iloc[-1]
    return float(current / avg) if avg > 0 else 1.0


def get_session_recommendation(
    session: SessionName, atr_val: float, volume_ratio: float
) -> str:
    """Produce a plain-text trading recommendation for the session."""
    if session == "Off":
        return "Off-hours — low liquidity, avoid trading"
    activity = (
        "high volume" if volume_ratio > 1.5
        else ("low volume" if volume_ratio < 0.7 else "normal volume")
    )
    messages = {
        "Asian": f"Asian session — range-bound, {activity}",
        "EU": f"EU session — trending likely, {activity}",
        "US": f"US session — high volatility expected, {activity}",
    }
    return messages.get(session, f"{session} session")
