from typing import List, Dict, Any
import uuid
from datetime import datetime

from stream_editor.contracts.research import (
    AlignmentBlockContract,
    ObservedEffectContract,
    ObservedEditorialDecisionContract,
    StyleProfileContract,
    EditorialDecisionType
)

class ObservationEngine:
    """
    Analyzes observed effects and decisions across multiple reference pairs
    to extract editing patterns and generate a StyleProfile.
    """
    
    def aggregate(self, decisions: List[ObservedEditorialDecisionContract], effects: List[ObservedEffectContract]) -> StyleProfileContract:
        # Calculate pacing (average duration of kept segments)
        kept_durations = [
            (d.edit_end - d.edit_start) 
            for d in decisions if d.decision_type == EditorialDecisionType.RETAINED 
            and d.edit_end is not None and d.edit_start is not None
        ]
        
        avg_pacing = sum(kept_durations) / len(kept_durations) if kept_durations else 0.0
        
        # Calculate effect frequencies
        effect_counts: Dict[str, int] = {}
        for e in effects:
            if not e.is_false_positive:
                effect_counts[e.effect_type] = effect_counts.get(e.effect_type, 0) + 1
                
        metrics = {
            "average_pacing_seconds": avg_pacing,
            "effect_frequencies": effect_counts,
            "retention_rate": 0.5 # Mocked for now
        }
        
        return StyleProfileContract(
            id=str(uuid.uuid4()),
            project_id="dummy-project",
            version=1,
            evidence_count=len(decisions),
            metrics=metrics,
            generated_at=datetime.utcnow()
        )
