from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
from datetime import datetime, timedelta
import structlog
from stream_editor.api.models.states import JobState
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

logger = structlog.get_logger()

@asynccontextmanager
async def acquire_job_lease(db: AsyncSession, run_model: Any, run_id: str, worker_id: str, lease_minutes: int = 15) -> AsyncGenerator[Any, None]:
    run = (await db.execute(select(run_model).where(run_model.id == run_id))).scalars().first()
    if not run:
        raise ValueError(f"Run {run_id} not found")
        
    if run.status == JobState.SUCCEEDED.value:
        logger.info("job_already_completed", run_id=run_id)
        yield None
        return
        
    now = datetime.utcnow()
    # Check if another worker is actively holding a lease
    if run.status == JobState.RUNNING.value and run.lease_expires_at and run.lease_expires_at > now and run.worker_id != worker_id:
        logger.info("job_currently_leased_by_other", run_id=run_id, other_worker=run.worker_id)
        raise ValueError(f"Job leased by {run.worker_id}")
        
    # Acquire lease
    run.status = JobState.RUNNING.value
    if not run.started_at:
        run.started_at = now
    run.worker_id = worker_id
    run.heartbeat_at = now
    run.lease_expires_at = now + timedelta(minutes=lease_minutes)
    if run.attempt is None:
        run.attempt = 1
    else:
        run.attempt += 1
        
    await db.commit()
    
    try:
        yield run
        run.status = JobState.SUCCEEDED.value
        if hasattr(run, "completed_at"):
            run.completed_at = datetime.utcnow()
        await db.commit()
    except Exception as e:
        logger.error("job_failed", run_id=run_id, error=str(e))
        run.status = JobState.FAILED.value
        if hasattr(run, 'error_msg'):
            run.error_msg = str(e)
        elif hasattr(run, 'error_message'):
            run.error_message = str(e)
        await db.commit()
        raise e
