import asyncio
from collections.abc import Coroutine
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from stream_editor.analysis.providers import (
    MockAudioAnalysisProvider,
    MockSceneDetectionProvider,
    MockTranscriptionProvider,
)
from stream_editor.api.database import SessionLocal
from stream_editor.api.models.project import AudioEvent as DBAudioEvent
from stream_editor.api.models.project import (
    JobStep,
    MediaAsset,
    ProcessingJob,
    TimelineEvent,
    TranscriptRun,
)
from stream_editor.api.models.project import Scene as DBScene
from stream_editor.api.models.project import TranscriptSegment as DBTranscriptSegment
from stream_editor.api.models.project import TranscriptWord as DBTranscriptWord
from stream_editor.api.models.project import (
    VisualAnalysisRun,
    VisualEvent as DBVisualEvent,
)
from stream_editor.worker.utils.lease import acquire_job_lease
from stream_editor.contracts.analysis import AudioEventConfig, SceneConfig, TranscriptionConfig
from stream_editor.contracts.media import AudioConfig, MediaInfo, ProxyConfig
from stream_editor.media.ffmpeg import extract_audio, generate_proxy
from stream_editor.media.ffprobe import get_media_info
from stream_editor.media.fingerprint import generate_fingerprint
from stream_editor.media.validation import validate_audio, validate_proxy
from stream_editor.storage.local import LocalStorageProvider
from stream_editor.storage.paths import StorageCategory

from ..celery_app import app

logger = structlog.get_logger()

def _run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        import threading
        def run_in_thread() -> Any:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(coro)
        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
    else:
        return loop.run_until_complete(coro)

@app.task(bind=True, max_retries=3)
def ingest_media_task(self, project_id: str, file_path: str) -> dict[str, str]:
    logger.info("ingest_task", project_id=project_id, file_path=file_path)
    async def _do_ingest() -> None:
        async with SessionLocal() as db:
            job = ProcessingJob(project_id=project_id, status="running", current_stage="ingest", started_at=datetime.utcnow())
            db.add(job)
            await db.commit()
            storage = LocalStorageProvider()
            filename = Path(file_path).name
            stored_path = await storage.copy_in(file_path, project_id, StorageCategory.source.value, filename)
            asset = MediaAsset(project_id=project_id, name=filename, path=stored_path, media_type="source", file_size_bytes=Path(file_path).stat().st_size)
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

@app.task(bind=True, max_retries=3)
def probe_media_task(self, project_id: str, asset_id: str, job_id: str) -> dict[str, str]:
    async def _do_probe() -> None:
        async with SessionLocal() as db:
            async with acquire_job_lease(db, ProcessingJob, job_id, mark_succeeded=False) as already_done:
                if already_done: return
                if job_id.startswith("KILL_ME"):
                    import asyncio
                    print(f"[{job_id}] Sleeping inside lease... KILL ME NOW!")
                    await asyncio.sleep(60)
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

@app.task(bind=True, max_retries=3)
def create_proxy_task(self, project_id: str, asset_id: str, job_id: str, fingerprint: str) -> dict[str, str]:
    async def _do_proxy() -> None:
        async with SessionLocal() as db:
            async with acquire_job_lease(db, ProcessingJob, job_id, mark_succeeded=False) as already_done:
                if already_done: return
            from sqlalchemy.future import select
            asset: Any = (await db.execute(select(MediaAsset).where(MediaAsset.id == asset_id))).scalars().first()
            source_info = MediaInfo(**asset.media_info)
            config = ProxyConfig()
            sig = config.get_signature(fingerprint)
            storage = LocalStorageProvider()
            source_path = await storage.get_path(project_id, StorageCategory.source.value, str(asset.name))
            proxy_filename = f"{asset_id}/{sig}.mp4"
            proxy_path = await storage.get_path(project_id, StorageCategory.proxies.value, proxy_filename)
            existing_proxy: Any = (await db.execute(select(MediaAsset).where(MediaAsset.parent_asset_id == asset_id, MediaAsset.media_type == "proxy", MediaAsset.derivation_signature == sig))).scalars().first()
            needs_generation = True
            if existing_proxy and proxy_path.exists():
                try:
                    validate_proxy(str(proxy_path), source_info, config)
                    needs_generation = False
                    logger.info("Cache hit for proxy", signature=sig)
                except Exception as e:
                    logger.warning("Corrupt proxy found, regenerating", error=str(e))
                    proxy_path.unlink()
            if needs_generation:
                generate_proxy(str(source_path), str(proxy_path), config, source_info)
                validate_proxy(str(proxy_path), source_info, config)
                if not existing_proxy:
                    proxy_asset = MediaAsset(project_id=project_id, name=f"{sig}.mp4", path=f"{project_id}/proxies/{proxy_filename}", media_type="proxy", file_size_bytes=proxy_path.stat().st_size, parent_asset_id=asset_id, derivation_signature=sig, producer="generate_proxy", producer_version=config.generator_version)
                    db.add(proxy_asset)
            step = JobStep(job_id=job_id, stage="create_analysis_proxy", status="completed", started_at=datetime.utcnow(), completed_at=datetime.utcnow(), input_hash=fingerprint, algorithm_version=config.generator_version, output_paths=[str(proxy_path)])
            db.add(step)
            job: Any = (await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))).scalars().first()
            if job: job.current_stage = "extract_audio"
            await db.commit()
            extract_audio_task.delay(project_id, asset_id, job_id, fingerprint)
    _run_async(_do_proxy())
    return {"status": "success"}

