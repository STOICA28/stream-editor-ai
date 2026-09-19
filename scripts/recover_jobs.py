import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api" / "src"))

from stream_editor.api.database import SessionLocal
from stream_editor.api.models.project import ProcessingJob

async def recover_jobs():
    """
    Finds all jobs that are marked as 'running' but whose lease has expired
    or heartbeat is stale.
    """
    async with SessionLocal() as db:
        from sqlalchemy.future import select
        jobs = (await db.execute(select(ProcessingJob).where(ProcessingJob.status == "running"))).scalars().all()
        
        recovered_count = 0
        now = datetime.utcnow()
        for job in jobs:
            stale = False
            if job.lease_expires_at and job.lease_expires_at < now:
                stale = True
            elif job.heartbeat_at and (now - job.heartbeat_at).total_seconds() > 300: # 5 minutes
                stale = True
                
            if stale:
                print(f"Recovering job {job.id} (stage: {job.current_stage}) -> interrupted")
                job.status = "interrupted"
                job.error_message = "worker death: lease expired"
                recovered_count += 1
            
        if recovered_count > 0:
            await db.commit()
            print(f"Successfully recovered {recovered_count} jobs.")
        else:
            print("No stalled jobs found.")

def main():
    asyncio.run(recover_jobs())

if __name__ == "__main__":
    main()
