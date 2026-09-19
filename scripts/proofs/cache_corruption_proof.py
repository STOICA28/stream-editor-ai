
import uuid
import time
from stream_editor.api.models.project import ProcessingJob, MediaAsset, Project
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime, UTC
from stream_editor.worker.tasks.pipeline import extract_audio_task
from stream_editor.contracts.media import AudioConfig
import os
import glob

if __name__ == "__main__":
    job_id = "CORRUPT_JOB_" + str(uuid.uuid4())
    project_id = "test-dupe-project"
    asset_id = "test-dupe-asset"
    
    # Assuming test-dupe-project already has audio from previous run.
    # Let's find the generated audio file and corrupt it.
    audio_dir = f"data/projects/{project_id}/audio"
    audio_files = glob.glob(f"{audio_dir}/*/*.wav")
    
    if not audio_files:
        print("No audio files found to corrupt.")
        exit(1)
        
    target_file = audio_files[0]
    print(f"Corrupting {target_file}...")
    with open(target_file, "wb") as f:
        f.write(b"THIS IS CORRUPT GARBAGE DATA INSTEAD OF A REAL WAV FILE" * 100)
    
    engine = create_engine("sqlite:///test.db")
    with Session(engine) as db:
        job = ProcessingJob(id=job_id, project_id=project_id, status="pending", current_stage="extract_audio", started_at=datetime.now(UTC))
        db.add(job)
        db.commit()

    print(f"Dispatching task {job_id}...")
    res = extract_audio_task.delay(project_id, asset_id, job_id, "test")
    print(f"Task ID: {res.id}")

