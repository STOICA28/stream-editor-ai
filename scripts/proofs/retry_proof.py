
import sys
import uuid
import time
from stream_editor.worker.tasks.pipeline import probe_media_task

if __name__ == "__main__":
    job_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    # asset_id not existing -> should cause a failure when pulling from db
    bad_asset_id = str(uuid.uuid4())
    
    print("Dispatching probe_media_task with nonexistent asset (NON-RETRYABLE expected)...")
    res = probe_media_task.delay(project_id, bad_asset_id, job_id)
    
    # Wait for completion
    try:
        out = res.get(timeout=5)
        print("Result:", out)
    except Exception as e:
        print("Task raised exception:", type(e), e)
    
    print("Done.")

