
import uuid
import time
from stream_editor.api.models.project import ProcessingJob
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime, UTC
from stream_editor.worker.tasks.pipeline import probe_media_task

if __name__ == "__main__":
    job_id = "KILL_ME_JOB_" + str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    asset_id = str(uuid.uuid4())
    
    engine = create_engine("sqlite:///test.db")
    with Session(engine) as db:
        job = ProcessingJob(id=job_id, project_id=project_id, status="running", current_stage="probe_media", started_at=datetime.now(UTC))
        db.add(job)
        db.commit()

    print(f"Dispatching task {job_id}...")
    res = probe_media_task.delay(project_id, asset_id, job_id)
    print("Task ID:", res.id)