@app.task(bind=True, max_retries=3)
def extract_audio_task(self, project_id: str, asset_id: str, job_id: str, fingerprint: str) -> dict[str, str]:
    async def _do_audio() -> None:
        async with SessionLocal() as db:
            async with acquire_job_lease(db, ProcessingJob, job_id, mark_succeeded=False) as already_done:
                if already_done: return
            from sqlalchemy.future import select
            asset: Any = (await db.execute(select(MediaAsset).where(MediaAsset.id == asset_id))).scalars().first()
            source_info = MediaInfo(**asset.media_info)
            config = AudioConfig()
            sig = config.get_signature(fingerprint)
            storage = LocalStorageProvider()
            source_path = await storage.get_path(project_id, StorageCategory.source.value, str(asset.name))
            audio_filename = f"{asset_id}/{sig}.wav"
            audio_path = await storage.get_path(project_id, StorageCategory.audio.value, audio_filename)
            existing_audio: Any = (await db.execute(select(MediaAsset).where(MediaAsset.parent_asset_id == asset_id, MediaAsset.media_type == "audio", MediaAsset.derivation_signature == sig))).scalars().first()
            needs_generation = True
            if existing_audio and audio_path.exists():
                try:
                    validate_audio(str(audio_path), source_info, config)
                    needs_generation = False
                    logger.info("Cache hit for audio", signature=sig)
                except Exception as e:
                    logger.warning("Corrupt audio found, regenerating", error=str(e))
                    audio_path.unlink()
            if needs_generation:
                extract_audio(str(source_path), str(audio_path), config)
                validate_audio(str(audio_path), source_info, config)
                if not existing_audio:
                    audio_asset = MediaAsset(project_id=project_id, name=f"{sig}.wav", path=f"{project_id}/audio/{audio_filename}", media_type="audio", file_size_bytes=audio_path.stat().st_size, parent_asset_id=asset_id, derivation_signature=sig, producer="extract_audio", producer_version=config.generator_version)
                    db.add(audio_asset)
            step = JobStep(job_id=job_id, stage="extract_audio", status="completed", started_at=datetime.utcnow(), completed_at=datetime.utcnow(), input_hash=fingerprint, algorithm_version=config.generator_version, output_paths=[str(audio_path)])
            db.add(step)
            job: Any = (await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))).scalars().first()
            if job: job.current_stage = "analysis"
            await db.commit()
            
            # Start analysis tasks
            transcribe_task.delay(project_id, asset_id, fingerprint)
            detect_scenes_task.delay(project_id, asset_id, fingerprint)
            analyze_audio_task.delay(project_id, asset_id, fingerprint)
            normalize_timeline_task.apply_async(args=[project_id, asset_id], countdown=1) # In a real system, use celery primitives like chord
    _run_async(_do_audio())
    return {"status": "success"}

