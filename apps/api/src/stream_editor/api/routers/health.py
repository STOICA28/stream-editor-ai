from typing import Any
import asyncio
from fastapi import APIRouter
from sqlalchemy import text
from stream_editor.api.database import SessionLocal

router = APIRouter()

@router.get("")
async def health() -> Any:
    return {"status": "ok", "version": "0.1.0"}

@router.get("/ready")
async def ready() -> Any:
    from stream_editor.api.config import settings
    from stream_editor.models.antigravity_client import AntigravityClient
    from stream_editor.api import database as db_mod
    import redis.asyncio as aioredis
    import os

    diagnostics = {}
    is_ready = True
    is_degraded = False

    # 1. Database Check
    try:
        async with db_mod.SessionLocal() as db:
            await db.execute(text("SELECT 1"))
            diagnostics["database"] = "available"
    except Exception as e:
        diagnostics["database"] = f"unavailable: {str(e)}"
        is_ready = False

    # 2. Storage Check
    try:
        data_dir = settings.DATA_DIR
        test_file = data_dir / ".health_check"
        data_dir.mkdir(parents=True, exist_ok=True)
        test_file.write_text("ok")
        test_file.unlink(missing_ok=True)
        diagnostics["storage"] = "available"
    except Exception as e:
        diagnostics["storage"] = f"unavailable: {str(e)}"
        is_ready = False

    # 3. Broker Check
    try:
        r = aioredis.from_url(settings.REDIS_URL)  # type: ignore[no-untyped-call]
        pong = await r.ping()
        await r.aclose()
        diagnostics["broker"] = "available" if pong else "unavailable"
    except Exception as e:
        diagnostics["broker"] = f"unavailable: {str(e)}"
        is_degraded = True

    # 4. Antigravity Diagnostic (Executable check only, zero model inference)
    try:
        client = AntigravityClient()
        if client.is_available:
            diagnostics["antigravity"] = "available"
        else:
            diagnostics["antigravity"] = "unavailable"
            is_degraded = True
    except Exception as e:
        diagnostics["antigravity"] = f"unavailable: {str(e)}"
        is_degraded = True

    if not is_ready:
        return {"status": "not_ready", "diagnostics": diagnostics}
    if is_degraded:
        return {"status": "degraded", "diagnostics": diagnostics}
    return {"status": "ready", "diagnostics": diagnostics}

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
