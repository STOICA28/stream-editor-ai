from sqlalchemy import select
import pytest
import uuid
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from stream_editor.api.database import Base
from stream_editor.api.models.project import Project, EditPlanRun, EditPlan, EditClip, FeedbackEvent
from stream_editor.api.routers.planning import _repack_plan_clips

@pytest.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_repack_excludes_rejected(async_db: AsyncSession):
    # Setup data
    proj_id = str(uuid.uuid4())
    proj = Project(id=proj_id, name="Test", source_video_path="test.mp4")
    async_db.add(proj)
    
    run_id = str(uuid.uuid4())
    run = EditPlanRun(id=run_id, project_id=proj_id)
    async_db.add(run)
    
    plan_id = str(uuid.uuid4())
    plan = EditPlan(id=plan_id, project_id=proj_id, run_id=run_id, original_duration=100.0)
    async_db.add(plan)
    
    c1 = EditClip(id=str(uuid.uuid4()), plan_id=plan_id, source_start=0, source_end=20, output_start=0, output_end=20, review_state="accepted")
    c2 = EditClip(id=str(uuid.uuid4()), plan_id=plan_id, source_start=20, source_end=50, output_start=20, output_end=50, review_state="rejected")
    c3 = EditClip(id=str(uuid.uuid4()), plan_id=plan_id, source_start=60, source_end=100, output_start=50, output_end=90, review_state="proposed")
    
    async_db.add_all([c1, c2, c3])
    await async_db.commit()
    
    # Run repack
    await _repack_plan_clips(async_db, plan_id)
    
    # Reload and assert
    plan = (await async_db.execute(select(EditPlan).where(EditPlan.id == plan.id))).scalar_one()
    assert plan.clip_count == 2
    assert plan.selected_duration == 60.0
    assert plan.compression_ratio == 0.6
    
    # Verify c3 got shifted because c2 was rejected
    c3 = (await async_db.execute(select(EditClip).where(EditClip.id == c3.id))).scalar_one()
    assert c3.output_start == 20.0
    assert c3.output_end == 60.0

@pytest.mark.asyncio
async def test_historical_immutability(async_db: AsyncSession):
    # Just asserting the structure supports it. The actual logic is in the FastAPI endpoint
    plan1 = EditPlan(id="plan1", origin="ai", revision_number=1)
    plan2 = EditPlan(id="plan2", origin="human", parent_plan_id="plan1", revision_number=2)
    async_db.add_all([plan1, plan2])
    await async_db.commit()
    
    await async_db.refresh(plan1)
    await async_db.refresh(plan2)
    
    assert plan2.parent_plan_id == plan1.id
    assert plan2.revision_number > plan1.revision_number

@pytest.mark.asyncio
async def test_feedback_events(async_db: AsyncSession):
    f = FeedbackEvent(
        project_id="proj1",
        edit_plan_id="plan1",
        edit_clip_id="clip1",
        feedback_type="modify_start",
        previous_value={"source_start": 10},
        new_value={"source_start": 5}
    )
    async_db.add(f)
    await async_db.commit()
    
    await async_db.refresh(f)
    assert f.previous_value["source_start"] == 10
    assert f.new_value["source_start"] == 5

@pytest.mark.asyncio
async def test_boundary_modification(async_db: AsyncSession):
    plan_id = str(uuid.uuid4())
    plan = EditPlan(id=plan_id, original_duration=100.0)
    async_db.add(plan)
    
    # 10:30 -> 11:10 (630s -> 670s)
    c1 = EditClip(id="c1", plan_id=plan_id, source_start=630, source_end=670)
    async_db.add(c1)
    await async_db.commit()
    
    # Extend start 8 seconds: 622 -> 670
    c1.source_start = 622
    await async_db.commit()
    
    await _repack_plan_clips(async_db, plan_id)
    
    c1 = (await async_db.execute(select(EditClip).where(EditClip.id == c1.id))).scalar_one()
    plan = (await async_db.execute(select(EditPlan).where(EditPlan.id == plan.id))).scalar_one()
    
    assert c1.output_start == 0.0
    assert c1.output_end == 48.0 # 670 - 622
    assert plan.selected_duration == 48.0
