from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from .effect_planning import EffectType, NormalizedBoundingBox

class RenderMode(str, Enum):
    PREVIEW = "preview"
    FINAL = "final"

class RenderConfig(BaseModel):
    mode: RenderMode = RenderMode.PREVIEW
    width: int = 1920
    height: int = 1080
    fps: float = 60.0
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    pixel_format: str = "yuv420p"
    crf: int = 23
    preset: str = "medium"
    audio_sample_rate: int = 48000
    container: str = "mp4"
    hw_accel: Optional[str] = None

class CompiledEffect(BaseModel):
    effect_id: str
    effect_type: EffectType
    source_start: float
    source_end: float
    output_start: float
    output_end: float
    target_box: Optional[NormalizedBoundingBox] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class CompiledSegment(BaseModel):
    """
    A single contiguous slice of source media with attached effects.
    Time representations here are in SECONDS for float, but internally the compiler 
    uses microseconds to avoid float drift during accumulation.
    """
    segment_index: int
    source_asset_id: str
    source_start: float
    source_end: float
    output_start: float
    output_end: float
    duration: float
    effects: List[CompiledEffect] = Field(default_factory=list)
    signature: Optional[str] = None # Filled by Cache

class CompiledTimeline(BaseModel):
    project_id: str
    render_job_id: str
    segments: List[CompiledSegment] = Field(default_factory=list)
    expected_duration: float

class RenderManifest(BaseModel):
    render_job_id: str
    source_assets: List[str]
    edit_plan: str
    effect_plan: Optional[str]
    renderer_version: str
    render_config: RenderConfig
    segments: List[CompiledSegment]
    expected_duration: float
    actual_duration: float
    output_hash: Optional[str] = None
