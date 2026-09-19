
import uuid
import time
from stream_editor.api.models.project import ProcessingJob, MediaAsset, Project
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime, UTC
from stream_editor.worker.tasks.pipeline import extract_audio_task
import os

if __name__ == "__main__":
    job_id_1 = "DUPE_JOB_1_" + str(uuid.uuid4())
    job_id_2 = "DUPE_JOB_2_" + str(uuid.uuid4())
    project_id = "test-dupe-project"
    asset_id = "test-dupe-asset"
    
    media_info = {
        "duration_seconds": 2.0,
        "width": 1280,
        "height": 720,
        "fps": 30.0,
        "video_codec": "h264",
        "audio_codec": "aac",
        "file_size_bytes": 1024,
        "format_name": "mp4",
        "bit_rate": 1000
    }
    
    os.makedirs(f"data/projects/{project_id}/source", exist_ok=True)
    os.system(f"ffmpeg -f lavfi -i testsrc=duration=2:size=1280x720:rate=30 -f lavfi -i sine=frequency=1000:duration=2 -c:v libx264 -c:a aac -y data/projects/{project_id}/source/test.mp4")

    engine = create_engine("sqlite:///test.db")
    with Session(engine) as db:
        proj = db.query(Project).filter_by(id=project_id).first()
        if not proj:
            proj = Project(id=project_id, name="Test")
            db.add(proj)
        asset = db.query(MediaAsset).filter_by(id=asset_id).first()
        if not asset:
            asset = MediaAsset(id=asset_id, project_id=project_id, name="test.mp4", media_type="video", media_info=media_info)
            db.add(asset)
        
        job1 = ProcessingJob(id=job_id_1, project_id=project_id, status="pending", current_stage="extract_audio", started_at=datetime.now(UTC))
        job2 = ProcessingJob(id=job_id_2, project_id=project_id, status="pending", current_stage="extract_audio", started_at=datetime.now(UTC))
        db.add(job1)
        db.add(job2)
        db.commit()

    print(f"Dispatching task {job_id_1}...")
    res1 = extract_audio_task.delay(project_id, asset_id, job_id_1, "test")
    print(f"Task ID 1: {res1.id}")
    
    print(f"Dispatching task {job_id_2}...")
    res2 = extract_audio_task.delay(project_id, asset_id, job_id_2, "test")
    print(f"Task ID 2: {res2.id}")

