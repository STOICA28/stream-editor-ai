from typing import Dict, Any, Optional, List
import json
from pydantic import BaseModel, Field
from stream_editor.models.antigravity_client import AntigravityClient

from stream_editor.contracts.visual_analysis import (
    VisualRegionSchema,
    StreamLayoutSchema,
    VisualEventSchema,
    FocusTargetSchema,
    BoundingBox
)
from stream_editor.analysis.providers.visual.base import VisualUnderstandingProvider

class VisualAnalysisResult(BaseModel):
    regions: List[VisualRegionSchema] = Field(default_factory=list)
    layouts: List[StreamLayoutSchema] = Field(default_factory=list)
    events: List[VisualEventSchema] = Field(default_factory=list)
    focus_targets: List[FocusTargetSchema] = Field(default_factory=list)

class AntigravityVisualUnderstandingProvider(VisualUnderstandingProvider):
    def __init__(self, client: AntigravityClient):
        self.client = client

    async def analyze_window(
        self,
        project_id: str,
        asset_id: str,
        start_time: float,
        end_time: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        prompt = f"Analyze visual window {start_time} to {end_time} for asset {asset_id}."
        if context:
            prompt += f"\nContext: {json.dumps(context)}"
            
        result = await self.client.generate_structured(prompt, VisualAnalysisResult)
        
        return {
            "regions": [r.model_dump() for r in result.regions],
            "layouts": [l.model_dump() for l in result.layouts],
            "events": [e.model_dump() for e in result.events],
            "focus_targets": [f.model_dump() for f in result.focus_targets]
        }
