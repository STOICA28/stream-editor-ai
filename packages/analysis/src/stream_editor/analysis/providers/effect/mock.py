from typing import List, Dict, Any, Optional
import uuid
from stream_editor.contracts.effect_planning import (
    EffectOpportunity,
    EffectInstructionSchema,
    EffectType,
    EffectPriority,
    EffectReviewState,
    NormalizedBoundingBox,
    EffectTargetType
)
from .base import EffectPlanningProvider, EffectPlanCritic

class MockEffectPlanner(EffectPlanningProvider):
    def __init__(self, scenario: str = "default"):
        self.scenario = scenario
        
    async def plan_effects(
        self,
        project_id: str,
        edit_plan_id: str,
        visual_analysis_run_id: Optional[str],
        opportunities: List[EffectOpportunity],
        context: Dict[str, Any]
    ) -> List[EffectInstructionSchema]:
        
        run_id = context.get("run_id", str(uuid.uuid4()))
        instructions = []
        
        for opp in opportunities:
            # Deterministic mapping for testing
            effect_type = EffectType.NONE
            parameters = {}
            target_box = opp.target_box
            target_type = opp.target_type
            
            if self.scenario == "screen_to_face" and opp.target_type == EffectTargetType.SCREEN_REGION:
                effect_type = EffectType.ZOOM_REGION
                parameters = {"scale": 1.5, "transition_in": 0.2, "transition_out": 0.2}
            elif self.scenario == "screen_to_face" and opp.target_type == EffectTargetType.FACECAM:
                effect_type = EffectType.ZOOM_FACE
                parameters = {"scale": 1.3, "transition_in": 0.1, "transition_out": 0.3}
            elif self.scenario == "chat_to_face" and opp.target_type == EffectTargetType.CHAT:
                effect_type = EffectType.ZOOM_CHAT
                parameters = {"scale": 2.0}
            elif self.scenario == "no_effect":
                effect_type = EffectType.NONE
            elif self.scenario == "grayscale":
                effect_type = EffectType.GRAYSCALE
            elif self.scenario == "fullscreen_facecam" and opp.target_type == EffectTargetType.FACECAM:
                effect_type = EffectType.NONE # Don't zoom if already fullscreen
            elif opp.target_type == EffectTargetType.UNKNOWN:
                effect_type = EffectType.NONE
            
            if effect_type != EffectType.NONE:
                instructions.append(EffectInstructionSchema(
                    id=str(uuid.uuid4()),
                    effect_plan_run_id=run_id,
                    edit_clip_id=None,
                    source_start=opp.source_start,
                    source_end=opp.source_end,
                    output_start=None,
                    output_end=None,
                    effect_type=effect_type,
                    target_type=target_type,
                    target_box=target_box,
                    parameters=parameters,
                    confidence=0.95,
                    priority=EffectPriority.NORMAL,
                    reason=f"Mock decided on {effect_type} for {target_type}",
                    evidence_references=[opp.id],
                    provider="mock",
                    review_state=EffectReviewState.PROPOSED
                ))
        
        return instructions

class MockEffectCritic(EffectPlanCritic):
    async def critique(
        self,
        project_id: str,
        instructions: List[EffectInstructionSchema],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        
        issues = []
        # Check for overediting
        zooms = [i for i in instructions if i.effect_type in (EffectType.ZOOM_REGION, EffectType.ZOOM_FACE, EffectType.ZOOM_CHAT)]
        if len(zooms) > 10:
            issues.append({
                "issue": "Overediting detected",
                "severity": "high",
                "affected_effect_id": None,
                "suggestion": "Reduce the number of zoom effects in this sequence."
            })
            
        return issues
