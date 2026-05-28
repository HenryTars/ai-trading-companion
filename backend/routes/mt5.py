"""MT5 REST endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.mt5_bridge.connector import connector
from backend.mt5_bridge.account import get_account_info
from backend.mt5_bridge.positions import (
    get_open_positions,
    open_position,
    close_position,
    get_history,
)

router = APIRouter()


@router.get("/status")
async def mt5_status():
    status = connector.status
    return {
        "connected":    status.connected,
        "reason":       status.reason,
        "account_id":   status.account_id,
        "broker":       status.broker,
        "server":       status.server,
        "last_checked": status.last_checked,
    }


@router.post("/connect")
async def mt5_connect():
    status = connector.connect()
    return {
        "connected":  status.connected,
        "reason":     status.reason,
        "account_id": status.account_id,
        "broker":     status.broker,
        "server":     status.server,
    }


@router.post("/disconnect")
async def mt5_disconnect():
    connector.disconnect()
    return {"connected": False}


@router.get("/account")
async def mt5_account():
    info = get_account_info()
    if info is None:
        raise HTTPException(status_code=503, detail="MT5 not connected or account unavailable")
    return info


@router.get("/positions")
async def mt5_positions(symbol: str | None = None):
    return get_open_positions(symbol=symbol)


@router.post("/positions/{ticket}/close")
async def mt5_close_position(ticket: int):
    result = close_position(ticket)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Close failed"))
    return result


@router.post("/positions/close-all")
async def mt5_close_all():
    positions = get_open_positions()
    results = [close_position(p["ticket"]) for p in positions]
    success = sum(1 for r in results if r["success"])
    return {"closed": success, "total": len(results), "results": results}


@router.get("/history")
async def mt5_history(limit: int = 50):
    return get_history(limit=limit)


# ── Order execution ───────────────────────────────────────────────────────────

class OrderRequest(BaseModel):
    symbol:    str
    direction: str = Field(..., pattern="^(BUY|SELL)$")
    volume:    float = Field(0.01, gt=0, le=100)
    sl:        float = Field(0.0, ge=0)
    tp:        float = Field(0.0, ge=0)
    comment:   str   = "AI trade"


@router.post("/orders")
async def place_order(req: OrderRequest):
    """Open a new market order on the MT5 demo account."""
    result = open_position(
        symbol    = req.symbol.upper(),
        direction = req.direction.upper(),
        volume    = req.volume,
        sl        = req.sl,
        tp        = req.tp,
        comment   = req.comment,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Order failed"))
    return result
