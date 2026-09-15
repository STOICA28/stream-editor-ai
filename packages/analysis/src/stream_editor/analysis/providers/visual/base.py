from typing import Protocol, List, Dict, Any, Optional
from stream_editor.contracts.visual_analysis import (
    VisualRegionSchema,
    StreamLayoutSchema,
    VisualEventSchema,
    FocusTargetSchema,
    BoundingBox
)

class VisualUnderstandingProvider(Protocol):
    """
    Protocol for visual understanding providers (Mock, Gemini).
    """
    async def analyze_window(
        self,
        project_id: str,
        asset_id: str,
        start_time: float,
        end_time: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a temporal window of video.
        
        Returns:
            Dict containing:
            - regions: List[VisualRegionSchema]
            - layouts: List[StreamLayoutSchema]
            - events: List[VisualEventSchema]
            - focus_targets: List[FocusTargetSchema]
        """
        ...
