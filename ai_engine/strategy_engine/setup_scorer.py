import pandas as pd
from ai_engine.chart_analysis.analyzer import analyze_chart


def score_setup(df: pd.DataFrame, entry: float, sl: float, tp: float,
                symbol: str = "", timeframe: str = "H1") -> dict:
    """Score a proposed trade setup from 0–100."""
    analysis = analyze_chart(df, symbol, timeframe)
    if "error" in analysis:
        return {"score": 0, "grade": "F", "error": analysis["error"]}

    score      = 0
    strengths  = []
    weaknesses = []

    risk   = abs(entry - sl)
    reward = abs(tp - entry)
    rr     = reward / risk if risk > 0 else 0
    direction = "long" if tp > entry else "short"

    # ── R:R ──────────────────────────────────────────────────
    if rr >= 3.0:
        score += 25; strengths.append(f"Excellent R:R  ({rr:.2f})")
    elif rr >= 2.0:
        score += 18; strengths.append(f"Good R:R  ({rr:.2f})")
    elif rr >= 1.5:
        score += 10; strengths.append(f"Acceptable R:R  ({rr:.2f})")
    else:
        score -= 5;  weaknesses.append(f"Poor R:R  ({rr:.2f}) — aim for ≥ 1.5")

    # ── Trend alignment ───────────────────────────────────────
    bias = analysis["bias"]
    if (bias == "bullish" and direction == "long") or \
       (bias == "bearish" and direction == "short"):
        score += 20
        strengths.append(f"Aligned with {analysis['trend_strength']} {bias} trend")
    elif bias == "ranging":
        score += 5
        weaknesses.append("Ranging market — lower probability setups")
    else:
        score -= 10
        weaknesses.append("Entry against the main trend — higher risk")

    # ── Momentum (RSI) ────────────────────────────────────────
    rsi = analysis["indicators"].get("rsi", 50.0)
    if direction == "long":
        if 40 < rsi < 70:  score += 10; strengths.append(f"RSI neutral-bullish ({rsi:.0f})")
        elif rsi > 70:     weaknesses.append(f"Overbought RSI ({rsi:.0f}) — late entry risk")
    else:
        if 30 < rsi < 60:  score += 10; strengths.append(f"RSI neutral-bearish ({rsi:.0f})")
        elif rsi < 30:     weaknesses.append(f"Oversold RSI ({rsi:.0f}) — late entry risk")

    # ── Trend strength (ADX) ──────────────────────────────────
    adx = analysis["indicators"].get("adx", 20.0)
    if adx > 25:   score += 10; strengths.append(f"Strong trend (ADX {adx:.0f})")
    elif adx < 15: weaknesses.append(f"Weak/ranging ADX ({adx:.0f})")

    # ── Pattern confirmation ──────────────────────────────────
    cp = analysis.get("candlestick_patterns", [])
    sp = analysis.get("smc_patterns", [])
    if cp: score += min(len(cp) * 3, 10); strengths.append(f"{len(cp)} candlestick pattern(s)")
    if sp: score += min(len(sp) * 5, 15); strengths.append(f"{len(sp)} SMC/ICT signal(s)")

    score = min(max(score, 0), 100)
    grade = "A" if score >= 80 else ("B" if score >= 65 else
            ("C" if score >= 50 else ("D" if score >= 35 else "F")))

    if score >= 80:   tip = "High-quality setup. Enter with full risk and disciplined management."
    elif score >= 65: tip = "Good setup. Wait for one more confirmation before entering."
    elif score >= 50: tip = "Average setup. Reduce position size or wait for better conditions."
    elif score >= 35: tip = "Below average. Consider skipping this trade."
    else:             tip = "Poor setup. Do not trade. Wait for a higher-probability opportunity."

    return {
        "score":      score,
        "grade":      grade,
        "rr_ratio":   round(rr, 2),
        "direction":  direction,
        "trend_bias": bias,
        "strengths":  strengths,
        "weaknesses": weaknesses,
        "suggestion": tip,
        "analysis":   analysis,
    }
