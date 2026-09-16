from typing import Any
import asyncio

from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def health() -> Any:
    return {"status": "ok", "version": "0.1.0"}

@router.get("/ready")
async def ready() -> Any:
    # In a real app this would check DB/Redis
    return {"status": "ready"}

@router.get("/ai")
async def ai_health() -> Any:
    from stream_editor.models.antigravity_client import AntigravityClient
    try:
        client = AntigravityClient()
        health_data = await client.health_check()
        
        if health_data.get("available"):
            return {
                "status": "ok",
                "provider": "antigravity",
                "model": client.model,
                "executable": client.bin_path,
                "details": health_data
            }
        else:
            return {
                "status": "error",
                "provider": "antigravity",
                "model": client.model,
                "message": "Antigravity CLI unavailable or unresponsive",
                "details": health_data
            }
    except Exception as e:
        return {
            "status": "error",
            "provider": "antigravity",
            "message": str(e)
        }
