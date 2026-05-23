from sqlalchemy.orm import Session
from database.sqlite.models import AnalysisResult
from backend.schemas import AnalysisCreate


def store_analysis(db: Session, analysis: AnalysisCreate) -> AnalysisResult:
    db_obj = AnalysisResult(**analysis.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_latest_analysis(
    db: Session, symbol: str, timeframe: str
) -> AnalysisResult | None:
    return (
        db.query(AnalysisResult)
        .filter(AnalysisResult.symbol == symbol.upper())
        .filter(AnalysisResult.timeframe == timeframe)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )


def get_analysis_history(
    db: Session, symbol: str, limit: int = 20
) -> list[AnalysisResult]:
    return (
        db.query(AnalysisResult)
        .filter(AnalysisResult.symbol == symbol.upper())
        .order_by(AnalysisResult.created_at.desc())
        .limit(limit)
        .all()
    )
