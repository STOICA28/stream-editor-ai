from enum import Enum
from uuid import UUID
from typing import Any, List
from pydantic import BaseModel, Field

class TimelineEventType(str, Enum):
    speech = "speech"
    silence = "silence"
    laughter = "laughter"
    shout = "shout"
    scene_change = "scene_change"
    face_reaction = "face_reaction"
    chat_message = "chat_message"
    chat_read = "chat_read"
    visual_event = "visual_event"
    game_event = "game_event"
    music = "music"
    emotion = "emotion"
    topic_change = "topic_change"
    callback = "callback"
    reference = "reference"

class TimelineEvent(BaseModel):
    id: UUID
    project_id: str
    source: str
    event_type: TimelineEventType
    start_seconds: float
    end_seconds: float
    confidence: float = Field(ge=0.0, le=1.0)
    structured_data: dict[str, Any]
    producer: str
    producer_version: str

class WordTimestamp(BaseModel):
    word: str
    start_seconds: float
    end_seconds: float
    confidence: float = Field(ge=0.0, le=1.0)

class TranscriptSegment(BaseModel):
    id: UUID
    project_id: str
    job_id: str
    start_seconds: float
    end_seconds: float
    text: str
    speaker: str
    confidence: float = Field(ge=0.0, le=1.0)
    word_timestamps: List[WordTimestamp]

class Scene(BaseModel):
    id: UUID
    project_id: str
    index: int
    start_seconds: float
    end_seconds: float
    scene_type: str
    key_frame_path: str
