from typing import List, Dict, Any, Optional
import uuid
from .base import VisualUnderstandingProvider
from stream_editor.contracts.visual_analysis import (
    VisualRegionSchema,
    StreamLayoutSchema,
    VisualEventSchema,
    FocusTargetSchema,
    BoundingBox
)

class MockVisualProvider(VisualUnderstandingProvider):
    """
    Mock visual provider for testing without GPU/Cloud costs.
    It returns deterministic mock data based on the start_time.
    """
    def __init__(self, scenario: str = "A"):
        self.scenario = scenario

    async def analyze_window(
        self,
        project_id: str,
        asset_id: str,
        start_time: float,
        end_time: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        
        run_id = context.get("run_id", str(uuid.uuid4())) if context else str(uuid.uuid4())
        
        # Scenario A: Stable game + bottom-right facecam
        regions = []
        layouts = []
        events = []
        focus_targets = []
        
        # Always output a baseline layout
        layouts.append(StreamLayoutSchema(
            id=str(uuid.uuid4()),
            visual_analysis_run_id=run_id,
            project_id=project_id,
            start_time=start_time,
            end_time=end_time,
            layout_name="Gameplay + BottomRight Facecam",
            description="Standard gaming layout"
        ))
        
        # Always output a facecam region
        regions.append(VisualRegionSchema(
            id=str(uuid.uuid4()),
            visual_analysis_run_id=run_id,
            project_id=project_id,
            region_type="facecam",
            start_time=start_time,
            end_time=end_time,
            box=BoundingBox(x=0.8, y=0.8, width=0.2, height=0.2),
            confidence=0.95,
            detector="mock",
            track_id="FACE_TRACK_01"
        ))
        
        # Scenario C: Game event followed by face reaction
        if self.scenario == "C" or (start_time < 30 and end_time > 30):
            event_time = start_time + 1.0
            reaction_time = start_time + 2.5
            
            # The game event
            events.append(VisualEventSchema(
                id=str(uuid.uuid4()),
                visual_analysis_run_id=run_id,
                project_id=project_id,
                event_type="visual_event",
                start_time=event_time,
                end_time=event_time + 1.5,
                confidence=0.9,
                description="Sudden appearance of an object"
            ))
            
            # The reaction
            events.append(VisualEventSchema(
                id=str(uuid.uuid4()),
                visual_analysis_run_id=run_id,
                project_id=project_id,
                event_type="strong_face_reaction",
                start_time=reaction_time,
                end_time=reaction_time + 1.5,
                confidence=0.95,
                description="Streamer reacts to event"
            ))
            
            # Focus Targets sequence
            seq_id = str(uuid.uuid4())
            focus_targets.append(FocusTargetSchema(
                id=str(uuid.uuid4()),
                visual_analysis_run_id=run_id,
                project_id=project_id,
                start_time=event_time,
                end_time=reaction_time,
                target_type="screen_region",
                box=BoundingBox(x=0.4, y=0.4, width=0.2, height=0.2),
                priority="high",
                confidence=0.9,
                evidence_summary="Important game event",
                provenance="mock_pro",
                sequence_id=seq_id,
                sequence_order=1
            ))
            
            focus_targets.append(FocusTargetSchema(
                id=str(uuid.uuid4()),
                visual_analysis_run_id=run_id,
                project_id=project_id,
                start_time=reaction_time,
                end_time=end_time,
                target_type="facecam",
                box=BoundingBox(x=0.8, y=0.8, width=0.2, height=0.2),
                priority="high",
                confidence=0.95,
                evidence_summary="Streamer reaction",
                provenance="mock_pro",
                sequence_id=seq_id,
                sequence_order=2
            ))
            
        else:
            # Normal baseline focus
            focus_targets.append(FocusTargetSchema(
                id=str(uuid.uuid4()),
                visual_analysis_run_id=run_id,
                project_id=project_id,
                start_time=start_time,
                end_time=end_time,
                target_type="full_frame",
                priority="low",
                confidence=0.8,
                evidence_summary="Nothing specific",
                provenance="mock_flash"
            ))

        return {
            "regions": regions,
            "layouts": layouts,
            "events": events,
            "focus_targets": focus_targets
        }
