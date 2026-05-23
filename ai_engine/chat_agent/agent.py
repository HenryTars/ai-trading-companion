"""
Trading Chat Agent
Routes messages to the right tools and formats responses.
Works in two modes:
  - Smart mode (no API key): intent detection + AI engine tools
  - Claude mode (Anthropic key set): full LLM conversation with tool context
"""
import re
from typing import Dict, List, Optional, Tuple
from ai_engine.chat_agent.tools import (
    resolve_symbol, resolve_timeframe,
    tool_analyze, tool_price, tool_patterns, tool_journal_stats,
    tool_paper_stats, tool_score_setup, tool_market_overview,
    tool_multi_timeframe, tool_backtest_summary,
    SYMBOL_ALIASES,
)


INTENTS = {
    "analyze":   ["analyz", "bias", "signal", "what do you think", "should i buy",
                  "should i sell", "outlook", "sentiment", "direction", "trend"],
    "price":     ["price", "how much", "rate", "quote", "trading at", "worth", "value"],
    "patterns":  ["pattern", "formation", "candlestick", "fvg", "order block",
                  "bos", "break of structure", "engulf", "hammer", "doji"],
    "journal":   ["journal", "my trades", "my history", "performance", "win rate",
                  "how many trades", "my results", "my stats", "pnl"],
    "paper":     ["paper", "paper account", "paper balance", "paper trading",
                  "virtual", "simulated"],
    "overview":  ["market", "overview", "all markets", "watchlist", "what's moving",
                  "markets today"],
    "mtf":       ["multi timeframe", "mtf", "all timeframes", "timeframe alignment",
                  "higher timeframe", "htf"],
    "backtest":  ["backtest", "back test", "historical", "test my strategy",
                  "how would", "simulate"],
    "score":     ["score", "evaluate this trade", "rate this setup", "entry", "stop loss",
                  "take profit", "good trade", "bad trade"],
    "help":      ["help", "what can you", "commands", "how do i", "guide", "capabilities"],
    "greet":     ["hello", "hi", "hey", "good morning", "good evening", "yo", "sup"],
}


def _detect_intent(msg: str) -> str:
    lower = msg.lower()
    for intent, keywords in INTENTS.items():
        if any(kw in lower for kw in keywords):
            return intent
    return "general"


def _extract_numbers(msg: str) -> List[float]:
    return [float(n) for n in re.findall(r"\d+(?:[.,]\d+)?", msg.replace(",", ""))]


def _fmt_bias(bias: str) -> str:
    return {"bullish": "📈 BULLISH", "bearish": "📉 BEARISH"}.get(bias, "↔️ RANGING")


def _fmt_conf(conf: int) -> str:
    if conf >= 75: return f"🟢 {conf}%"
    if conf >= 55: return f"🟡 {conf}%"
    return f"🔴 {conf}%"


# ── Smart mode response handlers ──────────────────────────────

def _respond_analyze(msg: str, sym: Optional[str]) -> str:
    sym = sym or "XAUUSD"
    tf  = resolve_timeframe(msg)
    r   = tool_analyze(sym, tf)
    if "error" in r:
        return f"⚠️ {r['error']}"

    ind = r.get("indicators", {})
    sr  = r.get("sr", {})
    resp  = f"### {sym} · {tf} Analysis\n\n"
    resp += f"**Bias:** {_fmt_bias(r['bias'])} &nbsp; **Confidence:** {_fmt_conf(r['confidence'])}\n\n"
    resp += f"**Trend strength:** {r['strength'].capitalize()} &nbsp;·&nbsp; "
    resp += f"**Momentum:** {r['momentum']} &nbsp;·&nbsp; **Risk:** {r['risk']}\n\n"

    if r.get("narrative"):
        resp += f"{r['narrative']}\n\n"

    if ind:
        resp += "**Indicators:**\n"
        resp += f"- RSI 14: `{ind.get('rsi', '—')}` &nbsp; MACD Hist: `{ind.get('macd_hist', '—')}`\n"
        resp += f"- ADX 14: `{ind.get('adx', '—')}` &nbsp; ATR 14: `{ind.get('atr', '—')}`\n\n"

    res_list = sr.get("resistance", [])
    sup_list = sr.get("support",    [])
    if res_list or sup_list:
        resp += "**Key levels:**\n"
        for lvl in res_list[:2]:
            resp += f"- 🔴 Resistance: `{lvl:.5f}`\n"
        for lvl in sup_list[:2]:
            resp += f"- 🟢 Support: `{lvl:.5f}`\n"
        resp += "\n"

    if r.get("scenarios"):
        resp += "**Scenarios:**\n"
        for s in r["scenarios"]:
            resp += f"{s}\n"

    return resp.strip()


