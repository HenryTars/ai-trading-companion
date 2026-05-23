import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from database.sqlite.init_db import init_db
from backend.routes import analysis, journal, autonomous, market
from backend.websocket.price_stream import manager, price_feed_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()                       # create tables on startup if they don't exist
    yield                           # app runs here


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Trading Companion — Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.FRONTEND_PORT}",
        f"http://127.0.0.1:{settings.FRONTEND_PORT}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST routers ──────────────────────────────────────────────
app.include_router(analysis.router,   prefix="/api/analysis",   tags=["Analysis"])
app.include_router(journal.router,    prefix="/api/journal",    tags=["Journal"])
app.include_router(autonomous.router, prefix="/api/autonomous", tags=["Autonomous"])
app.include_router(market.router,     prefix="/api/market",     tags=["Market"])


# ── Health endpoints ──────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "status":  "online",
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mode":    settings.TRADING_MODE,
    }


@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy"}


# ── WebSocket — live price stream ─────────────────────────────
@app.websocket("/ws/price/{symbol}")
async def ws_price(websocket: WebSocket, symbol: str):
    """
    Connect to receive live price ticks for a symbol.
    Messages are JSON: {"symbol": "XAUUSD", "price": 2345.6, "timestamp": "..."}
    """
    sym = symbol.upper()
    await manager.connect(websocket, sym)
    feed_task = asyncio.create_task(price_feed_loop(sym))
    try:
        while True:
            await websocket.receive_text()   # keep-alive ping from client
    except WebSocketDisconnect:
        manager.disconnect(websocket, sym)
        feed_task.cancel()
