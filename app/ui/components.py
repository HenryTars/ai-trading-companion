import streamlit as st


# ── Colour palette ────────────────────────────────────────────
GREEN  = "#238636"
RED    = "#da3633"
YELLOW = "#d29922"
BLUE   = "#58a6ff"
BG_CARD = "#161b22"
BORDER  = "#30363d"
TEXT    = "#e6edf3"
MUTED   = "#8b949e"


def _bias_color(bias: str) -> str:
    b = bias.lower()
    if b == "bullish":  return GREEN
    if b == "bearish":  return RED
    return YELLOW


def confidence_badge(confidence: float, label: str = "Confidence") -> None:
    """Render a colored confidence pill inline."""
    if confidence >= 0.75:
        color, level = GREEN, "HIGH"
    elif confidence >= 0.55:
        color, level = YELLOW, "MEDIUM"
    else:
        color, level = RED, "LOW"
    st.markdown(
        f'<span style="background:{color};color:#fff;padding:3px 10px;'
        f'border-radius:12px;font-size:12px;font-weight:600;">'
        f'{label}: {int(confidence * 100)}% — {level}</span>',
        unsafe_allow_html=True,
    )


def signal_card(symbol: str, bias: str, confidence: float,
                risk: str, timeframe: str = "H1") -> None:
    """Render an AI signal card with bias stripe."""
    bc = _bias_color(bias)
    st.markdown(f"""
    <div style="background:{BG_CARD};border:1px solid {BORDER};
                border-left:4px solid {bc};border-radius:8px;
                padding:12px 16px;margin:6px 0;">
        <div style="color:{TEXT};font-size:15px;font-weight:700;">
            {symbol} &nbsp; <span style="color:{MUTED};font-size:12px;">{timeframe}</span>
        </div>
        <div style="color:{bc};font-size:13px;margin:4px 0;">
            Bias: {bias.upper()}
        </div>
        <div style="color:{MUTED};font-size:12px;">
            Confidence: {int(confidence * 100)}% &nbsp;|&nbsp; Risk: {risk}
        </div>
    </div>""", unsafe_allow_html=True)


def status_pill(text: str, color: str = GREEN) -> None:
    st.markdown(
        f'<span style="background:{color};color:#fff;padding:2px 10px;'
        f'border-radius:10px;font-size:11px;font-weight:600;">{text}</span>',
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div style="margin-bottom:4px;">'
        f'<span style="color:{TEXT};font-size:18px;font-weight:700;">{title}</span>'
        + (f'<br><span style="color:{MUTED};font-size:12px;">{subtitle}</span>' if subtitle else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def price_fmt(price: float, symbol: str = "") -> str:
    """Format price based on instrument type."""
    if price >= 1000:
        return f"{price:,.2f}"
    if "JPY" in symbol.upper():
        return f"{price:.3f}"
    return f"{price:.5f}"
