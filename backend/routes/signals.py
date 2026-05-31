"""
AI Signals route — generates trading signals from the AI engine.
Results are cached in-memory for 5 minutes to avoid hammering yfinance.
"""

import time
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter()

_cache: dict[str, dict] = {}
_last_generated: float = 0.0
_CACHE_TTL = 300          # 5 minutes
_SIGNAL_SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "BTCUSDT", "ETHUSDT", "US100"]


def _bias_norm(raw: str) -> str:
    if raw == "bullish": return "bullish"
    if raw == "bearish": return "bearish"
    return "ranging"


def _grade(conf: float) -> str:
    if conf >= 0.80: return "A"
    if conf >= 0.70: return "B"
    if conf >= 0.60: return "C"
    if conf >= 0.55: return "D"
    return "F"


def _patterns(analysis: dict) -> list[str]:
    out: list[str] = []
    for key in ("candlestick_patterns", "smc_patterns"):
        raw = analysis.get(key, [])
        if isinstance(raw, list):
            for p in raw:
                if isinstance(p, dict):
                    out.append(p.get("type", p.get("name", "")))
                elif isinstance(p, str):
                    out.append(p)
        elif isinstance(raw, dict):
            for v in raw.values():
                if isinstance(v, list):
                    out.extend(str(x) for x in v[:2])
    return [p for p in out if p][:6]


def _generate_sync() -> list[dict]:
    from backend.services.ohlcv_service import get_ohlcv
    from ai_engine.chart_analysis.analyzer import analyze_chart

    results: list[dict] = []

    for symbol in _SIGNAL_SYMBOLS:
        try:
            candles = get_ohlcv(symbol, "H1")
            if not candles or len(candles) < 50:
                continue

            df = pd.DataFrame(candles)
            df = df.rename(columns={
                "open": "Open", "high": "High",
                "low":  "Low",  "close": "Close", "volume": "Volume",
            })
            df.index = pd.to_datetime(df["time"], unit="s", utc=True)

            analysis = analyze_chart(df, symbol, "H1")
            if "error" in analysis:
                continue

            conf = float(analysis.get("confidence", 0.0))
            bias = _bias_norm(analysis.get("bias", "ranging"))

            if bias == "ranging" or conf < 0.55:
                continue

            price = float(analysis.get("current_price", candles[-1]["close"]))
            atr   = float(analysis.get("indicators", {}).get("atr", price * 0.005))
            if atr == 0:
                atr = price * 0.005

            sl = (price - atr * 1.5) if bias == "bullish" else (price + atr * 1.5)
            tp = (price + atr * 3.0) if bias == "bullish" else (price - atr * 3.0)
            rr = abs(tp - price) / abs(sl - price) if abs(sl - price) > 0 else 0

            results.append({
                "id":          f"{symbol}_H1",
                "symbol":      symbol,
                "timeframe":   "H1",
                "bias":        bias,
                "confidence":  round(conf, 2),
                "grade":       _grade(conf),
                "entry_zone":  [round(price * 0.9998, 5), round(price * 1.0002, 5)],
                "stop_loss":   round(sl, 5),
                "take_profit": round(tp, 5),
                "risk_reward": round(rr, 2),
                "narrative":   analysis.get("narrative", ""),
                "patterns":    _patterns(analysis),
                "created_at":  datetime.now(tz=timezone.utc).isoformat(),
                "expires_at":  (datetime.now(tz=timezone.utc) + timedelta(hours=4)).isoformat(),
            })

        except Exception as exc:
            logger.warning("Signal generation failed for %s: %s", symbol, exc)

    return results


@router.get("")
async def list_signals():
    global _cache, _last_generated

    if time.time() - _last_generated > _CACHE_TTL:
        loop = asyncio.get_event_loop()
        signals = await loop.run_in_executor(None, _generate_sync)
        _cache = {s["id"]: s for s in signals}
        _last_generated = time.time()

    return list(_cache.values())


@router.post("/{signal_id}/approve")
async def approve_signal(signal_id: str):
    sig = _cache.get(signal_id)
    if not sig:
        return {"ok": False, "error": "Signal not found or expired"}

    from backend.mt5_bridge.connector import connector
    from backend.mt5_bridge.positions import open_position

    if not connector.is_connected:
        return {"ok": False, "error": "MT5 not connected — start MT5 and click Connect"}

    direction = "BUY" if sig["bias"] == "bullish" else "SELL"
    symbol, sl, tp, grade, conf = sig["symbol"], sig["stop_loss"], sig["take_profit"], sig["grade"], sig["confidence"]

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: open_position(
        symbol    = symbol,
        direction = direction,
        volume    = 0.01,
        sl        = sl,
        tp        = tp,
        comment   = f"AI {grade} {int(conf*100)}%",
    ))
    if result.get("success"):
        sig["status"] = "executed"
        sig["mt5_ticket"] = result["ticket"]
        return {"ok": True, "ticket": result["ticket"], "price": result["price"]}

    return {"ok": False, "error": result.get("error", "MT5 order failed")}


@router.post("/{signal_id}/reject")
async def reject_signal(signal_id: str):
    if signal_id in _cache:
        _cache[signal_id]["status"] = "rejected"
    return {"ok": True}
