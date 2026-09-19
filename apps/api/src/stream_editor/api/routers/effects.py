from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
from stream_editor.api.database import get_db, SessionLocal
from stream_editor.api.models.project import (
    Project,
    EffectPlanRun,
    EffectInstruction,
    VisualAnalysisRun,
    FocusTarget
)
from stream_editor.contracts.effect_planning import EffectOpportunity, EffectTargetType, NormalizedBoundingBox, EffectType
from stream_editor.analysis.providers.effect.mock import MockEffectPlanner, MockEffectCritic
import uuid

router = APIRouter(prefix="/projects/{project_id}/edit-plans/{edit_plan_id}/effects", tags=["Effect Planning"])

async def get_project_or_404(project_id: str, db: AsyncSession = Depends(get_db)):  # type: ignore[no-untyped-def]
    proj = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

async def run_effect_planning_task(run_id: str, project_id: str, edit_plan_id: str):  # type: ignore[no-untyped-def]
    async with SessionLocal() as db:
        run = (await db.execute(select(EffectPlanRun).where(EffectPlanRun.id == run_id))).scalar_one_or_none()
        if not run:
            return

        try:
            # Gather visual analysis evidence
            # In a real scenario we would fetch EditClips from the EditPlan, and correlate with FocusTargets
            # Here we just fetch FocusTargets from the VisualAnalysisRun linked, or latest.
            
            visual_run_id = run.visual_analysis_run_id
            opportunities = []
            
            if visual_run_id:
                fts_res = await db.execute(select(FocusTarget).where(FocusTarget.visual_analysis_run_id == visual_run_id))
                fts = fts_res.scalars().all()
                
                # Convert FocusTargets to EffectOpportunities
                for ft in fts:
                    target_type = EffectTargetType.UNKNOWN
                    if ft.target_type == "facecam":
                        target_type = EffectTargetType.FACECAM
                    elif ft.target_type == "chat":
                        target_type = EffectTargetType.CHAT
                    elif ft.target_type == "screen_region" or ft.target_type == "game_region":
                        target_type = EffectTargetType.SCREEN_REGION
                        
                    box = None
                    if ft.x is not None and ft.y is not None and ft.width is not None and ft.height is not None:
                        box = NormalizedBoundingBox(x=ft.x, y=ft.y, width=ft.width, height=ft.height)
                        
                    opp = EffectOpportunity(
                        id=str(uuid.uuid4()),
                        source_start=ft.start_time,
                        source_end=ft.end_time,
                        candidate_effect_types=[EffectType.ZOOM_FACE, EffectType.ZOOM_REGION, EffectType.ZOOM_CHAT],
                        target_type=target_type,
                        target_box=box,
                        confidence=ft.confidence,
                        source_event_id=ft.id,
                        reason=ft.evidence_summary or "Focus target identified"
                    )
                    opportunities.append(opp)
            
            # Execute provider
            scenario = run.configuration.get("scenario", "screen_to_face") if run.configuration else "screen_to_face"
            provider = MockEffectPlanner(scenario=scenario)
            
            instructions = await provider.plan_effects(
                project_id=project_id,
                edit_plan_id=edit_plan_id,
                visual_analysis_run_id=visual_run_id,  # type: ignore[arg-type,arg-type]
                opportunities=opportunities,
                context={"run_id": run_id}
            )

            # Insert instructions
            for inst in instructions:
                db.add(EffectInstruction(
                    id=inst.id,
                    effect_plan_run_id=run_id,
                    edit_clip_id=inst.edit_clip_id,
                    source_start=inst.source_start,
                    source_end=inst.source_end,
                    output_start=inst.output_start,
                    output_end=inst.output_end,
                    effect_type=inst.effect_type.value,
                    target_type=inst.target_type.value,
                    x=inst.target_box.x if inst.target_box else None,
                    y=inst.target_box.y if inst.target_box else None,
                    width=inst.target_box.width if inst.target_box else None,
                    height=inst.target_box.height if inst.target_box else None,
                    parameters=inst.parameters,
                    confidence=inst.confidence,
                    priority=inst.priority.value,
                    reason=inst.reason,
                    evidence_references=inst.evidence_references,
                    provider=inst.provider,
                    review_state=inst.review_state.value
                ))

            run.status = "completed"  # type: ignore[assignment]
            await db.commit()

        except Exception as e:
            run.status = "failed"  # type: ignore[assignment]
            run.error_message = str(e)  # type: ignore[assignment]
            await db.commit()

