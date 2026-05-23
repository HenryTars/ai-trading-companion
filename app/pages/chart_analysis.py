import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from app.ui.market_data import get_price_data, SYMBOL_MAP
from app.ui.components import price_fmt, section_header
from ai_engine.market_insights.bias_engine import generate_bias
from ai_engine.strategy_engine.setup_scorer import score_setup
from ai_engine.vision.screenshot_analyzer import analyze_screenshot


def _layout(height: int = 480) -> dict:
    return dict(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#e6edf3",
                xaxis=dict(gridcolor="#21262d", rangeslider_visible=False),
                yaxis=dict(gridcolor="#21262d", side="right"),
                legend=dict(bgcolor="#161b22", bordercolor="#30363d", font_size=11),
                margin=dict(l=0, r=0, t=10, b=0), height=height)

def _add_ma(fig, df):
    for span, color in [(20, "#58a6ff"), (50, "#d2a679"), (200, "#d29922")]:
        if len(df) >= span:
            fig.add_trace(go.Scatter(x=df.index, y=df["Close"].rolling(span).mean(),
                mode="lines", line=dict(color=color, width=1),
                name=f"MA{span}", opacity=0.85))
    return fig

def _add_bb(fig, df):
    if len(df) < 20: return fig
    ma  = df["Close"].rolling(20).mean()
    std = df["Close"].rolling(20).std()
    fig.add_trace(go.Scatter(x=df.index, y=ma + 2*std, mode="lines",
        line=dict(color="#58a6ff", width=1, dash="dot"), name="BB Upper", opacity=0.6))
    fig.add_trace(go.Scatter(x=df.index, y=ma - 2*std, mode="lines",
        line=dict(color="#58a6ff", width=1, dash="dot"), name="BB Lower", opacity=0.6,
        fill="tonexty", fillcolor="rgba(88,166,255,0.04)"))
    return fig