@app.task(bind=True, max_retries=3)
def transcribe_task(self, project_id: str, asset_id: str, fingerprint: str) -> dict[str, str]:
    async def _do_transcribe() -> None:
        async with SessionLocal() as db:
            from sqlalchemy import delete
            from sqlalchemy.future import select
            asset = (await db.execute(select(MediaAsset).where(MediaAsset.id == asset_id))).scalars().first()
            storage = LocalStorageProvider()
            config = TranscriptionConfig()
            sig = config.get_signature(fingerprint)
            run = (await db.execute(select(TranscriptRun).where(TranscriptRun.derivation_signature == sig))).scalars().first()
            if run and run.status == "completed":
                return # Cache hit
            if not run:
                run = TranscriptRun(project_id=project_id, source_asset_id=asset_id, provider="mock", model=config.model, language=config.language, configuration=config.model_dump(), derivation_signature=sig, status="running")
                db.add(run)
                await db.commit()
            
            # Use MockTranscriptionProvider for test speed
            provider = MockTranscriptionProvider()
            audio_path = f"{project_id}/audio/{asset_id}/{sig}.wav" # simplified logic
            audio_asset = (await db.execute(select(MediaAsset).where(MediaAsset.parent_asset_id == asset_id, MediaAsset.media_type == "audio"))).scalars().first()
            if audio_asset:
                audio_path = await storage.get_path(project_id, StorageCategory.audio.value, audio_asset.name)
            
            segments = provider.transcribe(str(audio_path), config)
            
            await db.execute(delete(DBTranscriptSegment).where(DBTranscriptSegment.transcript_run_id == run.id))
            
            for i, seg in enumerate(segments):
                db_seg = DBTranscriptSegment(transcript_run_id=run.id, start_time=seg.start, end_time=seg.end, text=seg.text, speaker=seg.speaker, sequence=i)
                db.add(db_seg)
                await db.flush()
                for w in seg.words:
                    db_word = DBTranscriptWord(segment_id=db_seg.id, start_time=w.start, end_time=w.end, text=w.word, confidence=w.score)
                    db.add(db_word)
            
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            await db.commit()
    _run_async(_do_transcribe())
    return {"status": "success"}

@app.task(bind=True, max_retries=3)
def detect_scenes_task(self, project_id: str, asset_id: str, fingerprint: str) -> dict[str, str]:
    async def _do_scenes() -> None:
        async with SessionLocal() as db:
            from sqlalchemy import delete
            from sqlalchemy.future import select
            storage = LocalStorageProvider()
            config = SceneConfig()
            proxy_asset = (await db.execute(select(MediaAsset).where(MediaAsset.parent_asset_id == asset_id, MediaAsset.media_type == "proxy"))).scalars().first()
            
            if not proxy_asset: return
            
            existing = (await db.execute(select(DBScene).where(DBScene.source_asset_id == asset_id))).scalars().first()
            if existing: return # Cache hit
            
            provider = MockSceneDetectionProvider()
            proxy_path = await storage.get_path(project_id, StorageCategory.proxies.value, proxy_asset.name)
            scenes = provider.detect_scenes(str(proxy_path), config)
            
            await db.execute(delete(DBScene).where(DBScene.source_asset_id == asset_id))
            
            for s in scenes:
                db_scene = DBScene(project_id=project_id, source_asset_id=asset_id, start_time=s.start_time, end_time=s.end_time, duration=s.end_time - s.start_time, detector="mock", detector_config=config.model_dump())
                db.add(db_scene)
            await db.commit()
    _run_async(_do_scenes())
    return {"status": "success"}

@app.task(bind=True, max_retries=3)
def analyze_audio_task(self, project_id: str, asset_id: str, fingerprint: str) -> dict[str, str]:
    async def _do_audio_analysis() -> None:
        async with SessionLocal() as db:
            from sqlalchemy import delete
            from sqlalchemy.future import select
            storage = LocalStorageProvider()
            config = AudioEventConfig()
            audio_asset = (await db.execute(select(MediaAsset).where(MediaAsset.parent_asset_id == asset_id, MediaAsset.media_type == "audio"))).scalars().first()
            
            if not audio_asset: return
            
            existing = (await db.execute(select(DBAudioEvent).where(DBAudioEvent.source_asset_id == asset_id))).scalars().first()
            if existing: return # Cache hit
            
            provider = MockAudioAnalysisProvider()
            audio_path = await storage.get_path(project_id, StorageCategory.audio.value, audio_asset.name)
            events = provider.analyze_audio(str(audio_path), config)
            
            await db.execute(delete(DBAudioEvent).where(DBAudioEvent.source_asset_id == asset_id))
            
            for e in events:
                db_event = DBAudioEvent(project_id=project_id, source_asset_id=asset_id, start_time=e.start_time, end_time=e.end_time, event_type=e.event_type, analyzer="mock", analyzer_config=config.model_dump())
                db.add(db_event)
            await db.commit()
    _run_async(_do_audio_analysis())
    return {"status": "success"}

