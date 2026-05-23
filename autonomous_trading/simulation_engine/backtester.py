"""
Backtester
Runs the AI signal engine on historical rolling windows to measure
strategy performance before deploying capital.

Algorithm:
  For each window of `lookback` bars ending at bar i:
    1. Run AI analyzer on that window
    2. If signal meets confidence threshold → simulate entry
    3. Scan next `forward` bars to see if SL or TP is hit first
    4. Record outcome
"""
import numpy as np
from typing import Dict, List


def _atr(df, period: int = 14) -> float:
    if len(df) < period:
        return float(df["Close"].iloc[-1]) * 0.001
    h = df["High"].values
    l = df["Low"].values
    c = df["Close"].values
    trs = []
    for i in range(1, len(c)):
        trs.append(max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1])))
    return float(np.mean(trs[-period:]))


def _simulate_trade(df, start_idx: int, direction: str,
                    entry: float, sl: float, tp: float,
                    forward: int = 20) -> str:
    """Scan bars after entry to find first SL or TP hit."""
    end = min(start_idx + forward, len(df))
    for i in range(start_idx, end):
        h = float(df["High"].iloc[i])
        l = float(df["Low"].iloc[i])
        if direction == "long":
            if l <= sl: return "loss"
            if h >= tp: return "win"
        else:
            if h >= sl: return "loss"
            if l <= tp: return "win"
    return "open"


def run_backtest(symbol: str, timeframe: str = "H4",
                 lookback: int = 50, forward: int = 20,
                 conf_threshold: float = 0.60,
                 risk_pct: float = 1.0,
                 sl_atr_mult: float = 1.5,
                 tp_atr_mult: float = 3.0) -> Dict:
    """
    Full walk-forward backtest.
    Returns metrics dict + trade log + equity curve.
    """
    from app.ui.market_data import get_price_data
    from ai_engine.chart_analysis.analyzer import analyze_chart

    df = get_price_data(symbol, timeframe)
    if df.empty or len(df) < lookback + forward + 10:
        return {"error": f"Not enough data for {symbol} · {timeframe}"}

    df = df.reset_index(drop=False)

    trades: List[Dict] = []
    equity = 10_000.0
    equity_curve = [equity]
    peak = equity
    max_dd = 0.0

    step = max(1, lookback // 5)

    for i in range(lookback, len(df) - forward):
        window = df.iloc[i - lookback: i].copy()
        if len(window) < 30:
            continue

        try:
            window_indexed = window.set_index(window.columns[0]) if not hasattr(window.index, 'freq') else window
            analysis = analyze_chart(window_indexed, symbol, timeframe)
        except Exception:
            continue

        bias = analysis.get("bias", "ranging")
        conf = analysis.get("confidence", 0)

        if bias not in ("bullish", "bearish") or conf < conf_threshold:
            continue

        atr_val = _atr(window)
        entry   = float(window["Close"].iloc[-1])
        direction = "long" if bias == "bullish" else "short"

        if direction == "long":
            sl = round(entry - atr_val * sl_atr_mult, 5)
            tp = round(entry + atr_val * tp_atr_mult, 5)
        else:
            sl = round(entry + atr_val * sl_atr_mult, 5)
            tp = round(entry - atr_val * tp_atr_mult, 5)

        rr = round(tp_atr_mult / sl_atr_mult, 2)

        future = df.iloc[i: i + forward]
        outcome = _simulate_trade(future, 0, direction, entry, sl, tp, forward)

        if outcome == "open":
            continue

        risk_amount = equity * risk_pct / 100
        if outcome == "win":
            pnl = risk_amount * rr
        else:
            pnl = -risk_amount

        equity = round(equity + pnl, 4)
        equity_curve.append(equity)

        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100
        if dd > max_dd:
            max_dd = dd

        trades.append({
            "bar":       i,
            "symbol":    symbol,
            "direction": direction,
            "confidence": round(conf, 3),
            "entry":     entry,
            "sl":        sl,
            "tp":        tp,
            "rr":        rr,
            "outcome":   outcome,
            "pnl":       round(pnl, 2),
            "equity":    equity,
        })

        i += step

    if not trades:
        return {
            "symbol": symbol, "timeframe": timeframe,
            "total_trades": 0, "win_rate": 0,
            "error": "No trades triggered — try lowering confidence threshold or use a longer timeframe.",
            "equity_curve": [10_000.0],
        }

    wins   = [t for t in trades if t["outcome"] == "win"]
    losses = [t for t in trades if t["outcome"] == "loss"]
    win_rate = round(len(wins) / len(trades) * 100, 1)

    returns = [t["pnl"] / (equity_curve[idx]) for idx, t in enumerate(trades)]
    sharpe = 0.0
    if len(returns) > 1:
        mean_r = np.mean(returns)
        std_r  = np.std(returns)
        if std_r > 0:
            sharpe = round(mean_r / std_r * (252 ** 0.5), 2)

    total_return = round((equity - 10_000) / 10_000 * 100, 2)
    avg_rr       = round(sum(t["rr"] for t in trades) / len(trades), 2)
    avg_conf     = round(sum(t["confidence"] for t in trades) / len(trades) * 100, 1)
    profit_factor = (
        round(sum(t["pnl"] for t in wins) / max(abs(sum(t["pnl"] for t in losses)), 0.01), 2)
        if losses else float("inf")
    )

    return {
        "symbol":        symbol,
        "timeframe":     timeframe,
        "lookback":      lookback,
        "forward":       forward,
        "conf_threshold": conf_threshold,
        "total_bars":    len(df),
        "total_trades":  len(trades),
        "wins":          len(wins),
        "losses":        len(losses),
        "win_rate":      win_rate,
        "avg_rr":        avg_rr,
        "avg_conf":      avg_conf,
        "total_return":  total_return,
        "final_equity":  round(equity, 2),
        "max_drawdown":  round(max_dd, 2),
        "sharpe":        sharpe,
        "profit_factor": profit_factor,
        "equity_curve":  equity_curve,
        "trades":        trades,
    }
