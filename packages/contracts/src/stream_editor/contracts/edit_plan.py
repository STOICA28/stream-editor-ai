from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, model_validator

from .editorial import NarrativeEdge
from .effects import Effect, validate_effect


class TransitionType(str, Enum):
    cut = "cut"
    crossfade = "crossfade"
    fade_to_black = "fade_to_black"

class EditClip(BaseModel):
    id: UUID
    source_asset_id: UUID
    source_start_seconds: float
    source_end_seconds: float
    output_position_seconds: float
    effects: list[Effect]
    narrative_node_ids: list[UUID]
    editorial_reason: str

class EditPlanVersion(BaseModel):
    version: int
    created_at: datetime
    model_provider: str
    model_name: str
    model_version: str
    prompt_version: str

class EditPlan(BaseModel):
    id: UUID
    project_id: str
    version: int
    clips: list[EditClip]
    transitions: list[dict[str, Any]]
    audio_operations: list[dict[str, Any]]
    provenance: EditPlanVersion
    status: str
    narrative_dependencies: list[NarrativeEdge]

    @model_validator(mode='after')
    def validate_plan(self) -> "EditPlan":
        if not self.clips:
            return self
        
        # total duration must be >0
        total_duration = max(c.output_position_seconds + (c.source_end_seconds - c.source_start_seconds) for c in self.clips)
        if total_duration <= 0:
            raise ValueError("Total duration must be > 0")
        
        # clips must not have overlapping output positions
        sorted_clips = sorted(self.clips, key=lambda c: c.output_position_seconds)
        for i in range(1, len(sorted_clips)):
            prev = sorted_clips[i-1]
            curr = sorted_clips[i]
            prev_end = prev.output_position_seconds + (prev.source_end_seconds - prev.source_start_seconds)
            if curr.output_position_seconds < prev_end:
                raise ValueError("Clips have overlapping output positions")
        
        # effect params must be valid
        for clip in self.clips:
            for effect in clip.effects:
                validate_effect(effect)
                
        return self
