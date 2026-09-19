from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class StyleSignal(BaseModel):
    name: str = Field(description="Name of the style signal (e.g., reaction_retention, zoom_duration)")
    stage: str = Field(description="Pipeline stage where this signal applies (M3, M5, M8)")
    direction: str = Field(description="increase, decrease, or match")
    strength: float = Field(ge=0.0, le=1.0, description="Raw strength of the signal from 0.0 to 1.0")
    confidence: float = Field(ge=0.0, le=1.0, description="Statistical confidence of the observation")
    sample_size: int = Field(description="N value (number of observations)")
    source_profile_metric: str = Field(description="Name of the source metric in the StyleProfile")
    source_finding_ids: List[str] = Field(default_factory=list, description="IDs of approved ResearchFindings")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Constraints/conditions for applying this signal")

class EditorialStylePolicyContract(BaseModel):
    id: str
    name: str
    description: str
    status: str
    source_reference_project_id: Optional[str] = None
    source_style_profile_id: Optional[str] = None
    source_style_profile_version: Optional[int] = None
    policy_version: int
    experimental: bool = False
    signals: List[StyleSignal] = Field(default_factory=list)
    created_at: datetime
    created_by: str

class StylePolicyVersionContract(EditorialStylePolicyContract):
    pass # Immutable snapshot

class StyleInfluence(BaseModel):
    candidate_id: Optional[str] = None
    dimension: str
    direction: str
    strength: float
    confidence: float
    source_metric: str
    source_finding: Optional[str] = None
    evidence_count: int

class StyledCandidateAssessment(BaseModel):
    candidate_id: str
    # Reference to base scores (kept immutable by application logic)
    base_scores: Dict[str, float]
    influences: List[StyleInfluence] = Field(default_factory=list)

class StyleApplicationConfig(BaseModel):
    style_policy_id: Optional[str] = None
    style_policy_version: Optional[int] = None
    enabled: bool = True
    experimental: bool = False
    influence_strength: str = Field(default="normal", description="off, subtle, normal, strong")

class StyleImpactMetric(BaseModel):
    name: str
    default_value: float
    styled_value: float
    unit: str

class StyleImpactReport(BaseModel):
    project_id: str
    style_policy_id: str
    metrics: List[StyleImpactMetric] = Field(default_factory=list)
    dry_run: bool = False

class StyleApplicationRunContract(BaseModel):
    id: str
    project_id: str
    style_policy_id: Optional[str] = None
    style_policy_version_id: Optional[str] = None
    style_application_config: Dict[str, Any] = Field(default_factory=dict)
    experimental: bool = False
    dry_run: bool = False
    
    input_candidate_run_id: Optional[str] = None
    input_story_graph_run_id: Optional[str] = None
    input_visual_analysis_run_id: Optional[str] = None
    
    output_edit_plan_run_id: Optional[str] = None
    output_effect_plan_run_id: Optional[str] = None
    
    signature: Optional[str] = None
    status: str = Field(default="pending", description="pending, running, completed, failed")
    
    created_at: datetime
    completed_at: Optional[datetime] = None

