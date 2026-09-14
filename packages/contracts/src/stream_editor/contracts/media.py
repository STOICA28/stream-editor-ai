from typing import Any, Dict
from pydantic import BaseModel

class MediaInfo(BaseModel):
    duration_seconds: float
    width: int
    height: int
    fps: float
    video_codec: str
    audio_codec: str
    file_size_bytes: int
    format_name: str
    bit_rate: int

class LayoutRegion(BaseModel):
    x: float
    y: float
    width: float
    height: float

class StreamLayoutProfile(BaseModel):
    project_id: str
    regions: Dict[str, LayoutRegion]

class ProbeResult(BaseModel):
    path: str
    media_info: MediaInfo
    raw_ffprobe: dict[str, Any]
