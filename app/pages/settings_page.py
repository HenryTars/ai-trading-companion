import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from config.settings import settings


def render():
    st.title("⚙️ Settings")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["🔗 Broker API", "🤖 AI Engine", "⚠️ Risk Limits"])

    with tab1:
        st.subheader("Broker Connections")
        st.text_input("Binance API Key", type="password", placeholder="Set in .env file")
        st.text_input("Binance Secret", type="password", placeholder="Set in .env file")
        st.text_input("Bybit API Key", type="password", placeholder="Set in .env file")
        st.text_input("Bybit Secret", type="password", placeholder="Set in .env file")
        st.text_input("MT5 Login", placeholder="Set in .env file")
        st.text_input("MT5 Password", type="password", placeholder="Set in .env file")
        st.text_input("MT5 Server", placeholder="e.g. ICMarkets-Demo")

    with tab2:
        st.subheader("AI Configuration")
        st.text_input("OpenAI API Key (optional)", type="password")
        st.slider("Confidence Threshold", 0.5, 0.95, settings.DEFAULT_CONFIDENCE_THRESHOLD)
        st.selectbox("Default Timeframe", ["D1", "H4", "H1", "M15", "M5"])

    with tab3:
        st.subheader("Risk Management")
        st.number_input("Max Risk per Trade (%)", value=settings.MAX_RISK_PER_TRADE * 100)
        st.number_input("Max Daily Drawdown (%)", value=settings.MAX_DAILY_DRAWDOWN * 100)
        st.toggle("Enable Emergency Shutdown")
        st.toggle("Enable News Filter")
        st.toggle("Enable Volatility Filter")

    if st.button("Save Settings", type="primary"):
        st.info("Settings persistence connects to database in Phase 4.")
