"""
OHLCV data service — pure FastAPI, no Streamlit dependency.
Uses yfinance with an in-process TTL cache.
"""

import time
import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

# ── Symbol / Timeframe maps ───────────────────────────────────────────────────

SYMBOL_MAP: dict[str, str] = {
    "EURUSD":  "EURUSD=X",
    "GBPUSD":  "GBPUSD=X",
    "USDJPY":  "USDJPY=X",
    "AUDUSD":  "AUDUSD=X",
    "USDCAD":  "USDCAD=X",
    "XAUUSD":  "GC=F",
    "XAGUSD":  "SI=F",
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "US100":   "NQ=F",
    "US500":   "^GSPC",
    "US30":    "YM=F",
    "OIL":     "CL=F",
}

# (period, interval) for yfinance, candle_count target
TIMEFRAME_MAP: dict[str, tuple[str, str, int]] = {
    "M5":  ("1d",  "5m",  200),
    "M15": ("5d",  "15m", 200),
    "H1":  ("1mo", "1h",  200),
    "H4":  ("3mo", "1h",  150),   # resample after fetch
    "D1":  ("1y",  "1d",  250),
    "W1":  ("5y",  "1wk", 200),
}

# ── Simple TTL cache ──────────────────────────────────────────────────────────

_cache: dict[str, tuple[float, list[dict]]] = {}
_CACHE_TTL = 60  # seconds


def _cache_key(symbol: str, timeframe: str) -> str:
    return f"{symbol}:{timeframe}"


def _get_cached(key: str) -> Optional[list[dict]]:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < _CACHE_TTL:
            return data
    return None


def _set_cached(key: str, data: list[dict]) -> None:
    _cache[key] = (time.time(), data)


# ── OHLCV fetch ───────────────────────────────────────────────────────────────

def get_ohlcv(symbol: str, timeframe: str = "H1") -> list[dict]:
    """
    Returns list of {time, open, high, low, close, volume} dicts.
    time is a Unix timestamp (seconds) — LightweightCharts format.
    """
    key = _cache_key(symbol.upper(), timeframe.upper())
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        import yfinance as yf

        tf = timeframe.upper()
        ticker_sym = SYMBOL_MAP.get(symbol.upper(), symbol.upper())
        period, interval, _ = TIMEFRAME_MAP.get(tf, ("1mo", "1h", 200))

        df = yf.download(
            ticker_sym,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
        )

        if df.empty:
            logger.warning("No data from yfinance for %s (%s)", symbol, ticker_sym)
            return []

        # Flatten MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        df.index = pd.to_datetime(df.index, utc=True)

        # Resample H4
        if tf == "H4":
            df = (
                df.resample("4h")
                .agg({"Open": "first", "High": "max", "Low": "min",
                      "Close": "last", "Volume": "sum"})
                .dropna()
            )

        result = []
        for ts, row in df.iterrows():
            o = float(row["Open"])
            h = float(row["High"])
            l = float(row["Low"])
            c = float(row["Close"])
            v = float(row.get("Volume", 0))
            if any(pd.isna(x) for x in [o, h, l, c]):
                continue
            result.append({
                "time":   int(ts.timestamp()),
                "open":   round(o, 5),
                "high":   round(h, 5),
                "low":    round(l, 5),
                "close":  round(c, 5),
                "volume": round(v, 2),
            })

        _set_cached(key, result)
        return result

    except Exception as exc:
        logger.error("OHLCV fetch failed for %s/%s: %s", symbol, timeframe, exc)
        return []


def get_latest_price(symbol: str) -> Optional[dict]:
    """Single latest price tick from yfinance."""
    try:
        import yfinance as yf
        ticker_sym = SYMBOL_MAP.get(symbol.upper(), symbol.upper())
        t = yf.Ticker(ticker_sym)
        info = t.fast_info
        price = getattr(info, "last_price", None) or getattr(info, "regularMarketPrice", None)
        prev  = getattr(info, "previous_close", None)
        if price and prev:
            change     = price - prev
            change_pct = (change / prev) * 100
        else:
            change = change_pct = 0.0
        return {
            "symbol":     symbol.upper(),
            "price":      round(price, 5) if price else 0,
            "change":     round(change, 5),
            "change_pct": round(change_pct, 3),
            "spread":     0.0,
        }
    except Exception:
        return None


def get_market_overview() -> list[dict]:
    symbols = ["XAUUSD", "EURUSD", "GBPUSD", "BTCUSDT", "US100"]
    result = []
    for sym in symbols:
        info = get_latest_price(sym)
        if info:
            result.append(info)
    return result