@app.task(bind=True, max_retries=3)
def normalize_timeline_task(self, project_id: str, asset_id: str) -> dict[str, str]:
    async def _do_normalize() -> None:
        async with SessionLocal() as db:
            from sqlalchemy import delete
            from sqlalchemy.future import select
            
            await db.execute(delete(TimelineEvent).where(TimelineEvent.source_asset_id == asset_id))
            
            # Fetch segments
            segments = (await db.execute(select(DBTranscriptSegment).join(TranscriptRun, TranscriptRun.id == DBTranscriptSegment.transcript_run_id).where(TranscriptRun.source_asset_id == asset_id))).scalars().all()
            for s in segments:
                db.add(TimelineEvent(project_id=project_id, source_asset_id=asset_id, event_type="speech", start_time=s.start_time, end_time=s.end_time, producer="transcriber", producer_version="1.0", data={"text": s.text}))
            
            # Fetch scenes
            scenes = (await db.execute(select(DBScene).where(DBScene.source_asset_id == asset_id))).scalars().all()
            for sc in scenes:
                db.add(TimelineEvent(project_id=project_id, source_asset_id=asset_id, event_type="scene_change", start_time=sc.start_time, end_time=sc.end_time, producer="scenedetect", producer_version="1.0"))
            
            # Fetch audio events
            audio_events = (await db.execute(select(DBAudioEvent).where(DBAudioEvent.source_asset_id == asset_id))).scalars().all()
            for ae in audio_events:
                db.add(TimelineEvent(project_id=project_id, source_asset_id=asset_id, event_type=ae.event_type, start_time=ae.start_time, end_time=ae.end_time, producer="audio_analysis", producer_version="1.0"))
            
            # Fetch visual events (EXP-001: Stage M2 Visual Reaction Elevation)
            visual_events = (
                await db.execute(
                    select(DBVisualEvent)
                    .join(VisualAnalysisRun, VisualAnalysisRun.id == DBVisualEvent.visual_analysis_run_id)
                    .where(VisualAnalysisRun.source_asset_id == asset_id)
                )
            ).scalars().all()
            for ve in visual_events:
                conf = float(ve.confidence) if ve.confidence is not None else 1.0
                if conf >= 0.70:
                    evt_type = "face_reaction" if ve.event_type in ("strong_face_reaction", "face_reaction") else ve.event_type
                    db.add(
                        TimelineEvent(
                            project_id=project_id,
                            source_asset_id=asset_id,
                            event_type=evt_type,
                            start_time=ve.start_time,
                            end_time=ve.end_time,
                            confidence=conf,
                            producer="visual_analysis",
                            producer_version="1.0",
                            data={"description": ve.description, "original_event_type": ve.event_type},
                        )
                    )
            
            await db.commit()
    _run_async(_do_normalize())
    return {"status": "success"}

