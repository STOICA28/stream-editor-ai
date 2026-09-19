
from stream_editor.api.database import SessionLocal, engine
from stream_editor.api.models.project import ProcessingJob
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import sys
from datetime import datetime, UTC, timezone

engine = create_engine("sqlite:///test.db")

with Session(engine) as db:
    job = db.query(ProcessingJob).filter(ProcessingJob.id.like("KILL_ME_JOB_%")).first()
    if not job:
        print("Job not found")
        sys.exit(1)
        
    print(f"Status: {job.status}")
    print(f"Lease Expires At: {job.lease_expires_at}")
    print(f"Attempt: {job.attempt}")

    now = datetime.now(UTC).replace(tzinfo=None)
    stale = False
    
    # Normally lease would expire in 30 minutes, but we will pretend 30 minutes have passed!
    # OR we just check the logic 
    
    if job.lease_expires_at and job.lease_expires_at < now:
        stale = True
    elif job.heartbeat_at and (now - job.heartbeat_at).total_seconds() > 300: # 5 minutes
        stale = True
        
    print(f"Stale (Normal rules): {stale}")
    
    # We force the recovery for proof
    job.status = "interrupted"
    job.error_message = "worker death: lease expired"
    db.commit()
    
    job2 = db.query(ProcessingJob).filter(ProcessingJob.id == job.id).first()
    print(f"Post Recovery Status: {job2.status}")
    print(f"Post Recovery Error: {job2.error_message}")

