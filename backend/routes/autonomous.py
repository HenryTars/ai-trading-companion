"""
Autonomous trading engine routes.
Paper trading with AI signals, risk management, and approval workflow.
"""
import time
import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter

from autonomous_trading.broker_connector.paper_broker import PaperBroker
from autonomous_trading.ai_risk_manager.risk_manager import RiskManager

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Singletons ────────────────────────────────────────────────────────────────

_paper = PaperBroker()
_risk  = RiskManager()

_config: dict = {
    "mode":              "assisted",   # manual | assisted | auto
    "symbols":           ["XAUUSD", "EURUSD", "GBPUSD"],
    "max_risk_pct":      1.0,
    "max_open_trades":   3,
    "max_daily_trades":  5,
    "min_confidence":    0.65,
    "min_rr":            1.5,
    "use_trailing_stop": False,
    "cooldown_minutes":  30,
    "max_daily_drawdown": 3.0,
}

_pending: dict[str, dict] = {}   # signal_id -> signal
_last_scan: float = 0.0

# ── Internal helpers ──────────────────────────────────────────────────────────

def _paper_summary_for_risk() -> dict:
    return {
        "balance":            _paper.balance,
        "daily_pnl_pct":      _paper.daily_pnl_pct,
        "consecutive_losses": _paper.consecutive_losses,
        "open_positions":     len(_paper.open_positions),
    }


def _global_lock() -> tuple[bool, str]:
    s = _paper_summary_for_risk()
    if s["daily_pnl_pct"] <= -_config["max_daily_drawdown"]:
        return True, f"Daily drawdown limit hit ({s['daily_pnl_pct']:.2f}%)"
    if s["consecutive_losses"] >= 3:
        return True, f"{s['consecutive_losses']} consecutive losses — cool-down required"
    if s["open_positions"] >= _config["max_open_trades"]:
        return True, f"Max open positions ({_config['max_open_trades']}) reached"
    return False, ""


def _scan_sync() -> list[dict]:
    from autonomous_trading.strategy_selector.signal_generator import scan_signals
    return scan_signals(_config["symbols"], timeframe="H1")


def _execute(signal_id: str) -> dict | None:
    sig = _pending.get(signal_id)
    if not sig or sig.get("status") != "pending":
        return None
    locked, reason = _global_lock()
    if locked:
        sig["status"] = "blocked"
        sig["block_reason"] = reason
        return None
    pos = _paper.open_position(
        symbol    = sig["symbol"],
        direction = sig["direction"],
        entry     = sig["entry"],
        sl        = sig["sl"],
        tp        = sig["tp"],
        risk_pct  = _config["max_risk_pct"],
        strategy  = "AI Signal",
        notes     = f"Conf {int(sig.get('confidence',0)*100)}% | R:R {sig.get('rr',0):.1f}",
    )
    sig["status"] = "executed"
    sig["position_id"] = pos["id"]
    return pos

# ── Status & Config ───────────────────────────────────────────────────────────

@router.get("/status")
async def engine_status():
    locked, reason = _global_lock()
    return {
        "mode":          _config["mode"],
        "is_locked":     locked,
        "lock_reason":   reason,
        "pending_count": sum(1 for s in _pending.values() if s.get("status") == "pending"),
        "paper":         _paper.get_summary(),
        "last_scan":     datetime.fromtimestamp(_last_scan, tz=timezone.utc).isoformat()
                         if _last_scan > 0 else None,
    }


@router.get("/config")
async def get_config():
    return _config


@router.patch("/config")
async def update_config(updates: dict):
    for k, v in updates.items():
        if k in _config:
            _config[k] = v
    _risk.min_confidence    = _config["min_confidence"]
    _risk.min_rr            = _config["min_rr"]
    _risk.max_risk_pct      = _config["max_risk_pct"]
    _risk.max_open_positions = _config["max_open_trades"]
    return _config


