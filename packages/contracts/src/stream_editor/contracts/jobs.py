from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"

class JobStage(str, Enum):
    ingest = "ingest"
    probe_media = "probe_media"
    create_analysis_proxy = "create_analysis_proxy"
    extract_audio = "extract_audio"
    transcribe = "transcribe"
    detect_scenes = "detect_scenes"
    detect_visual_events = "detect_visual_events"
    analyze_audio_events = "analyze_audio_events"
    import_or_analyze_chat = "import_or_analyze_chat"
    generate_candidates = "generate_candidates"
    score_candidates = "score_candidates"
    build_story_graph = "build_story_graph"
    generate_edit_plan = "generate_edit_plan"
    render_preview = "render_preview"
    human_review = "human_review"
    render_final = "render_final"

class JobStepResult(BaseModel):
    stage: JobStage
    status: JobStatus
    started_at: datetime
    completed_at: datetime
    input_hash: Optional[str]
    output_hash: Optional[str]
    algorithm_version: str
    error_message: Optional[str]
    retry_count: int
    output_paths: List[str]
