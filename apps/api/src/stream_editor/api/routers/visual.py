from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any
from stream_editor.api.database import get_db, SessionLocal
from stream_editor.api.models.project import (
    Project,
    MediaAsset,
    VisualAnalysisRun,
    StreamLayout,
    VisualRegion,
    VisualEvent,
    FocusTarget
)
from stream_editor.analysis.providers.visual import MockVisualProvider
import uuid

router = APIRouter(prefix="/projects/{project_id}/visual-analysis", tags=["Visual Analysis"])

# Dependency to check project
async def get_project_or_404(project_id: str, db: AsyncSession = Depends(get_db)):
    proj = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

async def run_visual_analysis_task(run_id: str, project_id: str):
    async with SessionLocal() as db:
        run = (await db.execute(select(VisualAnalysisRun).where(VisualAnalysisRun.id == run_id))).scalar_one_or_none()
        if not run:
            return

        try:
            # Get duration for analysis
            asset = (await db.execute(select(MediaAsset).where(MediaAsset.id == run.source_asset_id))).scalar_one_or_none()
            duration = asset.media_info.get("duration", 60.0) if asset and asset.media_info else 60.0

            # Execute provider
            provider = MockVisualProvider(scenario="C")
            results = await provider.analyze_window(
                project_id=project_id,
                asset_id=run.source_asset_id,
                start_time=0.0,
                end_time=duration,
                context={"run_id": run_id}
            )

            # Insert results
            # Layouts
            for layout in results["layouts"]:
                db.add(StreamLayout(
                    id=layout.id,
                    visual_analysis_run_id=run_id,
                    project_id=project_id,
                    start_time=layout.start_time,
                    end_time=layout.end_time,
                    layout_name=layout.layout_name,
                    description=layout.description
                ))
            
            # Regions
            for region in results["regions"]:
                db.add(VisualRegion(
                    id=region.id,
                    visual_analysis_run_id=run_id,
                    project_id=project_id,
                    region_type=region.region_type,
                    start_time=region.start_time,
                    end_time=region.end_time,
                    x=region.box.x if region.box else 0,
                    y=region.box.y if region.box else 0,
                    width=region.box.width if region.box else 0,
                    height=region.box.height if region.box else 0,
                    confidence=region.confidence,
                    detector=region.detector,
                    track_id=region.track_id
                ))
            
            # Events
            for ev in results["events"]:
                db.add(VisualEvent(
                    id=ev.id,
                    visual_analysis_run_id=run_id,
                    project_id=project_id,
                    event_type=ev.event_type,
                    start_time=ev.start_time,
                    end_time=ev.end_time,
                    confidence=ev.confidence,
                    description=ev.description
                ))

            # Focus Targets
            for ft in results["focus_targets"]:
                db.add(FocusTarget(
                    id=ft.id,
                    visual_analysis_run_id=run_id,
                    project_id=project_id,
                    start_time=ft.start_time,
                    end_time=ft.end_time,
                    target_type=ft.target_type,
                    x=ft.box.x if ft.box else None,
                    y=ft.box.y if ft.box else None,
                    width=ft.box.width if ft.box else None,
                    height=ft.box.height if ft.box else None,
                    priority=ft.priority,
                    confidence=ft.confidence,
                    evidence_summary=ft.evidence_summary,
                    provenance=ft.provenance,
                    sequence_id=ft.sequence_id,
                    sequence_order=ft.sequence_order
                ))

            run.status = "completed"
            await db.commit()

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            await db.commit()

@router.post("")
async def start_visual_analysis(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    proj: Project = Depends(get_project_or_404)
):
    asset = (await db.execute(
        select(MediaAsset)
        .where(MediaAsset.project_id == project_id)
        .where(MediaAsset.media_type == "source")
    )).scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=400, detail="Project has no source asset")

    derivation = f"visual_{uuid.uuid4()}"

    run = VisualAnalysisRun(
        project_id=project_id,
        source_asset_id=asset.id,
        provider="mock",
        configuration={"sampler": "event"},
        derivation_signature=derivation,
        status="running"
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    background_tasks.add_task(run_visual_analysis_task, run.id, project_id)

    return {"status": "started", "run_id": run.id}

@router.get("")
async def list_visual_runs(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    proj: Project = Depends(get_project_or_404)
):
    result = await db.execute(
        select(VisualAnalysisRun).where(VisualAnalysisRun.project_id == project_id)
    )
    runs = result.scalars().all()
    return {"runs": runs}

run_router = APIRouter(prefix="/visual-analysis/{run_id}", tags=["Visual Analysis Data"])

@run_router.get("/layouts")
async def get_layouts(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StreamLayout).where(StreamLayout.visual_analysis_run_id == run_id))
    return result.scalars().all()

@run_router.get("/regions")
async def get_regions(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VisualRegion).where(VisualRegion.visual_analysis_run_id == run_id))
    return result.scalars().all()

@run_router.get("/events")
async def get_events(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VisualEvent).where(VisualEvent.visual_analysis_run_id == run_id))
    return result.scalars().all()

@run_router.get("/focus-targets")
async def get_focus_targets(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FocusTarget)
        .where(FocusTarget.visual_analysis_run_id == run_id)
        .order_by(FocusTarget.start_time)
    )
    return result.scalars().all()
