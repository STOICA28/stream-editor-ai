import json
import uuid
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from stream_editor.models.antigravity_client import AntigravityClient, AIProviderUnavailable

from stream_editor.contracts.effect_planning import (
    EffectOpportunity,
    EffectInstructionSchema,
    EffectType,
    EffectTargetType,
    EffectPriority
)
from .base import EffectPlanningProvider, EffectPlanCritic

logger = logging.getLogger(__name__)

class EffectDecisionSchema(BaseModel):
    effect_type: str = Field(..., description="The effect type, e.g. zoom_face, zoom_region, grayscale, none")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Effect parameters")
    confidence: float = Field(..., description="Confidence score 0.0 to 1.0")
    reason: str = Field(..., description="Reasoning for this effect decision")

class EffectPlanResponseSchema(BaseModel):
    decisions: List[EffectDecisionSchema] = Field(..., description="One decision per opportunity")

class IssueSchema(BaseModel):
    issue: str = Field(...)
    severity: str = Field(...)
    affected_effect_id: Optional[str] = Field(None)
    suggestion: str = Field(...)

class CriticResponseSchema(BaseModel):
    issues: List[IssueSchema] = Field(default_factory=list)

class AntigravityEffectPlanner(EffectPlanningProvider):
    def __init__(self, client: AntigravityClient):
        self.client = client

    async def plan_effects(
        self,
        project_id: str,
        edit_plan_id: str,
        visual_analysis_run_id: Optional[str],
        opportunities: List[EffectOpportunity],
        context: Dict[str, Any]
    ) -> List[EffectInstructionSchema]:
        """
        Uses Antigravity to plan effects based on deterministic opportunities.
        """
        if not opportunities:
            return []
            
        opps_data = [opp.model_dump() for opp in opportunities]
        prompt = f"""
        Analyze only the provided evidence.
        Return the required structured output.
        Do not modify repository files.
        Do not execute commands.
        Do not invoke tools.
        Do not change project state.

        Review the following effect opportunities and decide what visual or audio effect to apply, if any.
        Opportunities:
        {json.dumps(opps_data, indent=2)}
        
        Do not over-edit. Use 'none' if no effect is needed.
        """

        try:
            response = await self.client.generate_structured(prompt, EffectPlanResponseSchema)
        except AIProviderUnavailable:
            logger.warning("Antigravity unavailable. Returning no effects.")
            return []
        except Exception as e:
            logger.error(f"Failed to get Antigravity effect planning response: {e}")
            return []

        instructions: List[EffectInstructionSchema] = []
        run_id = context.get("run_id", str(uuid.uuid4()))
        
        for i, dec in enumerate(response.decisions):
            opp = opportunities[i] if i < len(opportunities) else opportunities[-1]
            
            effect_type_str = dec.effect_type.lower()
            try:
                eff_type = EffectType(effect_type_str)
            except ValueError:
                eff_type = EffectType.NONE
            
            inst = EffectInstructionSchema(
                id=str(uuid.uuid4()),
                effect_plan_run_id=run_id,
                source_start=opp.source_start,
                source_end=opp.source_end,
                effect_type=eff_type,
                target_type=opp.target_type,
                target_box=opp.target_box,
                parameters=dec.parameters,
                confidence=dec.confidence,
                priority=EffectPriority.NORMAL,
                reason=dec.reason,
                evidence_references=[opp.id],
                provider=f"antigravity ({self.client.model})"
            )
            
            if eff_type != EffectType.NONE:
                instructions.append(inst)
                
        return instructions


class AntigravityEffectCritic(EffectPlanCritic):
    def __init__(self, client: AntigravityClient):
        self.client = client

    async def critique(
        self,
        project_id: str,
        instructions: List[EffectInstructionSchema],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        if not instructions:
            return []

        inst_data = [i.model_dump(mode="json") for i in instructions]
        
        prompt = f"""
        Analyze only the provided evidence.
        Return the required structured output.
        Do not modify repository files.
        Do not execute commands.
        Do not invoke tools.
        Do not change project state.

        You are an expert stream video editor acting as an Effect Critic.
        Review the following planned effect instructions for over-editing, jarring transitions, or conflicting effects.
        
        Instructions:
        {json.dumps(inst_data, indent=2)}
        """

        try:
            response = await self.client.generate_structured(prompt, CriticResponseSchema)
            return [issue.model_dump() for issue in response.issues]
        except Exception as e:
            logger.error(f"Failed to get Antigravity effect critic response: {e}")
            return []
