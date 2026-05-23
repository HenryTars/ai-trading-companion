import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests

from app.ui.components import section_header
from ai_engine.trade_journal_ai.habit_detector import detect_habits
from ai_engine.trade_journal_ai.performance_narrator import generate_narrative
from autonomous_trading.self_improvement_engine.pattern_tracker import build_stats
from autonomous_trading.adaptive_optimizer.optimizer import generate_recommendations

API = "http://localhost:8000/api/journal"


def _backend_live() -> bool:
    try:
        return requests.get("http://localhost:8000/health", timeout=2).status_code == 200
    except Exception:
        return False


def _equity_curve(trades: list) -> list:
    closed = sorted(
        [t for t in trades if t.get("status") in ("win", "loss", "breakeven")
         and t.get("pnl_percent") is not None],
        key=lambda x: x.get("created_at", "")
    )
    equity, bal = [100.0], 100.0
    for t in closed:
        bal = bal * (1 + float(t["pnl_percent"]) / 100)
        equity.append(round(bal, 4))
    return equity


def render():
    st.markdown("## 📈 AI Performance Analytics")

    live = _backend_live()
    if not live:
        st.warning("Backend offline — start `py -m uvicorn backend.api:app --port 8000 --reload`")
        return

    try:
        trades = requests.get(f"{API}/trades", params={"limit": 500}, timeout=5).json()
        perf   = requests.get(f"{API}/performance", timeout=5).json()
    except Exception as e:
        st.error(f"Could not reach backend: {e}"); return

    habits = detect_habits(trades)
    closed = [t for t in trades if t.get("status") in ("win","loss","breakeven")]

    # ── KPI strip ─────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Trades",  perf.get("total_trades", 0))
    col2.metric("Win Rate",      f"{perf.get('win_rate', 0):.1f}%")
    col3.metric("Avg R:R",       f"{perf.get('avg_rr', 0):.2f}")
    col4.metric("Total P&L",     f"{perf.get('total_pnl_pct', 0):+.2f}%")
    best_sess = habits.get("best_session", "—") or "—"
    col5.metric("Best Session",  best_sess)

    st.divider()

    tab_equity, tab_pattern, tab_breakdown, tab_ai, tab_improve = st.tabs(
        ["📊 Equity Curve", "🔬 Pattern Performance", "📂 Breakdown", "🧠 AI Self-Review", "🔧 Self-Improvement"])

    # ── Tab 1: Equity Curve ───────────────────────────────────
    with tab_equity:
        equity = _equity_curve(trades)
        if len(equity) > 1:
            x = list(range(len(equity)))
            color = "#238636" if equity[-1] >= equity[0] else "#da3633"
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x, y=equity, mode="lines",
                line=dict(color=color, width=2),
                fill="tozeroy",
                fillcolor="rgba(35,134,54,0.08)" if color == "#238636" else "rgba(218,54,51,0.08)",
                name="Equity"))
            fig.add_hline(y=100, line_dash="dot", line_color="#8b949e", line_width=1)
            fig.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#e6edf3",
                xaxis=dict(gridcolor="#21262d", title="Trade #"),
                yaxis=dict(gridcolor="#21262d", side="right", title="Equity (start=100)"),
                margin=dict(l=0, r=0, t=10, b=0), height=360)
            st.plotly_chart(fig, use_container_width=True)

            peak = max(equity)
            trough = min(equity)
            max_dd = round((peak - trough) / peak * 100, 2) if peak > 0 else 0
            e1, e2, e3 = st.columns(3)
            e1.metric("Peak Equity",    f"{peak:.2f}")
            e2.metric("Current Equity", f"{equity[-1]:.2f}")
            e3.metric("Max Drawdown",   f"-{max_dd}%")
        else:
            st.info("Close trades with P&L % to plot the equity curve.")

    # ── Tab 2: Pattern Performance ────────────────────────────
    with tab_pattern:
        if not habits.get("has_data"):
            st.info("No closed trades yet.")
        else:
            col_ses, col_str = st.columns(2)
            with col_ses:
                section_header("Sessions")
                for ses, wr in sorted(habits["session_wr"].items(), key=lambda x: -x[1]):
                    bc = "#238636" if wr >= 60 else ("#d29922" if wr >= 45 else "#da3633")
                    st.markdown(
                        f'<div style="background:#161b22;padding:6px 12px;border-radius:5px;'
                        f'display:flex;justify-content:space-between;margin:3px 0;">'
                        f'<span style="color:#e6edf3;">{ses}</span>'
                        f'<span style="color:{bc};font-weight:700;">{wr}%</span></div>',
                        unsafe_allow_html=True)

            with col_str:
                section_header("Strategies")
                for strat, wr in sorted(habits["strategy_wr"].items(), key=lambda x: -x[1]):
                    bc = "#238636" if wr >= 60 else ("#d29922" if wr >= 45 else "#da3633")
                    st.markdown(
                        f'<div style="background:#161b22;padding:6px 12px;border-radius:5px;'
                        f'display:flex;justify-content:space-between;margin:3px 0;">'
                        f'<span style="color:#e6edf3;">{strat}</span>'
                        f'<span style="color:{bc};font-weight:700;">{wr}%</span></div>',
                        unsafe_allow_html=True)

            st.divider()
            section_header("Direction Performance")
            d1, d2 = st.columns(2)
            lw = habits.get("long_wr")
            sw = habits.get("short_wr")
            d1.metric("Long Win Rate",  f"{lw}%" if lw is not None else "—")
            d2.metric("Short Win Rate", f"{sw}%" if sw is not None else "—")

    # ── Tab 3: Breakdown ──────────────────────────────────────
    with tab_breakdown:
        if not closed:
            st.info("No closed trades to analyse.")
        else:
            rows = [{
                "Symbol":   t["symbol"],
                "Dir":      t["direction"].upper(),
                "Status":   t["status"].upper(),
                "R:R":      round(abs(t["take_profit"]-t["entry_price"]) /
                                  max(abs(t["entry_price"]-t["stop_loss"]),1e-9), 2),
                "Risk %":   t.get("risk_percent", "—"),
                "P&L %":    f"{t['pnl_percent']:+.2f}%" if t.get("pnl_percent") else "—",
                "Session":  t.get("session","—"),
                "Strategy": t.get("strategy","—"),
                "Date":     (t.get("created_at") or "")[:10],
            } for t in closed]
            df = pd.DataFrame(rows)

            wins_df   = df[df["Status"] == "WIN"]
            losses_df = df[df["Status"] == "LOSS"]

            st.markdown(f"**{len(wins_df)} wins · {len(losses_df)} losses · {len(df)} total**")
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Tab 4: AI Self-Review ─────────────────────────────────
    with tab_ai:
        narrative = generate_narrative(perf, habits, trades)
        st.markdown(narrative)

        if habits.get("good_habits") or habits.get("risk_habits"):
            st.divider()
            col_g, col_r = st.columns(2)
            with col_g:
                section_header("Strengths")
                for h in habits.get("good_habits", []):
                    st.markdown(
                        f'<div style="background:#0d2818;border-left:3px solid #238636;'
                        f'padding:6px 10px;border-radius:4px;margin:4px 0;font-size:13px;">'
                        f'✅ {h}</div>', unsafe_allow_html=True)
            with col_r:
                section_header("Areas to Improve")
                for h in habits.get("risk_habits", []):
                    st.markdown(
                        f'<div style="background:#2d1117;border-left:3px solid #da3633;'
                        f'padding:6px 10px;border-radius:4px;margin:4px 0;font-size:13px;">'
                        f'⚠️ {h}</div>', unsafe_allow_html=True)

    # ── Tab 5: Self-Improvement ───────────────────────────────
    with tab_improve:
        section_header("AI Self-Improvement Engine", "Learns from paper trading outcomes")

        paper_stats = build_stats()
        recs = generate_recommendations(paper_stats)

        if not recs.get("has_data"):
            st.info(recs.get("message", "Run paper trades via the Autonomous Trading engine to unlock this."))
        else:
            verdict_colors = {"strong": "#238636", "developing": "#d29922", "needs-work": "#da3633"}
            vc = verdict_colors.get(recs["verdict"], "#8b949e")
            st.markdown(
                f'<div style="background:#161b22;border:1px solid {vc};border-radius:8px;padding:12px 16px;">'
                f'<span style="color:{vc};font-weight:700;">{recs["verdict"].upper()}</span> — '
                f'{recs["summary"]}</div>', unsafe_allow_html=True)

            st.divider()
            section_header("Optimization Recommendations")
            for rec in recs["recommendations"]:
                st.markdown(rec)

            if recs["boosts"] or recs["penalties"]:
                st.divider()
                col_b, col_p = st.columns(2)
                with col_b:
                    section_header("Confidence Boosts")
                    for b in recs["boosts"]:
                        bc = "#238636"
                        st.markdown(
                            f'<div style="background:#0d2818;border-left:3px solid {bc};'
                            f'padding:6px 10px;border-radius:4px;margin:4px 0;font-size:13px;">'
                            f'✅ <b>{b["condition"]}</b> ({b["win_rate"]}% WR)<br>'
                            f'<span style="color:#8b949e;">{b["action"]}</span></div>',
                            unsafe_allow_html=True)
                with col_p:
                    section_header("Confidence Penalties")
                    for p in recs["penalties"]:
                        pc = "#da3633"
                        st.markdown(
                            f'<div style="background:#2d1117;border-left:3px solid {pc};'
                            f'padding:6px 10px;border-radius:4px;margin:4px 0;font-size:13px;">'
                            f'⚠️ <b>{p["condition"]}</b> ({p["win_rate"]}% WR)<br>'
                            f'<span style="color:#8b949e;">{p["action"]}</span></div>',
                            unsafe_allow_html=True)

            if paper_stats.get("confidence_stats"):
                st.divider()
                section_header("Win Rate by Confidence Band")
                for band, data in paper_stats["confidence_stats"].items():
                    bc = "#238636" if data["win_rate"] >= 60 else ("#d29922" if data["win_rate"] >= 45 else "#da3633")
                    st.markdown(
                        f'<div style="background:#161b22;padding:6px 12px;border-radius:5px;'
                        f'display:flex;justify-content:space-between;margin:3px 0;">'
                        f'<span style="color:#e6edf3;">{band}</span>'
                        f'<span style="color:#8b949e;">{data["trades"]} trades</span>'
                        f'<span style="color:{bc};font-weight:700;">{data["win_rate"]}%</span></div>',
                        unsafe_allow_html=True)
