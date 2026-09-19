import uuid
import datetime
import socket
import asyncio
from contextlib import asynccontextmanager, contextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from stream_editor.api.models.states import JobState

WORKER_ID = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
LEASE_DURATION_MINUTES = 30

@asynccontextmanager
async def acquire_job_lease(db: AsyncSession, model_class: type, job_id: str, mark_succeeded: bool = True):
    job = (await db.execute(select(model_class).where(model_class.id == job_id))).scalar_one_or_none()
    if not job:
        raise ValueError(f"Job {job_id} of type {model_class.__name__} not found")
        
    if hasattr(job, 'status'):
        if job.status == JobState.SUCCEEDED.value:
            yield True 
            return
            
    job.worker_id = WORKER_ID
    if hasattr(job, 'started_at') and not job.started_at:
        job.started_at = datetime.datetime.utcnow()
    job.heartbeat_at = datetime.datetime.utcnow()
    job.lease_expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=LEASE_DURATION_MINUTES)
    if hasattr(job, 'attempt'):
        job.attempt = (job.attempt or 0) + 1
        
    if hasattr(job, 'status') and job.status != JobState.RUNNING.value:
        job.status = JobState.RUNNING.value
        
    await db.commit()
    
    try:
        yield False 
        
        if mark_succeeded:
            if hasattr(job, 'status'):
                job.status = JobState.SUCCEEDED.value
            if hasattr(job, 'completed_at'):
                job.completed_at = datetime.datetime.utcnow()
        await db.commit()
    except asyncio.TimeoutError as e:
        if hasattr(job, 'status'):
            job.status = JobState.FAILED.value
        if hasattr(job, 'error_message'):
            job.error_message = f"TimeoutError: {str(e)}"
        await db.commit()
        raise e
    except Exception as e:
        if hasattr(job, 'status'):
            job.status = JobState.FAILED.value
        if hasattr(job, 'error_message'):
            job.error_message = str(e)
        await db.commit()
        raise e

@contextmanager
def acquire_job_lease_sync(db, model_class: type, job_id: str, mark_succeeded: bool = True):
    job = db.get(model_class, job_id)
    if not job:
        raise ValueError(f"Job {job_id} of type {model_class.__name__} not found")
        
    if hasattr(job, 'status'):
        if job.status == JobState.SUCCEEDED.value:
            yield True 
            return
            
    job.worker_id = WORKER_ID
    if hasattr(job, 'started_at') and not job.started_at:
        job.started_at = datetime.datetime.utcnow()
    job.heartbeat_at = datetime.datetime.utcnow()
    job.lease_expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=LEASE_DURATION_MINUTES)
    if hasattr(job, 'attempt'):
        job.attempt = (job.attempt or 0) + 1
        
    if hasattr(job, 'status') and job.status != JobState.RUNNING.value:
        job.status = JobState.RUNNING.value
        
    db.commit()
    
    try:
        yield False 
        if mark_succeeded:
            if hasattr(job, 'status'):
                job.status = JobState.SUCCEEDED.value
            if hasattr(job, 'completed_at'):
                job.completed_at = datetime.datetime.utcnow()
        db.commit()
    except TimeoutError as e:
        if hasattr(job, 'status'):
            job.status = JobState.FAILED.value
        if hasattr(job, 'error_message'):
            job.error_message = f"TimeoutError: {str(e)}"
        db.commit()
        raise e
    except Exception as e:
        if hasattr(job, 'status'):
            job.status = JobState.FAILED.value
        if hasattr(job, 'error_message'):
            job.error_message = str(e)
        db.commit()
        raise e
