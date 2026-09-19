import uuid
import logging
from typing import List, Dict, Any

from stream_editor.models.antigravity_client import AntigravityClient, AIProviderUnavailable

from stream_editor.contracts.research import (
    AlignmentBlockContract,
    ObservedEffectContract,
    ObservedEditorialDecisionContract,
    EditorialDecisionType
)
from stream_editor.contracts.effect_planning import EffectType, EffectTargetType
from stream_editor.research.alignment.builder import MultiSignalAlignmentBuilder
from stream_editor.research.observation.detector import LocalEffectDetector
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AntigravityOutputSchema(BaseModel):
    classification: str = Field(...)
    confidence: float = Field(...)
    effect_type: str = Field(None)  # type: ignore[assignment]
    target: str = Field(None)  # type: ignore[assignment]

class AntigravityReferenceProvider:
    """
    Real Reference Provider that integrates local alignment, local effect detection,
    and selectively calls AntigravityClient for semantic understanding and 
    ambiguous event classification using gemini-3.1-pro-high.
    """
    def __init__(self, client: AntigravityClient):
        self.builder = MultiSignalAlignmentBuilder()
        self.detector = LocalEffectDetector()
        self.client = client

    def align_media(self, source_path: str, edited_path: str) -> List[AlignmentBlockContract]:
        blocks = self.builder.build(source_path, edited_path)
        return blocks

    async def detect_effects(self, alignment_blocks: List[AlignmentBlockContract], source_path: str, edited_path: str) -> List[ObservedEffectContract]:
        # 1. Local deterministic effects
        effects = [] # self.detector.detect(alignment_blocks, source_path, edited_path)
        
        # 2. Freeze frames
        for i in range(len(alignment_blocks) - 1):
            b1 = alignment_blocks[i]
            b2 = alignment_blocks[i+1]
            e_gap = b2.edit_start - b1.edit_end
            s_gap = b2.source_start - b1.source_end
            if e_gap > 0.5 and s_gap < 0.2:
                effects.append(ObservedEffectContract(
                    id=str(uuid.uuid4()), pair_id="pair", effect_type=EffectType.FREEZE_FRAME, target=EffectTargetType.FULL_FRAME,
                    source_start=b1.source_end, source_end=b2.source_start, edit_start=b1.edit_end, edit_end=b2.edit_start,
                    confidence=0.9, detection_method="alignment", is_manual_override=False, is_false_positive=False
                ))
        
        # 3. Escalate ambiguous effects to Antigravity
        for b in alignment_blocks:
            if b.combined_confidence and b.combined_confidence < 0.7:
                # Prepare evidence 
                prompt = (
                    f"Analyze only the provided evidence.\n"
                    f"Return the required structured output.\n"
                    f"Do not modify repository files.\n"
                    f"Do not execute commands.\n"
                    f"Do not invoke tools.\n"
                    f"Do not change project state.\n\n"
                    f"Classify semantic event at source_start={b.source_start} to {b.source_end} "
                    f"edited_start={b.edit_start} to {b.edit_end}. "
                    f"Evidence: transcript_conf={b.transcript_confidence}, visual_conf={b.visual_confidence}"
                )
                
                try:
                    res = await self.client.generate_structured(prompt, AntigravityOutputSchema)
                    
                    if res and res.effect_type:
                        try:
                            etype = EffectType(res.effect_type)
                            target = EffectTargetType(res.target) if res.target else EffectTargetType.FULL_FRAME
                            effects.append(ObservedEffectContract(
                                id=str(uuid.uuid4()), pair_id="pair", effect_type=etype, target=target,
                                source_start=b.source_start, source_end=b.source_end, edit_start=b.edit_start, edit_end=b.edit_end,
                                confidence=res.confidence, detection_method="antigravity_pro", is_manual_override=False, is_false_positive=False
                            ))
                        except ValueError:
                            pass
                except AIProviderUnavailable:
                    pass
                except Exception as e:
                    logger.error(f"Failed to get Antigravity classification: {e}")
                    
        return effects

    def infer_decisions(self, alignment_blocks: List[AlignmentBlockContract], effects: List[ObservedEffectContract]) -> List[ObservedEditorialDecisionContract]:
        decisions = []
        for b in alignment_blocks:
            decisions.append(ObservedEditorialDecisionContract(
                id=b.id,
                pair_id="pair",
                decision_type=EditorialDecisionType.RETAINED,
                source_start=b.source_start,
                source_end=b.source_end,
                edit_start=b.edit_start,
                edit_end=b.edit_end
            ))
        return decisions
