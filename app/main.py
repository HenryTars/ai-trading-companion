import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from config.settings import settings

st.set_page_config(
    page_title=settings.APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0d1117; }
    [data-testid="stSidebar"] * { color: #e6edf3 !important; }
    .main { background-color: #0d1117; }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        margin: 4px;
    }
    h1, h2, h3 { color: #e6edf3; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## 📈 {settings.APP_NAME}")
    st.caption(f"v{settings.APP_VERSION}")
    st.divider()

    pages = {
        "🏠  Dashboard":            "dashboard",
        "📊  Chart Analysis":       "chart_analysis",
        "🔍  Pattern Recognition":  "pattern_recognition",
        "🌍  Market Insights":      "market_insights",
        "📓  Trade Journal":        "trade_journal",
        "🤖  Autonomous Trading":   "autonomous_trading",
        "📈  Performance":          "performance",
        "⚙️  Settings":             "settings_page",
    }

    selected = st.radio("", list(pages.keys()), label_visibility="collapsed")
    st.divider()

    mode_color = {"manual": "🟡", "assisted": "🟠", "autonomous": "🔴"}.get(
        settings.TRADING_MODE, "⚪"
    )
    st.caption(f"{mode_color} Mode: **{settings.TRADING_MODE.upper()}**")
    st.caption(f"API: http://localhost:{settings.BACKEND_PORT}")

# ── Page Router ───────────────────────────────────────────────
page_key = pages[selected]

if page_key == "dashboard":
    from app.pages import dashboard; dashboard.render()
elif page_key == "chart_analysis":
    from app.pages import chart_analysis; chart_analysis.render()
elif page_key == "pattern_recognition":
    from app.pages import pattern_recognition; pattern_recognition.render()
elif page_key == "market_insights":
    from app.pages import market_insights; market_insights.render()
elif page_key == "trade_journal":
    from app.pages import trade_journal; trade_journal.render()
elif page_key == "autonomous_trading":
    from app.pages import autonomous_trading; autonomous_trading.render()
elif page_key == "performance":
    from app.pages import performance; performance.render()
elif page_key == "settings_page":
    from app.pages import settings_page; settings_page.render()