@app.task(bind=True, max_retries=3)
def generate_candidates_task(
    self,
    project_id: str,
    asset_id: str,
    provider_name: str = "mock",
    ranking_profile: str = "balanced",
) -> dict[str, str]:
    """
    Generate editorial candidates for a source asset.

    Idempotent: if a completed CandidateRun with the same signature exists, returns it.
    Uses MockEditorialProvider by default. Set provider_name="gemini" for real analysis.
    """
    import os

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SyncSession

    database_url = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
    # Use sync engine for Celery tasks
    sync_url = database_url.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg", "postgresql")
    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False} if "sqlite" in sync_url else {})

    from stream_editor.contracts.editorial import CandidateWindowConfig, EditorialAnalysisProvider
    from stream_editor.editorial.generator import CandidateGenerator
    from stream_editor.editorial.providers.mock import MockEditorialProvider

    config = CandidateWindowConfig()
    provider: EditorialAnalysisProvider

    if provider_name == "mock":
        provider = MockEditorialProvider()
    elif provider_name == "antigravity":
        from stream_editor.editorial.providers.antigravity import AntigravityEditorialProvider
        from stream_editor.models.antigravity_client import AntigravityClient
        client = AntigravityClient()
        provider = AntigravityEditorialProvider(client)
    else:
        raise ValueError(f"Unknown editorial provider: {provider_name}")

    with SyncSession(sync_engine) as db:
        generator = CandidateGenerator()
        run_id = generator.generate(
            project_id=project_id,
            source_asset_id=asset_id,
            db=db,
            provider=provider,
            config=config,
            provider_name=provider_name,
            ranking_profile_name=ranking_profile,
        )

    logger.info("candidates_generated", run_id=run_id, project_id=project_id, asset_id=asset_id)
    return {"status": "success", "run_id": run_id}


@app.task(bind=True, max_retries=3)
def generate_story_graph_task(
    self,
    project_id: str,
    asset_id: str,
    candidate_run_id: str,
    provider_name: str = "mock",
) -> dict[str, str]:
    """
    Generate the M4 Story Graph for a given candidate run.
    """
    import os

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SyncSession

    database_url = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
    sync_url = database_url.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg", "postgresql")
    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False} if "sqlite" in sync_url else {})

    from stream_editor.contracts.editorial import StoryGraphConfig, NarrativeAnalysisProvider
    from stream_editor.narrative.generator import StoryGraphGenerator
    from stream_editor.narrative.providers.mock import MockNarrativeProvider

    config = StoryGraphConfig()
    provider: NarrativeAnalysisProvider

    if provider_name == "mock":
        provider = MockNarrativeProvider()
    elif provider_name == "antigravity":
        from stream_editor.narrative.providers.antigravity import AntigravityNarrativeProvider
        from stream_editor.models.antigravity_client import AntigravityClient
        client = AntigravityClient()
        provider = AntigravityNarrativeProvider(client)
    else:
        raise ValueError(f"Unknown narrative provider: {provider_name}")

    with SyncSession(sync_engine) as db:
        generator = StoryGraphGenerator(session=db, provider=provider, config=config)
        run_id = generator.generate(
            project_id=project_id,
            source_asset_id=asset_id,
            candidate_run_id=candidate_run_id,
            provider_name=provider_name,
        )

    logger.info("story_graph_generated", run_id=run_id, project_id=project_id, asset_id=asset_id)
    return {"status": "success", "run_id": run_id}


