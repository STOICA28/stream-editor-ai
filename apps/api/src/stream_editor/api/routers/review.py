import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from stream_editor.api.database import get_db
from stream_editor.api.models.project import EditPlan, EditClip, FeedbackEvent

router = APIRouter(prefix="/projects/{project_id}/edit-plan", tags=["edit-plan-review"])

@router.get("/plans/{plan_id}/diff")
async def get_plan_diff(
    project_id: str,
    plan_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    res = await db.execute(
        select(EditPlan).options(selectinload(EditPlan.clips)).where(EditPlan.id == str(plan_id))
    )
    plan = res.scalars().first()
    if not plan or not plan.parent_plan_id:
        return {"error": "Plan has no parent to diff against."}
        
    res_parent = await db.execute(
        select(EditPlan).options(selectinload(EditPlan.clips)).where(EditPlan.id == str(plan.parent_plan_id))
    )
    parent = res_parent.scalars().first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent plan missing")
        
    # Maps candidate_id to clip (simplified mapping assuming 1-1 for MVP)
    parent_clips = {c.candidate_id: c for c in parent.clips if c.candidate_id}
    current_clips = {c.candidate_id: c for c in plan.clips if c.candidate_id}
    
    added = []
    removed = []
    modified = []
    locked = []
    
    for cid, clip in current_clips.items():
        if cid not in parent_clips:
            added.append(clip.id)
            continue
            
        p_clip = parent_clips[cid]
        
        # Check removed (rejected)
        if getattr(clip, 'review_state', 'proposed') == 'rejected' and getattr(p_clip, 'review_state', 'proposed') != 'rejected':
            removed.append(clip.id)
            
        # Check modified boundaries
        if clip.source_start != p_clip.source_start or clip.source_end != p_clip.source_end:
            modified.append(clip.id)
            
        # Check lock
        if clip.locked and not p_clip.locked:
            locked.append(clip.id)
            
    return {
        "summary": f"AI Plan {parent.id[:8]} -> Human Revision {plan.id[:8]}",
        "added": len(added),
        "rejected": len(removed),
        "modified": len(modified),
        "locked": len(locked),
        "duration_before": parent.selected_duration,
        "duration_after": plan.selected_duration
    }

@router.get("/feedback")
async def query_feedback(
    project_id: str,
    plan_id: str | None = None,
    feedback_type: str | None = None,
    reason_category: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[Dict[str, Any]]:
    query = select(FeedbackEvent).where(FeedbackEvent.project_id == str(project_id))
    if plan_id:
        query = query.where(FeedbackEvent.edit_plan_id == str(plan_id))
    if feedback_type:
        query = query.where(FeedbackEvent.feedback_type == str(feedback_type))
    if reason_category:
        query = query.where(FeedbackEvent.reason_category == str(reason_category))
        
    query = query.order_by(FeedbackEvent.created_at.desc()).limit(100)
    res = await db.execute(query)
    events = res.scalars().all()
    
    return [
        {
            "id": e.id,
            "feedback_type": e.feedback_type,
            "previous_value": e.previous_value,
            "new_value": e.new_value,
            "reason_category": e.reason_category,
            "created_at": e.created_at.isoformat() if e.created_at else None
        }
        for e in events
    ]

@router.get("/feedback/stats")
async def get_feedback_stats(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    res = await db.execute(select(FeedbackEvent).where(FeedbackEvent.project_id == str(project_id)))
    events = res.scalars().all()
    
    stats = {
        "reviewed_clips": len(set(e.edit_clip_id for e in events if e.edit_clip_id)),
        "accepted": len([e for e in events if e.feedback_type == "accept_clip"]),
        "rejected": len([e for e in events if e.feedback_type == "reject_clip"]),
        "modified": len([e for e in events if "modify_" in e.feedback_type]),
        "reasons": {},
        "boundary_changes": []
    }
    
    for e in events:
        if e.reason_category:
            stats["reasons"][e.reason_category] = stats["reasons"].get(e.reason_category, 0) + 1  # type: ignore[attr-defined, index]
            
        if e.feedback_type == "modify_start" and e.previous_value and e.new_value:
            try:
                diff = e.previous_value.get("source_start", 0) - e.new_value.get("source_start", 0)
                stats["boundary_changes"].append(diff)  # type: ignore[attr-defined]
            except:
                pass
                
    if stats["boundary_changes"]:
        stats["average_start_extension"] = sum(stats["boundary_changes"]) / len(stats["boundary_changes"])  # type: ignore[arg-type, call-overload]
    else:
        stats["average_start_extension"] = 0.0
        
    return stats
