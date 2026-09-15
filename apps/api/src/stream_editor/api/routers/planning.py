import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stream_editor.api.database import get_db
from stream_editor.api.models.project import EditPlan, EditPlanRun, Project
from stream_editor.contracts.edit_plan import PlanningProfile
from stream_editor.worker.tasks.pipeline import generate_edit_plan_task

router = APIRouter(prefix="/projects/{project_id}/edit-plan", tags=["edit-plan"])


class EditPlanRequest(BaseModel):
    target_duration_seconds: float = 9000.0
    tolerance_seconds: float = 900.0
    profile: PlanningProfile = PlanningProfile.balanced
    provider: str = "mock"


class EditPlanRunResponse(BaseModel):
    message: str
    run_id: str


@router.post("", response_model=EditPlanRunResponse)
async def start_edit_plan_generation(
    project_id: str,
    request: EditPlanRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> EditPlanRunResponse:
    # Verify project exists
    proj_res = await db.execute(select(Project).where(Project.id == str(project_id)))
    project = proj_res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not project.source_video_path:
        raise HTTPException(status_code=400, detail="Project has no source video")

    # Create run record
    run_id = str(uuid.uuid4())
    run = EditPlanRun(
        id=run_id,
        project_id=str(project_id),
        # In a full impl we might link candidate_run_id and story_graph_run_id from request
        target_duration_seconds=request.target_duration_seconds,
        tolerance_seconds=request.tolerance_seconds,
        planning_profile=request.profile.value,
        provider=request.provider,
        model="gemini-2.5-pro" if request.provider == "gemini" else "mock",
        prompt_version="1.0",
        planner_version="1.0",
        derivation_signature=str(uuid.uuid4()), # simplified for MVP
        status="pending"
    )
    db.add(run)
    await db.commit()

    # Enqueue task
    background_tasks.add_task(
        generate_edit_plan_task.delay,
        str(project_id),
        run_id,
        request.model_dump(),
    )

    return EditPlanRunResponse(
        message="Edit Plan generation task queued.",
        run_id=run_id,
    )


@router.get("/runs")
async def list_edit_plan_runs(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    res = await db.execute(
        select(EditPlanRun).where(EditPlanRun.project_id == str(project_id)).order_by(EditPlanRun.created_at.desc())
    )
    runs = res.scalars().all()
    
    return [
        {
            "id": r.id,
            "status": r.status,
            "target_duration_seconds": r.target_duration_seconds,
            "profile": r.planning_profile,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]


@router.get("/plans")
async def list_edit_plans(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    res = await db.execute(
        select(EditPlan).where(EditPlan.project_id == str(project_id)).order_by(EditPlan.created_at.desc())
    )
    plans = res.scalars().all()
    
    return [
        {
            "id": p.id,
            "run_id": p.run_id,
            "status": p.status,
            "original_duration": p.original_duration,
            "selected_duration": p.selected_duration,
            "clip_count": p.clip_count,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in plans
    ]

@router.get("/plans/{plan_id}")
async def get_edit_plan(
    project_id: str,
    plan_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    from stream_editor.api.models.project import EditClip
    from sqlalchemy.orm import selectinload
    
    res = await db.execute(
        select(EditPlan)
        .options(selectinload(EditPlan.clips))
        .where(EditPlan.id == str(plan_id), EditPlan.project_id == str(project_id))
    )
    plan = res.scalars().first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Edit plan not found")
        
    # Sort clips chronologically
    clips = sorted(plan.clips, key=lambda c: c.output_start)
        
    return {
        "id": plan.id,
        "run_id": plan.run_id,
        "status": plan.status,
        "original_duration": plan.original_duration,
        "selected_duration": plan.selected_duration,
        "compression_ratio": plan.compression_ratio,
        "clip_count": plan.clip_count,
        "locked": plan.locked,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "clips": [
            {
                "id": c.id,
                "candidate_id": c.candidate_id,
                "source_start": c.source_start,
                "source_end": c.source_end,
                "output_start": c.output_start,
                "output_end": c.output_end,
                "selection_reason": c.selection_reason,
                "priority": c.priority,
                "confidence": c.confidence,
                "locked": c.locked
            }
            for c in clips
        ]
    }

class ClipPatchRequest(BaseModel):
    source_start: float | None = None
    source_end: float | None = None

async def _repack_plan_clips(db: AsyncSession, plan_id: str):
    from stream_editor.api.models.project import EditPlan, EditClip
    from sqlalchemy.orm import selectinload
    
    res = await db.execute(
        select(EditPlan)
        .options(selectinload(EditPlan.clips))
        .where(EditPlan.id == str(plan_id))
    )
    plan = res.scalars().first()
    if not plan:
        return
        
    clips = sorted(plan.clips, key=lambda c: c.output_start)
    current_time = 0.0
    
    for clip in clips:
        # source_duration
        dur = clip.source_end - clip.source_start
        clip.output_start = current_time
        clip.output_end = current_time + dur
        current_time += dur
        
    plan.selected_duration = current_time
    plan.clip_count = len(clips)
    if plan.original_duration and plan.original_duration > 0:
        plan.compression_ratio = plan.selected_duration / plan.original_duration
    
    await db.commit()

@router.delete("/plans/{plan_id}/clips/{clip_id}")
async def delete_clip(
    project_id: str,
    plan_id: str,
    clip_id: str,
    db: AsyncSession = Depends(get_db),
):
    from stream_editor.api.models.project import EditClip
    clip = await db.get(EditClip, clip_id)
    if not clip or clip.plan_id != plan_id:
        raise HTTPException(status_code=404, detail="Clip not found")
        
    await db.delete(clip)
    await db.commit()
    
    # Recalculate output times and plan stats
    await _repack_plan_clips(db, plan_id)
    return {"status": "ok"}

@router.patch("/plans/{plan_id}/clips/{clip_id}")
async def update_clip(
    project_id: str,
    plan_id: str,
    clip_id: str,
    request: ClipPatchRequest,
    db: AsyncSession = Depends(get_db),
):
    from stream_editor.api.models.project import EditClip
    clip = await db.get(EditClip, clip_id)
    if not clip or clip.plan_id != plan_id:
        raise HTTPException(status_code=404, detail="Clip not found")
        
    if request.source_start is not None:
        clip.source_start = request.source_start
    if request.source_end is not None:
        clip.source_end = request.source_end
        
    if clip.source_start > clip.source_end:
        raise HTTPException(status_code=400, detail="source_start must be <= source_end")
        
    await db.commit()
    
    # Recalculate output times and plan stats
    await _repack_plan_clips(db, plan_id)
    return {"status": "ok"}