@router.post("/generate")
async def generate_effects(  # type: ignore[no-untyped-def]
    project_id: str,
    edit_plan_id: str,
    background_tasks: BackgroundTasks,
    config: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    proj: Project = Depends(get_project_or_404)
):
    # Find latest visual analysis run
    res = await db.execute(
        select(VisualAnalysisRun)
        .where(VisualAnalysisRun.project_id == project_id)
        .where(VisualAnalysisRun.status == "completed")
        .order_by(VisualAnalysisRun.created_at.desc())
    )
    visual_run = res.scalars().first()
    
    derivation = f"effect_{uuid.uuid4()}"

    run = EffectPlanRun(
        project_id=project_id,
        edit_plan_id=edit_plan_id,
        visual_analysis_run_id=visual_run.id if visual_run else None,
        provider="mock",
        configuration=config or {},
        derivation_signature=derivation,
        status="running"
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    background_tasks.add_task(run_effect_planning_task, run.id, project_id, edit_plan_id)  # type: ignore[arg-type,arg-type]

    return {"status": "started", "run_id": run.id}

@router.get("/runs")
async def list_effect_runs(  # type: ignore[no-untyped-def]
    project_id: str,
    edit_plan_id: str,
    db: AsyncSession = Depends(get_db),
    proj: Project = Depends(get_project_or_404)
):
    result = await db.execute(
        select(EffectPlanRun)
        .where(EffectPlanRun.project_id == project_id)
        .where(EffectPlanRun.edit_plan_id == edit_plan_id)
        .order_by(EffectPlanRun.created_at.desc())
    )
    return {"runs": result.scalars().all()}


run_router = APIRouter(prefix="/effect-plans/{effect_plan_id}", tags=["Effect Plans"])

@run_router.get("")
async def get_effect_plan(effect_plan_id: str, db: AsyncSession = Depends(get_db)):  # type: ignore[no-untyped-def]
    run = (await db.execute(select(EffectPlanRun).where(EffectPlanRun.id == effect_plan_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Effect plan not found")
    return run

@run_router.get("/effects")
async def get_effect_instructions(effect_plan_id: str, db: AsyncSession = Depends(get_db)):  # type: ignore[no-untyped-def]
    result = await db.execute(
        select(EffectInstruction)
        .where(EffectInstruction.effect_plan_run_id == effect_plan_id)
        .order_by(EffectInstruction.source_start)
    )
    return result.scalars().all()

@run_router.post("/critique")
async def critique_effects(effect_plan_id: str, db: AsyncSession = Depends(get_db)):  # type: ignore[no-untyped-def]
    # Fetch instructions
    res = await db.execute(select(EffectInstruction).where(EffectInstruction.effect_plan_run_id == effect_plan_id))
    instructions = res.scalars().all()
    
    # We would convert back to schema here, doing quickly for mock
    from stream_editor.contracts.effect_planning import EffectInstructionSchema, EffectType, EffectTargetType, EffectPriority, EffectReviewState
    
    schemas = []
    for inst in instructions:
        schemas.append(EffectInstructionSchema(
            id=inst.id,
            effect_plan_run_id=inst.effect_plan_run_id,
            source_start=inst.source_start,
            source_end=inst.source_end,
            effect_type=EffectType(inst.effect_type),
            target_type=EffectTargetType(inst.target_type),
            confidence=inst.confidence,
            priority=EffectPriority(inst.priority),
            provider=inst.provider
        ))
        
    critic = MockEffectCritic()
    issues = await critic.critique(
        project_id="mock",
        instructions=schemas,
        context={}
    )
    
    return {"issues": issues}
