import asyncio
import json
from fastapi import WebSocket


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


async def price_feed_loop(symbol: str, interval: float = 10.0) -> None:
    """Fetch latest price every `interval` seconds and push to subscribed clients."""
    import yfinance as yf
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from app.ui.market_data import SYMBOL_MAP

    ticker_sym = SYMBOL_MAP.get(symbol, symbol)

    while True:
        if manager.subscriber_count(symbol) == 0:
            await asyncio.sleep(interval)
            continue
        try:
            hist = yf.download(ticker_sym, period="1d", interval="1m",
                               progress=False, auto_adjust=True)
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                await manager.broadcast(symbol, {
                    "symbol":    symbol,
                    "price":     price,
                    "timestamp": str(hist.index[-1]),
                })
        except Exception:
            pass
        await asyncio.sleep(interval)
