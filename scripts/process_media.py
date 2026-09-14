import asyncio
import json
import sys
from pathlib import Path

# Adjust sys.path to discover apps
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "worker" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "storage" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "media" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "contracts" / "src"))

from stream_editor.api.database import SessionLocal, engine
from stream_editor.api.models.project import Base, MediaAsset, ProcessingJob, Project
from stream_editor.worker.celery_app import app as celery_app

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

from stream_editor.worker.tasks.pipeline import ingest_media_task


async def create_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_proj():
    async with SessionLocal() as db:
        project = Project(name="E2E Test Project")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return str(project.id)

def main():
    asyncio.run(create_schema())
    project_id = asyncio.run(create_proj())
    
    files = sys.argv[1:]
    if not files:
        print("Usage: python process_media.py <path_to_video> ...")
        sys.exit(1)
        
    for file_path in files:
        print("\n======================================")
        print(f"Importing: {file_path}")
        print("\n--- FIRST RUN ---")
        ingest_media_task(project_id, file_path)
        print("\n--- SECOND RUN (Idempotency) ---")
        ingest_media_task(project_id, file_path)
    
    # Run async validation
    async def validate():
        async with SessionLocal() as db:
            from sqlalchemy.future import select
            jobs = (await db.execute(select(ProcessingJob).where(ProcessingJob.project_id == project_id))).scalars().all()
            assets = (await db.execute(select(MediaAsset).where(MediaAsset.project_id == project_id))).scalars().all()
            
            from stream_editor.api.models.project import TimelineEvent
            events = (await db.execute(select(TimelineEvent).where(TimelineEvent.project_id == project_id))).scalars().all()
            
            print("\n======================================")
            print("--- RESULTS ---")
            print(f"Jobs created: {len(jobs)}")
            print(f"Assets created: {len(assets)}")
            for a in assets:
                parent = f"parent={a.parent_asset_id}" if a.parent_asset_id else "root"
                print(f"  - [{a.id}] {a.media_type}: {a.name} ({a.file_size_bytes} bytes, {parent})")
                
                info = a.media_info
                if info:
                    if isinstance(info, str):
                        try:
                            info = json.loads(info)
                        except:
                            pass
                    if isinstance(info, dict):
                        print(f"    width: {info.get('width')}, height: {info.get('height')}, fps: {info.get('fps')}")

            print(f"\nTimeline Events created: {len(events)}")
            for e in events:
                print(f"  - [{e.event_type}] {e.start_time:.2f}s - {e.end_time:.2f}s (producer={e.producer})")
                
    asyncio.run(validate())

if __name__ == "__main__":
    main()
