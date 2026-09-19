
import uuid
import asyncio
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from stream_editor.api.models.project import MediaAsset
from stream_editor.contracts.rendering import RenderConfig, CompiledTimeline, CompiledSegment

async def render_latest_edit_plan():
    engine = create_engine("sqlite:///test.db")
    with Session(engine) as db:
        # Get the original 5h source asset
        asset = db.query(MediaAsset).filter_by(project_id="real-5h-65655576").first()
        if not asset:
            print("No source asset found!")
            return
        
        asset_id = str(asset.id)
        project_id = asset.project_id
        source_path = Path("data/projects") / project_id / "source" / asset.name
        
    print(f"Rendering fallback manual plan for project {project_id}...")
    
    # Manually compile a timeline with 2 short clips from the 5h source
    # e.g., 00:01:00 to 00:01:10 and 00:02:00 to 00:02:10
    segments = [
        CompiledSegment(
            id=str(uuid.uuid4()),
            segment_index=0,
            source_asset_id=asset_id,
            source_start=60.0,
            source_end=70.0,
            duration=10.0,
            output_start=0.0,
            output_end=10.0,
            volume=1.0,
            speed=1.0
        ),
        CompiledSegment(
            id=str(uuid.uuid4()),
            segment_index=1,
            source_asset_id=asset_id,
            source_start=120.0,
            source_end=130.0,
            duration=10.0,
            output_start=10.0,
            output_end=20.0,
            volume=1.0,
            speed=1.0
        )
    ]
    
    timeline = CompiledTimeline(
        project_id=project_id,
        source_asset_id=asset_id,
        render_job_id=str(uuid.uuid4()),
        expected_duration=20.0,
        duration=20.0,
        resolution=(1920, 1080),
        fps=30.0,
        segments=segments,
        effects=[],
        audio_tracks=[]
    )
    
    from stream_editor.rendering.engine import RenderingEngine
    render_engine = RenderingEngine(work_dir=Path("data/work/renders"))
    config = RenderConfig()
    
    print("Starting render engine...")
    output = await render_engine.render(
        timeline=timeline,
        config=config,
        source_paths={asset_id: source_path},
        job_id="render_" + str(uuid.uuid4())
    )
    
    print(f"Render completed: {output}")

if __name__ == "__main__":
    asyncio.run(render_latest_edit_plan())

if __name__ == "__main__":
    asyncio.run(render_latest_edit_plan())

