from typing import Optional, Any, Dict, List
from enum import Enum
from pydantic import BaseModel, Field

class EffectType(str, Enum):
    NONE = "none"
    ZOOM_REGION = "zoom_region"
    ZOOM_FACE = "zoom_face"
    ZOOM_CHAT = "zoom_chat"
    CROP_FOCUS = "crop_focus"
    GRAYSCALE = "grayscale"
    FREEZE_FRAME = "freeze_frame"
    SLOW_MOTION = "slow_motion"
    SPEED_UP = "speed_up"
    TEXT_EMPHASIS = "text_emphasis"
    HIGHLIGHT_REGION = "highlight_region"
    AUDIO_DUCK = "audio_duck"
    AUDIO_GAIN = "audio_gain"
    FADE = "fade"

class EffectTargetType(str, Enum):
    FULL_FRAME = "full_frame"
    FACECAM = "facecam"
    CHAT = "chat"
    SCREEN_REGION = "screen_region"
    TEXT_REGION = "text_region"
    CONTENT_REGION = "content_region"
    VISUAL_EVENT = "visual_event"
    UNKNOWN = "unknown"

class EffectPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class EffectReviewState(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"

class NormalizedBoundingBox(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    width: float = Field(..., ge=0.0, le=1.0)
    height: float = Field(..., ge=0.0, le=1.0)

class EffectOpportunity(BaseModel):
    """An opportunity for an effect identified by deterministic heuristics (e.g. strong reaction)."""
    id: str
    source_start: float
    source_end: float
    candidate_effect_types: List[EffectType]
    target_type: EffectTargetType
    target_box: Optional[NormalizedBoundingBox] = None
    confidence: float
    source_event_id: Optional[str] = None
    reason: str

class EffectInstructionSchema(BaseModel):
    id: str
    effect_plan_run_id: str
    edit_clip_id: Optional[str] = None
    
    source_start: float
    source_end: float
    output_start: Optional[float] = None
    output_end: Optional[float] = None
    
    effect_type: EffectType
    target_type: EffectTargetType
    
    target_box: Optional[NormalizedBoundingBox] = None
    
    parameters: Optional[Dict[str, Any]] = None
    
    confidence: float = Field(..., ge=0.0, le=1.0)
    priority: EffectPriority
    reason: Optional[str] = None
    evidence_references: Optional[List[str]] = None
    
    provider: str
    review_state: EffectReviewState = EffectReviewState.PROPOSED
