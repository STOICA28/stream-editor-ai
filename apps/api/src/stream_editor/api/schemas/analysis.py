from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    source_asset_id: Optional[str]
    event_type: str
    start_time: float
    end_time: float
    producer: str
    producer_version: str
    confidence: Optional[float]
    data: Optional[Dict[str, Any]]

class TranscriptWordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float]

class TranscriptSegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str]
    confidence: Optional[float]
    sequence: int
    words: List[TranscriptWordResponse] = []

class SceneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    source_asset_id: Optional[str]
    start_time: float
    end_time: float
    duration: float
    detector: str
    detector_config: Optional[Dict[str, Any]]
    confidence: Optional[float]
