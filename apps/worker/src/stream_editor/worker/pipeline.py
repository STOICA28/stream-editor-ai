from celery import chain
from .tasks.pipeline import (
    ingest_media_task, probe_media_task, create_proxy_task, extract_audio_task,
    transcribe_task, detect_scenes_task, generate_candidates_task, generate_edit_plan_task
)
from typing import Any

def run_pipeline(job_id: str, project_id: str, file_path: str) -> Any:
    pipeline = chain(
        ingest_media_task.s(project_id, file_path),
        probe_media_task.s(project_id),
        create_proxy_task.s(project_id),
        extract_audio_task.s(project_id),
        transcribe_task.s(project_id),
        detect_scenes_task.s(project_id),
        generate_candidates_task.s(project_id),
        generate_edit_plan_task.s(project_id)
    )
    return pipeline.apply_async()