def render():
    st.markdown("## 📊 AI Chart Analysis")

    tab_live, tab_ai, tab_score, tab_upload = st.tabs(
        ["📡 Live Chart", "🤖 AI Analysis", "📐 Setup Scorer", "📁 Upload"])

    # ── Shared controls ───────────────────────────────────────
    with st.sidebar:
        st.divider()
        st.caption("Chart controls")
        symbol = st.selectbox("Symbol", list(SYMBOL_MAP.keys()), key="ca_sym")
        tf     = st.selectbox("Timeframe", ["H1", "H4", "D1", "M15", "M5", "W1"], key="ca_tf")
        show_ma = st.toggle("Moving Averages", value=True,  key="ca_ma")
        show_bb = st.toggle("Bollinger Bands",  value=False, key="ca_bb")

    with st.spinner(f"Loading {symbol} · {tf}…"):
        df = get_price_data(symbol, tf)

    # ── Tab 1: Live Chart ─────────────────────────────────────
    with tab_live:
        if df.empty:
            st.warning(f"No data for {symbol} · {tf}.")
        else:
            fig = go.Figure(go.Candlestick(
                x=df.index, open=df["Open"], high=df["High"],
                low=df["Low"], close=df["Close"],
                increasing_line_color="#238636", decreasing_line_color="#da3633", name=symbol))
            if show_ma: fig = _add_ma(fig, df)
            if show_bb: fig = _add_bb(fig, df)
            fig.update_layout(**_layout(480))
            st.plotly_chart(fig, use_container_width=True)

            if "Volume" in df.columns and df["Volume"].sum() > 0:
                colors = ["#238636" if float(df["Close"].iloc[i]) >= float(df["Open"].iloc[i])
                          else "#da3633" for i in range(len(df))]
                vf = go.Figure(go.Bar(x=df.index, y=df["Volume"], marker_color=colors))
                vf.update_layout(**_layout(120)); vf.update_layout(showlegend=False)
                st.plotly_chart(vf, use_container_width=True)

            c = df["Close"]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Last",  price_fmt(float(c.iloc[-1]), symbol))
            m2.metric("High",  price_fmt(float(df["High"].max()), symbol))
            m3.metric("Low",   price_fmt(float(df["Low"].min()),  symbol))
            pct = (float(c.iloc[-1]) - float(c.iloc[0])) / float(c.iloc[0]) * 100
            m4.metric("Period Δ", f"{pct:+.2f}%", delta_color="normal" if pct >= 0 else "inverse")

    # ── Tab 2: AI Analysis ────────────────────────────────────
    with tab_ai:
        if df.empty:
            st.warning(f"No data for {symbol} · {tf}.")
        else:
            with st.spinner("Running AI analysis…"):
                analysis = generate_bias(df, symbol, tf)

            bias  = analysis.get("bias", "ranging")
            conf  = analysis.get("confidence", 0.5)
            risk  = analysis.get("risk_level", "—")
            bc    = "#238636" if bias == "bullish" else ("#da3633" if bias == "bearish" else "#d29922")
            ind   = analysis.get("indicators", {})
            sr    = analysis.get("support_resistance", {})

            # Score bar
            bar = int(conf * 100)
            bar_c = "#238636" if bar >= 75 else ("#d29922" if bar >= 55 else "#da3633")
            st.markdown(
                f'<div style="background:#21262d;border-radius:6px;height:26px;margin-bottom:12px;">'
                f'<div style="background:{bar_c};width:{bar}%;height:26px;border-radius:6px;'
                f'text-align:center;color:#fff;font-size:14px;font-weight:700;line-height:26px;">'
                f'AI Confidence: {bar}%</div></div>', unsafe_allow_html=True)

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Bias",       bias.capitalize())
            k2.metric("Strength",   analysis.get("trend_strength", "—").capitalize())
            k3.metric("Momentum",   analysis.get("momentum", "—"))
            k4.metric("Risk",       risk)
            k5.metric("Volatility", analysis.get("volatility", "—"))

            st.divider()
            left, right = st.columns([2, 1])

            with left:
                st.markdown(analysis.get("narrative", ""))
                st.divider()
                section_header("Scenarios")
                for s in analysis.get("scenarios", []):
                    st.markdown(s)

            with right:
                section_header("Indicators")
                st.markdown(f"- **RSI 14:** {ind.get('rsi', '—')}")
                st.markdown(f"- **ADX 14:** {ind.get('adx', '—')}")
                st.markdown(f"- **MACD Hist:** {ind.get('macd_hist', '—')}")
                st.markdown(f"- **ATR 14:** {ind.get('atr', '—')}")
                st.markdown(f"- **EMA 20:** {ind.get('ema20', '—')}")
                st.markdown(f"- **EMA 50:** {ind.get('ema50', '—')}")
                st.divider()
                section_header("Support / Resistance")
                for lvl in sr.get("resistance", [])[:3]:
                    st.markdown(f'<span style="color:#da3633;">▲ {lvl:.5f}</span>', unsafe_allow_html=True)
                st.markdown(f'<span style="color:#8b949e;">── price ──</span>', unsafe_allow_html=True)
                for lvl in sr.get("support", [])[:3]:
                    st.markdown(f'<span style="color:#238636;">▼ {lvl:.5f}</span>', unsafe_allow_html=True)

    # ── Tab 3: Setup Scorer ───────────────────────────────────
    with tab_score:
        if df.empty:
            st.warning(f"No data for {symbol} · {tf}.")
        else:
            st.markdown("Enter a proposed trade and get an AI quality score.")
            with st.form("scorer_form"):
                sc1, sc2, sc3 = st.columns(3)
                with sc1: entry = st.number_input("Entry Price", min_value=0.0, format="%.5f")
                with sc2: sl    = st.number_input("Stop Loss",   min_value=0.0, format="%.5f")
                with sc3: tp    = st.number_input("Take Profit", min_value=0.0, format="%.5f")
                run = st.form_submit_button("Score This Setup", type="primary")

            if run and entry > 0 and sl > 0 and tp > 0:
                with st.spinner("Scoring setup…"):
                    result = score_setup(df, entry, sl, tp, symbol, tf)

                grade_color = {"A": "#238636", "B": "#58a6ff", "C": "#d29922",
                               "D": "#d2a679", "F": "#da3633"}.get(result["grade"], "#8b949e")

                st.markdown(
                    f'<div style="text-align:center;background:#161b22;border:2px solid {grade_color};'
                    f'border-radius:12px;padding:20px;margin:10px 0;">'
                    f'<div style="color:{grade_color};font-size:48px;font-weight:800;">'
                    f'{result["grade"]}</div>'
                    f'<div style="color:#e6edf3;font-size:24px;">{result["score"]} / 100</div>'
                    f'<div style="color:#8b949e;font-size:13px;margin-top:6px;">'
                    f'R:R {result["rr_ratio"]} · {result["direction"].upper()} · {result["trend_bias"].capitalize()} bias'
                    f'</div></div>', unsafe_allow_html=True)

                st.markdown(f"**Recommendation:** {result['suggestion']}")
                col_s, col_w = st.columns(2)
                with col_s:
                    st.markdown("**Strengths**")
                    for s in result["strengths"]: st.markdown(f"✅ {s}")
                with col_w:
                    st.markdown("**Weaknesses**")
                    for w in result["weaknesses"]: st.markdown(f"⚠️ {w}")

    # ── Tab 4: Upload ─────────────────────────────────────────
    with tab_upload:
        uploaded = st.file_uploader("Upload chart screenshot (PNG / JPG)",
                                    type=["png", "jpg", "jpeg"])
        if uploaded:
            col_orig, col_ann = st.columns(2)
            with col_orig:
                st.caption("Original")
                st.image(uploaded, use_container_width=True)

            if st.button("Analyze Screenshot", type="primary", use_container_width=True):
                with st.spinner("Running vision analysis…"):
                    result = analyze_screenshot(uploaded.read())

                if "error" in result:
                    st.error(result["error"])
                else:
                    with col_ann:
                        st.caption("Annotated (S/R zones + trend)")
                        st.image(result["annotated_image"], use_container_width=True)

                    bias   = result["bias"]
                    conf   = result["confidence"]
                    bc     = "#238636" if bias == "bullish" else ("#da3633" if bias == "bearish" else "#d29922")
                    trend  = result["trend"]
                    candle = result["candle_structure"]
                    sr     = result["sr_zones"]

                    st.markdown(
                        f'<div style="background:#161b22;border:1px solid {bc};border-radius:8px;'
                        f'padding:14px;margin:8px 0;">'
                        f'<div style="color:{bc};font-weight:700;font-size:16px;">'
                        f'{bias.upper()} BIAS</div>'
                        f'<div style="color:#e6edf3;">Vision Confidence: {conf}%</div>'
                        f'<div style="color:#8b949e;font-size:12px;margin-top:4px;">'
                        f'Trend lines: {trend["direction"].capitalize()} · '
                        f'Candle sentiment: {candle["sentiment"].capitalize()}</div>'
                        f'</div>', unsafe_allow_html=True)

                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Trend Direction", trend["direction"].capitalize())
                    k2.metric("Detected Lines",  trend["total_lines"])
                    k3.metric("S/R Zones",        len(sr.get("zones", [])))
                    k4.metric("Bullish Candles",  f"{candle['bullish_pct']}%")

                    if result["pattern_hints"]:
                        st.divider()
                        st.markdown("**AI Observations**")
                        for hint in result["pattern_hints"]:
                            st.markdown(f"- {hint}")
        else:
            st.markdown("""
**How it works:**
1. Screenshot any chart (TradingView, MT4/5, etc.)
2. Upload here — AI analyzes it with OpenCV computer vision
3. Detects: trend direction, S/R zones, candle sentiment, pattern hints
4. Annotated image returned with highlighted zones
""")
