from enum import Enum
from uuid import UUID
from typing import Any, Optional
from pydantic import BaseModel

class FeedbackType(str, Enum):
    keep_override = "keep_override"
    cut_override = "cut_override"
    boundary_adjustment = "boundary_adjustment"
    effect_modification = "effect_modification"
    score_correction = "score_correction"

class FeedbackEvent(BaseModel):
    id: UUID
    project_id: str
    edit_plan_id: UUID
    clip_id: UUID
    feedback_type: FeedbackType
    original_value: dict[str, Any]
    modified_value: dict[str, Any]
    surrounding_context: dict[str, Any]
    reason: Optional[str]
    editorial_style_version: str
