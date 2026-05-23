import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd

from app.ui.components import section_header, price_fmt
from app.ui.market_data import get_price_data, SYMBOL_MAP
from autonomous_trading.broker_connector.paper_broker import PaperBroker
from autonomous_trading.ai_risk_manager.risk_manager import RiskManager
from autonomous_trading.strategy_selector.signal_generator import scan_signals, WATCHLIST
from autonomous_trading.execution_engine.executor import TradingExecutor


def _color(direction: str) -> str:
    return "#238636" if direction == "long" else "#da3633"

def _conf_color(c: float) -> str:
    return "#238636" if c >= 0.75 else ("#d29922" if c >= 0.55 else "#da3633")


def render():
    st.markdown("## 🤖 Autonomous Trading Engine")
    st.caption("Paper trading mode — no real money at risk")

    # ── Sidebar risk controls ──────────────────────────────────
    with st.sidebar:
        st.divider()
        st.caption("Engine settings")
        mode = st.radio("Trading Mode",
                        ["Manual", "Assisted", "Paper Auto"],
                        index=0, key="auto_mode")
        st.divider()
        max_risk    = st.slider("Max Risk / Trade (%)", 0.5, 5.0, 1.0, 0.5, key="auto_risk")
        max_dd      = st.slider("Max Daily Drawdown (%)", 1.0, 10.0, 3.0, 0.5, key="auto_dd")
        max_losses  = st.slider("Max Consecutive Losses", 1, 10, 3, key="auto_losses")
        max_pos     = st.slider("Max Open Positions", 1, 10, 3, key="auto_pos")
        min_rr      = st.slider("Min R:R", 1.0, 4.0, 1.5, 0.5, key="auto_rr")
        min_conf    = st.slider("Min AI Confidence (%)", 40, 90, 60, 5, key="auto_conf")
        scan_tf     = st.selectbox("Scan Timeframe", ["H4", "H1", "D1"], key="auto_tf")
        watchlist   = st.multiselect("Watchlist", list(SYMBOL_MAP.keys()),
                                     default=WATCHLIST[:5], key="auto_wl")

    rm = RiskManager(
        max_risk_pct           = max_risk,
        max_daily_drawdown_pct = max_dd,
        max_consecutive_losses = max_losses,
        max_open_positions     = max_pos,
        min_rr                 = min_rr,
        min_confidence         = min_conf / 100,
    )
    executor = TradingExecutor(risk_manager=rm)
    broker   = executor.broker
    summary  = broker.get_summary()

    tab_dash, tab_scan, tab_pos, tab_hist = st.tabs(
        ["📊 Dashboard", "🔍 Signal Scanner", "📂 Open Positions", "📋 Trade History"])

    # ── Tab 1: Dashboard ──────────────────────────────────────
    with tab_dash:
        # Status banner
        mode_colors = {"Manual": "#8b949e", "Assisted": "#d29922", "Paper Auto": "#238636"}
        mc = mode_colors.get(mode, "#8b949e")
        st.markdown(
            f'<div style="background:#161b22;border:1px solid {mc};border-radius:8px;'
            f'padding:10px 16px;margin-bottom:12px;display:flex;align-items:center;">'
            f'<span style="color:{mc};font-weight:700;font-size:15px;">⬤ {mode.upper()}</span>'
            f'<span style="color:#8b949e;margin-left:12px;font-size:13px;">Paper account · No real funds</span>'
            f'</div>', unsafe_allow_html=True)

        # KPI strip
        ret_color = "#238636" if summary["total_return_pct"] >= 0 else "#da3633"
        d_color   = "#238636" if summary["daily_pnl"] >= 0 else "#da3633"
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("Balance",      f"${summary['balance']:,.2f}")
        k2.metric("Equity",       f"${summary['equity']:,.2f}")
        k3.metric("Total Return", f"{summary['total_return_pct']:+.2f}%")
        k4.metric("Today P&L",    f"${summary['daily_pnl']:+.2f}")
        k5.metric("Win Rate",     f"{summary['win_rate']}%")
        k6.metric("Open",         summary['open_positions'])

        st.divider()

        col_stats, col_rules = st.columns([1, 1])
        with col_stats:
            section_header("Account Stats")
            st.markdown(f"- **Starting balance:** $10,000.00")
            st.markdown(f"- **Total trades:** {summary['total_trades']}")
            st.markdown(f"- **Wins / Losses:** {summary['wins']} / {summary['losses']}")
            st.markdown(f"- **Consecutive losses:** {summary['consecutive_losses']}")
            st.markdown(f"- **Daily P&L %:** {summary['daily_pnl_pct']:+.3f}%")

        with col_rules:
            section_header("Active Risk Rules")
            st.markdown(f"- Max risk/trade: **{max_risk}%**")
            st.markdown(f"- Daily drawdown limit: **{max_dd}%**")
            st.markdown(f"- Max consecutive losses: **{max_losses}**")
            st.markdown(f"- Max open positions: **{max_pos}**")
            st.markdown(f"- Minimum R:R: **{min_rr}**")
            st.markdown(f"- Minimum AI confidence: **{min_conf}%**")

        st.divider()
        if st.button("🔄 Reset Paper Account", type="secondary"):
            broker.reset()
            st.success("Paper account reset to $10,000. All trades cleared.")
            st.rerun()

    # ── Tab 2: Signal Scanner ─────────────────────────────────
    with tab_scan:
        section_header("AI Signal Scanner", f"{scan_tf} · {len(watchlist)} symbols")

        col_scan, col_auto = st.columns([1, 1])
        with col_scan:
            run_scan = st.button("🔍 Scan for Signals", type="primary", use_container_width=True)
        with col_auto:
            if mode == "Paper Auto":
                run_auto = st.button("⚡ Auto-Execute All Valid Signals",
                                     type="primary", use_container_width=True)
            else:
                run_auto = False

        if run_scan or run_auto:
            with st.spinner(f"Scanning {len(watchlist)} symbols on {scan_tf}…"):
                if run_auto and mode == "Paper Auto":
                    results = executor.scan_and_execute(watchlist, scan_tf, dry_run=False)
                else:
                    results = executor.scan_and_execute(watchlist, scan_tf, dry_run=True)

            st.session_state["last_scan"] = results

        signals = st.session_state.get("last_scan", [])

        if signals:
            valid   = [s for s in signals if s["allowed"]]
            blocked = [s for s in signals if not s["allowed"]]

            if valid:
                st.markdown(f"**{len(valid)} signal(s) pass risk filter:**")
                for s in valid:
                    dc = _color(s["direction"])
                    cc = _conf_color(s["confidence"])
                    executed_badge = ' <span style="color:#238636;">✓ EXECUTED</span>' if s.get("executed") else ""
                    st.markdown(
                        f'<div style="background:#161b22;border:1px solid #30363d;'
                        f'border-left:3px solid {dc};border-radius:8px;'
                        f'padding:10px 14px;margin:6px 0;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                        f'<span style="color:{dc};font-weight:700;font-size:15px;">'
                        f'{s["symbol"]} {s["direction"].upper()}</span>'
                        f'<span style="color:{cc};">Conf {int(s["confidence"]*100)}%</span>'
                        f'</div>'
                        f'<div style="color:#8b949e;font-size:12px;margin-top:4px;">'
                        f'Entry {s["entry"]} · SL {s["sl"]} · TP {s["tp"]} · R:R {s["rr"]}'
                        f'{executed_badge}</div></div>',
                        unsafe_allow_html=True)

                    if mode == "Assisted" and not s.get("executed"):
                        if st.button(f"✅ Execute {s['symbol']} {s['direction'].upper()}",
                                     key=f"exec_{s['symbol']}_{s['direction']}"):
                            pos = broker.open_position(
                                symbol=s["symbol"], direction=s["direction"],
                                entry=s["entry"], sl=s["sl"], tp=s["tp"],
                                risk_pct=rm.get_position_size_pct(s),
                                strategy=f"AI {scan_tf} Signal (Assisted)",
                            )
                            st.success(f"Opened #{pos['id']} — {s['symbol']} {s['direction'].upper()}")
                            st.rerun()

            if blocked:
                with st.expander(f"{len(blocked)} signal(s) blocked by risk filter"):
                    for s in blocked:
                        st.markdown(f"- **{s['symbol']} {s['direction'].upper()}** — {s['reason']}")
        else:
            st.info("Press **Scan for Signals** to run the AI scanner.")

    # ── Tab 3: Open Positions ─────────────────────────────────
    with tab_pos:
        section_header("Open Positions", f"{summary['open_positions']} active")

        positions = broker.open_positions
        if not positions:
            st.info("No open positions. Run the scanner to find and enter trades.")
        else:
            with st.spinner("Fetching current prices…"):
                current_prices = {}
                for pos in positions:
                    try:
                        df = get_price_data(pos["symbol"], "M5")
                        if not df.empty:
                            current_prices[pos["symbol"]] = float(df["Close"].iloc[-1])
                    except Exception:
                        pass

            auto_closed = executor.check_auto_close(current_prices)
            if auto_closed:
                for c in auto_closed:
                    color = "#238636" if c["status"] == "win" else "#da3633"
                    st.markdown(
                        f'<div style="background:#161b22;border-left:3px solid {color};'
                        f'padding:8px 12px;border-radius:6px;margin:4px 0;">'
                        f'Auto-closed {c["symbol"]} — {c["reason"]} · '
                        f'P&L: <b style="color:{color};">{c["pnl_pct"]:+.2f}%</b></div>',
                        unsafe_allow_html=True)

            for pos in broker.open_positions:
                price = current_prices.get(pos["symbol"], pos["entry"])
                if pos["direction"] == "long":
                    unreal_pct = (price - pos["entry"]) / pos["entry"] * 100
                else:
                    unreal_pct = (pos["entry"] - price) / pos["entry"] * 100
                uc = "#238636" if unreal_pct >= 0 else "#da3633"
                dc = _color(pos["direction"])

                with st.container():
                    st.markdown(
                        f'<div style="background:#161b22;border:1px solid #30363d;'
                        f'border-left:3px solid {dc};border-radius:8px;padding:12px 16px;margin:6px 0;">'
                        f'<div style="display:flex;justify-content:space-between;">'
                        f'<span style="color:{dc};font-weight:700;">{pos["symbol"]} {pos["direction"].upper()}</span>'
                        f'<span style="color:{uc};font-weight:700;">{unreal_pct:+.2f}%</span>'
                        f'</div>'
                        f'<div style="color:#8b949e;font-size:12px;">'
                        f'Entry {pos["entry"]} · SL {pos["sl"]} · TP {pos["tp"]} · '
                        f'Current {price_fmt(price, pos["symbol"])} · #{pos["id"]}'
                        f'</div></div>', unsafe_allow_html=True)

                    c1, c2 = st.columns([3, 1])
                    with c2:
                        if st.button("Close", key=f"close_{pos['id']}"):
                            closed = broker.close_position(pos["id"], price, "manual")
                            if closed:
                                st.success(f"Closed {pos['symbol']} at {price}")
                                st.rerun()

    # ── Tab 4: Trade History ──────────────────────────────────
    with tab_hist:
        section_header("Closed Paper Trades", f"{summary['total_trades']} total")

        closed = broker.closed_trades
        if not closed:
            st.info("No closed trades yet.")
        else:
            rows = [{
                "ID":        t["id"],
                "Symbol":    t["symbol"],
                "Dir":       t["direction"].upper(),
                "Entry":     t["entry"],
                "Exit":      t.get("exit", "—"),
                "SL":        t["sl"],
                "TP":        t["tp"],
                "P&L %":    f"{t['pnl_pct']:+.3f}%" if t.get("pnl_pct") is not None else "—",
                "P&L $":    f"${t['pnl_amount']:+.2f}" if t.get("pnl_amount") is not None else "—",
                "Status":   t["status"].upper(),
                "Reason":   t.get("reason", "—"),
                "Opened":   (t.get("opened_at") or "")[:10],
            } for t in reversed(closed)]

            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            total_pnl = summary["total_pnl_amount"]
            p_color = "#238636" if total_pnl >= 0 else "#da3633"
            st.markdown(
                f'<div style="text-align:right;color:{p_color};font-weight:700;font-size:15px;">'
                f'Net P&L: ${total_pnl:+.2f}</div>', unsafe_allow_html=True)