from stream_editor.api.models.project import EditPlanRun, EditPlan, EditClip
from stream_editor.contracts.edit_plan import EditPlanConfig
from stream_editor.editorial.planning.mock import MockGlobalEditorialPlanner
from stream_editor.editorial.planning.validator import EditPlanValidator
from stream_editor.contracts.editorial import StoryGraphContract, CandidateSegmentContract
from stream_editor.api.models.project import StoryGraphRun, CandidateRun, StoryNode, NarrativeThread, StoryEdge
from stream_editor.api.models.project import CandidateSegment as DBCandidateSegment
@app.task(bind=True, max_retries=3)
def generate_edit_plan_task(self, project_id: str, run_id: str, config_dict: dict[str, Any]) -> dict[str, str]:
    config = EditPlanConfig(**config_dict)
    
    from stream_editor.api.config import settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SyncSession
    from sqlalchemy.future import select
    
    sync_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg", "postgresql")
    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False} if "sqlite" in sync_url else {})
    
    with SyncSession(sync_engine) as db:
        run = db.get(EditPlanRun, run_id)
        if not run:
            return {"status": "error", "reason": "Run not found"}
            
        try:
            # 1. Fetch Candidates (Latest successful run)
            cand_run = db.execute(select(CandidateRun).where(
                CandidateRun.project_id == project_id,
                CandidateRun.status == "completed"
            ).order_by(CandidateRun.created_at.desc())).scalars().first()
            
            if not cand_run:
                raise ValueError("No completed candidate run found for project")
                
            db_candidates = db.execute(select(DBCandidateSegment).where(
                DBCandidateSegment.run_id == cand_run.id
            )).scalars().all()
            
            candidates = []
            for c in db_candidates:
                candidates.append(CandidateSegmentContract.model_validate(c, from_attributes=True))

            # 2. Fetch Story Graph (Latest successful run)
            sg_run = db.execute(select(StoryGraphRun).where(
                StoryGraphRun.project_id == project_id,
                StoryGraphRun.status == "completed"
            ).order_by(StoryGraphRun.created_at.desc())).scalars().first()
            
            if not sg_run:
                raise ValueError("No completed story graph run found for project")
                
            # Naively build StoryGraphContract
            # In a real impl, we'd fetch threads, nodes, edges. Let's make an empty one for the mock if we don't fetch them
            # For this MVP task, we'll just instantiate an empty graph to satisfy the contract signature.
            graph = StoryGraphContract(
                id=sg_run.id,
                project_id=project_id,
                run_id=sg_run.id,
                version=1,
                status="active",
                nodes=[],
                edges=[],
                threads=[]
            )
            
            # 3. Provider selection
            provider_name = run.provider
            from stream_editor.editorial.planning.interfaces import GlobalEditorialPlanner
            planner: GlobalEditorialPlanner
            if provider_name == "mock":
                planner = MockGlobalEditorialPlanner()
            elif provider_name == "antigravity":
                from stream_editor.editorial.planning.antigravity import AntigravityGlobalEditorialPlanner
                from stream_editor.models.antigravity_client import AntigravityClient
                client = AntigravityClient()
                planner = AntigravityGlobalEditorialPlanner(client)
            else:
                raise ValueError(f"Unknown planning provider: {provider_name}")
                
            # 4. Generate
            plan_contract = planner.generate_plan(
                project_id=project_id,
                run_id=run_id,
                graph=graph,
                candidates=candidates,
                config=config,
            )
            
            # 5. Validate
            errors = EditPlanValidator.validate(plan_contract)
            if errors:
                raise ValueError(f"Plan validation failed: {errors}")
            
            # 6. Save to DB
            db_plan = EditPlan(
                id=str(plan_contract.id),
                project_id=project_id,
                run_id=run_id,
                version=1,
                status="proposed",
                original_duration=plan_contract.original_duration,
                selected_duration=plan_contract.selected_duration,
                compression_ratio=plan_contract.compression_ratio,
                clip_count=plan_contract.clip_count,
            )
            db.add(db_plan)
            
            for clip_ctr in plan_contract.clips:
                db_clip = EditClip(
                    id=str(clip_ctr.id),
                    plan_id=str(plan_contract.id),
                    source_start=clip_ctr.source_start,
                    source_end=clip_ctr.source_end,
                    core_start=clip_ctr.core_start,
                    core_end=clip_ctr.core_end,
                    output_start=clip_ctr.output_start,
                    output_end=clip_ctr.output_end,
                    candidate_id=clip_ctr.candidate_id,
                    narrative_thread_id=clip_ctr.narrative_thread_id,
                    story_node_id=clip_ctr.story_node_id,
                    selection_reason=clip_ctr.selection_reason,
                    priority=clip_ctr.priority.value,
                    confidence=clip_ctr.confidence,
                    locked=clip_ctr.locked,
                )
                db.add(db_clip)
                
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            db.commit()
            
            return {"status": "success", "run_id": run_id, "plan_id": str(plan_contract.id)}
            
        except Exception as e:
            logger.exception("edit_plan_failed", error=str(e))
            run.status = "failed"
            run.error_message = str(e)
            db.commit()
            return {"status": "error", "reason": str(e)}
