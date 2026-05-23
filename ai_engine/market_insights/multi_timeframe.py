import streamlit as st
from ai_engine.chart_analysis.analyzer import analyze_chart

TIMEFRAMES = ["W1", "D1", "H4", "H1", "M15"]


@st.cache_data(ttl=120)
def multi_timeframe_analysis(symbol: str, timeframes: list[str] | None = None) -> dict:
    from app.ui.market_data import get_price_data

    timeframes = timeframes or TIMEFRAMES
    results: dict = {}
    votes = {"bullish": 0, "bearish": 0, "ranging": 0}

    for tf in timeframes:
        df = get_price_data(symbol, tf)
        if not df.empty and len(df) >= 20:
            a = analyze_chart(df, symbol, tf)
            bias = a.get("bias", "ranging")
            results[tf] = {
                "bias":           bias,
                "confidence":     a.get("confidence", 0.5),
                "trend_strength": a.get("trend_strength", "weak"),
                "rsi":            a.get("indicators", {}).get("rsi"),
                "adx":            a.get("indicators", {}).get("adx"),
            }
            votes[bias] = votes.get(bias, 0) + 1
        else:
            results[tf] = {"bias": "no_data", "confidence": 0}

    valid = sum(1 for v in results.values() if v["bias"] != "no_data")
    dominant = max(votes, key=votes.get) if valid else "unknown"
    alignment = round(votes.get(dominant, 0) / valid * 100, 1) if valid else 0

    return {
        "symbol":          symbol,
        "results":         results,
        "overall_bias":    dominant,
        "alignment_score": alignment,
        "bias_votes":      votes,
    }
