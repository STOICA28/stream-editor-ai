from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator
from datetime import datetime

class BoundingBox(BaseModel):
    """
    Normalized bounding box. Origin is top-left.
    Coordinates and dimensions are in the range [0, 1].
    """
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    width: float = Field(..., gt=0.0, le=1.0)
    height: float = Field(..., gt=0.0, le=1.0)

    @model_validator(mode='before')
    def validate_bounds(cls, values):
        x, y, w, h = values.get('x'), values.get('y'), values.get('width'), values.get('height')
        if x is not None and w is not None and x + w > 1.0:
            raise ValueError("x + width must be <= 1.0")
        if y is not None and h is not None and y + h > 1.0:
            raise ValueError("y + height must be <= 1.0")
        return values

class VisualRegionSchema(BaseModel):
    id: str
    visual_analysis_run_id: str
    project_id: str
    
    region_type: str
    start_time: float
    end_time: float
    
    box: Optional[BoundingBox] = None
    
    confidence: float
    detector: str
    track_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class StreamLayoutSchema(BaseModel):
    id: str
    visual_analysis_run_id: str
    project_id: str
    
    start_time: float
    end_time: float
    
    layout_name: str
    description: Optional[str] = None

class VisualEventSchema(BaseModel):
    id: str
    visual_analysis_run_id: str
    project_id: str
    
    event_type: str
    start_time: float
    end_time: float
    
    confidence: float
    description: Optional[str] = None

class FocusTargetSchema(BaseModel):
    id: str
    visual_analysis_run_id: str
    project_id: str
    
    start_time: float
    end_time: float
    
    target_type: str
    
    box: Optional[BoundingBox] = None
    
    priority: Optional[str] = None
    confidence: float
    evidence_summary: Optional[str] = None
    provenance: str
    
    sequence_id: Optional[str] = None
    sequence_order: Optional[int] = None

class VisualAnalysisRunSchema(BaseModel):
    id: str
    project_id: str
    source_asset_id: str
    proxy_asset_id: Optional[str] = None
    
    provider: str
    configuration: Dict[str, Any]
    derivation_signature: str
    
    status: str
    error_message: Optional[str] = None
    
    flash_requests: int
    pro_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_latency_ms: int
    
    created_at: datetime
    completed_at: Optional[datetime] = None

class LayoutProfile(BaseModel):
    facecam_region: Optional[BoundingBox] = None
    chat_region: Optional[BoundingBox] = None
    main_content_region: Optional[BoundingBox] = None
