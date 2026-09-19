
import uuid
import time
import os
import structlog
import sys
from datetime import datetime, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from stream_editor.api.models.project import ProcessingJob, MediaAsset, Project, JobStep

from stream_editor.worker.tasks.pipeline import (
    generate_candidates_task,
    generate_story_graph_task,
    generate_edit_plan_task
)
from stream_editor.worker.celery_app import app as celery_app

def log(msg):
    print(msg)
    sys.stdout.flush()

if __name__ == "__main__":
    engine = create_engine("sqlite:///test.db")
    project_id = None
    asset_id = None
    
    with Session(engine) as db:
        # find the real-5h project
        proj = db.query(Project).filter(Project.id == "real-5h-65655576").first()
        if not proj:
            log("No real-5h project found!")
            exit(1)
        project_id = proj.id
        asset = db.query(MediaAsset).filter_by(project_id=project_id, media_type="source").first()
        asset_id = asset.id

    log(f"[{datetime.now().time()}] Skipping M5 (already complete). Finding candidate run...")
    #res = generate_candidates_task.delay(project_id, asset_id, provider_name="antigravity")
    
    # Wait for CandidateRun
    from stream_editor.api.models.project import CandidateRun
    candidate_run_id = None
    while not candidate_run_id:
        time.sleep(10)
        with Session(engine) as db:
            run = db.query(CandidateRun).filter_by(source_asset_id=asset_id, status="completed").first()
            if run:
                candidate_run_id = run.id
                log(f"[{datetime.now().time()}] Candidate generation completed! Run ID: {candidate_run_id}")
                
    log(f"[{datetime.now().time()}] Dispatching M7 (Story Graph) with Antigravity...")
    generate_story_graph_task.delay(project_id, asset_id, candidate_run_id, provider_name="antigravity")
    
    from stream_editor.api.models.project import StoryGraphRun
    story_graph_id = None
    while not story_graph_id:
        time.sleep(10)
        with Session(engine) as db:
            run = db.query(StoryGraphRun).filter_by(source_asset_id=asset_id, status="completed").first()
            if run:
                story_graph_id = run.id
                log(f"[{datetime.now().time()}] Story graph completed! Run ID: {story_graph_id}")

    log(f"[{datetime.now().time()}] Dispatching M9 (Edit Plan) with Antigravity...")
    from stream_editor.api.models.project import EditPlanRun, EditPlan
    
    with Session(engine) as db:
        run = EditPlanRun(
            project_id=project_id,
            source_asset_id=asset_id,
            story_graph_run_id=story_graph_id,
            planning_profile="default",
            provider="antigravity",
            status="pending",
            target_duration_seconds=300.0,
            derivation_signature=f"antigravity-default-{story_graph_id}"
        )
        db.add(run)
        db.commit()
        plan_run_id = run.id

    res = generate_edit_plan_task.delay(project_id, plan_run_id, {"provider": "antigravity", "flash_model": "gemini-1.5-flash", "pro_model": "gemini-1.5-pro", "target_duration_seconds": 300.0})
    
    plan_id = None
    while not plan_id:
        time.sleep(5)
        with Session(engine) as db:
            plan = db.query(EditPlan).filter_by(run_id=plan_run_id, status="proposed").first()
            if plan:
                plan_id = plan.id
                log(f"[{datetime.now().time()}] Edit plan completed! Plan ID: {plan_id}")

    log(f"[{datetime.now().time()}] ALL REAL SEMANTIC STAGES COMPLETED FOR 5H SOURCE!")