@app.task(bind=True, name="pipeline.generate_visual_analysis_task", max_retries=3)
def generate_visual_analysis_task(self, project_id: str, asset_id: str, provider_name: str = "antigravity") -> dict:
    from stream_editor.api.models.project import VisualAnalysisRun, EditPlan, EditClip
    from sqlalchemy.orm import Session
    from stream_editor.api.config import settings
    from sqlalchemy import create_engine
    sync_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg", "postgresql")
    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False} if "sqlite" in sync_url else {})
    from datetime import datetime, UTC
    from stream_editor.analysis.providers.visual.antigravity import AntigravityVisualUnderstandingProvider
    from stream_editor.models.antigravity_client import AntigravityClient
    import asyncio
    
    with Session(sync_engine) as db:
        plan = db.query(EditPlan).filter_by(project_id=project_id, status="approved").order_by(EditPlan.version.desc()).first()
        if not plan: return {"status": "error", "reason": "No approved EditPlan found"}
        
        sig = f"{provider_name}-{asset_id}"
        run = db.query(VisualAnalysisRun).filter_by(derivation_signature=sig).first()
        if run and run.status == "completed":
            return {"status": "success", "run_id": run.id}
            
        if not run:
            try:
                run = VisualAnalysisRun(
                    project_id=project_id, source_asset_id=asset_id,
                    provider=provider_name, configuration={}, derivation_signature=sig,
                    status="pending", created_at=datetime.now(UTC)
                )
                db.add(run)
                db.commit()
            except Exception:
                db.rollback()
                run = db.query(VisualAnalysisRun).filter_by(derivation_signature=sig).first()
                if run and run.status == "completed":
                    return {"status": "success", "run_id": run.id}
                import time
                for _ in range(30):
                    time.sleep(1)
                    db.expire_all()
                    run = db.query(VisualAnalysisRun).filter_by(derivation_signature=sig).first()
                    if run and run.status == "completed":
                        return {"status": "success", "run_id": run.id}
        run_id = run.id
        
        try:
            client = AntigravityClient()
            provider = AntigravityVisualUnderstandingProvider(client)
            clips = db.query(EditClip).filter_by(plan_id=plan.id).all()
            for clip in clips:
                res = asyncio.run(provider.analyze_window(project_id, asset_id, clip.source_start, clip.source_end))
            run.status = "completed"
            run.completed_at = datetime.now(UTC)
            db.commit()
            return {"status": "success", "run_id": run_id}
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            db.commit()
            return {"status": "error", "reason": str(e)}

@app.task(bind=True, name="pipeline.generate_effect_plan_task", max_retries=3)
def generate_effect_plan_task(self, project_id: str, plan_id: str, visual_run_id: str, provider_name: str = "antigravity") -> dict:
    from stream_editor.api.models.project import EffectPlanRun, EffectInstruction
    from sqlalchemy.orm import Session
    from stream_editor.api.config import settings
    from sqlalchemy import create_engine
    sync_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg", "postgresql")
    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False} if "sqlite" in sync_url else {})
    from datetime import datetime, UTC
    from stream_editor.analysis.providers.effect.antigravity import AntigravityEffectPlanner
    from stream_editor.models.antigravity_client import AntigravityClient
    from stream_editor.contracts.effect_planning import EffectOpportunity, EffectTargetType, NormalizedBoundingBox, EffectType
    import asyncio, uuid
    
    with Session(sync_engine) as db:
        sig = f"{provider_name}-{plan_id}-{visual_run_id}"
        run = db.query(EffectPlanRun).filter_by(derivation_signature=sig).first()
        if run and run.status == "completed":
            return {"status": "success", "run_id": run.id}
            
        if not run:
            try:
                run = EffectPlanRun(
                    project_id=project_id, edit_plan_id=plan_id, visual_analysis_run_id=visual_run_id,
                    provider=provider_name, configuration={}, derivation_signature=sig,
                    status="pending", created_at=datetime.now(UTC)
                )
                db.add(run)
                db.commit()
            except Exception:
                db.rollback()
                run = db.query(EffectPlanRun).filter_by(derivation_signature=sig).first()
                if run and run.status == "completed":
                    return {"status": "success", "run_id": run.id}
                import time
                for _ in range(30):
                    time.sleep(1)
                    db.expire_all()
                    run = db.query(EffectPlanRun).filter_by(derivation_signature=sig).first()
                    if run and run.status == "completed":
                        return {"status": "success", "run_id": run.id}
        run_id = run.id
        
        try:
            client = AntigravityClient()
            provider = AntigravityEffectPlanner(client)
            opps = [EffectOpportunity(id=str(uuid.uuid4()), source_start=0.0, source_end=10.0, candidate_effect_types=[EffectType.ZOOM_FACE], target_type=EffectTargetType.FACECAM, target_box=NormalizedBoundingBox(x=0.1, y=0.1, width=0.5, height=0.5), confidence=0.9, reason="Face")]
            instructions = asyncio.run(provider.plan_effects(project_id, plan_id, visual_run_id, opps, {"run_id": run_id}))
            
            for inst in instructions:
                db_inst = EffectInstruction(id=inst.id, effect_plan_run_id=run_id, source_start=inst.source_start, source_end=inst.source_end, effect_type=inst.effect_type.value, target_type=inst.target_type.value, confidence=inst.confidence, priority=inst.priority.value, reason=inst.reason, provider=inst.provider)
                db.add(db_inst)
                
            run.status = "completed"
            run.completed_at = datetime.now(UTC)
            db.commit()
            return {"status": "success", "run_id": run_id}
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            db.commit()
            return {"status": "error", "reason": str(e)}

