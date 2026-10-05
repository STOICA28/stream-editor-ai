import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import select, delete

from stream_editor.api.config import settings
from stream_editor.api.database import SessionLocal, engine, Base
from stream_editor.api.models.project import (
    MediaAsset,
    Project,
    TimelineEvent,
    VisualObservation as DBVisualObservation,
)
from stream_editor.contracts.analysis import VisualReactionConfig
from stream_editor.worker.tasks.pipeline import (
    analyze_visual_observations_task,
    normalize_timeline_task,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def ensure_db_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


async def test_visual_reactions_enabled_generates_timeline_events(monkeypatch):
    """When M2_VISUAL_REACTIONS_ENABLED=True, normalize_timeline_task generates face_reaction TimelineEvents."""
    monkeypatch.setattr(settings, "M2_VISUAL_REACTIONS_ENABLED", True)

    async with SessionLocal() as db:
        proj = Project(name="Test Visual Reactions Enabled")
        db.add(proj)
        await db.commit()

        asset = MediaAsset(
            project_id=proj.id, media_type="source", media_info={"duration": 60.0}
        )
        db.add(asset)
        await db.commit()

        # Seed visual observation
        config = VisualReactionConfig()
        obs = DBVisualObservation(
            project_id=proj.id,
            source_asset_id=asset.id,
            event_type="face_reaction",
            start_time=10.0,
            end_time=12.5,
            confidence=0.92,
            description="Streamer facial reaction detected",
            detector="visual_observation@1.0.0",
            detector_config=config.model_dump(),
        )
        db.add(obs)
        await db.commit()

        proj_id = proj.id
        asset_id = asset.id

    # Run normalize_timeline_task logic
    normalize_timeline_task(proj_id, asset_id)

    # Check TimelineEvents
    async with SessionLocal() as db:
        events = (
            await db.execute(
                select(TimelineEvent).where(
                    TimelineEvent.source_asset_id == asset_id,
                    TimelineEvent.event_type == "face_reaction",
                )
            )
        ).scalars().all()

        assert len(events) == 1
        ev = events[0]
        assert ev.start_time == 10.0
        assert ev.end_time == 12.5
        assert ev.confidence == 0.92
        assert ev.producer == "visual_observation"
        assert ev.producer_version == "v1"


async def test_visual_reactions_disabled_suppresses_timeline_events(monkeypatch):
    """When M2_VISUAL_REACTIONS_ENABLED=False, normalize_timeline_task generates 0 face_reaction TimelineEvents (rollback baseline)."""
    monkeypatch.setattr(settings, "M2_VISUAL_REACTIONS_ENABLED", False)

    async with SessionLocal() as db:
        proj = Project(name="Test Visual Reactions Disabled")
        db.add(proj)
        await db.commit()

        asset = MediaAsset(
            project_id=proj.id, media_type="source", media_info={"duration": 60.0}
        )
        db.add(asset)
        await db.commit()

        # Seed visual observation in DB
        config = VisualReactionConfig()
        obs = DBVisualObservation(
            project_id=proj.id,
            source_asset_id=asset.id,
            event_type="face_reaction",
            start_time=10.0,
            end_time=12.5,
            confidence=0.95,
            description="Streamer facial reaction detected",
            detector="visual_observation@1.0.0",
            detector_config=config.model_dump(),
        )
        db.add(obs)
        await db.commit()

        proj_id = proj.id
        asset_id = asset.id

    # Run normalize_timeline_task logic
    normalize_timeline_task(proj_id, asset_id)

    # Check TimelineEvents - must be 0 face_reaction events
    async with SessionLocal() as db:
        events = (
            await db.execute(
                select(TimelineEvent).where(
                    TimelineEvent.source_asset_id == asset_id,
                    TimelineEvent.event_type == "face_reaction",
                )
            )
        ).scalars().all()

        assert len(events) == 0


async def test_visual_observations_task_clears_on_disabled(monkeypatch):
    """When M2_VISUAL_REACTIONS_ENABLED=False, analyze_visual_observations_task deletes existing DB records and skips execution."""
    monkeypatch.setattr(settings, "M2_VISUAL_REACTIONS_ENABLED", False)

    async with SessionLocal() as db:
        proj = Project(name="Test Visual Task Disabled")
        db.add(proj)
        await db.commit()

        asset = MediaAsset(
            project_id=proj.id, media_type="source", media_info={"duration": 60.0}
        )
        db.add(asset)
        await db.commit()

        # Existing stale observation
        obs = DBVisualObservation(
            project_id=proj.id,
            source_asset_id=asset.id,
            event_type="face_reaction",
            start_time=5.0,
            end_time=6.0,
            confidence=0.88,
            detector="mock",
        )
        db.add(obs)
        await db.commit()

        proj_id = proj.id
        asset_id = asset.id

    # Call task
    res = analyze_visual_observations_task(proj_id, asset_id, "fake_fingerprint")
    assert res == {"status": "success"}

    # Verify DB observation was cleared
    async with SessionLocal() as db:
        remaining = (
            await db.execute(
                select(DBVisualObservation).where(DBVisualObservation.source_asset_id == asset_id)
            )
        ).scalars().all()
        assert len(remaining) == 0


async def test_visual_observations_degraded_failure_mode(monkeypatch):
    """When visual observation provider throws an unexpected exception, task handles it degraded without failing."""
    monkeypatch.setattr(settings, "M2_VISUAL_REACTIONS_ENABLED", True)

    async with SessionLocal() as db:
        proj = Project(name="Test Visual Degraded Mode")
        db.add(proj)
        await db.commit()

        asset = MediaAsset(
            project_id=proj.id, media_type="source", media_info={"duration": 60.0}
        )
        db.add(asset)
        await db.commit()

        proxy_asset = MediaAsset(
            project_id=proj.id,
            parent_asset_id=asset.id,
            media_type="proxy",
            name="test_proxy.mp4",
            media_info={"duration": 60.0},
        )
        db.add(proxy_asset)
        await db.commit()

        proj_id = proj.id
        asset_id = asset.id

    # Mock provider that crashes
    mock_bad_provider = MagicMock()
    mock_bad_provider.analyze_visuals.side_effect = RuntimeError("OpenCV decoder hardware fault")

    with patch(
        "stream_editor.worker.tasks.pipeline.OpenCVVisualObservationProvider",
        return_value=mock_bad_provider,
    ):
        with patch.dict("os.environ", {"VISUAL_OBSERVATION_PROVIDER": "opencv"}):
            # Task must succeed with degraded mode (0 observations), not crash
            res = analyze_visual_observations_task(proj_id, asset_id, "fake_fingerprint")
            assert res == {"status": "success"}

    # No observations created
    async with SessionLocal() as db:
        obs = (
            await db.execute(
                select(DBVisualObservation).where(DBVisualObservation.source_asset_id == asset_id)
            )
        ).scalars().all()
        assert len(obs) == 0
