import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from app.ui.market_data import get_market_overview, get_price_data, SYMBOL_MAP
from app.ui.components import signal_card, price_fmt, section_header
from ai_engine.chart_analysis.analyzer import analyze_chart


@st.cache_data(ttl=120)
def _quick_bias(symbol: str) -> dict:
    df = get_price_data(symbol, "H4")
    if df.empty or len(df) < 20:
        return {"bias": "—", "confidence": 0, "risk_level": "—"}
    return analyze_chart(df, symbol, "H4")


def render():
    st.markdown("## 🏠 AI Trading Dashboard")
    st.caption("Live market data · AI bias refreshes every 2 min")

    # ── Market strip ──────────────────────────────────────────
    with st.spinner("Loading prices…"):
        overview = get_market_overview()

    if overview:
        cols = st.columns(len(overview))
        for col, item in zip(cols, overview):
            sym, price, pct = item["symbol"], item["price"], item["change_pct"]
            col.metric(sym, price_fmt(price, sym),
                       delta=f"{pct:+.2f}%",
                       delta_color="normal" if pct >= 0 else "inverse")
    else:
        st.warning("Market data unavailable — check internet connection.")

    st.divider()

    # ── Main area ─────────────────────────────────────────────
    col_chart, col_sig = st.columns([3, 1])

    with col_chart:
        section_header("Live Chart")
        r1, r2 = st.columns([2, 1])
        with r1: symbol = st.selectbox("Symbol", list(SYMBOL_MAP.keys()), key="d_sym",
                                        label_visibility="collapsed")
        with r2: tf     = st.selectbox("Timeframe", ["H1", "H4", "D1", "M15", "M5", "W1"],
                                        key="d_tf", label_visibility="collapsed")

        with st.spinner(f"Fetching {symbol} · {tf}…"):
            df = get_price_data(symbol, tf)

        if not df.empty:
            fig = go.Figure(go.Candlestick(
                x=df.index, open=df["Open"], high=df["High"],
                low=df["Low"], close=df["Close"],
                increasing_line_color="#238636", decreasing_line_color="#da3633", name=symbol))
            if len(df) >= 20:
                fig.add_trace(go.Scatter(x=df.index, y=df["Close"].rolling(20).mean(),
                    mode="lines", line=dict(color="#58a6ff", width=1), name="MA20", opacity=0.7))
            fig.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#e6edf3",
                xaxis=dict(gridcolor="#21262d", rangeslider_visible=False),
                yaxis=dict(gridcolor="#21262d", side="right"),
                margin=dict(l=0, r=0, t=10, b=0), height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            c = df["Close"]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Last",  price_fmt(float(c.iloc[-1]),      symbol))
            m2.metric("High",  price_fmt(float(df["High"].max()), symbol))
            m3.metric("Low",   price_fmt(float(df["Low"].min()),  symbol))
            pct = (float(c.iloc[-1]) - float(c.iloc[0])) / float(c.iloc[0]) * 100
            m4.metric("Period Δ", f"{pct:+.2f}%", delta_color="normal" if pct >= 0 else "inverse")
        else:
            st.info(f"No chart data for {symbol} · {tf}.")

    with col_sig:
        section_header("AI Signals", "H4 bias · live")
        watchlist = ["XAUUSD", "EURUSD", "BTCUSDT"]
        for sym in watchlist:
            a = _quick_bias(sym)
            bias = a.get("bias", "ranging")
            conf = a.get("confidence", 0.5)
            risk = a.get("risk_level", "—")
            if bias != "—":
                signal_card(sym, bias, conf, risk, "H4")

        st.divider()
        section_header("Full AI Analysis")
        if st.button("Analyze Current Chart", type="primary", use_container_width=True):
            if not df.empty:
                with st.spinner("Analyzing…"):
                    a = analyze_chart(df, symbol, tf)
                b  = a.get("bias", "ranging")
                co = int(a.get("confidence", 0) * 100)
                bc = "#238636" if b == "bullish" else ("#da3633" if b == "bearish" else "#d29922")
                st.markdown(
                    f'<div style="background:#161b22;border:1px solid {bc};border-radius:8px;padding:12px;">'
                    f'<div style="color:{bc};font-weight:700;font-size:15px;">{b.upper()}</div>'
                    f'<div style="color:#e6edf3;">Confidence: {co}%</div>'
                    f'<div style="color:#8b949e;font-size:12px;">{a.get("trend_strength","").capitalize()} trend · '
                    f'{a.get("risk_level","")} risk</div></div>',
                    unsafe_allow_html=True)

    st.divider()

    # ── AI Stats + watchlist ──────────────────────────────────
    section_header("AI Intelligence Summary")
    a1, a2, a3, a4 = st.columns(4)

    bullish_count = sum(1 for item in overview if item["change_pct"] > 0.1) if overview else 0
    bearish_count = sum(1 for item in overview if item["change_pct"] < -0.1) if overview else 0
    a1.metric("Markets Bullish", bullish_count)
    a2.metric("Markets Bearish", bearish_count)
    a3.metric("AI Win Rate",     "— ", help="Populates from trade journal (Phase 7)")
    a4.metric("Active Setups",   len(watchlist))

    if overview:
        st.divider()
        section_header("Watchlist")
        rows = [{"Symbol": i["symbol"],
                 "Price":  price_fmt(i["price"], i["symbol"]),
                 "Change": f"{i['change_pct']:+.2f}%",
                 "H4 Bias": _quick_bias(i["symbol"]).get("bias", "—").capitalize(),
                 "Conf":   f"{int(_quick_bias(i['symbol']).get('confidence', 0) * 100)}%"}
                for i in overview]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
