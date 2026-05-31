import os
import aiofiles
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database.sqlite.database import get_db
from backend.schemas import TradeCreate, TradeUpdate, TradeResponse
from backend.services import trade_service

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


@router.post("/trades", response_model=TradeResponse)
async def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    return trade_service.create_trade(db, trade)


@router.get("/trades", response_model=list[TradeResponse])
async def list_trades(
    skip: int = 0,
    limit: int = 100,
    symbol: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return trade_service.get_trades(db, skip=skip, limit=limit,
                                    symbol=symbol, status=status)


@router.get("/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = trade_service.get_trade(db, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.patch("/trades/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: int, update: TradeUpdate, db: Session = Depends(get_db)
):
    trade = trade_service.update_trade(db, trade_id, update)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.delete("/trades/{trade_id}")
async def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    if not trade_service.delete_trade(db, trade_id):
        raise HTTPException(status_code=404, detail="Trade not found")
    return {"message": "Trade deleted"}


@router.get("/performance")
async def get_performance(db: Session = Depends(get_db)):
    return trade_service.get_performance_summary(db)


@router.post("/trades/{trade_id}/screenshot")
async def upload_screenshot(
    trade_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    trade = trade_service.get_trade(db, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    ext  = os.path.splitext(file.filename or "chart.png")[1] or ".png"
    path = UPLOAD_DIR / f"trade_{trade_id}{ext}"

    async with aiofiles.open(path, "wb") as f:
        await f.write(await file.read())

    trade.screenshot_path = str(path)
    db.commit()
    return {"message": "Screenshot saved", "path": str(path)}