def _respond_price(msg: str, sym: Optional[str]) -> str:
    sym = sym or "XAUUSD"
    r = tool_price(sym)
    if "error" in r:
        return f"⚠️ {r['error']}"
    sign = "+" if r["change_pct"] >= 0 else ""
    color = "📈" if r["change_pct"] >= 0 else "📉"
    return (f"**{sym}** is currently trading at **`{r['price']:.5f}`** "
            f"{color} `{sign}{r['change_pct']:.2f}%` on M5")


def _respond_patterns(msg: str, sym: Optional[str]) -> str:
    sym = sym or "XAUUSD"
    tf  = resolve_timeframe(msg)
    r   = tool_patterns(sym, tf)
    if "error" in r:
        return f"⚠️ {r['error']}"
    patterns = r.get("patterns", [])
    if not patterns:
        return f"No significant patterns detected on **{sym} · {tf}** right now."

    resp = f"### Patterns on {sym} · {tf}\n\n"
    for p in patterns:
        icon = "◆" if any(k in p["type"] for k in ["FVG","Block","BOS"]) else "■"
        bc   = "🟢" if p["bias"] == "bullish" else ("🔴" if p["bias"] == "bearish" else "🟡")
        resp += f"{bc} {icon} **{p['type']}** — confidence `{int(p['confidence']*100)}%` · bar `{p['index']}`\n"
    return resp.strip()


def _respond_journal(msg: str) -> str:
    r = tool_journal_stats()
    if r.get("error") or r.get("source") == "none":
        return f"⚠️ {r.get('error', 'Could not reach the API')}. Make sure the backend is running."
    perf   = r.get("perf", {})
    recent = r.get("recent", [])
    resp  = "### 📓 Your Trade Journal\n\n"
    resp += f"- **Total trades:** {perf.get('total_trades', 0)}\n"
    resp += f"- **Wins / Losses:** {perf.get('wins', 0)} / {perf.get('losses', 0)}\n"
    resp += f"- **Win rate:** {perf.get('win_rate', 0):.1f}%\n"
    resp += f"- **Avg R:R:** {perf.get('avg_rr', 0):.2f}\n"
    resp += f"- **Total P&L:** {perf.get('total_pnl_pct', 0):+.2f}%\n"
    if recent:
        resp += "\n**Recent trades:**\n"
        for t in recent[:3]:
            status = t.get("status", "—").upper()
            icon   = "✅" if status == "WIN" else ("❌" if status == "LOSS" else "⏳")
            resp += f"{icon} {t['symbol']} {t['direction'].upper()} — {status}\n"
    return resp.strip()


def _respond_paper(msg: str) -> str:
    r = tool_paper_stats()
    if "error" in r:
        return f"⚠️ {r['error']}"
    ret = round((r["balance"] - 10000) / 10000 * 100, 2)
    sign = "+" if ret >= 0 else ""
    resp  = "### 🤖 Paper Account\n\n"
    resp += f"- **Balance:** `${r['balance']:,.2f}` ({sign}{ret:.2f}% return)\n"
    resp += f"- **Today's P&L:** `${r['daily_pnl']:+.2f}`\n"
    resp += f"- **Trades:** {r['total']} closed · {r['wins']} wins · **{r['win_rate']}% WR**\n"
    if r["consec_loss"] >= 2:
        resp += f"- ⚠️ **{r['consec_loss']} consecutive losses** — consider pausing\n"
    return resp.strip()


def _respond_overview(msg: str) -> str:
    r = tool_market_overview()
    markets = r.get("markets", [])
    if not markets:
        return "⚠️ Could not fetch market data right now."
    resp = "### 🌍 Market Overview\n\n"
    for m in markets:
        sign = "+" if m["change_pct"] >= 0 else ""
        icon = "📈" if m["change_pct"] > 0.1 else ("📉" if m["change_pct"] < -0.1 else "↔️")
        resp += f"{icon} **{m['symbol']}** `{m['price']:.5f}` · `{sign}{m['change_pct']:.2f}%`\n"
    return resp.strip()


