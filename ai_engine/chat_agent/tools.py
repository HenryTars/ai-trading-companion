"""
Chat Agent Tools
Each function fetches real data from the AI engine and returns a structured dict.
The agent calls these based on detected intent.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from typing import Dict, List, Optional


SYMBOL_ALIASES = {
    "gold": "XAUUSD", "xau": "XAUUSD", "xauusd": "XAUUSD",
    "bitcoin": "BTCUSDT", "btc": "BTCUSDT", "btcusdt": "BTCUSDT", "crypto": "BTCUSDT",
    "euro": "EURUSD", "eur": "EURUSD", "eurusd": "EURUSD",
    "pound": "GBPUSD", "gbp": "GBPUSD", "gbpusd": "GBPUSD", "sterling": "GBPUSD",
    "nasdaq": "US100", "nas": "US100", "us100": "US100", "ndx": "US100", "tech": "US100",
    "oil": "USOIL", "crude": "USOIL",
    "silver": "XAGUSD", "xag": "XAGUSD",
}

TIMEFRAME_ALIASES = {
    "daily": "D1", "day": "D1", "d": "D1", "d1": "D1", "1d": "D1",
    "4h": "H4", "h4": "H4", "4hour": "H4", "four hour": "H4",
    "1h": "H1", "h1": "H1", "hourly": "H1", "hour": "H1",
    "15m": "M15", "m15": "M15", "15min": "M15", "15": "M15",
    "5m": "M5", "m5": "M5",
    "weekly": "W1", "week": "W1", "w1": "W1", "w": "W1",
}


def resolve_symbol(text: str) -> Optional[str]:
    text = text.lower().strip()
    for alias, sym in SYMBOL_ALIASES.items():
        if alias in text:
            return sym
    return None


def resolve_timeframe(text: str) -> str:
    text = text.lower()
    for alias, tf in TIMEFRAME_ALIASES.items():
        if alias in text:
            return tf
    return "H4"


# ── Tools ─────────────────────────────────────────────────────

def tool_analyze(symbol: str, timeframe: str = "H4") -> Dict:
    from app.ui.market_data import get_price_data
    from ai_engine.chart_analysis.analyzer import analyze_chart
    df = get_price_data(symbol, timeframe)
    if df.empty:
        return {"error": f"No data available for {symbol} · {timeframe}"}
    a = analyze_chart(df, symbol, timeframe)
    return {
        "symbol":     symbol,
        "timeframe":  timeframe,
        "bias":       a.get("bias", "ranging"),
        "confidence": int(a.get("confidence", 0) * 100),
        "strength":   a.get("trend_strength", "—"),
        "momentum":   a.get("momentum", "—"),
        "risk":       a.get("risk_level", "—"),
        "volatility": a.get("volatility", "—"),
        "price":      a.get("current_price", 0),
        "narrative":  a.get("narrative", ""),
        "indicators": a.get("indicators", {}),
        "sr":         a.get("support_resistance", {}),
        "scenarios":  a.get("scenarios", []),
    }


def tool_price(symbol: str) -> Dict:
    from app.ui.market_data import get_price_data
    df = get_price_data(symbol, "M5")
    if df.empty:
        return {"error": f"Could not fetch price for {symbol}"}
    price = float(df["Close"].iloc[-1])
    pct   = (float(df["Close"].iloc[-1]) - float(df["Close"].iloc[0])) / float(df["Close"].iloc[0]) * 100
    return {"symbol": symbol, "price": price, "change_pct": round(pct, 3)}


def tool_patterns(symbol: str, timeframe: str = "H4") -> Dict:
    from app.ui.market_data import get_price_data
    from ai_engine.pattern_recognition.candlestick import detect_candlestick_patterns
    from ai_engine.pattern_recognition.smc_patterns import detect_smc_patterns
    from ai_engine.pattern_recognition.classic_patterns import detect_classic_patterns
    df = get_price_data(symbol, timeframe)
    if df.empty:
        return {"error": f"No data for {symbol}"}
    cp  = detect_candlestick_patterns(df)
    sp  = detect_smc_patterns(df)
    clp = detect_classic_patterns(df)
    all_p = sorted(cp + sp + clp, key=lambda x: x["index"], reverse=True)[:8]
    return {"symbol": symbol, "timeframe": timeframe, "patterns": all_p, "total": len(all_p)}


def tool_journal_stats() -> Dict:
    try:
        import requests
        perf = requests.get("http://localhost:8000/api/journal/performance", timeout=3).json()
        trades = requests.get("http://localhost:8000/api/journal/trades", params={"limit": 50}, timeout=3).json()
        return {"source": "journal", "perf": perf, "recent": trades[:5]}
    except Exception:
        pass
    return {"source": "none", "error": "Backend offline — start the API to access journal stats"}


def tool_paper_stats() -> Dict:
    import json
    state_file = ROOT / "database" / "paper_account.json"
    if not state_file.exists():
        return {"error": "No paper account found — run the autonomous scanner first"}
    data = json.loads(state_file.read_text(encoding="utf-8"))
    closed = data.get("closed_trades", [])
    wins = sum(1 for t in closed if t.get("status") == "win")
    return {
        "balance":    data.get("balance", 10000),
        "equity":     data.get("equity", 10000),
        "daily_pnl":  data.get("daily_pnl", 0),
        "total":      len(closed),
        "wins":       wins,
        "win_rate":   round(wins / len(closed) * 100, 1) if closed else 0,
        "consec_loss": data.get("consecutive_losses", 0),
    }


def tool_score_setup(symbol: str, entry: float, sl: float, tp: float, timeframe: str = "H4") -> Dict:
    from app.ui.market_data import get_price_data
    from ai_engine.strategy_engine.setup_scorer import score_setup
    df = get_price_data(symbol, timeframe)
    if df.empty:
        return {"error": f"No data for {symbol}"}
    return score_setup(df, entry, sl, tp, symbol, timeframe)


def tool_market_overview() -> Dict:
    from app.ui.market_data import get_market_overview
    overview = get_market_overview()
    return {"markets": overview or []}


def tool_multi_timeframe(symbol: str) -> Dict:
    from ai_engine.market_insights.multi_timeframe import multi_timeframe_analysis
    return multi_timeframe_analysis(symbol)


def tool_backtest_summary(symbol: str, timeframe: str = "H4") -> Dict:
    from autonomous_trading.simulation_engine.backtester import run_backtest
    result = run_backtest(symbol, timeframe, lookback=50, forward=20,
                          conf_threshold=0.60, risk_pct=1.0)
    if "error" in result:
        return result
    return {
        "symbol":       result["symbol"],
        "timeframe":    result["timeframe"],
        "total_trades": result["total_trades"],
        "win_rate":     result["win_rate"],
        "total_return": result["total_return"],
        "max_drawdown": result["max_drawdown"],
        "sharpe":       result["sharpe"],
        "profit_factor": result["profit_factor"],
    }
