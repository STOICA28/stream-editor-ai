from typing import List, Optional
from stream_editor.contracts.research import (
    AlignmentBlockContract,
    ObservedEffectContract,
    ObservedEditorialDecisionContract,
    EditorialDecisionType
)
from stream_editor.contracts.effect_planning import EffectType, EffectTargetType
from packages.research.tests.synthetic_oracle.generator import SyntheticOracle

class MockReferenceProvider:
    """
    Simulates the pipeline by returning the Synthetic Oracle's ground truth.
    In a real implementation, this provider would call the aligners and Gemini.
    """
    def __init__(self) -> None:
        self.oracle = SyntheticOracle()
        self.data = self.oracle.generate_scenario_1()
        
    def align_media(self, source_asset_id: str, edited_asset_id: str) -> List[AlignmentBlockContract]:
        return [AlignmentBlockContract(**b) for b in self.data["blocks"]]
        
    def detect_effects(self, alignment_blocks: List[AlignmentBlockContract], source_asset_id: str, edited_asset_id: str) -> List[ObservedEffectContract]:
        effects = []
        for e in self.data["effects"]:
            effects.append(ObservedEffectContract(**e))
        return effects
        
    def infer_decisions(self, alignment_blocks: List[AlignmentBlockContract], effects: List[ObservedEffectContract]) -> List[ObservedEditorialDecisionContract]:
        # Simple inference: everything in alignment blocks is a KEEP decision
        # Gaps are CUT decisions
        decisions = []
        for b in alignment_blocks:
            decisions.append(ObservedEditorialDecisionContract(
                id=b.id,
                pair_id="dummy-pair-id",
                decision_type=EditorialDecisionType.RETAINED,
                source_start=b.source_start,
                source_end=b.source_end,
                edit_start=b.edit_start,
                edit_end=b.edit_end
            ))
        return decisions
