import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from stream_editor.api.database import Base, get_db
from stream_editor.api.models.project import Project, MediaAsset, VisualAnalysisRun, StreamLayout, FocusTarget
from stream_editor.api.main import app

@pytest.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

@pytest.fixture
async def async_client(async_db):
    app.dependency_overrides[get_db] = lambda: async_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

pytestmark = pytest.mark.asyncio

async def test_bounding_box_validation():
    from stream_editor.contracts.visual_analysis import BoundingBox
    # Valid
    box = BoundingBox(x=0.1, y=0.1, width=0.5, height=0.5)
    
    # Invalid width + x
    with pytest.raises(ValueError):
        BoundingBox(x=0.8, y=0.1, width=0.5, height=0.5)

    # Invalid negative
    with pytest.raises(ValueError):
        BoundingBox(x=-0.1, y=0.1, width=0.5, height=0.5)

async def test_visual_analysis_start_and_retrieve(async_client: AsyncClient, async_db: AsyncSession, monkeypatch):
    from fastapi import BackgroundTasks
    monkeypatch.setattr(BackgroundTasks, "add_task", lambda *args, **kwargs: None)
    
    proj = Project(name="Test Visual")
    async_db.add(proj)
    await async_db.commit()

    asset = MediaAsset(project_id=proj.id, media_type="source", media_info={"duration": 60.0})
    async_db.add(asset)
    await async_db.commit()

    # Start analysis
    res = await async_client.post(f"/api/v1/projects/{proj.id}/visual-analysis")
    assert res.status_code == 200, res.text
    run_id = res.json()["run_id"]

    # The background task might have executed or we can run it manually.
    # To be safe and deterministic in test, run the task logic
    from stream_editor.api.routers.visual import run_visual_analysis_task
    # We must patch async_session_maker temporarily for this test
    # Or just write a direct DB test for the provider
    
    run = (await async_db.execute(select(VisualAnalysisRun).where(VisualAnalysisRun.id == run_id))).scalar_one_or_none()
    assert run is not None
    assert run.status == "running"

    from stream_editor.analysis.providers.visual import MockVisualProvider
    provider = MockVisualProvider(scenario="C")
    results = await provider.analyze_window(proj.id, asset.id, 0.0, 60.0, {"run_id": run_id})
    
    # Insert results (mimic the background task)
    for layout in results["layouts"]:
        async_db.add(StreamLayout(**layout.model_dump()))
    for ft in results["focus_targets"]:
        ft_dump = ft.model_dump()
        if ft.box:
            ft_dump["x"] = ft.box.x
            ft_dump["y"] = ft.box.y
            ft_dump["width"] = ft.box.width
            ft_dump["height"] = ft.box.height
        del ft_dump["box"]
        async_db.add(FocusTarget(**ft_dump))
    
    run.status = "completed"
    await async_db.commit()

    # Check layouts
    res = await async_client.get(f"/api/v1/visual-analysis/{run_id}/layouts")
    assert res.status_code == 200
    assert len(res.json()) > 0
    assert res.json()[0]["layout_name"] == "Gameplay + BottomRight Facecam"

    # Check focus targets
    res = await async_client.get(f"/api/v1/visual-analysis/{run_id}/focus-targets")
    assert res.status_code == 200
    targets = res.json()
    assert len(targets) > 0
    assert any(t["target_type"] == "facecam" for t in targets)

