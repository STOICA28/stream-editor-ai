import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Adjust sys.path to discover apps
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "worker" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "storage" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "media" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "contracts" / "src"))

from stream_editor.api.database import SessionLocal, engine
from stream_editor.api.models.project import Project, MediaAsset, ProcessingJob, JobStep, Base

from stream_editor.worker.celery_app import app as celery_app
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

from stream_editor.worker.tasks.pipeline import ingest_media_task

async def create_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def run_e2e_process(file_path: str):
    await create_schema()
    
    async with SessionLocal() as db:
        project = Project(name="E2E Test Project")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)
        
    print(f"Created project: {project_id}")
    print(f"Importing: {file_path}")
    
    # We invoke the celery task directly for testing, or we just call the function.
    # Celery tasks executed synchronously in test environments or scripts
    ingest_media_task(project_id, file_path)
    
    async with SessionLocal() as db:
        from sqlalchemy.future import select
        jobs = (await db.execute(select(ProcessingJob).where(ProcessingJob.project_id == project_id))).scalars().all()
        assets = (await db.execute(select(MediaAsset).where(MediaAsset.project_id == project_id))).scalars().all()
        steps = (await db.execute(select(JobStep).where(JobStep.job_id == jobs[0].id))).scalars().all()
        
        print("\n--- RESULTS ---")
        print(f"Jobs: {len(jobs)} -> Status: {jobs[0].status}, Stage: {jobs[0].current_stage}")
        print(f"Assets created: {len(assets)}")
        for a in assets:
            print(f"  - {a.media_type}: {a.name} ({a.file_size_bytes} bytes)")
        
        print(f"Job Steps: {len(steps)}")
        for s in steps:
            print(f"  - {s.stage}: {s.status}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python process_media.py <path_to_video>")
        sys.exit(1)
        
    user_path = os.environ.get("PATH", "")
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            val, _ = winreg.QueryValueEx(key, "Path")
            os.environ["PATH"] = val + ";" + os.environ["PATH"]
    except Exception:
        pass
        
    asyncio.run(create_schema())
    
    # Create project and run async
    async def create_proj():
        async with SessionLocal() as db:
            project = Project(name="E2E Test Project")
            db.add(project)
            await db.commit()
            await db.refresh(project)
            return str(project.id)
            
    project_id = asyncio.run(create_proj())
    file_path = sys.argv[1]
    
    print(f"Created project: {project_id}")
    print(f"Importing: {file_path}")
    
    # Run sync task 1
    print("\n--- FIRST RUN ---")
    ingest_media_task(project_id, file_path)
    
    # Run sync task 2
    print("\n--- SECOND RUN ---")
    ingest_media_task(project_id, file_path)
    
    # Run async validation
    async def validate():
        async with SessionLocal() as db:
            from sqlalchemy.future import select
            jobs = (await db.execute(select(ProcessingJob).where(ProcessingJob.project_id == project_id))).scalars().all()
            assets = (await db.execute(select(MediaAsset).where(MediaAsset.project_id == project_id))).scalars().all()
            
            if not jobs:
                print("Error: No job created!")
                return
                
            steps = (await db.execute(select(JobStep).where(JobStep.job_id == jobs[0].id))).scalars().all()
            
            print("\n--- RESULTS ---")
            print(f"Jobs: {len(jobs)} -> Status: {jobs[0].status}, Stage: {jobs[0].current_stage}")
            print(f"Assets created: {len(assets)}")
            for a in assets:
                print(f"  - {a.media_type}: {a.name} ({a.file_size_bytes} bytes)")
            
            print(f"Job Steps: {len(steps)}")
            for s in steps:
                print(f"  - {s.stage}: {s.status}")
                
    asyncio.run(validate())

if __name__ == "__main__":
    main()
