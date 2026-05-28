"""System status endpoint."""

import time
from fastapi import APIRouter
from config.settings import settings
from backend.mt5_bridge.connector import connector

_start_time = time.time()

router = APIRouter()


@router.get("")
async def system_status():
    # Check DB
    db_ok = True
    try:
        from database.sqlite.database import engine
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_ok = False

    # Check AI engine
    ai_ok = True
    try:
        from ai_engine.chart_analysis.indicators import rsi  # noqa: F401
        from ai_engine.chart_analysis.analyzer import analyze_chart  # noqa: F401
    except Exception:
        ai_ok = False

    return {
        "backend":      True,
        "mt5":          connector.is_connected,
        "database":     db_ok,
        "ai_engine":    ai_ok,
        "version":      settings.APP_VERSION,
        "uptime":       round(time.time() - _start_time),
        "trading_mode": settings.TRADING_MODE,
    }
