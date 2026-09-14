from ..celery_app import app
import structlog
import asyncio
from pathlib import Path
from datetime import datetime

from stream_editor.api.database import SessionLocal
from stream_editor.api.models.project import Project, MediaAsset, ProcessingJob, JobStep
from stream_editor.storage.local import LocalStorageProvider
from stream_editor.storage.paths import StorageCategory
from stream_editor.media.ffprobe import get_media_info
from stream_editor.media.ffmpeg import generate_proxy, extract_audio
from stream_editor.media.fingerprint import generate_fingerprint
from stream_editor.api.models.project import ProcessingJob, JobStep, MediaAsset
from stream_editor.storage.local import LocalStorageProvider
from stream_editor.storage.paths import StorageCategory
from typing import Any, Coroutine
import asyncio

logger = structlog.get_logger()

def _run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        # Fallback if somehow called within a running loop
        import threading
        def run_in_thread() -> Any:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(coro)
        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        # This is a hacky fallback, but generally the loop shouldn't be running.
    else:
        return loop.run_until_complete(coro)

@app.task
def ingest_media_task(project_id: str, file_path: str) -> dict[str, str]:
    logger.info("ingest_task", project_id=project_id, file_path=file_path)
    
    async def _do_ingest() -> None:
        async with SessionLocal() as db:
            job = ProcessingJob(project_id=project_id, status="running", current_stage="ingest", started_at=datetime.utcnow())
            db.add(job)
            await db.commit()
            
            storage = LocalStorageProvider()
            filename = Path(file_path).name
            stored_path = await storage.copy_in(file_path, project_id, StorageCategory.source.value, filename)
            
            asset = MediaAsset(
                project_id=project_id,
                name=filename,
                path=stored_path,
                media_type="source",
                file_size_bytes=Path(file_path).stat().st_size
            )
            db.add(asset)
            await db.commit()
            logger.info("File copied to project storage", stored_path=stored_path)
            
            probe_media_task.delay(project_id, str(asset.id), str(job.id))
            
    try:
        _run_async(_do_ingest())
        return {"status": "success"}
    except Exception as e:
        logger.error("ingest_failed", error=str(e))
        return {"status": "error", "message": str(e)}

@app.task
def probe_media_task(project_id: str, asset_id: str, job_id: str) -> dict[str, str]:
    async def _do_probe() -> None:
        async with SessionLocal() as db:
            from sqlalchemy.future import select
            asset: Any = (await db.execute(select(MediaAsset).where(MediaAsset.id == asset_id))).scalars().first()
            if not asset: raise Exception("Asset not found")
            
            storage = LocalStorageProvider()
            full_path = await storage.get_path(project_id, StorageCategory.source.value, str(asset.name))
            
            fingerprint = generate_fingerprint(str(full_path))
            media_info = get_media_info(str(full_path))
            
            asset.media_info = media_info.model_dump()
            
            step = JobStep(job_id=job_id, stage="probe_media", status="completed", started_at=datetime.utcnow(), completed_at=datetime.utcnow(), input_hash=fingerprint, algorithm_version="1.0", output_paths=[])
            db.add(step)
            
            job: Any = (await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))).scalars().first()
            if job: job.current_stage = "create_analysis_proxy"
            
            await db.commit()
            
            create_proxy_task.delay(project_id, asset_id, job_id, fingerprint)
            
    _run_async(_do_probe())
    return {"status": "success"}

@app.task
def create_proxy_task(project_id: str, asset_id: str, job_id: str, fingerprint: str) -> dict[str, str]:
    async def _do_proxy() -> None:
        async with SessionLocal() as db:
            from sqlalchemy.future import select
            asset: Any = (await db.execute(select(MediaAsset).where(MediaAsset.id == asset_id))).scalars().first()
            
            storage = LocalStorageProvider()
            source_path = await storage.get_path(project_id, StorageCategory.source.value, str(asset.name))
            proxy_filename = "proxy.mp4"
            proxy_path = await storage.get_path(project_id, StorageCategory.proxies.value, proxy_filename)
            
            if not proxy_path.exists():
                generate_proxy(str(source_path), str(proxy_path))
            
            proxy_asset = MediaAsset(project_id=project_id, name=proxy_filename, path=f"{project_id}/proxies/{proxy_filename}", media_type="proxy", file_size_bytes=proxy_path.stat().st_size)
            db.add(proxy_asset)
            
            step = JobStep(job_id=job_id, stage="create_analysis_proxy", status="completed", started_at=datetime.utcnow(), completed_at=datetime.utcnow(), input_hash=fingerprint, algorithm_version="1.0", output_paths=[str(proxy_path)])
            db.add(step)
            
            job: Any = (await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))).scalars().first()
            if job: job.current_stage = "extract_audio"
            await db.commit()
            
            extract_audio_task.delay(project_id, asset_id, job_id, fingerprint)
            
    _run_async(_do_proxy())
    return {"status": "success"}

@app.task
def extract_audio_task(project_id: str, asset_id: str, job_id: str, fingerprint: str) -> dict[str, str]:
    async def _do_audio() -> None:
        async with SessionLocal() as db:
            from sqlalchemy.future import select
            asset: Any = (await db.execute(select(MediaAsset).where(MediaAsset.id == asset_id))).scalars().first()
            
            storage = LocalStorageProvider()
            source_path = await storage.get_path(project_id, StorageCategory.source.value, str(asset.name))
            audio_filename = "analysis.wav"
            audio_path = await storage.get_path(project_id, StorageCategory.audio.value, audio_filename)
            
            if not audio_path.exists():
                extract_audio(str(source_path), str(audio_path))
            
            audio_asset = MediaAsset(project_id=project_id, name=audio_filename, path=f"{project_id}/audio/{audio_filename}", media_type="audio", file_size_bytes=audio_path.stat().st_size)
            db.add(audio_asset)
            
            step = JobStep(job_id=job_id, stage="extract_audio", status="completed", started_at=datetime.utcnow(), completed_at=datetime.utcnow(), input_hash=fingerprint, algorithm_version="1.0", output_paths=[str(audio_path)])
            db.add(step)
            
            job: Any = (await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))).scalars().first()
            if job: 
                job.current_stage = "completed"
                job.status = "completed"
                job.completed_at = datetime.utcnow()
            await db.commit()
            
    _run_async(_do_audio())
    return {"status": "success"}

@app.task
def transcribe_task(project_id: str) -> dict[str, str]: return {"status": "success"}
@app.task
def detect_scenes_task(project_id: str) -> dict[str, str]: return {"status": "success"}
@app.task
def generate_candidates_task(project_id: str) -> dict[str, str]: return {"status": "success"}
@app.task
def generate_edit_plan_task(project_id: str) -> dict[str, str]: return {"status": "success"}
