import pandas as pd
import numpy as np

from ai_engine.chart_analysis.indicators import compute_all
from ai_engine.chart_analysis.market_structure import get_trend, get_support_resistance
from ai_engine.pattern_recognition.candlestick import detect_candlestick_patterns
from ai_engine.pattern_recognition.smc_patterns import detect_smc_patterns


def _safe(series: pd.Series) -> float:
    val = series.iloc[-1]
    return float(val) if not (isinstance(val, float) and np.isnan(val)) else 0.0


def _confidence(trend: dict, rsi: float, adx: float, macd_hist: float,
                candles: list, smc: list) -> float:
    score = 50.0

    if trend["strength"] == "strong":   score += 15
    elif trend["strength"] == "moderate": score += 8

    if adx > 30:    score += 10
    elif adx > 20:  score += 5
    elif adx < 15:  score -= 10

    if trend["direction"] == "bullish":
        if 40 < rsi < 70:  score += 8
        elif rsi > 70:     score -= 5
    elif trend["direction"] == "bearish":
        if 30 < rsi < 60:  score += 8
        elif rsi < 30:     score -= 5

    if (trend["direction"] == "bullish" and macd_hist > 0) or \
       (trend["direction"] == "bearish" and macd_hist < 0):
        score += 7

    score += min(len(candles) * 3, 10)
    score += min(len(smc)     * 5, 15)

    return round(min(max(score, 10), 95), 1)


def _narrative(trend: dict, rsi: float, adx: float, momentum: str,
               risk: str, sr: dict, symbol: str, timeframe: str) -> str:
    d  = trend["direction"].capitalize()
    st = trend["strength"]
    ns = f"{sr['nearest_support']:.5f}"    if sr.get("nearest_support")    else "—"
    nr = f"{sr['nearest_resistance']:.5f}" if sr.get("nearest_resistance") else "—"

    trend_desc = "confirms a trending market" if adx > 25 else "suggests ranging / consolidating conditions"
    lines = [
        f"**{symbol} · {timeframe} AI Analysis**",
        f"The market is in a **{st} {d}** phase. ADX at {adx:.1f} {trend_desc}.",
        f"Momentum is **{momentum}** (RSI: {rsi:.1f}).",
        f"Nearest support: **{ns}**  ·  Nearest resistance: **{nr}**.",
        f"Overall risk classification: **{risk}**.",
    ]

    if trend["direction"] == "bullish":
        lines.append("Look for pullback entries near support / demand zones with bullish confirmation candles.")
    elif trend["direction"] == "bearish":
        lines.append("Look for bearish continuation setups near resistance / supply zones.")
    else:
        lines.append("Range conditions — trade the boundaries or wait for a confirmed directional breakout.")

    return "\n\n".join(lines)


def analyze_chart(df: pd.DataFrame, symbol: str = "", timeframe: str = "H1") -> dict:
    if df.empty or len(df) < 20:
        return {"error": "Insufficient data (need ≥ 20 candles)"}

    ind     = compute_all(df)
    trend   = get_trend(df)
    sr      = get_support_resistance(df)
    candles = detect_candlestick_patterns(df)
    smc     = detect_smc_patterns(df)

    rsi_val      = _safe(ind["rsi"])
    adx_val      = _safe(ind["adx"])
    macd_hist    = _safe(ind["macd_hist"])
    atr_val      = _safe(ind["atr"])
    price        = float(df["Close"].iloc[-1])

    # Momentum label
    if rsi_val > 70:       momentum = "Overbought"
    elif rsi_val < 30:     momentum = "Oversold"
    elif rsi_val > 55:     momentum = "Bullish Momentum"
    elif rsi_val < 45:     momentum = "Bearish Momentum"
    else:                  momentum = "Neutral"

    # Volatility label (ATR as % of price)
    atr_pct = (atr_val / price * 100) if price > 0 else 0
    if atr_pct > 1.5:      volatility = "High"
    elif atr_pct > 0.5:    volatility = "Medium"
    else:                  volatility = "Low"

    # Risk label
    risk = volatility   # risk and volatility share the same threshold

    conf = _confidence(trend, rsi_val, adx_val, macd_hist, candles, smc)

    return {
        "symbol":         symbol,
        "timeframe":      timeframe,
        "bias":           trend["direction"],
        "trend_strength": trend["strength"],
        "confidence":     round(conf / 100, 2),
        "risk_level":     risk,
        "momentum":       momentum,
        "volatility":     volatility,
        "current_price":  price,
        "indicators": {
            "rsi":       round(rsi_val, 2),
            "adx":       round(adx_val, 2),
            "macd_hist": round(macd_hist, 6),
            "atr":       round(atr_val,  5),
            "ema20":     round(_safe(ind["ema20"]),  5),
            "ema50":     round(_safe(ind["ema50"]),  5),
            "bb_upper":  round(_safe(ind["bb_upper"]), 5),
            "bb_lower":  round(_safe(ind["bb_lower"]), 5),
        },
        "support_resistance":  sr,
        "candlestick_patterns": candles,
        "smc_patterns":         smc,
        "narrative": _narrative(trend, rsi_val, adx_val, momentum, risk, sr, symbol, timeframe),
    }
