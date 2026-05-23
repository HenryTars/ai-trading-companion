import streamlit as st


def render():
    st.title("🤖 Autonomous Trading Engine")
    st.markdown("Configure and monitor the AI autonomous execution system.")
    st.divider()

    st.warning(
        "Autonomous mode executes real trades. "
        "Ensure broker connection and risk limits are configured before enabling.",
        icon="⚠️",
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Mode Control")
        mode = st.radio(
            "Trading Mode",
            ["Manual", "Assisted (AI suggests, you approve)", "Autonomous (AI executes)"],
        )
        st.divider()
        st.subheader("Risk Controls")
        st.number_input("Max Risk per Trade (%)", value=1.0, min_value=0.1, max_value=5.0)
        st.number_input("Max Daily Drawdown (%)", value=3.0, min_value=0.5, max_value=10.0)
        st.number_input("Max Consecutive Losses", value=3, min_value=1, max_value=10)

    with col2:
        st.subheader("System Status")
        st.metric("Engine Status", "OFFLINE")
        st.metric("Broker", "Not Connected")
        st.metric("Trades Today", "—")
        st.metric("P&L Today", "—")

    st.divider()
    st.info("Broker connectors and execution engine build in Phase 8.")
