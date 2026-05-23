import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import requests
import pandas as pd

from app.ui.components import section_header
from ai_engine.trade_journal_ai.trade_reviewer import review_trade
from ai_engine.trade_journal_ai.habit_detector import detect_habits
from ai_engine.trade_journal_ai.performance_narrator import generate_narrative, weekly_summary

API = "http://localhost:8000/api/journal"


def _backend_live() -> bool:
    try:
        return requests.get("http://localhost:8000/health", timeout=2).status_code == 200
    except Exception:
        return False


def _rr(entry: float, sl: float, tp: float) -> float:
    risk   = abs(entry - sl)
    reward = abs(tp - entry)
    return round(reward / risk, 2) if risk > 0 else 0.0


# ── Page ──────────────────────────────────────────────────────

def render():
    st.markdown("## 📓 AI Trade Journal")

    live = _backend_live()
    if live:
        st.success("Backend connected", icon="✅")
    else:
        st.warning(
            "Backend API offline — start it with: "
            "`py -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload`",
            icon="⚠️",
        )

    tab_log, tab_hist, tab_close, tab_review = st.tabs(
        ["➕ Log Trade", "📋 History", "🔒 Close Trade", "📊 AI Review"]
    )

    # ── Tab 1: Log Trade ──────────────────────────────────────
    with tab_log:
        with st.form("log_trade_form"):
            c1, c2 = st.columns(2)
            with c1:
                symbol    = st.text_input("Symbol", "XAUUSD").strip().upper()
                direction = st.selectbox("Direction", ["long", "short"])
                entry     = st.number_input("Entry Price", min_value=0.0, format="%.5f")
                sl        = st.number_input("Stop Loss",   min_value=0.0, format="%.5f")
                tp        = st.number_input("Take Profit", min_value=0.0, format="%.5f")
            with c2:
                risk      = st.number_input("Risk %", 0.1, 10.0, 1.0, step=0.1)
                session   = st.selectbox("Session", ["London", "New York", "Asian", "Other"])
                strategy  = st.selectbox("Strategy",
                                         ["SMC", "ICT", "Price Action", "Breakout",
                                          "Trend Follow", "Reversal", "Custom"])
                notes     = st.text_area("Notes", height=100)

            submit = st.form_submit_button("💾 Save Trade", type="primary")

        if submit:
            if not live:
                st.error("Backend offline — cannot save.")
            elif entry <= 0 or sl <= 0 or tp <= 0:
                st.error("Entry, SL, and TP must all be greater than zero.")
            else:
                rr = _rr(entry, sl, tp)
                try:
                    resp = requests.post(f"{API}/trade", json={
                        "symbol": symbol, "direction": direction,
                        "entry_price": entry, "stop_loss": sl, "take_profit": tp,
                        "risk_percent": risk, "session": session,
                        "strategy": strategy, "notes": notes,
                    }, timeout=5)
                    if resp.status_code == 200:
                        t = resp.json()
                        st.success(f"Trade #{t['id']} saved  ·  R:R = {rr}  ·  {direction.upper()} {symbol}")
                    else:
                        st.error(f"API error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    # ── Tab 2: History ────────────────────────────────────────
    with tab_hist:
        if not live:
            st.info("Backend offline.")
        else:
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                f_sym = st.text_input("Symbol filter", "").upper() or None
            with fc2:
                f_status_raw = st.selectbox("Status", ["All", "open", "win", "loss", "breakeven"])
                f_status = None if f_status_raw == "All" else f_status_raw
            with fc3:
                f_limit = st.number_input("Max rows", 5, 500, 50)

            try:
                params = {"limit": int(f_limit)}
                if f_sym:    params["symbol"] = f_sym
                if f_status: params["status"] = f_status
                trades = requests.get(f"{API}/trades", params=params, timeout=5).json()

                if trades:
                    rows = [{
                        "ID":       t["id"],
                        "Symbol":   t["symbol"],
                        "Dir":      t["direction"].upper(),
                        "Entry":    t["entry_price"],
                        "SL":       t["stop_loss"],
                        "TP":       t["take_profit"],
                        "Risk %":   t["risk_percent"],
                        "R:R":      _rr(t["entry_price"], t["stop_loss"], t["take_profit"]),
                        "Status":   t["status"].upper(),
                        "P&L %":    f"{t['pnl_percent']:+.2f}%" if t.get("pnl_percent") else "—",
                        "Strategy": t.get("strategy") or "—",
                        "Session":  t.get("session")  or "—",
                        "Date":     t["created_at"][:10],
                    } for t in trades]

                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                    # Performance strip
                    perf = requests.get(f"{API}/performance", timeout=5).json()
                    st.divider()
                    section_header("Performance Summary")
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Trades",   perf["total_trades"])
                    m2.metric("Wins",     perf["wins"])
                    m3.metric("Losses",   perf["losses"])
                    m4.metric("Win Rate", f"{perf['win_rate']:.1f}%")
                    m5.metric("Avg R:R",  f"{perf['avg_rr']:.2f}")
                else:
                    st.info("No trades yet — log your first trade in the 'Log Trade' tab.")
            except Exception as e:
                st.error(f"Could not load trades: {e}")

    # ── Tab 3: Close Trade ────────────────────────────────────
    with tab_close:
        if not live:
            st.info("Backend offline.")
        else:
            with st.form("close_trade_form"):
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    close_id     = st.number_input("Trade ID", min_value=1, step=1)
                with cc2:
                    close_status = st.selectbox("Outcome", ["win", "loss", "breakeven"])
                with cc3:
                    close_price  = st.number_input("Exit Price", min_value=0.0, format="%.5f")
                close_pnl = st.number_input("P&L % (optional)", format="%.2f")
                close_submit = st.form_submit_button("Close Trade", type="primary")

            if close_submit:
                payload = {
                    "status":      close_status,
                    "exit_price":  close_price if close_price > 0 else None,
                    "pnl_percent": close_pnl if close_pnl != 0 else None,
                }
                try:
                    r = requests.patch(f"{API}/trade/{int(close_id)}", json=payload, timeout=5)
                    if r.status_code == 200:
                        st.success(f"Trade #{int(close_id)} closed as **{close_status.upper()}**.")
                    else:
                        st.error(f"API error: {r.text}")
                except Exception as e:
                    st.error(str(e))

    # ── Tab 4: AI Review ──────────────────────────────────────
    with tab_review:
        section_header("AI Trade Review")

        if not live:
            st.info("Backend offline — start the API to use AI review.")
        else:
            try:
                trades = requests.get(f"{API}/trades", params={"limit": 200}, timeout=5).json()
                perf   = requests.get(f"{API}/performance", timeout=5).json()
            except Exception as e:
                st.error(f"Could not load trades: {e}")
                trades, perf = [], {}

            sub_single, sub_habits, sub_narr, sub_week = st.tabs(
                ["🔍 Review a Trade", "🧠 Habit Analysis", "📝 Narrative", "📅 This Week"])

            # ── Single trade review ────────────────────────────
            with sub_single:
                if not trades:
                    st.info("No trades found. Log trades first.")
                else:
                    open_trades = [t for t in trades if t.get("status") == "open"]
                    closed_trades = [t for t in trades if t.get("status") in ("win","loss","breakeven")]
                    review_pool = closed_trades if closed_trades else trades
                    options = {f"#{t['id']} — {t['symbol']} {t['direction'].upper()} ({t['status'].upper()})": t
                               for t in review_pool}
                    chosen_label = st.selectbox("Select a trade to review", list(options.keys()))
                    chosen = options[chosen_label]

                    result = review_trade(chosen)
                    grade_colors = {"A":"#238636","B":"#58a6ff","C":"#d29922","D":"#d2a679","F":"#da3633"}
                    gc = grade_colors.get(result["grade"], "#8b949e")

                    st.markdown(
                        f'<div style="text-align:center;background:#161b22;border:2px solid {gc};'
                        f'border-radius:12px;padding:20px;margin:10px 0;">'
                        f'<div style="color:{gc};font-size:52px;font-weight:800;">{result["grade"]}</div>'
                        f'<div style="color:#e6edf3;font-size:22px;">{result["score"]} / 100</div>'
                        f'<div style="color:#8b949e;font-size:13px;margin-top:4px;">'
                        f'R:R {result["rr_ratio"]} · {chosen.get("session","—")} · {chosen.get("strategy","—")}'
                        f'</div></div>', unsafe_allow_html=True)

                    st.markdown(f"**AI Tip:** {result['improvement']}")
                    st.divider()
                    col_s, col_w = st.columns(2)
                    with col_s:
                        st.markdown("**Strengths**")
                        for s in result["strengths"]: st.markdown(f"✅ {s}")
                    with col_w:
                        st.markdown("**Weaknesses**")
                        for w in result["weaknesses"]: st.markdown(f"⚠️ {w}")

            # ── Habit analysis ────────────────────────────────
            with sub_habits:
                habits = detect_habits(trades)
                if not habits.get("has_data"):
                    st.info(habits.get("message", "No closed trades yet."))
                else:
                    h1, h2, h3, h4 = st.columns(4)
                    h1.metric("Closed Trades", habits["total_closed"])
                    h2.metric("Win Rate",      f"{habits['win_rate']}%")
                    h3.metric("Avg R:R",       habits["avg_rr"])
                    h4.metric("Avg Risk",      f"{habits['avg_risk']}%")

                    st.divider()
                    col_g, col_r = st.columns(2)
                    with col_g:
                        section_header("Good Habits")
                        if habits["good_habits"]:
                            for h in habits["good_habits"]:
                                st.markdown(
                                    f'<div style="background:#0d2818;border-left:3px solid #238636;'
                                    f'padding:6px 10px;border-radius:4px;margin:4px 0;font-size:13px;">'
                                    f'✅ {h}</div>', unsafe_allow_html=True)
                        else:
                            st.caption("Log more closed trades to detect patterns.")
                    with col_r:
                        section_header("Risk Habits")
                        if habits["risk_habits"]:
                            for h in habits["risk_habits"]:
                                st.markdown(
                                    f'<div style="background:#2d1117;border-left:3px solid #da3633;'
                                    f'padding:6px 10px;border-radius:4px;margin:4px 0;font-size:13px;">'
                                    f'⚠️ {h}</div>', unsafe_allow_html=True)
                        else:
                            st.caption("No major risk patterns detected.")

                    if habits["patterns"]:
                        st.divider()
                        section_header("Other Patterns")
                        for p in habits["patterns"]: st.markdown(f"- {p}")

                    st.divider()
                    col_ses, col_str = st.columns(2)
                    with col_ses:
                        section_header("Win Rate by Session")
                        for ses, wr in sorted(habits["session_wr"].items(), key=lambda x: -x[1]):
                            bar_c = "#238636" if wr >= 60 else ("#d29922" if wr >= 45 else "#da3633")
                            st.markdown(
                                f'<div style="display:flex;justify-content:space-between;'
                                f'background:#161b22;padding:5px 10px;border-radius:5px;margin:3px 0;">'
                                f'<span style="color:#e6edf3;">{ses}</span>'
                                f'<span style="color:{bar_c};font-weight:700;">{wr}%</span></div>',
                                unsafe_allow_html=True)
                    with col_str:
                        section_header("Win Rate by Strategy")
                        for strat, wr in sorted(habits["strategy_wr"].items(), key=lambda x: -x[1]):
                            bar_c = "#238636" if wr >= 60 else ("#d29922" if wr >= 45 else "#da3633")
                            st.markdown(
                                f'<div style="display:flex;justify-content:space-between;'
                                f'background:#161b22;padding:5px 10px;border-radius:5px;margin:3px 0;">'
                                f'<span style="color:#e6edf3;">{strat}</span>'
                                f'<span style="color:{bar_c};font-weight:700;">{wr}%</span></div>',
                                unsafe_allow_html=True)

            # ── Narrative ─────────────────────────────────────
            with sub_narr:
                habits_data = detect_habits(trades)
                narrative = generate_narrative(perf, habits_data, trades)
                st.markdown(narrative)

            # ── Weekly summary ────────────────────────────────
            with sub_week:
                st.markdown(weekly_summary(trades))
