import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go

from app.ui.market_data import get_price_data, SYMBOL_MAP
from app.ui.components import price_fmt, section_header
from ai_engine.pattern_recognition.candlestick import detect_candlestick_patterns
from ai_engine.pattern_recognition.smc_patterns import detect_smc_patterns
from ai_engine.pattern_recognition.classic_patterns import detect_classic_patterns


def _color(bias: str) -> str:
    return "#238636" if bias == "bullish" else ("#da3633" if bias == "bearish" else "#d29922")


def render():
    st.markdown("## 🔍 Pattern Recognition Engine")

    c1, c2 = st.columns([2, 1])
    with c1: symbol    = st.selectbox("Symbol",    list(SYMBOL_MAP.keys()))
    with c2: timeframe = st.selectbox("Timeframe", ["H1", "H4", "D1", "M15"])

    with st.spinner(f"Scanning {symbol} · {timeframe}…"):
        df = get_price_data(symbol, timeframe)

    if df.empty:
        st.warning(f"No data for {symbol} · {timeframe}."); return

    cp  = detect_candlestick_patterns(df)
    sp  = detect_smc_patterns(df)
    clp = detect_classic_patterns(df)
    all_p = sorted(cp + sp + clp, key=lambda x: x["index"])

    # ── Chart with pattern markers ────────────────────────────
    fig = go.Figure(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing_line_color="#238636", decreasing_line_color="#da3633",
        name=symbol,
    ))

    for p in all_p:
        idx = p["index"]
        if idx >= len(df): continue
        short_label = p["type"].split(" ")[0]
        fig.add_trace(go.Scatter(
            x=[df.index[idx]],
            y=[float(df["High"].iloc[idx]) * 1.0018],
            mode="markers+text",
            marker=dict(symbol="triangle-down", size=9, color=_color(p["bias"])),
            text=[short_label],
            textposition="top center",
            textfont=dict(size=8, color=_color(p["bias"])),
            showlegend=False,
        ))

    fig.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#e6edf3",
        xaxis=dict(gridcolor="#21262d", rangeslider_visible=False),
        yaxis=dict(gridcolor="#21262d", side="right"),
        margin=dict(l=0, r=0, t=10, b=0), height=430,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    col_found, col_lib = st.columns([1, 1])

    with col_found:
        section_header("Detected Patterns", f"Last {len(df)} candles · {timeframe}")

        if all_p:
            for p in sorted(all_p, key=lambda x: x["index"], reverse=True)[:12]:
                c = _color(p["bias"])
                icon = "◆" if "FVG" in p["type"] or "Block" in p["type"] or "BOS" in p["type"] else "■"
                st.markdown(
                    f'<div style="background:#161b22;border-left:3px solid {c};'
                    f'padding:6px 10px;border-radius:4px;margin:3px 0;font-size:13px;">'
                    f'<span style="color:{c};">{icon}</span> '
                    f'<span style="color:#e6edf3;">{p["type"]}</span> '
                    f'<span style="color:#8b949e;font-size:11px;">'
                    f'conf {int(p["confidence"]*100)}% · bar {p["index"]}</span></div>',
                    unsafe_allow_html=True)
        else:
            st.info("No patterns detected in the current window. Try a different timeframe.")

        st.divider()
        b_count = sum(1 for p in all_p if p["bias"] == "bullish")
        br_count = sum(1 for p in all_p if p["bias"] == "bearish")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total", len(all_p))
        m2.metric("Bullish", b_count)
        m3.metric("Bearish", br_count)

    with col_lib:
        section_header("Pattern Library")
        t_cl, t_smc, t_cs = st.tabs(["Classic", "SMC / ICT", "Candlestick"])

        with t_cl:
            active_cl = ["Head & Shoulders ✓", "Inverse Head & Shoulders ✓",
                         "Double Top ✓", "Double Bottom ✓",
                         "Ascending Triangle ✓", "Descending Triangle ✓",
                         "Symmetrical Triangle ✓", "Bull Flag ✓", "Bear Flag ✓",
                         "Rising Wedge ✓", "Falling Wedge ✓"]
            planned_cl = ["Pennant", "Cup & Handle", "Rounding Bottom"]
            for p in active_cl:  st.markdown(f"- **{p}**")
            for p in planned_cl: st.markdown(f"- {p} *(Phase 9)*")

        with t_smc:
            active = ["Fair Value Gap ✓", "Order Block ✓", "BOS (Break of Structure) ✓"]
            planned = ["CHOCH", "Liquidity Grab", "Inducement",
                       "Premium / Discount Zones", "Equal Highs / Lows"]
            for p in active:  st.markdown(f"- **{p}**")
            for p in planned: st.markdown(f"- {p} *(Phase 5)*")

        with t_cs:
            active = ["Bullish Engulfing ✓", "Bearish Engulfing ✓",
                      "Doji ✓", "Hammer ✓", "Shooting Star ✓",
                      "Bullish Marubozu ✓", "Bearish Marubozu ✓"]
            planned = ["Morning Star", "Evening Star", "Harami", "Tweezer Tops/Bottoms"]
            for p in active:  st.markdown(f"- **{p}**")
            for p in planned: st.markdown(f"- {p} *(Phase 5)*")
