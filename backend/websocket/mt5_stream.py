"""
MT5 WebSocket broadcaster.
Pushes account info + open positions every 2 seconds.
"""

import asyncio
import logging
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from backend.mt5_bridge.account import get_account_info
from backend.mt5_bridge.positions import get_open_positions

logger = logging.getLogger(__name__)


async def mt5_stream_handler(websocket: WebSocket) -> None:
    """
    Accepts a WebSocket connection and streams MT5 account + position data.
    MT5 calls are synchronous but microseconds-fast — safe to call directly
    in the event loop (no run_in_executor needed for this cadence).
    """
    await websocket.accept()
    logger.info("MT5 WS client connected")

    try:
        while True:
            account   = get_account_info()
            positions = get_open_positions()

            payload = {
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "account":   account,
                "positions": positions,
            }
            await websocket.send_json(payload)
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        logger.info("MT5 WS client disconnected")
    except Exception as exc:
        logger.warning("MT5 WS error: %s", exc)