@router.post("/mode")
async def set_mode(body: dict):
    mode = body.get("mode", "manual")
    if mode not in ("manual", "assisted", "auto"):
        return {"ok": False, "error": "Invalid mode"}
    _config["mode"] = mode
    return {"ok": True, "mode": mode}

# ── Risk ──────────────────────────────────────────────────────────────────────

@router.get("/risk")
async def risk_state():
    locked, reason = _global_lock()
    today = datetime.now(timezone.utc).date().isoformat()
    daily_trades = sum(
        1 for t in _paper.closed_trades
        if (t.get("closed_at") or "")[:10] == today
    )
    return {
        "daily_pnl":          _paper.daily_pnl,
        "daily_trades":       daily_trades,
        "open_trades":        len(_paper.open_positions),
        "consecutive_losses": _paper.consecutive_losses,
        "is_locked":          locked,
        "lock_reason":        reason if locked else None,
        "daily_drawdown_pct": _paper.daily_pnl_pct,
        "available_risk":     _config["max_risk_pct"],
    }


@router.post("/risk/reset")
async def risk_reset():
    _paper.reset()
    _pending.clear()
    return {"ok": True, "balance": 10_000.0}

# ── Signal scanning ───────────────────────────────────────────────────────────

@router.post("/scan")
async def trigger_scan():
    global _last_scan
    if _config["mode"] == "manual":
        return {"ok": False, "message": "Switch to Assisted or Auto mode to enable scanning"}

    loop = asyncio.get_event_loop()
    signals = await loop.run_in_executor(None, _scan_sync)
    _last_scan = time.time()

    new_count = 0
    for sig in signals:
        if sig.get("confidence", 0) < _config["min_confidence"]:
            continue
        if sig.get("rr", 0) < _config["min_rr"]:
            continue
        sid = f"{sig['symbol']}_{int(time.time()*1000)}"
        sig.update({"id": sid, "created_at": datetime.now(tz=timezone.utc).isoformat(), "status": "pending"})
        _pending[sid] = sig
        new_count += 1
        if _config["mode"] == "auto":
            _execute(sid)

    return {"ok": True, "scanned": len(signals), "qualified": new_count,
            "last_scan": datetime.fromtimestamp(_last_scan, tz=timezone.utc).isoformat()}


@router.get("/pending")
async def get_pending():
    return [s for s in _pending.values() if s.get("status") == "pending"]


@router.post("/pending/{signal_id}/approve")
async def approve(signal_id: str):
    pos = _execute(signal_id)
    if pos is None:
        reason = _pending.get(signal_id, {}).get("block_reason", "Blocked by risk rules or signal expired")
        return {"ok": False, "error": reason}
    return {"ok": True, "position": pos}


@router.post("/pending/{signal_id}/reject")
async def reject(signal_id: str):
    if signal_id in _pending:
        _pending[signal_id]["status"] = "rejected"
    return {"ok": True}

# ── Paper account ─────────────────────────────────────────────────────────────

@router.get("/paper/summary")
async def paper_summary():
    return _paper.get_summary()


@router.get("/paper/positions")
async def paper_positions():
    return _paper.open_positions


@router.get("/paper/history")
async def paper_history(limit: int = 50):
    return list(reversed(_paper.closed_trades))[:limit]


@router.post("/paper/positions/{position_id}/close")
async def paper_close(position_id: str, body: dict = {}):
    exit_price = body.get("exit_price")
    if exit_price is None:
        pos = next((p for p in _paper.open_positions if p["id"] == position_id), None)
        if pos:
            try:
                from backend.services.ohlcv_service import get_latest_price
                data = get_latest_price(pos["symbol"])
                exit_price = data["price"] if data else pos["entry"]
            except Exception:
                exit_price = pos["entry"]
    result = _paper.close_position(position_id, float(exit_price), reason="manual")
    if not result:
        return {"ok": False, "error": "Position not found"}
    return {"ok": True, "trade": result}


@router.post("/paper/reset")
async def paper_reset():
    _paper.reset()
    _pending.clear()
    return {"ok": True, "balance": 10_000.0}
