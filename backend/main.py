"""
V2 Backend entry point.
Run with: .\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
"""

import sys
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from database.sqlite.init_db import init_db
from backend.routes import analysis, journal, autonomous, market
from backend.routes.mt5 import router as mt5_router
from backend.routes.status import router as status_router
from backend.routes.signals import router as signals_router
from backend.websocket.price_stream import manager, price_feed_loop
from backend.websocket.mt5_stream import mt5_stream_handler
from backend.mt5_bridge.connector import connector

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────
    init_db()
    logger.info("Database initialised")

    # Try connecting to MT5 on startup (non-fatal if unavailable)
    status = connector.connect()
    if status.connected:
        logger.info("MT5 connected on startup: account %s @ %s", status.account_id, status.server)
    else:
        logger.warning("MT5 not connected on startup: %s", status.reason)

    yield

    # ── Shutdown ─────────────────────────────────────────────────
    connector.disconnect()
    logger.info("Backend shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Trading Companion V2 — Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev
        "http://127.0.0.1:3000",
        "http://localhost:8502",      # Legacy Streamlit
        "http://127.0.0.1:8502",
        f"http://localhost:{settings.FRONTEND_PORT}",
        f"http://127.0.0.1:{settings.FRONTEND_PORT}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(status_router,     prefix="/api/status",     tags=["System"])
app.include_router(mt5_router,        prefix="/api/mt5",        tags=["MT5"])
app.include_router(signals_router,    prefix="/api/signals",    tags=["Signals"])
app.include_router(analysis.router,   prefix="/api/analysis",   tags=["Analysis"])
app.include_router(journal.router,    prefix="/api/journal",    tags=["Journal"])
app.include_router(autonomous.router, prefix="/api/autonomous", tags=["Autonomous"])
app.include_router(market.router,     prefix="/api/market",     tags=["Market"])

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["System"])
async def root():
    return {
        "status":  "online",
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mode":    settings.TRADING_MODE,
        "docs":    "/docs",
    }


@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy"}


# ── WebSocket — live price stream ─────────────────────────────────────────────

@app.websocket("/ws/price/{symbol}")
async def ws_price(websocket: WebSocket, symbol: str):
    """Stream live price ticks: {"symbol": "XAUUSD", "price": 2345.6, "timestamp": "..."}"""
    sym = symbol.upper()
    await manager.connect(websocket, sym)
    feed_task = asyncio.create_task(price_feed_loop(sym))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, sym)
        feed_task.cancel()


@app.websocket("/ws/mt5")
async def ws_mt5(websocket: WebSocket):
    """Stream MT5 account + open positions every 2 seconds."""
    await mt5_stream_handler(websocket)