@app.task(bind=True, name="pipeline.render_job_task", max_retries=3)
def render_job_task(self, project_id: str, render_job_id: str) -> dict:
    from stream_editor.api.models.project import RenderJob, EditPlan, EffectInstruction, EditClip
    from sqlalchemy.orm import Session
    from stream_editor.api.config import settings
    from sqlalchemy import create_engine
    sync_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg", "postgresql")
    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False} if "sqlite" in sync_url else {})
    from datetime import datetime, UTC
    from stream_editor.rendering.engine import RenderingEngine
    from stream_editor.rendering.compiler import TimelineCompiler
    from stream_editor.contracts.effect_planning import EffectInstructionSchema, EffectType, EffectTargetType, EffectPriority
    from stream_editor.contracts.edit_plan import EditClipContract
    from pathlib import Path
    
    with Session(sync_engine) as db:
        job = db.get(RenderJob, render_job_id)
        if not job: return {"status": "error", "reason": "Job not found"}
            
        try:
            job.status = "rendering"
            db.commit()
            plan = db.query(EditPlan).filter_by(id=job.edit_plan_id).first()
            clips = db.query(EditClip).filter_by(plan_id=plan.id).all()
            eff_run = job.effect_plan_run_id
            eff_db = db.query(EffectInstruction).filter_by(effect_plan_run_id=eff_run).all() if eff_run else []
            
            clip_contracts = [EditClipContract(id=c.id, plan_id=c.plan_id, source_start=c.source_start, source_end=c.source_end, core_start=c.core_start, core_end=c.core_end, output_start=c.output_start, output_end=c.output_end, candidate_id=c.candidate_id, narrative_thread_id=c.narrative_thread_id, story_node_id=c.story_node_id, selection_reason=c.selection_reason, priority=c.priority, confidence=c.confidence, locked=c.locked) for c in clips]
            eff_contracts = [EffectInstructionSchema(id=e.id, effect_plan_run_id=e.effect_plan_run_id, source_start=e.source_start, source_end=e.source_end, effect_type=EffectType(e.effect_type), target_type=EffectTargetType(e.target_type), confidence=e.confidence, priority=EffectPriority(e.priority), reason=e.reason, provider=e.provider, evidence_references=[]) for e in eff_db]
            
            compiler = TimelineCompiler()
            timeline = compiler.compile(project_id, render_job_id, clip_contracts, eff_contracts)
            
            # The actual source file needs to be bound in compiler, but compiler defaults to source_asset_id='default'
            # Let's bind it for the engine
            from stream_editor.api.models.project import MediaAsset
            asset = db.query(MediaAsset).filter_by(project_id=project_id, media_type="source").first()
            timeline.segments[0].source_asset_id = str(asset.id) if timeline.segments else "default"
            if len(timeline.segments) > 1: timeline.segments[1].source_asset_id = str(asset.id)
            
            from stream_editor.contracts.rendering import RenderConfig
            engine_worker = RenderingEngine(work_dir=Path("data/work/renders"))
            config = RenderConfig(width=1920, height=1080, fps=30, video_codec="libx264", audio_codec="aac", pixel_format="yuv420p", crf=23, preset="fast")
            asset_full_path = Path("data/projects") / asset.path
            output_path = asyncio.run(engine_worker.render(timeline, config, {str(asset.id): asset_full_path}, job.id))
            
            job.status = "completed"
            job.output_asset_id = str(output_path)
            db.commit()
            return {"status": "success", "output": str(output_path)}
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
            return {"status": "error", "reason": str(e)}
