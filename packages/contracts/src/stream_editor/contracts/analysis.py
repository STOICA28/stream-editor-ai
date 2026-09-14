import hashlib
import json
from typing import Protocol

from pydantic import BaseModel


class TranscriptionConfig(BaseModel):
    model: str = "large-v3"
    language: str | None = None
    compute_type: str = "float16"
    batch_size: int = 16
    generator_version: str = "1.0.0"

    def get_signature(self, source_fingerprint: str) -> str:
        data = self.model_dump()
        data["source_fingerprint"] = source_fingerprint
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SceneConfig(BaseModel):
    threshold: float = 27.0
    min_scene_len: int = 15
    generator_version: str = "1.0.0"

    def get_signature(self, source_fingerprint: str) -> str:
        data = self.model_dump()
        data["source_fingerprint"] = source_fingerprint
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class AudioEventConfig(BaseModel):
    silence_thresh: float = -30.0 # dB
    silence_duration: float = 0.5 # seconds
    generator_version: str = "1.0.0"

    def get_signature(self, source_fingerprint: str) -> str:
        data = self.model_dump()
        data["source_fingerprint"] = source_fingerprint
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class TranscriptWord(BaseModel):
    word: str
    start: float
    end: float
    score: float | None = None

class TranscriptSegment(BaseModel):
    text: str
    start: float
    end: float
    words: list[TranscriptWord] = []
    speaker: str | None = None

class Scene(BaseModel):
    start_time: float
    end_time: float

class AudioEvent(BaseModel):
    event_type: str  # e.g., "silence" or "high_energy"
    start_time: float
    end_time: float

class TranscriptionProvider(Protocol):
    def transcribe(self, audio_path: str, config: TranscriptionConfig) -> list[TranscriptSegment]:
        ...

class SceneDetectionProvider(Protocol):
    def detect_scenes(self, video_path: str, config: SceneConfig) -> list[Scene]:
        ...

class AudioAnalysisProvider(Protocol):
    def analyze_audio(self, audio_path: str, config: AudioEventConfig) -> list[AudioEvent]:
        ...
