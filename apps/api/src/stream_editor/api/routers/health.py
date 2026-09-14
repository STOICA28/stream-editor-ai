from typing import Any

from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def health() -> Any:
    return {"status": "ok", "version": "0.1.0"}

@router.get("/ready")
async def ready() -> Any:
    # In a real app this would check DB/Redis
    return {"status": "ready"}
