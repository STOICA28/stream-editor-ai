from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from stream_editor.contracts.effect_planning import EffectType, EffectTargetType

class ResearchFindingType(str, Enum):
    OBSERVATION = "observation"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"

class ResearchFindingStatus(str, Enum):
    PENDING = "pending"
    NEEDS_MORE_DATA = "needs_more_data"
    APPROVED = "approved"
    REJECTED = "rejected"

class EditorialDecisionType(str, Enum):
    RETAINED = "retained"
    OMITTED = "omitted"
    SHORTENED = "shortened"
    CONTEXT_PRESERVED = "context_preserved"
    CONTEXT_REMOVED = "context_removed"
    EFFECT_APPLIED = "effect_applied"
    SPEED_CHANGED = "speed_changed"
    EXTERNAL_INSERT = "external_insert"
    UNKNOWN = "unknown"

class AlignmentMethod(str, Enum):
    AUDIO = "audio"
    TRANSCRIPT = "transcript"
    VISUAL = "visual"
    COMBINED = "combined"
    MANUAL = "manual"

class AlignmentBlockContract(BaseModel):
    id: str
    run_id: str
    source_start: float
    source_end: float
    edit_start: float
    edit_end: float
    audio_confidence: Optional[float] = None
    transcript_confidence: Optional[float] = None
    visual_confidence: Optional[float] = None
    combined_confidence: float
    speed_ratio: float
    method: AlignmentMethod
    is_manual_override: bool = False
    
class ObservedEditorialDecisionContract(BaseModel):
    id: str
    pair_id: str
    decision_type: EditorialDecisionType
    source_start: Optional[float] = None
    source_end: Optional[float] = None
    edit_start: Optional[float] = None
    edit_end: Optional[float] = None
    context_before: Optional[float] = None
    context_after: Optional[float] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)

class ObservedEffectContract(BaseModel):
    id: str
    pair_id: str
    alignment_block_id: Optional[str] = None
    effect_type: EffectType
    target: Optional[EffectTargetType] = None
    source_start: float
    source_end: float
    edit_start: float
    edit_end: float
    scale: Optional[float] = None
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    confidence: float
    detection_method: str
    is_manual_override: bool = False
    is_false_positive: bool = False

class ReferenceVideoPairContract(BaseModel):
    id: str
    project_id: str
    source_asset_id: str
    edited_asset_id: str
    analysis_status: str
    
class ReferenceProjectContract(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str

class StyleProfileContract(BaseModel):
    id: str
    project_id: str
    version: int
    evidence_count: int
    metrics: Dict[str, Any]
    generated_at: datetime
    
class ResearchFindingContract(BaseModel):
    id: str
    project_id: str
    finding_type: ResearchFindingType
    status: ResearchFindingStatus
    description: str
    evidence: Dict[str, Any]
    pair_id: Optional[str] = None
