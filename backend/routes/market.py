"""Market data routes — OHLCV, prices, overview."""

from fastapi import APIRouter, HTTPException
from backend.services.ohlcv_service import get_ohlcv, get_latest_price, get_market_overview

router = APIRouter()


@router.get("/ohlcv/{symbol}")
async def ohlcv(symbol: str, timeframe: str = "H1"):
    """Return OHLCV candles for LightweightCharts."""
    candles = get_ohlcv(symbol.upper(), timeframe.upper())
    if not candles:
        raise HTTPException(status_code=404, detail=f"No market data for {symbol}")
    return {"symbol": symbol.upper(), "timeframe": timeframe.upper(), "candles": candles}


@router.get("/price/{symbol}")
async def price(symbol: str):
    """Latest price snapshot."""
    data = get_latest_price(symbol.upper())
    if not data:
        raise HTTPException(status_code=404, detail=f"No price data for {symbol}")
    return data


@router.get("/overview")
async def overview():
    """Multi-symbol overview for watchlist."""
    return get_market_overview()


@router.get("/sentiment")
async def sentiment():
    data = get_market_overview()
    bullish = sum(1 for d in data if d["change_pct"] >  0.1)
    bearish = sum(1 for d in data if d["change_pct"] < -0.1)
    neutral = len(data) - bullish - bearish
    overall = "bullish" if bullish > bearish else ("bearish" if bearish > bullish else "neutral")
    return {
        "bullish_count": bullish,
        "bearish_count": bearish,
        "neutral_count": neutral,
        "overall":       overall,
    }
