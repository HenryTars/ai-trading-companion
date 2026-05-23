"""
Adaptive Optimizer
Reads pattern tracker stats and generates:
  - Confidence adjustments per condition
  - Ranked list of what's working vs what's hurting performance
  - Actionable improvement recommendations
"""
from typing import Dict, List


def _grade_wr(wr: float) -> tuple:
    if wr >= 65: return "excellent", "#238636"
    if wr >= 52: return "good",      "#58a6ff"
    if wr >= 45: return "average",   "#d29922"
    return "poor", "#da3633"


def generate_recommendations(stats: Dict) -> Dict:
    if not stats.get("has_data"):
        return {
            "has_data": False,
            "message": stats.get("message", "No data available."),
        }

    recs: List[str] = []
    boosts: List[Dict] = []
    penalties: List[Dict] = []

    # ── Strategy recommendations ──────────────────────────────
    best_strat = worst_strat = None
    best_wr = worst_wr = -1
    for strat, data in stats.get("strategy_stats", {}).items():
        if data["trades"] < 2:
            continue
        wr = data["win_rate"]
        if wr > best_wr:
            best_wr, best_strat = wr, strat
        if worst_wr < 0 or wr < worst_wr:
            worst_wr, worst_strat = wr, strat

    if best_strat:
        label, _ = _grade_wr(best_wr)
        recs.append(f"🏆 **{best_strat}** is your top strategy ({best_wr}% win rate) — prioritize these setups")
        boosts.append({"condition": f"Strategy: {best_strat}", "win_rate": best_wr, "action": "+5% confidence boost"})

    if worst_strat and worst_strat != best_strat and worst_wr < 45:
        recs.append(f"⚠️ **{worst_strat}** underperforms ({worst_wr}% win rate) — consider pausing or revising entry rules")
        penalties.append({"condition": f"Strategy: {worst_strat}", "win_rate": worst_wr, "action": "−10% confidence penalty"})

    # ── Direction recommendations ─────────────────────────────
    dir_stats = stats.get("direction_stats", {})
    long_wr  = dir_stats.get("long",  {}).get("win_rate", 0)
    short_wr = dir_stats.get("short", {}).get("win_rate", 0)
    long_cnt  = dir_stats.get("long",  {}).get("trades",   0)
    short_cnt = dir_stats.get("short", {}).get("trades",   0)

    if long_cnt >= 3 and short_cnt >= 3:
        if long_wr > short_wr + 15:
            recs.append(f"📈 Long trades win at **{long_wr}%** vs shorts **{short_wr}%** — bias your filters bullish")
            boosts.append({"condition": "Direction: Long", "win_rate": long_wr, "action": "+3% confidence boost"})
            penalties.append({"condition": "Direction: Short", "win_rate": short_wr, "action": "−3% confidence penalty"})
        elif short_wr > long_wr + 15:
            recs.append(f"📉 Short trades win at **{short_wr}%** vs longs **{long_wr}%** — bias your filters bearish")
            boosts.append({"condition": "Direction: Short", "win_rate": short_wr, "action": "+3% confidence boost"})
            penalties.append({"condition": "Direction: Long", "win_rate": long_wr, "action": "−3% confidence penalty"})
        else:
            recs.append(f"⚖️ Long ({long_wr}%) and short ({short_wr}%) win rates are balanced — no directional bias needed")

    # ── Confidence band recommendations ───────────────────────
    conf_stats = stats.get("confidence_stats", {})
    for band, data in conf_stats.items():
        if data["trades"] < 3:
            continue
        wr = data["win_rate"]
        label, _ = _grade_wr(wr)
        if "High" in band and wr >= 65:
            recs.append(f"✅ High-confidence signals ({band}) deliver **{wr}%** win rate — raise min confidence threshold")
            boosts.append({"condition": band, "win_rate": wr, "action": "Raise min confidence to 75%"})
        elif "Low" in band and wr < 50:
            recs.append(f"🚫 Low-confidence signals ({band}) only deliver **{wr}%** — filter them out entirely")
            penalties.append({"condition": band, "win_rate": wr, "action": "Block signals below 65% confidence"})

    # ── Close reason analysis ─────────────────────────────────
    reason_stats = stats.get("reason_stats", {})
    tp_data = reason_stats.get("TP hit", {})
    sl_data = reason_stats.get("SL hit", {})
    if tp_data.get("count", 0) > 0 and sl_data.get("count", 0) > 0:
        tp_rate = tp_data.get("count", 0) / max(tp_data.get("count", 0) + sl_data.get("count", 0), 1) * 100
        if tp_rate >= 60:
            recs.append(f"🎯 {tp_rate:.0f}% of exits hit TP — your take-profit levels are well-calibrated")
        elif tp_rate <= 35:
            recs.append(f"🛑 Only {tp_rate:.0f}% of exits hit TP — consider using tighter TPs or ATR × 2 instead of × 3")

    # ── Overall verdict ───────────────────────────────────────
    wr = stats.get("overall_win_rate", 0)
    pnl = stats.get("total_pnl", 0)
    if wr >= 60 and pnl > 0:
        verdict = "strong"
        summary = f"Engine performing well — {wr}% win rate with positive P&L. Focus on scaling what works."
    elif wr >= 50 or pnl >= 0:
        verdict = "developing"
        summary = f"Engine is marginally profitable ({wr}% win rate). Apply the recommendations below to improve edge."
    else:
        verdict = "needs-work"
        summary = f"Engine needs tuning — {wr}% win rate is below break-even. Tighten filters before increasing activity."

    if not recs:
        recs.append("Log more paper trades to unlock personalized optimization recommendations.")

    return {
        "has_data":        True,
        "verdict":         verdict,
        "summary":         summary,
        "recommendations": recs,
        "boosts":          boosts,
        "penalties":       penalties,
        "overall_wr":      wr,
        "total_pnl":       pnl,
    }


def get_adjusted_confidence(base_conf: float, signal: Dict, stats: Dict) -> float:
    """Apply learned adjustments to a raw AI confidence score."""
    if not stats.get("has_data"):
        return base_conf

    adjusted = base_conf
    dir_stats = stats.get("direction_stats", {})

    direction = signal.get("direction", "long")
    dir_wr = dir_stats.get(direction, {}).get("win_rate", 50)
    if dir_wr >= 65:
        adjusted = min(0.98, adjusted + 0.04)
    elif dir_wr <= 40:
        adjusted = max(0.10, adjusted - 0.06)

    strat = signal.get("strategy", "")
    for s, data in stats.get("strategy_stats", {}).items():
        if s in strat and data["trades"] >= 3:
            swr = data["win_rate"]
            if swr >= 65:
                adjusted = min(0.98, adjusted + 0.03)
            elif swr <= 40:
                adjusted = max(0.10, adjusted - 0.05)

    return round(adjusted, 3)
