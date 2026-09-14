from typing import Any

from pydantic import BaseModel, ConfigDict


class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    source_asset_id: str | None
    event_type: str
    start_time: float
    end_time: float
    producer: str
    producer_version: str
    confidence: float | None
    data: dict[str, Any] | None

class TranscriptWordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    start_time: float
    end_time: float
    text: str
    confidence: float | None

class TranscriptSegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    start_time: float
    end_time: float
    text: str
    speaker: str | None
    confidence: float | None
    sequence: int
    words: list[TranscriptWordResponse] = []

class SceneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    source_asset_id: str | None
    start_time: float
    end_time: float
    duration: float
    detector: str
    detector_config: dict[str, Any] | None
    confidence: float | None
