from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from database.sqlite.database import get_db
from backend.schemas import AnalysisCreate, AnalysisResponse
from backend.services import market_service

router = APIRouter()


@router.get("/symbol/{symbol}")
async def analyze_symbol(symbol: str, timeframe: str = "H1",
                         db: Session = Depends(get_db)):
    """Run full AI analysis and cache result in DB."""
    from app.ui.market_data import get_price_data
    from ai_engine.market_insights.bias_engine import generate_bias

    df = get_price_data(symbol.upper(), timeframe)
    if df.empty:
        return {"error": f"No market data for {symbol}"}

    result = generate_bias(df, symbol.upper(), timeframe)

    if "error" not in result:
        market_service.store_analysis(db, AnalysisCreate(
            symbol=symbol.upper(),
            timeframe=timeframe,
            bias=result["bias"],
            confidence=result["confidence"],
            trend_strength=result.get("trend_strength"),
            risk_level=result.get("risk_level"),
            analysis_text=result.get("narrative"),
        ))

    return result


@router.post("/screenshot")
async def analyze_screenshot(file: UploadFile = File(...)):
    return {
        "status":   "pending",
        "filename": file.filename,
        "message":  "OpenCV screenshot analysis connects in Phase 6.",
    }


@router.post("/store", response_model=AnalysisResponse)
async def store_analysis(analysis: AnalysisCreate, db: Session = Depends(get_db)):
    return market_service.store_analysis(db, analysis)


@router.get("/history/{symbol}")
async def analysis_history(symbol: str, limit: int = 20,
                           db: Session = Depends(get_db)):
    return market_service.get_analysis_history(db, symbol.upper(), limit=limit)
