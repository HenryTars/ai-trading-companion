"""
AI Trade Reviewer
Scores a single trade on entry quality, R:R, timing, and alignment.
Works fully offline — no external API required.
"""
from typing import Dict, List


def _rr(entry: float, sl: float, tp: float) -> float:
    risk   = abs(entry - sl)
    reward = abs(tp - entry)
    return round(reward / risk, 2) if risk > 0 else 0.0


def _grade(score: int) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    if score >= 40: return "D"
    return "F"


def review_trade(trade: Dict) -> Dict:
    """
    Scores a trade dict and returns a structured AI review.
    Required fields: entry_price, stop_loss, take_profit, direction,
                     symbol, session, strategy, status, risk_percent
    Optional: pnl_percent, notes, ai_confidence
    """
    entry  = float(trade.get("entry_price", 0) or 0)
    sl     = float(trade.get("stop_loss",   0) or 0)
    tp     = float(trade.get("take_profit", 0) or 0)
    risk   = float(trade.get("risk_percent", 1) or 1)
    status = trade.get("status", "open")
    direction = trade.get("direction", "long")
    session   = trade.get("session",   "Other")
    strategy  = trade.get("strategy",  "Custom")
    ai_conf   = float(trade.get("ai_confidence") or 0)

    score      = 50
    strengths: List[str] = []
    weaknesses: List[str] = []

    # ── R:R scoring ───────────────────────────────────────────
    rr = _rr(entry, sl, tp)
    if rr >= 3.0:
        score += 20; strengths.append(f"Excellent R:R of {rr} — reward strongly outweighs risk")
    elif rr >= 2.0:
        score += 12; strengths.append(f"Good R:R of {rr} — solid risk management")
    elif rr >= 1.5:
        score += 5;  strengths.append(f"Acceptable R:R of {rr}")
    elif rr >= 1.0:
        score -= 5;  weaknesses.append(f"Marginal R:R of {rr} — reward barely covers risk")
    else:
        score -= 15; weaknesses.append(f"Poor R:R of {rr} — risk exceeds potential reward")

    # ── Risk sizing ───────────────────────────────────────────
    if risk <= 1.0:
        score += 8; strengths.append(f"Conservative risk sizing at {risk}% — capital protected")
    elif risk <= 2.0:
        score += 4; strengths.append(f"Reasonable risk at {risk}%")
    elif risk <= 3.0:
        score -= 5; weaknesses.append(f"Elevated risk at {risk}% — consider reducing")
    else:
        score -= 15; weaknesses.append(f"High risk at {risk}% — significantly above safe threshold")

    # ── Session quality ───────────────────────────────────────
    high_vol_sessions = {"London", "New York"}
    if session in high_vol_sessions:
        score += 6; strengths.append(f"{session} session — optimal liquidity and volatility")
    elif session == "Asian":
        score -= 3; weaknesses.append("Asian session — lower volatility, wider spreads on most pairs")

    # ── Strategy recognition ──────────────────────────────────
    structured = {"SMC", "ICT", "Price Action", "Trend Follow"}
    if strategy in structured:
        score += 5; strengths.append(f"Structured strategy ({strategy}) with defined rules")

    # ── AI confidence alignment ───────────────────────────────
    if ai_conf >= 0.75:
        score += 8; strengths.append(f"High AI confidence ({int(ai_conf*100)}%) at trade entry")
    elif ai_conf >= 0.55:
        score += 3
    elif 0 < ai_conf < 0.4:
        score -= 8; weaknesses.append(f"Low AI confidence ({int(ai_conf*100)}%) — trade taken against signal")

    # ── Outcome adjustment (for closed trades) ────────────────
    if status == "win":
        score += 5; strengths.append("Trade reached target — execution validated")
    elif status == "loss":
        if rr >= 2.0:
            weaknesses.append("Loss on a good setup — review entry timing and market conditions")
        else:
            score -= 5; weaknesses.append("Loss on a poor R:R setup — avoid low-quality entries")
    elif status == "breakeven":
        strengths.append("Breakeven — risk was managed and capital preserved")

    # ── Clamp and grade ───────────────────────────────────────
    score = max(10, min(98, score))
    grade = _grade(score)

    # ── Improvement tip ───────────────────────────────────────
    if score >= 85:
        improvement = "Excellent execution. Keep following this framework consistently."
    elif score >= 70:
        improvement = f"Good trade. Focus on {'improving R:R to 2.5+' if rr < 2.5 else 'reducing risk per trade to ≤1.5%'}."
    elif score >= 55:
        improvement = f"Average setup. {'Wait for higher R:R before entering.' if rr < 2 else 'Stick to London/New York sessions for better fills.'}"
    else:
        improvement = "Below standard. Review your entry criteria — only take trades with R:R ≥ 2 and clear directional bias."

    return {
        "score":       score,
        "grade":       grade,
        "rr_ratio":    rr,
        "strengths":   strengths,
        "weaknesses":  weaknesses,
        "improvement": improvement,
        "summary":     f"Grade **{grade}** · Score {score}/100 · R:R {rr} · {session} session · {strategy}",
    }
