import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from app.ui.market_data import get_price_data, get_market_overview, SYMBOL_MAP
from app.ui.components import price_fmt, section_header
from ai_engine.market_insights.bias_engine import generate_bias
from ai_engine.market_insights.multi_timeframe import multi_timeframe_analysis


def _color(bias: str) -> str:
    return "#238636" if bias == "bullish" else ("#da3633" if bias == "bearish" else "#d29922")


def render():
    st.markdown("## 🌍 Market Insights Engine")

    c1, c2 = st.columns([3, 1])
    with c1: selected  = st.selectbox("Market", list(SYMBOL_MAP.keys()))
    with c2: timeframe = st.selectbox("Timeframe", ["D1", "H4", "H1", "W1", "M15"])

    with st.spinner(f"Running AI analysis for {selected} · {timeframe}…"):
        df = get_price_data(selected, timeframe)

    if df.empty:
        st.warning(f"No data for **{selected}** · **{timeframe}**.")
        return

    analysis = generate_bias(df, selected, timeframe)

    bias      = analysis.get("bias", "ranging")
    conf      = analysis.get("confidence", 0.5)
    strength  = analysis.get("trend_strength", "—")
    risk      = analysis.get("risk_level", "—")
    momentum  = analysis.get("momentum", "—")
    volatility = analysis.get("volatility", "—")
    price_now = analysis.get("current_price", 0.0)
    ind       = analysis.get("indicators", {})
    certainty = analysis.get("certainty", "—")
    bc        = _color(bias)

    # ── KPI strip ─────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Price",      price_fmt(price_now, selected))
    k2.metric("Bias",       bias.capitalize())
    k3.metric("Confidence", f"{int(conf * 100)}%")
    k4.metric("Risk",       risk)
    k5.metric("Momentum",   momentum)
    k6.metric("Volatility", volatility)

    st.divider()

    # ── Chart + analysis ──────────────────────────────────────
    col_chart, col_panel = st.columns([3, 2])

    with col_chart:
        close = df["Close"]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=close.index, y=close, mode="lines",
            line=dict(color=bc, width=2),
            fill="tozeroy",
            fillcolor=f"rgba(35,134,54,0.06)" if bias == "bullish" else "rgba(218,54,51,0.06)",
            name=selected,
        ))
        if len(df) >= 20:
            ma20 = close.rolling(20).mean()
            fig.add_trace(go.Scatter(x=ma20.index, y=ma20, mode="lines",
                line=dict(color="#58a6ff", width=1, dash="dot"), name="MA20", opacity=0.7))
        fig.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#e6edf3",
            xaxis=dict(gridcolor="#21262d", rangeslider_visible=False),
            yaxis=dict(gridcolor="#21262d", side="right"),
            margin=dict(l=0, r=0, t=10, b=0), height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_panel:
        section_header("AI Confidence Score")
        bar_pct = int(conf * 100)
        bar_color = "#238636" if bar_pct >= 75 else ("#d29922" if bar_pct >= 55 else "#da3633")
        st.markdown(
            f'<div style="background:#21262d;border-radius:6px;height:22px;">'
            f'<div style="background:{bar_color};width:{bar_pct}%;height:22px;border-radius:6px;'
            f'text-align:center;color:#fff;font-size:13px;font-weight:700;line-height:22px;">'
            f'{bar_pct}%</div></div>', unsafe_allow_html=True
        )
        st.caption(f"Certainty: **{certainty.capitalize()}**")
        st.divider()

        section_header("Indicators")
        st.markdown(f"- **RSI (14):** {ind.get('rsi', '—')}")
        st.markdown(f"- **ADX (14):** {ind.get('adx', '—')}")
        st.markdown(f"- **MACD Hist:** {ind.get('macd_hist', '—')}")
        st.markdown(f"- **ATR (14):** {ind.get('atr', '—')}")

        sr = analysis.get("support_resistance", {})
        if sr.get("nearest_support"):
            st.markdown(f"- **Support:** {sr['nearest_support']:.5f}")
        if sr.get("nearest_resistance"):
            st.markdown(f"- **Resistance:** {sr['nearest_resistance']:.5f}")

    st.divider()

    # ── AI Narrative ──────────────────────────────────────────
    tab_narr, tab_scenarios, tab_patterns, tab_mtf = st.tabs(
        ["📝 AI Narrative", "🔀 Scenarios", "🔍 Patterns", "📊 Multi-TF"]
    )

    with tab_narr:
        narrative = analysis.get("narrative", "Analysis unavailable.")
        st.markdown(narrative)

    with tab_scenarios:
        for s in analysis.get("scenarios", []):
            st.markdown(s)

    with tab_patterns:
        cp = analysis.get("candlestick_patterns", [])
        sp = analysis.get("smc_patterns", [])
        if cp or sp:
            for p in cp[-5:]:
                c = _color(p.get("bias", "neutral"))
                st.markdown(
                    f'<div style="background:#161b22;border-left:3px solid {c};'
                    f'padding:5px 10px;border-radius:4px;margin:3px 0;font-size:13px;">'
                    f'<span style="color:{c};">■</span> {p["type"]} '
                    f'<span style="color:#8b949e;font-size:11px;">({int(p["confidence"]*100)}% conf)</span>'
                    f'</div>', unsafe_allow_html=True)
            for p in sp[-5:]:
                c = _color(p.get("bias", "neutral"))
                st.markdown(
                    f'<div style="background:#161b22;border-left:3px solid {c};'
                    f'padding:5px 10px;border-radius:4px;margin:3px 0;font-size:13px;">'
                    f'<span style="color:{c};">◆</span> {p["type"]} '
                    f'<span style="color:#8b949e;font-size:11px;">({int(p["confidence"]*100)}% conf)</span>'
                    f'</div>', unsafe_allow_html=True)
        else:
            st.info("No patterns detected in the current window.")

    with tab_mtf:
        with st.spinner("Running multi-timeframe analysis…"):
            mtf = multi_timeframe_analysis(selected)

        st.metric("MTF Alignment", f"{mtf['alignment_score']}%",
                  help="% of timeframes agreeing on the overall bias")
        st.markdown(f"**Overall bias:** {mtf['overall_bias'].capitalize()}")
        st.divider()

        for tf, data in mtf["results"].items():
            b   = data.get("bias", "—")
            co  = data.get("confidence", 0)
            col = _color(b)
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'background:#161b22;padding:6px 12px;border-radius:6px;margin:3px 0;">'
                f'<span style="color:#e6edf3;font-weight:600;">{tf}</span>'
                f'<span style="color:{col};">{b.capitalize()}</span>'
                f'<span style="color:#8b949e;">{int(co*100)}%</span></div>',
                unsafe_allow_html=True)

    st.divider()

    # ── Global overview table ─────────────────────────────────
    section_header("Global Market Overview")
    overview = get_market_overview()
    if overview:
        rows = [{"Symbol": i["symbol"],
                 "Price":  price_fmt(i["price"], i["symbol"]),
                 "Change": f"{i['change_pct']:+.2f}%",
                 "High":   price_fmt(i["high"], i["symbol"]),
                 "Low":    price_fmt(i["low"],  i["symbol"]),
                 "Bias":   "↑ Bullish" if i["change_pct"] > 0.1
                           else ("↓ Bearish" if i["change_pct"] < -0.1 else "→ Ranging")}
                for i in overview]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
