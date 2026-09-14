from typing import Any

from fastapi import APIRouter

router = APIRouter()

@router.get("/{job_id}")
async def get_job(job_id: str) -> Any: return {"id": job_id, "status": "running"}

@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str) -> Any: return {"status": "cancelled"}
