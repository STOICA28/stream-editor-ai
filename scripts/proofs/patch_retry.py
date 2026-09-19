
with open("apps/worker/src/stream_editor/worker/tasks/pipeline.py", "r") as f:
    content = f.read()

content = content.replace("async with acquire_job_lease(db, ProcessingJob, job_id, mark_succeeded=False) as already_done:", """if job_id == "TIMEOUT_INJECT": raise TimeoutError("Simulated Network Timeout")
            async with acquire_job_lease(db, ProcessingJob, job_id, mark_succeeded=False) as already_done:""")

with open("apps/worker/src/stream_editor/worker/tasks/pipeline.py", "w") as f:
    f.write(content)

