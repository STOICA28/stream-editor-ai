
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
    ingest_media_task,
    generate_candidates_task,
    generate_story_graph_task,
    generate_edit_plan_task
)

def log(msg):
    print(msg)
    sys.stdout.flush()

if __name__ == "__main__":
    project_id = "real-5h-" + str(uuid.uuid4())[:8]
    source_path = "data/source_5hr.mp4"
    
    engine = create_engine("sqlite:///test.db")
    with Session(engine) as db:
        proj = Project(id=project_id, name="5H Production Proof")
        db.add(proj)
        db.commit()
    
    log(f"[{datetime.now().time()}] Dispatching INGEST -> PROBE -> PROXY -> AUDIO...")
    res = ingest_media_task.delay(project_id, source_path)
    
    # Get the generated asset and job
    job_id = None
    asset_id = None
    log("Waiting for ingest to create asset and job...")
    while not job_id or not asset_id:
        time.sleep(2)
        with Session(engine) as db:
            job = db.query(ProcessingJob).filter_by(project_id=project_id).first()
            asset = db.query(MediaAsset).filter_by(project_id=project_id, media_type="source").first()
            if job and asset:
                job_id = job.id
                asset_id = asset.id
                log(f"Found Job ID: {job_id}, Asset ID: {asset_id}")
    
    # Wait for audio extraction to complete
    audio_done = False
    log("Waiting for audio extraction to complete...")
    while not audio_done:
        time.sleep(10)
        with Session(engine) as db:
            step = db.query(JobStep).filter_by(job_id=job_id, stage="extract_audio", status="completed").first()
            if step:
                audio_done = True
                log(f"[{datetime.now().time()}] Audio extraction completed!")
            else:
                job = db.query(ProcessingJob).filter_by(id=job_id).first()
                if job and job.status == "failed":
                    log(f"Job failed at stage {job.current_stage}!")
                    exit(1)

    log(f"[{datetime.now().time()}] Waiting for M2/M3/M4 (transcribe, scene, audio)...")
    time.sleep(30)
    
    log(f"[{datetime.now().time()}] Dispatching M5 (Candidates) with Antigravity...")
    res = generate_candidates_task.delay(project_id, asset_id, provider_name="antigravity")
    
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
    generate_edit_plan_task.delay(project_id, asset_id, story_graph_id, provider_name="antigravity", profile_name="default")
    
    from stream_editor.api.models.project import EditPlanRun
    edit_plan_id = None
    while not edit_plan_id:
        time.sleep(10)
        with Session(engine) as db:
            run = db.query(EditPlanRun).filter_by(source_asset_id=asset_id, status="completed").first()
            if run:
                edit_plan_id = run.id
                log(f"[{datetime.now().time()}] Edit plan completed! Run ID: {edit_plan_id}")

    log(f"[{datetime.now().time()}] ALL REAL SEMANTIC STAGES COMPLETED FOR 5H SOURCE!")

