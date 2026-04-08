"""Tests for circuit breaker logic and daily reset behaviour.

Run from the project root:
    python -m pytest tests/test_circuit_breaker.py -v
or:
    python -m tests.test_circuit_breaker
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from src.bot.risk.risk_manager import RiskConfig, RiskManager


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def make_rm(equity: float = 1000.0, max_daily_loss_pct: float = 0.02) -> RiskManager:
    cfg = RiskConfig(
        risk_per_trade_pct=0.01,
        max_daily_loss_pct=max_daily_loss_pct,
    )
    return RiskManager(cfg, initial_equity=equity)


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
# Test: CB does not trip when no losses
# ─────────────────────────────────────────────────────────────

def test_cb_no_losses() -> None:
    print("\n[CB: no losses]")
    rm = make_rm()
    check("CB returns False when daily_pnl=0", not rm.check_daily_circuit_breaker())
    rm.record_trade_close(5.0)  # profitable trade
    check("CB returns False after profit", not rm.check_daily_circuit_breaker())


# ─────────────────────────────────────────────────────────────
# Test: CB trips at threshold
# ─────────────────────────────────────────────────────────────

def test_cb_trips_at_threshold() -> None:
    print("\n[CB: trips at 2% loss]")
    rm = make_rm(equity=1000.0, max_daily_loss_pct=0.02)
    # 1.9% loss — should NOT trip
    rm.record_trade_close(-19.0)
    check("CB False at 1.9% loss", not rm.check_daily_circuit_breaker())
    # Additional loss to reach 2.0%
    rm.record_trade_close(-1.0)
    check("CB True at exactly 2.0% loss", rm.check_daily_circuit_breaker())


# ─────────────────────────────────────────────────────────────
# Test: daily reset clears CB state
# ─────────────────────────────────────────────────────────────

def test_daily_reset_clears_cb() -> None:
    print("\n[CB: daily reset]")
    rm = make_rm(equity=1000.0, max_daily_loss_pct=0.02)
    rm.record_trade_close(-25.0)  # 2.5% — CB tripped
    check("CB tripped before reset", rm.check_daily_circuit_breaker())
    rm.reset_daily_stats()
    check("CB False after reset_daily_stats", not rm.check_daily_circuit_breaker())
    check("daily_pnl zeroed", rm.daily_pnl == 0.0)
    check("daily_trades zeroed", rm.daily_trades == 0)


# ─────────────────────────────────────────────────────────────
# Test: equity tracks correctly across trades
# ─────────────────────────────────────────────────────────────

def test_equity_tracking() -> None:
    print("\n[RM: equity tracking]")
    rm = make_rm(equity=1000.0)
    rm.record_trade_close(10.0)
    check("equity +10 after win", rm.equity == 1010.0)
    rm.record_trade_close(-5.0)
    check("equity -5 after loss", rm.equity == 1005.0)
    check("daily_pnl = net +5", rm.daily_pnl == 5.0)
    check("daily_trades = 2", rm.daily_trades == 2)


# ─────────────────────────────────────────────────────────────
# Test: CB computes loss_pct against CURRENT equity (not initial)
# ─────────────────────────────────────────────────────────────

def test_cb_uses_current_equity() -> None:
    print("\n[CB: uses current equity]")
    rm = make_rm(equity=1000.0, max_daily_loss_pct=0.02)
    # Win pushes equity to 1100 — now 2% threshold is $22, not $20
    rm.record_trade_close(100.0)
    rm.reset_daily_stats()  # new day — equity stays at 1100
    rm.record_trade_close(-21.0)  # 1.9% of 1100 — should NOT trip
    check("CB False: 21 loss vs 1100 equity (1.9%)", not rm.check_daily_circuit_breaker())
    rm.record_trade_close(-2.0)  # now 23/1100 = 2.09% — should trip
    check("CB True: 23 loss vs 1100 equity (2.09%)", rm.check_daily_circuit_breaker())


# ─────────────────────────────────────────────────────────────
# Test: _signal_pause_until cleared on BotRunner daily reset
# (integration: verifies _check_daily_reset clears the pause)
# ─────────────────────────────────────────────────────────────

def test_botrunner_daily_reset_pause_behaviour() -> None:
    """V8: daily reset only clears an EXPIRED pause, preserves an active one.

    A CB that trips at 23:59 and sets a 4-hour pause must not be cut to 1 minute
    by the midnight daily reset — the full 4 hours must still elapse.
    """
    print("\n[BotRunner: daily reset pause behaviour (V8)]")

    from src.bot.bot_runner import BotState, BotRunner
    from src.config.settings import Settings

    settings = Settings(initial_capital=1000.0, default_mode="paper", default_style="scalping")

    # Case 1: pause still active — should NOT be cleared by daily reset
    state = BotState(settings)
    future = datetime.now(timezone.utc) + timedelta(hours=3)
    state._signal_pause_until = future
    state._daily_reset_date = "2000-01-01"
    BotRunner(state)._check_daily_reset()
    check("Active pause preserved across daily reset", state._signal_pause_until == future)
    check("daily_pnl zeroed on reset", state.portfolio.daily_pnl == 0.0)
    check("risk_manager daily_pnl zeroed on reset", state.risk_manager.daily_pnl == 0.0)

    # Case 2: pause already expired — should be cleared
    state2 = BotState(settings)
    expired = datetime.now(timezone.utc) - timedelta(minutes=1)
    state2._signal_pause_until = expired
    state2._daily_reset_date = "2000-01-01"
    BotRunner(state2)._check_daily_reset()
    check("Expired pause cleared at daily reset", state2._signal_pause_until is None)


# ─────────────────────────────────────────────────────────────
# Test: CB in _tick does NOT keep resetting pause timer
# ─────────────────────────────────────────────────────────────

def test_cb_pause_not_extended_on_subsequent_ticks() -> None:
    """
    Core regression: when the CB is already paused, subsequent ticks must NOT
    overwrite _signal_pause_until (which would perpetually extend the pause).
    The fixed logic skips the CB check entirely when an active pause exists.
    """
    print("\n[BotRunner: CB pause timer not reset on every tick]")

    from src.bot.bot_runner import BotState, BotRunner
    from src.config.settings import Settings

    settings = Settings(
        initial_capital=1000.0,
        default_mode="paper",
        default_style="scalping",
    )
    state = BotState(settings)

    # Artificially set a 4-hour pause 1 minute ago (so it started 1 min ago, expires in 3h59m)
    original_pause = datetime.now(timezone.utc) + timedelta(hours=3, minutes=59)
    state._signal_pause_until = original_pause

    # Also put daily_pnl into CB territory
    state.risk_manager.daily_pnl = -30.0  # 3% loss on $1000 equity

    # Mock client to avoid network calls
    mock_client = MagicMock()
    mock_client.get_price.return_value = 85000.0

    with patch.object(state, "get_client", return_value=mock_client):
        runner = BotRunner(state)
        runner._check_daily_reset = MagicMock()  # skip date check
        runner._tick()

    # pause_until should NOT have been overwritten to a later time
    check(
        "_signal_pause_until unchanged after tick with active pause",
        state._signal_pause_until == original_pause,
    )


# ─────────────────────────────────────────────────────────────
# Test: CB watermark prevents re-trip on same losses
# ─────────────────────────────────────────────────────────────

def test_cb_watermark_prevents_retrip() -> None:
    """After CB trips, it must NOT re-trip at the same loss level.

    This prevents the 4h-pause → re-trip → 4h-pause infinite loop that
    locked the bot out for the rest of the day.
    """
    print("\n[CB: watermark prevents re-trip on same losses]")
    rm = make_rm(equity=1000.0, max_daily_loss_pct=0.02)
    rm.record_trade_close(-25.0)  # 2.5% — will trip
    check("CB trips on first check", rm.check_daily_circuit_breaker())
    # Same loss level — should NOT re-trip (watermark set to -25)
    check("CB does NOT re-trip at same loss", not rm.check_daily_circuit_breaker())
    # New loss deepens past watermark — should re-trip
    rm.record_trade_close(-5.0)  # daily_pnl now -30
    check("CB re-trips after deeper loss", rm.check_daily_circuit_breaker())
    # Same deeper level — should NOT re-trip again
    check("CB does NOT re-trip at same deeper loss", not rm.check_daily_circuit_breaker())
    # Daily reset clears watermark
    rm.reset_daily_stats()
    check("Watermark cleared after reset", rm._cb_pnl_watermark is None)


# ─────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_cb_no_losses()
    test_cb_trips_at_threshold()
    test_daily_reset_clears_cb()
    test_equity_tracking()
    test_cb_uses_current_equity()
    test_botrunner_daily_reset_pause_behaviour()
    test_cb_pause_not_extended_on_subsequent_ticks()
    test_cb_watermark_prevents_retrip()

    print()
    if _failures:
        print(f"\033[31m{len(_failures)} test(s) failed:\033[0m")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\033[32mAll tests passed.\033[0m")
