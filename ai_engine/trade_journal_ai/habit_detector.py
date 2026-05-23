"""
Habit Detector
Finds recurring patterns — good and bad — across a trader's closed trade history.
"""
from collections import defaultdict
from typing import Dict, List, Any


def _rr(entry: float, sl: float, tp: float) -> float:
    risk   = abs(entry - sl)
    reward = abs(tp - entry)
    return round(reward / risk, 2) if risk > 0 else 0.0


def detect_habits(trades: List[Dict]) -> Dict[str, Any]:
    closed = [t for t in trades if t.get("status") in ("win", "loss", "breakeven")]
    if not closed:
        return {
            "has_data": False,
            "message": "No closed trades yet. Log and close trades to unlock habit analysis.",
        }

    total   = len(closed)
    wins    = [t for t in closed if t["status"] == "win"]
    losses  = [t for t in closed if t["status"] == "loss"]
    win_rate = round(len(wins) / total * 100, 1) if total else 0

    # ── Session analysis ──────────────────────────────────────
    session_stats: Dict[str, Dict] = defaultdict(lambda: {"wins": 0, "total": 0})
    for t in closed:
        s = t.get("session", "Other") or "Other"
        session_stats[s]["total"] += 1
        if t["status"] == "win":
            session_stats[s]["wins"] += 1

    session_wr = {s: round(v["wins"] / v["total"] * 100, 1)
                  for s, v in session_stats.items() if v["total"] >= 2}
    best_session  = max(session_wr, key=session_wr.get) if session_wr else None
    worst_session = min(session_wr, key=session_wr.get) if session_wr else None

    # ── Strategy analysis ─────────────────────────────────────
    strat_stats: Dict[str, Dict] = defaultdict(lambda: {"wins": 0, "total": 0})
    for t in closed:
        st = t.get("strategy", "Custom") or "Custom"
        strat_stats[st]["total"] += 1
        if t["status"] == "win":
            strat_stats[st]["wins"] += 1

    strat_wr = {s: round(v["wins"] / v["total"] * 100, 1)
                for s, v in strat_stats.items() if v["total"] >= 2}
    best_strategy  = max(strat_wr, key=strat_wr.get) if strat_wr else None
    worst_strategy = min(strat_wr, key=strat_wr.get) if strat_wr else None

    # ── R:R habits ────────────────────────────────────────────
    rrs = [_rr(t["entry_price"], t["stop_loss"], t["take_profit"]) for t in closed]
    avg_rr     = round(sum(rrs) / len(rrs), 2) if rrs else 0
    low_rr_cnt = sum(1 for r in rrs if r < 1.5)

    # ── Risk habits ───────────────────────────────────────────
    risks = [float(t.get("risk_percent", 1) or 1) for t in closed]
    avg_risk      = round(sum(risks) / len(risks), 2) if risks else 0
    high_risk_cnt = sum(1 for r in risks if r > 2)

    # ── Consecutive losses ────────────────────────────────────
    max_consec_loss = 0
    cur_consec = 0
    for t in closed:
        if t["status"] == "loss":
            cur_consec += 1
            max_consec_loss = max(max_consec_loss, cur_consec)
        else:
            cur_consec = 0

    # ── Direction bias ────────────────────────────────────────
    long_trades  = [t for t in closed if t.get("direction") == "long"]
    short_trades = [t for t in closed if t.get("direction") == "short"]
    long_wr  = round(sum(1 for t in long_trades  if t["status"] == "win") / len(long_trades)  * 100, 1) if long_trades  else None
    short_wr = round(sum(1 for t in short_trades if t["status"] == "win") / len(short_trades) * 100, 1) if short_trades else None

    # ── Build pattern list ────────────────────────────────────
    patterns: List[str] = []
    good_habits: List[str] = []
    risk_habits: List[str] = []

    if best_session and session_wr.get(best_session, 0) >= 60:
        good_habits.append(f"You perform best in the **{best_session}** session ({session_wr[best_session]}% win rate)")
    if worst_session and session_wr.get(worst_session, 0) <= 40:
        risk_habits.append(f"Avoid the **{worst_session}** session — only {session_wr[worst_session]}% win rate")

    if best_strategy and strat_wr.get(best_strategy, 0) >= 60:
        good_habits.append(f"**{best_strategy}** is your strongest strategy ({strat_wr[best_strategy]}% win rate)")
    if worst_strategy and strat_wr.get(worst_strategy, 0) <= 40 and worst_strategy != best_strategy:
        risk_habits.append(f"**{worst_strategy}** underperforms ({strat_wr[worst_strategy]}% win rate) — refine or drop it")

    if avg_rr >= 2.0:
        good_habits.append(f"Average R:R of {avg_rr} — excellent risk discipline")
    elif avg_rr < 1.5:
        risk_habits.append(f"Average R:R of {avg_rr} is below 1.5 — you need better setups")

    if low_rr_cnt > total * 0.3:
        risk_habits.append(f"{low_rr_cnt} of {total} trades had R:R < 1.5 — too many low-quality entries")

    if high_risk_cnt > total * 0.25:
        risk_habits.append(f"{high_risk_cnt} trades exceeded 2% risk — position sizing needs tightening")

    if avg_risk <= 1.0:
        good_habits.append(f"Conservative avg risk of {avg_risk}% — capital is well protected")

    if max_consec_loss >= 4:
        risk_habits.append(f"Max {max_consec_loss} consecutive losses — consider a daily loss limit rule")
    elif max_consec_loss >= 2:
        patterns.append(f"Longest losing streak: {max_consec_loss} trades — monitor for overtrading after losses")

    if long_wr and short_wr:
        if long_wr > short_wr + 20:
            good_habits.append(f"Long trades win at {long_wr}% vs shorts at {short_wr}% — lean bullish bias")
        elif short_wr > long_wr + 20:
            good_habits.append(f"Short trades win at {short_wr}% vs longs at {long_wr}% — lean bearish bias")

    if win_rate >= 60:
        good_habits.append(f"Strong overall win rate of {win_rate}%")
    elif win_rate < 40:
        risk_habits.append(f"Win rate of {win_rate}% is below average — review entry criteria")

    return {
        "has_data":       True,
        "total_closed":   total,
        "win_rate":       win_rate,
        "avg_rr":         avg_rr,
        "avg_risk":       avg_risk,
        "best_session":   best_session,
        "worst_session":  worst_session,
        "best_strategy":  best_strategy,
        "worst_strategy": worst_strategy,
        "session_wr":     session_wr,
        "strategy_wr":    strat_wr,
        "long_wr":        long_wr,
        "short_wr":       short_wr,
        "max_consec_loss": max_consec_loss,
        "low_rr_count":   low_rr_cnt,
        "high_risk_count": high_risk_cnt,
        "good_habits":    good_habits,
        "risk_habits":    risk_habits,
        "patterns":       patterns,
    }
