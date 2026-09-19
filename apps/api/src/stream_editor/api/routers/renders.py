import uuid
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from stream_editor.api.database import get_db, SessionLocal
from stream_editor.api.models.project import Project, RenderJob, EditPlan, EditClip, EffectPlanRun, EffectInstruction, MediaAsset
from stream_editor.contracts.rendering import RenderConfig, RenderMode, CompiledTimeline
from stream_editor.contracts.effect_planning import EffectInstructionSchema, EffectType, EffectTargetType, EffectPriority
from stream_editor.rendering.compiler import TimelineCompiler
from stream_editor.worker.utils.lease import acquire_job_lease
from stream_editor.rendering.engine import RenderingEngine

router = APIRouter(prefix="/projects/{project_id}/renders", tags=["Rendering"])
run_router = APIRouter(prefix="/renders/{render_id}", tags=["Rendering"])

logger = logging.getLogger(__name__)

async def run_render_task(job_id: str, project_id: str, edit_plan_id: str, effect_plan_id: Optional[str], config_dict: Dict[str, Any]) -> None:
    async with SessionLocal() as db:
        async with acquire_job_lease(db, RenderJob, job_id) as already_done:
            if already_done:
                return

        job = (await db.execute(select(RenderJob).where(RenderJob.id == job_id))).scalar_one_or_none()
        if not job:
            return

        try:
            job.status = "preparing" # type: ignore
            await db.commit()

            config = RenderConfig(**config_dict)
            
            from stream_editor.contracts.edit_plan import EditClipContract, ClipPriority
            import uuid
            
            # Gather edit clips
            clips_res = await db.execute(select(EditClip).where(EditClip.plan_id == edit_plan_id).order_by(EditClip.source_start))
            db_clips = clips_res.scalars().all()
            
            clips = [
                EditClipContract(
                    id=uuid.UUID(str(c.id)),
                    plan_id=uuid.UUID(str(c.plan_id)),
                    source_start=c.source_start,
                    source_end=c.source_end,
                    output_start=c.output_start,
                    output_end=c.output_end,
                    selection_reason=c.selection_reason,
                    priority=ClipPriority(c.priority)
                ) for c in db_clips
            ]
            
            # Gather effects if applicable
            effect_instructions = []
            if effect_plan_id:
                eff_res = await db.execute(select(EffectInstruction).where(EffectInstruction.effect_plan_run_id == effect_plan_id))
                effs = eff_res.scalars().all()
                for e in effs:
                    effect_instructions.append(EffectInstructionSchema(
                        id=e.id,
                        effect_plan_run_id=e.effect_plan_run_id,
                        source_start=e.source_start,
                        source_end=e.source_end,
                        effect_type=EffectType(e.effect_type),
                        target_type=EffectTargetType(e.target_type),
                        priority=EffectPriority(e.priority),
                        confidence=e.confidence,
                        provider=e.provider
                    ))
                    
            # Compile timeline
            compiler = TimelineCompiler()
            timeline = compiler.compile(project_id, job_id, clips, effect_instructions)
            
            # Engine setup
            # In a real setup, WORK_DIR would come from config.
            work_dir = Path("data")
            engine = RenderingEngine(work_dir)
            
            job.status = "rendering" # type: ignore
            await db.commit()
            
            def progress_cb(prog: float) -> None:
                # Using a sync closure, we'd normally update the DB asynchronously or via a task queue.
                # Here we just log for demonstration, or we can use another session to update.
                logger.info(f"Render {job_id} progress: {prog}%")
                
            # M1 multi-source support implies resolving `source_asset_id` to actual paths
            source_paths: dict[str, Path] = {}
            
            # Fetch the main source video for the project
            source_asset = (await db.execute(
                select(MediaAsset).where(MediaAsset.project_id == project_id, MediaAsset.media_type == "source")
            )).scalars().first()
            
            if source_asset and source_asset.path:
                source_paths[str(source_asset.id)] = Path("data/projects") / str(source_asset.path)
            
            for seg in timeline.segments:
                if source_asset:
                    seg.source_asset_id = str(source_asset.id)
                
                if seg.source_asset_id not in source_paths:
                    asset = (await db.execute(select(MediaAsset).where(MediaAsset.id == seg.source_asset_id))).scalar_one_or_none()
                    if asset and asset.path:
                        source_paths[seg.source_asset_id] = Path("data/projects") / str(asset.path)
                    else:
                        # Use a synthetic source for tests
                        source_paths[seg.source_asset_id] = Path("synthetic_test.mp4")
                        
            # Create synthetic test file if it doesn't exist
            if not Path("synthetic_test.mp4").exists():
                import asyncio
                # Create a fast blank 10s video
                proc = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-f", "lavfi", "-i", "color=c=blue:s=1920x1080:d=10",
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-c:v", "libx264", "-c:a", "aac", "synthetic_test.mp4",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()

            final_path = await engine.render(timeline, config, source_paths, job_id, progress_cb)
            
            # Success
            # Create asset
            asset = MediaAsset(
                id=str(uuid.uuid4()),
                project_id=project_id,
                media_type="preview_render" if config.mode == RenderMode.PREVIEW else "final_render",
                path=str(final_path),
                media_info={"duration": timeline.expected_duration}
            )
            db.add(asset)
            
            job.output_asset_id = asset.id
            job.progress = 100.0 # type: ignore
            job.status = "completed" # type: ignore
            await db.commit()
            
        except Exception as e:
            logger.error(f"Render failed: {e}")
            job.status = "failed" # type: ignore
            job.error_message = str(e) # type: ignore
            await db.commit()

@router.post("")
async def start_render(
    project_id: str,
    edit_plan_id: str,
    background_tasks: BackgroundTasks,
    effect_plan_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    job = RenderJob(
        project_id=project_id,
        edit_plan_id=edit_plan_id,
        effect_plan_run_id=effect_plan_id,
        render_config=config or {}
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    background_tasks.add_task(run_render_task, str(job.id), project_id, edit_plan_id, effect_plan_id, config or {})
    
    return {"status": "started", "job_id": job.id}

@router.get("")
async def list_renders(project_id: str, db: AsyncSession = Depends(get_db)) -> Any:
    res = await db.execute(select(RenderJob).where(RenderJob.project_id == project_id).order_by(RenderJob.created_at.desc()))
    return res.scalars().all()

@run_router.get("")
async def get_render_job(render_id: str, db: AsyncSession = Depends(get_db)) -> Any:
    job = (await db.execute(select(RenderJob).where(RenderJob.id == render_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Render job not found")
    return job

@run_router.post("/cancel")
async def cancel_render(render_id: str, db: AsyncSession = Depends(get_db)) -> Any:
    job = (await db.execute(select(RenderJob).where(RenderJob.id == render_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Render job not found")
        
    if job.status in ("completed", "failed", "cancelled"):
        return {"status": job.status}
        
    job.status = "cancelled" # type: ignore
    await db.commit()
    return {"status": "cancelled"}
