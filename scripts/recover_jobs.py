import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api" / "src"))

from stream_editor.api.database import SessionLocal
from stream_editor.api.models.project import ProcessingJob

async def recover_jobs():
    """
    Finds all jobs that are marked as 'running' but have no active Celery worker processing them.
    In a single-node setup without heartbeat checks, this simply marks all 'running' jobs as 'interrupted'.
    A future enhancement can check Celery worker state.
    """
    async with SessionLocal() as db:
        from sqlalchemy.future import select
        jobs = (await db.execute(select(ProcessingJob).where(ProcessingJob.status == "running"))).scalars().all()
        
        if not jobs:
            print("No stalled jobs found.")
            return
            
        for job in jobs:
            print(f"Recovering job {job.id} (stage: {job.current_stage}) -> interrupted")
            job.status = "interrupted"
            
        await db.commit()
        print(f"Successfully recovered {len(jobs)} jobs.")

def main():
    asyncio.run(recover_jobs())

if __name__ == "__main__":
    main()