def _respond_mtf(msg: str, sym: Optional[str]) -> str:
    sym = sym or "XAUUSD"
    r = tool_multi_timeframe(sym)
    resp  = f"### 📊 Multi-Timeframe Alignment — {sym}\n\n"
    resp += f"**Alignment score:** `{r.get('alignment_score', 0)}%` &nbsp; "
    resp += f"**Overall bias:** {_fmt_bias(r.get('overall_bias', 'ranging'))}\n\n"
    for tf, data in r.get("results", {}).items():
        b    = data.get("bias", "—")
        conf = int(data.get("confidence", 0) * 100)
        icon = "🟢" if b == "bullish" else ("🔴" if b == "bearish" else "🟡")
        resp += f"{icon} **{tf}:** {b.capitalize()} `{conf}%`\n"
    return resp.strip()


def _respond_backtest(msg: str, sym: Optional[str]) -> str:
    sym = sym or "XAUUSD"
    tf  = resolve_timeframe(msg)
    resp_init = f"Running backtest on **{sym} · {tf}**... this takes a few seconds.\n\n"
    r = tool_backtest_summary(sym, tf)
    if "error" in r:
        return f"⚠️ {r['error']}"
    ret_icon = "📈" if r["total_return"] >= 0 else "📉"
    resp  = f"### 🧪 Backtest Results — {sym} · {tf}\n\n"
    resp += f"- **Trades triggered:** {r['total_trades']}\n"
    resp += f"- **Win rate:** `{r['win_rate']}%`\n"
    resp += f"- **Total return:** {ret_icon} `{r['total_return']:+.2f}%`\n"
    resp += f"- **Max drawdown:** `{r['max_drawdown']}%`\n"
    resp += f"- **Sharpe ratio:** `{r['sharpe']}`\n"
    resp += f"- **Profit factor:** `{r['profit_factor']}`\n\n"
    if r["win_rate"] >= 55 and r["total_return"] > 0:
        resp += "✅ Strategy shows a positive edge on historical data."
    elif r["total_return"] < 0:
        resp += "⚠️ Strategy was unprofitable on this data — try adjusting the confidence threshold."
    return resp.strip()


def _respond_score(msg: str, sym: Optional[str]) -> str:
    sym  = sym or "XAUUSD"
    tf   = resolve_timeframe(msg)
    nums = _extract_numbers(msg)
    if len(nums) < 3:
        return ("To score a setup, give me entry, stop loss, and take profit. Example:\n\n"
                "*Score my XAUUSD trade: entry 2320, SL 2300, TP 2370*")
    entry, sl, tp = nums[0], nums[1], nums[2]
    r = tool_score_setup(sym, entry, sl, tp, tf)
    if "error" in r:
        return f"⚠️ {r['error']}"
    grade = r.get("grade", "—")
    score = r.get("score", 0)
    gc    = {"A":"🟢","B":"🔵","C":"🟡","D":"🟠","F":"🔴"}.get(grade, "⚪")
    resp  = f"### Setup Score — {sym}\n\n"
    resp += f"{gc} **Grade {grade}** · `{score}/100` &nbsp; R:R `{r.get('rr_ratio', 0)}`\n\n"
    resp += f"**{r.get('suggestion', '')}**\n\n"
    if r.get("strengths"):
        resp += "**Strengths:**\n"
        for s in r["strengths"]: resp += f"✅ {s}\n"
        resp += "\n"
    if r.get("weaknesses"):
        resp += "**Weaknesses:**\n"
        for w in r["weaknesses"]: resp += f"⚠️ {w}\n"
    return resp.strip()


def _respond_help() -> str:
    return """### 💬 What I can do

**Market Analysis**
- *"Analyze XAUUSD H4"* — full AI bias, indicators, S/R, narrative
- *"What's the price of gold?"* — live price + change
- *"Multi-timeframe analysis on EURUSD"* — alignment across all timeframes

**Patterns**
- *"Any patterns on BTCUSDT?"* — candlestick, SMC, classic patterns

**Your Trading**
- *"Show my journal stats"* — win rate, trades, P&L
- *"Paper account balance"* — paper trading performance
- *"Score my XAUUSD trade: entry 2320, SL 2300, TP 2380"* — A-F grade

**Market Overview**
- *"What's the market overview?"* — all watchlist symbols

**Backtesting**
- *"Backtest XAUUSD H4"* — walk-forward simulation

**Tip:** Add an Anthropic API key in Settings → Broker API → `.env` (key: `ANTHROPIC_API_KEY`) to unlock full conversational AI mode."""


