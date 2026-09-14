from enum import Enum
from pathlib import Path

class StorageCategory(str, Enum):
    source = "source"
    proxies = "proxies"
    audio = "audio"
    transcripts = "transcripts"
    frames = "frames"
    analysis = "analysis"
    previews = "previews"
    renders = "renders"

def get_proxy_path(project_id: str, filename: str) -> str:
    return f"{project_id}/{StorageCategory.proxies.value}/{filename}"

def get_audio_path(project_id: str, filename: str) -> str:
    return f"{project_id}/{StorageCategory.audio.value}/{filename}"

def get_transcript_path(project_id: str, filename: str) -> str:
    return f"{project_id}/{StorageCategory.transcripts.value}/{filename}"

def get_render_path(project_id: str, filename: str) -> str:
    return f"{project_id}/{StorageCategory.renders.value}/{filename}"
