import asyncio
import json
import logging
from datetime import datetime, timezone
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Typical pip-unit spreads for yfinance fallback (in price units)
_SPREADS: dict[str, float] = {
    "XAUUSD":  0.30,
    "EURUSD":  0.00012,
    "GBPUSD":  0.00015,
    "BTCUSDT": 5.0,
    "US100":   0.5,
}


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, symbol: str) -> None:
        await websocket.accept()
        self._connections.setdefault(symbol, []).append(websocket)

    def disconnect(self, websocket: WebSocket, symbol: str) -> None:
        conns = self._connections.get(symbol, [])
        if websocket in conns:
            conns.remove(websocket)

    async def broadcast(self, symbol: str, data: dict) -> None:
        dead = []
        for ws in self._connections.get(symbol, []):
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, symbol)

    def subscriber_count(self, symbol: str) -> int:
        return len(self._connections.get(symbol, []))


manager = ConnectionManager()


def _mt5_tick(symbol: str) -> dict | None:
    """Get real bid/ask from MT5 (synchronous — runs in executor)."""
    try:
        import MetaTrader5 as mt5
        tick = mt5.symbol_info_tick(symbol)
        if tick is None or tick.bid == 0:
            return None
        spread = round(tick.ask - tick.bid, 5)
        return {
            "symbol":    symbol,
            "bid":       round(tick.bid, 5),
            "ask":       round(tick.ask, 5),
            "spread":    round(spread, 5),
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
    except Exception:
        return None


def _yfinance_tick(symbol: str) -> dict | None:
    """Fetch latest price from yfinance and simulate bid/ask."""
    try:
        import yfinance as yf
        import pandas as pd
        from backend.services.ohlcv_service import SYMBOL_MAP

        ticker_sym = SYMBOL_MAP.get(symbol, symbol)
        hist = yf.download(ticker_sym, period="1d", interval="1m",
                           progress=False, auto_adjust=True)
        if hist.empty:
            return None

        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [c[0] for c in hist.columns]

        price  = float(hist["Close"].iloc[-1])
        spread = _SPREADS.get(symbol, 0.0001)
        half   = spread / 2

        return {
            "symbol":    symbol,
            "bid":       round(price - half, 5),
            "ask":       round(price + half, 5),
            "spread":    round(spread, 5),
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
    except Exception:
        return None


async def price_feed_loop(symbol: str, interval: float = 5.0) -> None:
    """Stream live price ticks with correct bid/ask/spread format."""
    from backend.mt5_bridge.connector import connector

    loop = asyncio.get_event_loop()

    while True:
        if manager.subscriber_count(symbol) == 0:
            await asyncio.sleep(interval)
            continue

        try:
            tick = None

            # Prefer MT5 for real bid/ask spreads
            if connector.is_connected:
                tick = await loop.run_in_executor(None, _mt5_tick, symbol)

            # Fallback to yfinance with simulated spread
            if tick is None:
                tick = await loop.run_in_executor(None, _yfinance_tick, symbol)

            if tick:
                await manager.broadcast(symbol, tick)

        except Exception as exc:
            logger.debug("Price feed error for %s: %s", symbol, exc)

        await asyncio.sleep(interval)
