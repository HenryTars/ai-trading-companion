from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def engine_status():
    """Return autonomous engine status. (Phase 8)"""
    return {
        "engine": "offline",
        "broker": "disconnected",
        "mode": "manual",
        "message": "Autonomous engine builds in Phase 8.",
    }


@router.post("/start")
async def start_engine():
    """Start the autonomous trading engine. (Phase 8)"""
    return {"status": "pending", "message": "Engine starts in Phase 8."}


@router.post("/stop")
async def stop_engine():
    """Emergency stop. (Phase 8)"""
    return {"status": "pending", "message": "Emergency stop wires in Phase 8."}
