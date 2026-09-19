from contextlib import contextmanager
import uuid
import datetime
import socket

from collections.abc import Generator
from typing import Any

WORKER_ID = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
LEASE_DURATION_MINUTES = 30

@contextmanager
def acquire_job_lease_sync(db: Any, model_class: type, job_id: str) -> Generator[bool, None, None]:
    from stream_editor.api.models.states import JobState
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
        
    if hasattr(job, 'status'):
        job.status = JobState.RUNNING.value
        
    db.commit()
    
    try:
        yield False 
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
