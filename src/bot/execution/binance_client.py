"""Binance REST API client supporting paper, testnet, and live modes."""

import hashlib
import hmac
import logging
import time
from typing import Any, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

BINANCE_BASE = "https://api.binance.com"
TESTNET_BASE = "https://testnet.binance.vision"

_MAX_RETRIES = 3
_RETRY_DELAY = 1.0  # seconds between retries


class BinanceClient:
    """Wraps Binance public and private REST endpoints."""

    def __init__(
        self,
        api_key: str = "",
        secret_key: str = "",
        testnet: bool = False,
        paper: bool = True,
    ) -> None:
        """Initialise the client. Paper mode skips order placement."""
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._base_url = TESTNET_BASE if testnet and not paper else BINANCE_BASE
        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": api_key})

    def _sign(self, params: dict) -> dict:
        """Add HMAC-SHA256 signature to a parameter dict."""
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        sig = hmac.new(
            self._secret_key.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        params["signature"] = sig
        return params

    def _get(self, endpoint: str, params: Optional[dict] = None) -> Any:
        """Unsigned GET with retry on transient network errors."""
        last_exc: Exception = RuntimeError("No attempts made")
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = self._session.get(
                    f"{self._base_url}{endpoint}", params=params, timeout=10
                )
                resp.raise_for_status()
                return resp.json()
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                logger.warning("GET %s attempt %d/%d failed: %s", endpoint, attempt, _MAX_RETRIES, exc)
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY * attempt)
            except requests.HTTPError as exc:
                # Don't retry on 4xx client errors
                raise
        raise last_exc

    def _post_signed(self, endpoint: str, params: dict) -> Any:
        """Signed POST with retry on transient network errors."""
        last_exc: Exception = RuntimeError("No attempts made")
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = self._session.post(
                    f"{self._base_url}{endpoint}", params=self._sign(params), timeout=10
                )
                resp.raise_for_status()
                return resp.json()
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                logger.warning("POST %s attempt %d/%d failed: %s", endpoint, attempt, _MAX_RETRIES, exc)
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY * attempt)
            except requests.HTTPError as exc:
                raise
        raise last_exc

    def get_price(self, symbol: str) -> float:
        """Return the latest price for a symbol."""
        data = self._get("/api/v3/ticker/price", {"symbol": symbol})
        price = float(data["price"])
        if price <= 0:
            raise ValueError(f"Invalid price returned for {symbol}: {price}")
        return price

    def get_ticker_24h(self, symbol: str) -> dict:
        """Return 24-hour ticker statistics."""
        return self._get("/api/v3/ticker/24hr", {"symbol": symbol})

    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> list[dict]:
        """Return OHLCV klines as a list of dicts."""
        raw = self._get(
            "/api/v3/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
        )
        if not isinstance(raw, list):
            raise ValueError(f"Unexpected klines response type: {type(raw)}")
        return [
            {
                "open_time": r[0],
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
                "close_time": r[6],
            }
            for r in raw
        ]

    def place_order(self, symbol: str, side: str, quantity: float) -> dict:
        """Place a market order. In paper mode, logs and returns a mock response."""
        if self._paper:
            logger.info("PAPER ORDER: %s %s qty=%.6f", side, symbol, quantity)
            return {
                "orderId": "paper",
                "status": "FILLED",
                "side": side,
                "executedQty": str(quantity),
            }
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": f"{quantity:.6f}",
        }
        return self._post_signed("/api/v3/order", params)