def _respond_greet() -> str:
    return ("👋 Hey! I'm your AI Trading Agent. I can analyze markets, scan patterns, "
            "check your journal stats, score setups, run backtests, and more.\n\n"
            "Try: *\"Analyze gold H4\"* or *\"Show my performance\"* or *\"What's moving today?\"*")


def _respond_general(msg: str, sym: Optional[str]) -> str:
    if sym:
        return _respond_analyze(msg, sym)
    return ("I'm not sure what you're asking. Try something like:\n"
            "- *Analyze XAUUSD H4*\n"
            "- *What patterns are on EURUSD?*\n"
            "- *Show my journal stats*\n"
            "- *Score my trade: entry 1.0850, SL 1.0820, TP 1.0920*\n\n"
            "Type **help** to see everything I can do.")


# ── Claude API mode ───────────────────────────────────────────

def _build_system_prompt() -> str:
    try:
        from app.ui.market_data import get_market_overview
        overview = get_market_overview()
        market_ctx = "\n".join(
            f"- {m['symbol']}: {m['price']:.5f} ({m['change_pct']:+.2f}%)"
            for m in (overview or [])
        ) or "Market data unavailable"
    except Exception:
        market_ctx = "Market data unavailable"

    return f"""You are an expert AI trading assistant embedded in the AI Trading Companion app.
You have deep knowledge of technical analysis, price action, SMC/ICT concepts, risk management, and trading psychology.

CURRENT MARKET SNAPSHOT:
{market_ctx}

YOUR CAPABILITIES:
- Analyze charts (bias, confidence, indicators, S/R levels) for any symbol
- Detect candlestick, SMC, and classic patterns
- Score trade setups with A-F grades
- Review journal performance and habits
- Run backtests on strategies
- Provide market overview and multi-timeframe analysis

RULES:
- Be concise, specific, and data-driven
- Always include risk warnings when suggesting trades
- Never guarantee profits
- Format responses in clean markdown
- When asked to analyze a symbol, be specific about bias direction and key levels
- Use the tools available to provide real data, not generic advice

The user is trading via a paper account (no real money at risk unless they connect a broker)."""


def _claude_respond(msg: str, history: List[Dict], api_key: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        messages = []
        for h in history[-10:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": msg})

        sym = resolve_symbol(msg)
        tf  = resolve_timeframe(msg)
        context_parts = []

        intent = _detect_intent(msg)
        if intent in ("analyze", "general") and sym:
            try:
                r = tool_analyze(sym, tf)
                context_parts.append(f"LIVE DATA for {sym} {tf}: {r}")
            except Exception:
                pass
        if intent == "patterns" and sym:
            try:
                r = tool_patterns(sym, tf)
                context_parts.append(f"PATTERN SCAN {sym} {tf}: {r}")
            except Exception:
                pass
        if intent == "overview":
            try:
                r = tool_market_overview()
                context_parts.append(f"MARKET OVERVIEW: {r}")
            except Exception:
                pass
        if intent in ("journal", "paper"):
            try:
                r = tool_paper_stats()
                context_parts.append(f"PAPER ACCOUNT: {r}")
            except Exception:
                pass

        system = _build_system_prompt()
        if context_parts:
            system += "\n\nREAL-TIME CONTEXT (use this data in your response):\n" + "\n".join(context_parts)

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Claude API error: {e}\n\nFalling back to smart mode:\n\n" + smart_respond(msg, history)


# ── Public API ────────────────────────────────────────────────

def smart_respond(msg: str, history: List[Dict] = None) -> str:
    sym    = resolve_symbol(msg)
    intent = _detect_intent(msg)

    handlers = {
        "greet":    lambda: _respond_greet(),
        "help":     lambda: _respond_help(),
        "price":    lambda: _respond_price(msg, sym),
        "analyze":  lambda: _respond_analyze(msg, sym),
        "patterns": lambda: _respond_patterns(msg, sym),
        "journal":  lambda: _respond_journal(msg),
        "paper":    lambda: _respond_paper(msg),
        "overview": lambda: _respond_overview(msg),
        "mtf":      lambda: _respond_mtf(msg, sym),
        "backtest": lambda: _respond_backtest(msg, sym),
        "score":    lambda: _respond_score(msg, sym),
        "general":  lambda: _respond_general(msg, sym),
    }

    return handlers.get(intent, handlers["general"])()


def respond(msg: str, history: List[Dict] = None, api_key: str = "") -> str:
    if history is None:
        history = []
    if api_key and api_key.strip().startswith("sk-ant-"):
        return _claude_respond(msg, history, api_key.strip())
    return smart_respond(msg, history)
