import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from ai_engine.chat_agent.agent import respond

QUICK_PROMPTS = [
    "Analyze XAUUSD H4",
    "What's the price of gold?",
    "Show my journal stats",
    "Market overview",
    "Patterns on EURUSD",
    "Multi-timeframe XAUUSD",
    "Backtest BTCUSDT H4",
    "Paper account balance",
]


def _get_api_key() -> str:
    try:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("ANTHROPIC_API_KEY"):
                    val = line.split("=", 1)[-1].strip().strip('"').strip("'")
                    return val
    except Exception:
        pass
    return ""


def render():
    st.markdown("## 💬 AI Trading Agent")

    api_key = _get_api_key()
    if api_key and api_key.startswith("sk-ant-"):
        st.caption("🟢 Claude AI mode — full conversational AI active")
    else:
        st.caption("🟡 Smart mode — add `ANTHROPIC_API_KEY` to `.env` for full AI conversation")

    # ── Init session state ─────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "agent_thinking" not in st.session_state:
        st.session_state.agent_thinking = False

    # ── Quick-action chips ─────────────────────────────────────
    with st.expander("⚡ Quick actions", expanded=len(st.session_state.chat_history) == 0):
        cols = st.columns(4)
        for i, prompt in enumerate(QUICK_PROMPTS):
            if cols[i % 4].button(prompt, key=f"quick_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.spinner("Thinking…"):
                    reply = respond(prompt, st.session_state.chat_history[:-1], api_key)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()

    st.divider()

    # ── Chat history display ───────────────────────────────────
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown(
                '<div style="text-align:center;padding:40px;color:#8b949e;">'
                '<div style="font-size:48px;">🤖</div>'
                '<div style="font-size:18px;margin-top:8px;">Ask me anything about the markets</div>'
                '<div style="font-size:13px;margin-top:4px;">'
                'Analysis · Patterns · Journal · Setups · Backtests</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"],
                                     avatar="🧑" if msg["role"] == "user" else "🤖"):
                    st.markdown(msg["content"])

    # ── Input bar ──────────────────────────────────────────────
    user_input = st.chat_input("Ask me about markets, setups, your journal…")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking…"):
                reply = respond(user_input, st.session_state.chat_history[:-1], api_key)
            st.markdown(reply)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    # ── Sidebar controls ───────────────────────────────────────
    with st.sidebar:
        st.divider()
        st.caption("Chat controls")
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

        msg_count = len(st.session_state.chat_history)
        if msg_count:
            st.caption(f"{msg_count // 2} message(s) in session")

        st.divider()
        st.caption("**Tips:**")
        st.caption("• Name a symbol: *gold, bitcoin, EURUSD*")
        st.caption("• Name a timeframe: *H4, daily, 1h*")
        st.caption("• Score a trade: *entry X, SL Y, TP Z*")
        st.caption("• Add Anthropic key in `.env` for full AI")
