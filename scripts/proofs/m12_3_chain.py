import uuid
import time
import os
import structlog
import sys
from datetime import datetime, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from stream_editor.api.models.project import Project, EditPlan, EditClip, RenderJob

from stream_editor.worker.tasks.pipeline import (
    generate_visual_analysis_task,
    generate_effect_plan_task,
    render_job_task
)

def log(msg):
    print(msg)
    sys.stdout.flush()

if __name__ == "__main__":
    engine = create_engine("sqlite:///test.db")
    project_id = None
    
    with Session(engine) as db:
        proj = db.query(Project).filter(Project.id == "real-5h-65655576").first()
        if not proj:
            log("No real-5h project found!")
            exit(1)
        project_id = proj.id
        
        # M6: Simulated Human Review Revision
        log(f"[{datetime.now().time()}] Executing M6 (Review Revision)...")
        old_plan = db.query(EditPlan).filter_by(project_id=project_id, status="proposed").first()
        
        plan_id = str(uuid.uuid4())
        new_plan = EditPlan(
            id=plan_id,
            project_id=project_id,
            run_id=old_plan.run_id,
            version=2,
            status="approved",
            original_duration=old_plan.original_duration,
            selected_duration=20.0,
            compression_ratio=20.0/old_plan.original_duration,
            clip_count=2
        )
        db.add(new_plan)
        
        # Add 2 clips
        c1 = EditClip(id=str(uuid.uuid4()), plan_id=plan_id, source_start=0.0, source_end=10.0, core_start=0.0, core_end=10.0, output_start=0.0, output_end=10.0, candidate_id="mock", priority="high", confidence=1.0, selection_reason="First good moment")
        c2 = EditClip(id=str(uuid.uuid4()), plan_id=plan_id, source_start=3600.0, source_end=3610.0, core_start=3600.0, core_end=3610.0, output_start=10.0, output_end=20.0, candidate_id="mock", priority="high", confidence=1.0, selection_reason="Second good moment")
        db.add(c1)
        db.add(c2)
        db.commit()
        log(f"[{datetime.now().time()}] M6 Revision approved. Plan ID: {plan_id}")

        from stream_editor.api.models.project import MediaAsset
        asset = db.query(MediaAsset).filter_by(project_id=project_id, media_type="source").first()
        asset_id = asset.id
        
    log(f"[{datetime.now().time()}] Dispatching M7 (Visual Analysis)...")
    res = generate_visual_analysis_task.delay(project_id, str(asset_id), provider_name="antigravity")
    
    result_m7 = res.get(timeout=120)
    if result_m7.get("status") != "success":
        log(f"M7 failed: {result_m7}")
        exit(1)
    visual_run_id = result_m7["run_id"]
    log(f"[{datetime.now().time()}] M7 completed! Run ID: {visual_run_id}")

    log(f"[{datetime.now().time()}] Dispatching M8 (Effect Plan)...")
    res2 = generate_effect_plan_task.delay(project_id, plan_id, visual_run_id, provider_name="antigravity")
    
    result_m8 = res2.get(timeout=120)
    if result_m8.get("status") != "success":
        log(f"M8 failed: {result_m8}")
        exit(1)
    effect_run_id = result_m8["run_id"]
    log(f"[{datetime.now().time()}] M8 completed! Run ID: {effect_run_id}")


    log(f"[{datetime.now().time()}] Dispatching M9 (Render Job)...")
    render_job_id = str(uuid.uuid4())
    with Session(engine) as db:
        job = RenderJob(
            id=render_job_id, project_id=project_id, edit_plan_id=plan_id, effect_plan_run_id=effect_run_id,
            status="pending", render_config={}
        )
        db.add(job)
        db.commit()
    
    res3 = render_job_task.delay(project_id, render_job_id)
    
    result_m9 = res3.get(timeout=120)
    if result_m9.get("status") != "success":
        log(f"M9 failed: {result_m9}")
        exit(1)
    
    log(f"[{datetime.now().time()}] M9 completed! Render output: {result_m9['output']}")
    log("ALL REAL PIPELINE STAGES COMPLETED!")
