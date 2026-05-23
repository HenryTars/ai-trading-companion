from fastapi import APIRouter
from app.ui.market_data import get_market_overview, get_price_data

router = APIRouter()


@router.get("/overview")
async def market_overview():
    data = get_market_overview()
    return {"symbols": data, "count": len(data)}


@router.get("/price/{symbol}")
async def get_price(symbol: str, timeframe: str = "H1"):
    df = get_price_data(symbol.upper(), timeframe)
    if df.empty:
        return {"symbol": symbol.upper(), "timeframe": timeframe, "error": "No data"}
    return {
        "symbol":    symbol.upper(),
        "timeframe": timeframe,
        "last":      float(df["Close"].iloc[-1]),
        "high":      float(df["High"].max()),
        "low":       float(df["Low"].min()),
        "open":      float(df["Open"].iloc[0]),
        "candles":   len(df),
    }


@router.get("/sentiment")
async def market_sentiment():
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
        "symbols":       len(data),
    }
