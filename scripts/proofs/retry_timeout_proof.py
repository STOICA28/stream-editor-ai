
import sys
import uuid
import time
from stream_editor.worker.tasks.pipeline import probe_media_task

if __name__ == "__main__":
    job_id = "TIMEOUT_INJECT"
    project_id = str(uuid.uuid4())
    asset_id = str(uuid.uuid4())
    
    print("Dispatching probe_media_task with TIMEOUT_INJECT (RETRYABLE expected)...")
    res = probe_media_task.delay(project_id, asset_id, job_id)
    
    print("Task ID:", res.id)
    print("Check worker logs for retries.")

