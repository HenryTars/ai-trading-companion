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
    h1, h2, h3 { color: #e6edf3; }
    div[data-testid="metric-container"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px 14px;
    }
</style>
""", unsafe_allow_html=True)


def _backend_live() -> bool:
    try:
        import requests
        return requests.get("http://localhost:8000/health", timeout=1).status_code == 200
    except Exception:
        return False


def _paper_balance() -> str:
    try:
        import json
        state_file = ROOT / "database" / "paper_account.json"
        if state_file.exists():
            data = json.loads(state_file.read_text(encoding="utf-8"))
            bal = data.get("balance", 10000)
            ret = round((bal - 10000) / 10000 * 100, 2)
            sign = "+" if ret >= 0 else ""
            return f"${bal:,.0f} ({sign}{ret:.1f}%)"
    except Exception:
        pass
    return "$10,000 (0.0%)"


def _saved_mode() -> str:
    try:
        from app.services.settings_service import get_setting
        return get_setting("trading_mode") or settings.TRADING_MODE
    except Exception:
        return settings.TRADING_MODE


# ── Sidebar Navigation ────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 📈 {settings.APP_NAME}")
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

    # ── Status panel ──────────────────────────────────────────
    trading_mode = _saved_mode()
    mode_colors  = {"manual": "🟡", "assisted": "🟠", "autonomous": "🟢"}
    mode_icon    = mode_colors.get(trading_mode, "⚪")

    backend_ok   = _backend_live()
    api_icon     = "🟢" if backend_ok else "🔴"
    api_label    = "API online" if backend_ok else "API offline"

    st.markdown(
        f'<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 12px;">'
        f'<div style="font-size:12px;color:#8b949e;margin-bottom:6px;">SYSTEM STATUS</div>'
        f'<div style="font-size:13px;">{api_icon} {api_label}</div>'
        f'<div style="font-size:13px;">{mode_icon} Mode: <b>{trading_mode.upper()}</b></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    # ── Paper account quick view ──────────────────────────────
    paper_bal = _paper_balance()
    st.markdown(
        f'<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 12px;">'
        f'<div style="font-size:12px;color:#8b949e;margin-bottom:4px;">PAPER ACCOUNT</div>'
        f'<div style="font-size:13px;font-weight:700;color:#e6edf3;">{paper_bal}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
    st.caption(f"Backend: http://localhost:8000")
    st.caption(f"Docs: http://localhost:8000/docs")


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
