import pandas as pd
import streamlit as st

# yfinance ticker symbols for each display name
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
    "DXY":     "DX-Y.NYB",
}

# (yfinance period, interval) per display timeframe
TIMEFRAME_MAP: dict[str, tuple[str, str]] = {
    "M5":  ("1d",  "5m"),
    "M15": ("5d",  "15m"),
    "H1":  ("1mo", "1h"),
    "H4":  ("3mo", "1h"),   # resample to 4h after fetch
    "D1":  ("1y",  "1d"),
    "W1":  ("5y",  "1wk"),
}

WATCHLIST_DEFAULT = ["EURUSD", "XAUUSD", "BTCUSDT", "US100", "GBPUSD"]


@st.cache_data(ttl=60)
def get_price_data(symbol: str, timeframe: str = "H1") -> pd.DataFrame:
    try:
        import yfinance as yf
        ticker = SYMBOL_MAP.get(symbol, symbol)
        period, interval = TIMEFRAME_MAP.get(timeframe, ("1mo", "1h"))
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        # Flatten MultiIndex columns that yfinance sometimes returns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df.index = pd.to_datetime(df.index)
        # Resample H1 → H4 when needed
        if timeframe == "H4":
            df = df.resample("4h").agg({
                "Open": "first", "High": "max",
                "Low": "min",   "Close": "last", "Volume": "sum",
            }).dropna()
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=30)
def get_market_overview(symbols: list[str] | None = None) -> list[dict]:
    try:
        import yfinance as yf
        symbols = symbols or WATCHLIST_DEFAULT
        result = []
        for sym in symbols:
            ticker = SYMBOL_MAP.get(sym, sym)
            try:
                hist = yf.download(ticker, period="2d", interval="1h",
                                   progress=False, auto_adjust=True)
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = [c[0] for c in hist.columns]
                if hist.empty or len(hist) < 2:
                    continue
                current = float(hist["Close"].iloc[-1])
                prev    = float(hist["Close"].iloc[-2])
                pct     = (current - prev) / prev * 100 if prev != 0 else 0.0
                result.append({
                    "symbol":     sym,
                    "price":      current,
                    "change_pct": pct,
                    "high":       float(hist["High"].max()),
                    "low":        float(hist["Low"].min()),
                })
            except Exception:
                continue
        return result
    except Exception:
        return []
