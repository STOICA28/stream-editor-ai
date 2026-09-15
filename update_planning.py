import re

with open('apps/api/src/stream_editor/api/routers/planning.py', 'r') as f:
    content = f.read()

# First, find the _repack_plan_clips function and replace it and everything after it.
repack_idx = content.find('async def _repack_plan_clips')
if repack_idx != -1:
    content = content[:repack_idx]

new_code = """
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
        
    plan.selected_duration = current_time
    plan.clip_count = active_clips
    if plan.original_duration and plan.original_duration > 0:
        plan.compression_ratio = plan.selected_duration / plan.original_duration
    
    await db.commit()

class PlanRevisionRequest(BaseModel):
    revision_reason: str | None = None

@router.post("/plans/{plan_id}/revisions")
async def create_plan_revision(
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
async def give_clip_feedback(
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
        clip.review_state = "rejected"
    elif request.action == "accept":
        feedback_type = "accept_clip"
        previous_value = {"review_state": clip.review_state}
        new_value = {"review_state": "accepted"}
        clip.review_state = "accepted"
    elif request.action == "modify_boundaries":
        if request.source_start is not None:
            feedback_type = "modify_start"
            previous_value["source_start"] = clip.source_start
            new_value["source_start"] = request.source_start
            clip.source_start = request.source_start
        if request.source_end is not None:
            feedback_type = "modify_end" if "modify_start" not in feedback_type else "modify_boundaries"
            previous_value["source_end"] = clip.source_end
            new_value["source_end"] = request.source_end
            clip.source_end = request.source_end
            
        if clip.source_start > clip.source_end:
            raise HTTPException(status_code=400, detail="source_start must be <= source_end")
        clip.review_state = "modified"
    elif request.action == "lock":
        feedback_type = "lock_clip"
        previous_value = {"locked": clip.locked}
        new_value = {"locked": True}
        clip.locked = True
    elif request.action == "unlock":
        feedback_type = "unlock_clip"
        previous_value = {"locked": clip.locked}
        new_value = {"locked": False}
        clip.locked = False
    
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
"""

content += new_code
with open('apps/api/src/stream_editor/api/routers/planning.py', 'w') as f:
    f.write(content)
print("Updated planning.py successfully")
