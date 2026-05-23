import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import requests

from app.ui.components import section_header
from app.services.settings_service import get_all, save_all, get_setting


def _backend_live() -> bool:
    try:
        return requests.get("http://localhost:8000/health", timeout=2).status_code == 200
    except Exception:
        return False


def render():
    st.markdown("## ⚙️ Settings")

    live = _backend_live()
    if live:
        st.success("Backend API connected", icon="✅")
    else:
        st.warning("Backend API offline — start it to save settings to database", icon="⚠️")

    current = get_all()

    tab_ai, tab_risk, tab_engine, tab_broker, tab_system = st.tabs(
        ["🤖 AI Engine", "⚠️ Risk Limits", "🔧 Engine", "🔗 Broker API", "🖥️ System"])

    # ── Tab 1: AI Engine ──────────────────────────────────────
    with tab_ai:
        section_header("AI Engine Configuration")

        conf_threshold = st.slider(
            "Minimum Confidence Threshold",
            min_value=0.40, max_value=0.95,
            value=float(current.get("confidence_threshold", 0.65)),
            step=0.05,
            help="Signals below this confidence are ignored by the scanner and analyzer",
        )
        default_tf = st.selectbox(
            "Default Analysis Timeframe",
            ["H4", "D1", "H1", "W1", "M15"],
            index=["H4","D1","H1","W1","M15"].index(current.get("default_timeframe", "H4")),
        )
        scan_tf = st.selectbox(
            "Auto-Scan Timeframe",
            ["H4", "H1", "D1"],
            index=["H4","H1","D1"].index(current.get("scan_timeframe", "H4")),
            help="Timeframe used by the autonomous scanner",
        )
        watchlist_raw = st.text_input(
            "Watchlist (comma-separated symbols)",
            value=current.get("watchlist", "XAUUSD,EURUSD,BTCUSDT,GBPUSD,US100"),
            help="Symbols scanned by the autonomous engine",
        )

        if st.button("💾 Save AI Settings", type="primary"):
            save_all({
                "confidence_threshold": str(conf_threshold),
                "default_timeframe":    default_tf,
                "scan_timeframe":       scan_tf,
                "watchlist":            watchlist_raw.upper().replace(" ", ""),
            })
            st.success("AI settings saved.")

    # ── Tab 2: Risk Limits ────────────────────────────────────
    with tab_risk:
        section_header("Risk Management Rules")
        st.caption("These limits apply to both Assisted and Paper Auto modes.")

        col1, col2 = st.columns(2)
        with col1:
            max_risk = st.number_input(
                "Max Risk per Trade (%)",
                min_value=0.1, max_value=10.0, step=0.1,
                value=float(current.get("max_risk_pct", 1.0)),
            )
            max_dd = st.number_input(
                "Max Daily Drawdown (%)",
                min_value=0.5, max_value=20.0, step=0.5,
                value=float(current.get("max_daily_drawdown", 3.0)),
                help="Engine pauses for the day when this drawdown is hit",
            )
            min_rr = st.number_input(
                "Minimum R:R Ratio",
                min_value=0.5, max_value=10.0, step=0.5,
                value=float(current.get("min_rr", 1.5)),
                help="Trades with R:R below this are rejected",
            )
        with col2:
            max_losses = st.number_input(
                "Max Consecutive Losses",
                min_value=1, max_value=20, step=1,
                value=int(float(current.get("max_consecutive_losses", 3))),
                help="Engine pauses after this many losses in a row",
            )
            max_pos = st.number_input(
                "Max Open Positions",
                min_value=1, max_value=20, step=1,
                value=int(float(current.get("max_open_positions", 3))),
            )

        st.divider()
        emergency = st.toggle("🚨 Emergency Shutdown", value=False,
                               help="Immediately halts all new trades when toggled on")
        if emergency:
            st.error("Emergency shutdown active — no new trades will be executed.")

        if st.button("💾 Save Risk Settings", type="primary"):
            save_all({
                "max_risk_pct":           str(max_risk),
                "max_daily_drawdown":     str(max_dd),
                "min_rr":                 str(min_rr),
                "max_consecutive_losses": str(max_losses),
                "max_open_positions":     str(max_pos),
            })
            st.success("Risk settings saved.")

    # ── Tab 3: Engine Mode ────────────────────────────────────
    with tab_engine:
        section_header("Trading Mode")

        mode_opts = ["manual", "assisted", "autonomous"]
        cur_mode  = current.get("trading_mode", "manual")
        mode_idx  = mode_opts.index(cur_mode) if cur_mode in mode_opts else 0

        mode = st.radio(
            "Select mode",
            mode_opts,
            index=mode_idx,
            captions=[
                "You control all trades manually.",
                "AI scans and suggests, you approve each trade.",
                "AI executes paper trades automatically within risk limits.",
            ],
        )

        if mode == "autonomous":
            st.warning("Autonomous mode will auto-execute paper trades within your risk limits.")

        if st.button("💾 Save Mode", type="primary"):
            save_all({"trading_mode": mode})
            st.success(f"Mode set to **{mode.upper()}**. Restart the app to apply globally.")

        st.divider()
        section_header("Paper Account")
        start_bal = st.number_input(
            "Starting Balance ($)",
            min_value=1000.0, max_value=1_000_000.0, step=1000.0,
            value=float(current.get("paper_start_balance", 10000)),
        )
        if st.button("💾 Save Starting Balance"):
            save_all({"paper_start_balance": str(start_bal)})
            st.success("Starting balance saved. Reset the paper account in Autonomous Trading to apply.")

    # ── Tab 4: Broker API ─────────────────────────────────────
    with tab_broker:
        section_header("API Credentials")
        st.caption("All keys are stored in your `.env` file, not the database. Edit `.env` directly.")

        env_path = ROOT / ".env"
        if env_path.exists():
            env_content = env_path.read_text(encoding="utf-8")
            st.code(env_content, language="ini")
            st.caption("Edit `.env` in the project root to set API keys.")
        else:
            st.info("`.env` file not found. Copy `.env.example` to `.env` and fill in your keys.")

        st.divider()
        section_header("Connection Test")
        if st.button("Test Backend API"):
            if live:
                try:
                    resp = requests.get("http://localhost:8000/", timeout=3).json()
                    st.success(f"Backend online — {resp.get('app')} v{resp.get('version')} · mode: {resp.get('mode')}")
                except Exception as e:
                    st.error(str(e))
            else:
                st.error("Backend not reachable at http://localhost:8000")

    # ── Tab 5: System ─────────────────────────────────────────
    with tab_system:
        section_header("System Information")

        import platform
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(f"- **Python:** {platform.python_version()}")
            st.markdown(f"- **OS:** {platform.system()} {platform.release()}")
            st.markdown(f"- **Frontend:** http://localhost:8502")
            st.markdown(f"- **Backend:** http://localhost:8000")
            st.markdown(f"- **API Docs:** http://localhost:8000/docs")
        with col_r:
            try:
                import streamlit
                import plotly
                import pandas
                import numpy
                st.markdown(f"- **Streamlit:** {streamlit.__version__}")
                st.markdown(f"- **Plotly:** {plotly.__version__}")
                st.markdown(f"- **Pandas:** {pandas.__version__}")
                st.markdown(f"- **NumPy:** {numpy.__version__}")
            except Exception:
                pass

        st.divider()
        section_header("All Saved Settings")
        all_s = get_all()
        rows = [{"Key": k, "Value": v} for k, v in sorted(all_s.items())]
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.divider()
        if st.button("🔄 Reset All Settings to Defaults", type="secondary"):
            from app.services.settings_service import DEFAULTS
            save_all(DEFAULTS)
            st.success("All settings reset to defaults.")
            st.rerun()
