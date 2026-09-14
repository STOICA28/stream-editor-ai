from typing import Any

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
    regions: dict[str, LayoutRegion]

class ProbeResult(BaseModel):
    path: str
    media_info: MediaInfo
    raw_ffprobe: dict[str, Any]

class ProxyConfig(BaseModel):
    max_height: int = 720
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    container: str = "mp4"
    crf: int = 23
    fps_mode: str = "cap"  # "preserve" or "cap"
    fps_max: float = 30.0
    generator_version: str = "1.0.0"

    def get_signature(self, source_fingerprint: str) -> str:
        import hashlib
        import json
        data = self.model_dump()
        data["source_fingerprint"] = source_fingerprint
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

class AudioConfig(BaseModel):
    channels: int = 1
    sample_rate: int = 16000
    codec: str = "pcm_s16le"
    container: str = "wav"
    generator_version: str = "1.0.0"

    def get_signature(self, source_fingerprint: str) -> str:
        import hashlib
        import json
        data = self.model_dump()
        data["source_fingerprint"] = source_fingerprint
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
