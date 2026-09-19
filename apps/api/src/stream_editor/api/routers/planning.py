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


async def _repack_plan_clips(db: AsyncSession, plan_id: str):  # type: ignore[no-untyped-def]
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
        
    # Sort clips chronologically by original source start, ignoring rejected clips for output timeline
    clips = sorted(plan.clips, key=lambda c: c.source_start)
    current_time = 0.0
    
    active_clips = 0
    for clip in clips:
        if getattr(clip, 'review_state', 'proposed') == 'rejected':
            continue
            
        dur = clip.source_end - clip.source_start
        clip.output_start = current_time
        clip.output_end = current_time + dur
        current_time += dur
        active_clips += 1
        
    plan.selected_duration = current_time  # type: ignore[assignment]
    plan.clip_count = active_clips  # type: ignore[assignment]
    if plan.original_duration and plan.original_duration > 0:
        plan.compression_ratio = plan.selected_duration / plan.original_duration  # type: ignore[assignment]
    
    await db.commit()

class PlanRevisionRequest(BaseModel):
    revision_reason: str | None = None

@router.post("/plans/{plan_id}/revisions")
async def create_plan_revision(  # type: ignore[no-untyped-def]
    project_id: str,
    plan_id: str,
    request: PlanRevisionRequest,
    db: AsyncSession = Depends(get_db),
):
    from stream_editor.api.models.project import EditPlan, EditClip
    from sqlalchemy.orm import selectinload
    
    res = await db.execute(
        select(EditPlan)
        .options(selectinload(EditPlan.clips))
        .where(EditPlan.id == str(plan_id), EditPlan.project_id == str(project_id))
    )
    parent_plan = res.scalars().first()
    if not parent_plan:
        raise HTTPException(status_code=404, detail="Parent plan not found")
        
    new_plan_id = str(uuid.uuid4())
    new_plan = EditPlan(
        id=new_plan_id,
        project_id=parent_plan.project_id,
        run_id=parent_plan.run_id,
        status=parent_plan.status,
        original_duration=parent_plan.original_duration,
        selected_duration=parent_plan.selected_duration,
        compression_ratio=parent_plan.compression_ratio,
        clip_count=parent_plan.clip_count,
        locked=parent_plan.locked,
        parent_plan_id=parent_plan.id,
        revision_number=getattr(parent_plan, 'revision_number', 1) + 1,
        origin="human",
        revision_reason=request.revision_reason
    )
    db.add(new_plan)
    
    for clip in parent_plan.clips:
        new_clip = EditClip(
            id=str(uuid.uuid4()),
            plan_id=new_plan_id,
            source_start=clip.source_start,
            source_end=clip.source_end,
            core_start=clip.core_start,
            core_end=clip.core_end,
            output_start=clip.output_start,
            output_end=clip.output_end,
            candidate_id=clip.candidate_id,
            selection_reason=clip.selection_reason,
            priority=clip.priority,
            confidence=clip.confidence,
            locked=clip.locked,
            review_state=getattr(clip, 'review_state', 'proposed')
        )
        db.add(new_clip)
        
    await db.commit()
    return {"status": "ok", "plan_id": new_plan_id}

class ClipFeedbackRequest(BaseModel):
    action: str # reject | accept | modify_boundaries | lock | unlock
    source_start: float | None = None
    source_end: float | None = None
    reason_category: str | None = None
    reason_text: str | None = None

@router.post("/plans/{plan_id}/clips/{clip_id}/feedback")
async def give_clip_feedback(  # type: ignore[no-untyped-def]
    project_id: str,
    plan_id: str,
    clip_id: str,
    request: ClipFeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    from stream_editor.api.models.project import EditPlan, EditClip, FeedbackEvent
    
    # Check plan immutability
    plan = await db.get(EditPlan, plan_id)
    if not plan or getattr(plan, 'origin', 'ai') == 'ai':
        raise HTTPException(status_code=400, detail="Cannot modify AI generated plans directly. Create a revision first.")
        
    clip = await db.get(EditClip, clip_id)
    if not clip or clip.plan_id != plan_id:
        raise HTTPException(status_code=404, detail="Clip not found")
        
    feedback_type = request.action
    previous_value = {}
    new_value = {}
    
    if request.action == "reject":
        feedback_type = "reject_clip"
        previous_value = {"review_state": clip.review_state}
        new_value = {"review_state": "rejected"}
        clip.review_state = "rejected"  # type: ignore[assignment]
    elif request.action == "accept":
        feedback_type = "accept_clip"
        previous_value = {"review_state": clip.review_state}
        new_value = {"review_state": "accepted"}
        clip.review_state = "accepted"  # type: ignore[assignment]
    elif request.action == "modify_boundaries":
        if request.source_start is not None:
            feedback_type = "modify_start"
            previous_value["source_start"] = clip.source_start
            new_value["source_start"] = request.source_start  # type: ignore[assignment]
            clip.source_start = request.source_start  # type: ignore[assignment]
        if request.source_end is not None:
            feedback_type = "modify_end" if "modify_start" not in feedback_type else "modify_boundaries"
            previous_value["source_end"] = clip.source_end
            new_value["source_end"] = request.source_end  # type: ignore[assignment]
            clip.source_end = request.source_end  # type: ignore[assignment]
            
        if clip.source_start > clip.source_end:
            raise HTTPException(status_code=400, detail="source_start must be <= source_end")
        clip.review_state = "modified"  # type: ignore[assignment]
    elif request.action == "lock":
        feedback_type = "lock_clip"
        previous_value = {"locked": clip.locked}  # type: ignore[dict-item]
        new_value = {"locked": True}  # type: ignore[dict-item]
        clip.locked = True  # type: ignore[assignment]
    elif request.action == "unlock":
        feedback_type = "unlock_clip"
        previous_value = {"locked": clip.locked}  # type: ignore[dict-item]
        new_value = {"locked": False}  # type: ignore[dict-item]
        clip.locked = False  # type: ignore[assignment]
    
    feedback = FeedbackEvent(
        project_id=project_id,
        source_asset_id=plan.run_id, # Simplified for MVP (real asset is fetched via run)
        edit_plan_id=plan_id,
        edit_clip_id=clip_id,
        feedback_type=feedback_type,
        previous_value=previous_value,
        new_value=new_value,
        reason_category=request.reason_category,
        reason_text=request.reason_text,
        candidate_id=clip.candidate_id
    )
    db.add(feedback)
    await db.commit()
    
    # Recalculate output times
    await _repack_plan_clips(db, plan_id)
    return {"status": "ok"}
