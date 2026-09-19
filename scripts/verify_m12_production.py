import asyncio
import json
import sys
import subprocess
import os
from pathlib import Path
import datetime

db_path = os.path.abspath("apps/api/test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "worker" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "storage" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "media" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "contracts" / "src"))

from stream_editor.api.database import SessionLocal
from stream_editor.api.models.project import Base, MediaAsset, ProcessingJob, Project, EditPlan, CandidateRun, StoryGraphRun, EditPlanRun
from stream_editor.worker.celery_app import app as celery_app
from stream_editor.api.routers.renders import run_render_task
from stream_editor.worker.tasks.pipeline import (
    ingest_media_task, normalize_timeline_task, generate_candidates_task,
    generate_story_graph_task, generate_edit_plan_task
)
from sqlalchemy.future import select

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

MOCK_VIDEO = "data/8hr_mock.mp4"

async def create_proj():
    async with SessionLocal() as db:
        project = Project(name="M12 E2E Production Run")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return str(project.id)

async def trigger_full_dag(project_id: str):
    async with SessionLocal() as db:
        # Get source asset
        asset = (await db.execute(select(MediaAsset).where(MediaAsset.project_id == project_id, MediaAsset.media_type == 'source'))).scalars().first()
        asset_id = str(asset.id)
        
    print("--- 1. NORMALIZE TIMELINE ---")
    normalize_timeline_task.delay(project_id, asset_id)
    
    print("--- 2. GENERATE CANDIDATES ---")
    res = generate_candidates_task.delay(project_id, asset_id, "mock").result
    candidate_run_id = res["run_id"]
    
    print("--- 3. GENERATE STORY GRAPH ---")
    res = generate_story_graph_task.delay(project_id, asset_id, candidate_run_id, "mock").result
    story_graph_run_id = res["run_id"]
    
    print("--- 4. GENERATE EDIT PLAN ---")
    async with SessionLocal() as db:
        plan_run = EditPlanRun(project_id=project_id, provider="mock", status="running", created_at=datetime.datetime.utcnow())
        db.add(plan_run)
        await db.commit()
        await db.refresh(plan_run)
        plan_run_id = str(plan_run.id)
        
    res = generate_edit_plan_task.delay(project_id, plan_run_id, {}).result
    plan_id = res["plan_id"]
    
    print("--- 5. RENDER FINAL ---")
    async with SessionLocal() as db:
        from stream_editor.api.models.project import RenderJob
        job = RenderJob(
            project_id=project_id,
            edit_plan_id=plan_id,
            effect_plan_run_id=None,
            render_config={"mode": "final", "resolution": "1080p"}
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = str(job.id)
        
    print("Executing Render Task...")
    await run_render_task(job_id, project_id, plan_id, None, {"mode": "final", "resolution": "1080p"})
    
    async with SessionLocal() as db:
        job = (await db.execute(select(RenderJob).where(RenderJob.id == job_id))).scalar_one()
        print(f"Render Job Status: {job.status}")
        
        asset = (await db.execute(select(MediaAsset).where(MediaAsset.id == job.output_asset_id))).scalar_one_or_none()
        if asset:
            print(f"Final Render Asset Created: {asset.id}")
            print(f"File Path: {asset.path}")
            if os.path.exists(asset.path):
                size = os.path.getsize(asset.path)
                print(f"File Exists. Size: {size} bytes.")
                if size > 0:
                    print("\n[SUCCESS] M12 PRODUCTION HARDENING FIXTURE COMPLETE: VERIFIED.")
                else:
                    print("ERROR: File is empty.")
                    sys.exit(1)
            else:
                print("ERROR: File not found.")
                sys.exit(1)
        else:
            print("ERROR: Asset not found in DB.")
            sys.exit(1)

def main():
    project_id = asyncio.run(create_proj())
    
    print("\n======================================")
    print("--- INGEST & ANALYSIS PIPELINE ---")
    # ingest_media_task automatically cascades down to extract_audio and transcribe via .delay
    ingest_media_task.delay(project_id, MOCK_VIDEO)
    
    print("\n======================================")
    print("--- ADVANCED PIPELINE ---")
    asyncio.run(trigger_full_dag(project_id))

if __name__ == "__main__":
    main()

