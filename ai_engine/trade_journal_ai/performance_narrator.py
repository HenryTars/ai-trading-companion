"""
Performance Narrator
Generates markdown narrative summaries from trade history and habit data.
"""
from typing import Dict, List


def generate_narrative(perf: Dict, habits: Dict, recent_trades: List[Dict]) -> str:
    if not habits.get("has_data"):
        return "_No closed trades yet. Start logging trades and closing them to get AI performance narratives._"

    total   = habits["total_closed"]
    wr      = habits["win_rate"]
    avg_rr  = habits["avg_rr"]
    avg_risk = habits["avg_risk"]

    # ── Opening assessment ────────────────────────────────────
    if wr >= 65 and avg_rr >= 2.0:
        tone = "strong"
        opener = f"Your trading performance is **strong**. A {wr}% win rate combined with an average R:R of {avg_rr} puts you in profitable territory."
    elif wr >= 55 or avg_rr >= 2.0:
        tone = "developing"
        opener = f"Your trading is **developing well**. With a {wr}% win rate and {avg_rr} average R:R, you have a solid foundation to build on."
    elif wr >= 45:
        tone = "average"
        opener = f"Your performance is **average** across {total} closed trades. A {wr}% win rate is workable but needs improvement — focus on setup quality."
    else:
        tone = "needs-work"
        opener = f"Your recent trading needs **attention**. A {wr}% win rate across {total} trades suggests entry criteria need tightening."

    lines = [f"### Performance Assessment\n{opener}\n"]

    # ── Session insight ───────────────────────────────────────
    if habits.get("best_session") and habits.get("session_wr"):
        bs  = habits["best_session"]
        bwr = habits["session_wr"].get(bs, 0)
        lines.append(f"**Best session:** {bs} ({bwr}% win rate). Focus your screen time here.")
        if habits.get("worst_session"):
            ws  = habits["worst_session"]
            wwr = habits["session_wr"].get(ws, 0)
            if wwr < 45:
                lines.append(f"**Underperforming session:** {ws} ({wwr}% win rate) — consider reducing exposure.")

    # ── Strategy insight ──────────────────────────────────────
    if habits.get("best_strategy"):
        lines.append(f"**Top strategy:** {habits['best_strategy']} — your highest win rate setup. Double down on mastering it.")
    if habits.get("worst_strategy") and habits["worst_strategy"] != habits.get("best_strategy"):
        lines.append(f"**Weakest strategy:** {habits['worst_strategy']} — consider pausing it until you identify the issue.")

    # ── R:R and risk ──────────────────────────────────────────
    lines.append("")
    if avg_rr >= 2.5:
        lines.append(f"Your R:R discipline is excellent at {avg_rr}. Keep rejecting setups below 2:1.")
    elif avg_rr >= 1.5:
        lines.append(f"Your average R:R of {avg_rr} is acceptable. Aim for 2.5+ to give your edge more room.")
    else:
        lines.append(f"⚠️ Average R:R of {avg_rr} is too low. A 50% win rate needs R:R ≥ 2 just to break even.")

    if avg_risk > 2:
        lines.append(f"⚠️ Average risk of {avg_risk}% per trade is elevated — drawdowns will be severe. Target ≤ 1.5%.")
    elif avg_risk <= 1.0:
        lines.append(f"Risk management is disciplined at {avg_risk}% avg per trade — keep it consistent.")

    # ── Losing streak warning ─────────────────────────────────
    if habits.get("max_consec_loss", 0) >= 3:
        lines.append(f"\n⚠️ **Losing streak alert:** Up to {habits['max_consec_loss']} consecutive losses detected. "
                     f"Implement a daily stop-loss rule — e.g., stop after 2 losses in a day.")

    # ── Direction bias ────────────────────────────────────────
    lw = habits.get("long_wr")
    sw = habits.get("short_wr")
    if lw and sw:
        if lw > sw + 15:
            lines.append(f"\nYou win **{lw}%** on longs vs **{sw}%** on shorts — lean into bullish setups.")
        elif sw > lw + 15:
            lines.append(f"\nYou win **{sw}%** on shorts vs **{lw}%** on longs — lean into bearish setups.")

    # ── Closing advice ────────────────────────────────────────
    lines.append("\n---")
    if tone == "strong":
        lines.append("**Keep doing:** Stay consistent, don't increase risk after wins, and review every trade.")
    elif tone == "developing":
        lines.append("**Next focus:** Raise the quality bar on entries — only take setups with R:R ≥ 2.5 and session alignment.")
    elif tone == "average":
        lines.append("**Priority:** Pick 1–2 strategies and master them. Fewer, higher-quality trades beat quantity.")
    else:
        lines.append("**Action required:** Step back, paper-trade for a week, and identify your edge before risking real capital.")

    return "\n".join(lines)


def weekly_summary(trades: List[Dict]) -> str:
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=7)

    recent = []
    for t in trades:
        try:
            dt_str = t.get("created_at", "")
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00").replace("+00:00", ""))
            if dt >= cutoff:
                recent.append(t)
        except Exception:
            pass

    if not recent:
        return "_No trades in the last 7 days._"

    closed = [t for t in recent if t.get("status") in ("win", "loss", "breakeven")]
    wins   = sum(1 for t in closed if t["status"] == "win")
    losses = sum(1 for t in closed if t["status"] == "loss")
    wr     = round(wins / len(closed) * 100, 1) if closed else 0
    pnl    = sum(float(t.get("pnl_percent") or 0) for t in closed)

    lines = [f"### 7-Day Summary",
             f"- **Trades logged:** {len(recent)}  ·  **Closed:** {len(closed)}",
             f"- **Wins:** {wins}  ·  **Losses:** {losses}  ·  **Win rate:** {wr}%",
             f"- **Net P&L:** {pnl:+.2f}%"]

    if pnl > 0 and wr >= 50:
        lines.append("\nSolid week — stay disciplined and protect the gains.")
    elif pnl < 0:
        lines.append("\n⚠️ Negative week — review each loss before trading again.")

    return "\n".join(lines)
