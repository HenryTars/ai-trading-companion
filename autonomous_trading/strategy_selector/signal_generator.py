"""
Signal Generator
Scans a watchlist using the AI engine and produces structured trade signals
with entry, SL, TP, direction, confidence, and R:R.
"""
from typing import Dict, List

WATCHLIST = ["XAUUSD", "EURUSD", "BTCUSDT", "GBPUSD", "US100"]
SCAN_TIMEFRAMES = ["H4", "H1"]


def _atr_from_df(df) -> float:
    if df.empty or len(df) < 14:
        return float(df["Close"].iloc[-1]) * 0.001 if not df.empty else 1.0
    high = df["High"]
    low  = df["Low"]
    close = df["Close"]
    tr = (high - low).combine(
        (high - close.shift()).abs(),
        max).combine(
        (low  - close.shift()).abs(),
        max)
    return float(tr.rolling(14).mean().iloc[-1])


def _build_signal(symbol: str, df, analysis: Dict, timeframe: str) -> Dict:
    bias  = analysis.get("bias", "ranging")
    conf  = analysis.get("confidence", 0.5)
    price = float(df["Close"].iloc[-1])
    atr   = _atr_from_df(df)

    if bias == "bullish":
        direction = "long"
        entry = price
        sl    = round(price - atr * 1.5, 5)
        tp    = round(price + atr * 3.0, 5)
    elif bias == "bearish":
        direction = "short"
        entry = price
        sl    = round(price + atr * 1.5, 5)
        tp    = round(price - atr * 3.0, 5)
    else:
        return {}

    rr = round(abs(tp - entry) / max(abs(entry - sl), 1e-10), 2)

    return {
        "symbol":      symbol,
        "timeframe":   timeframe,
        "direction":   direction,
        "bias":        bias,
        "confidence":  conf,
        "entry":       round(entry, 5),
        "sl":          sl,
        "tp":          tp,
        "rr":          rr,
        "risk_pct":    1.0,
        "trend_strength": analysis.get("trend_strength", "—"),
        "risk_level":  analysis.get("risk_level", "—"),
        "narrative":   analysis.get("narrative", ""),
    }


def scan_signals(symbols: List[str] = None, timeframe: str = "H4") -> List[Dict]:
    """
    Scans symbols on the given timeframe.
    Returns list of signal dicts, sorted by confidence descending.
    """
    from app.ui.market_data import get_price_data
    from ai_engine.chart_analysis.analyzer import analyze_chart

    if symbols is None:
        symbols = WATCHLIST

    signals = []
    for symbol in symbols:
        try:
            df = get_price_data(symbol, timeframe)
            if df.empty or len(df) < 30:
                continue
            analysis = analyze_chart(df, symbol, timeframe)
            sig = _build_signal(symbol, df, analysis, timeframe)
            if sig:
                signals.append(sig)
        except Exception:
            pass

    return sorted(signals, key=lambda s: s.get("confidence", 0), reverse=True)


def get_signal_for(symbol: str, timeframe: str = "H4") -> Dict:
    """Single-symbol signal lookup."""
    results = scan_signals([symbol], timeframe)
    return results[0] if results else {}
