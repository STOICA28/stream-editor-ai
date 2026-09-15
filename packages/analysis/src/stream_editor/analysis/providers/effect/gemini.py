import json
import uuid
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from stream_editor.contracts.effect_planning import (
    EffectOpportunity,
    EffectInstructionSchema,
    EffectType,
    EffectTargetType,
    EffectPriority,
    EffectReviewState
)
from .base import EffectPlanningProvider

logger = logging.getLogger(__name__)

class GeminiEffectPlanner(EffectPlanningProvider):
    def __init__(self, api_key: str, default_model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.default_model = default_model

    async def plan_effects(
        self,
        project_id: str,
        edit_plan_id: str,
        visual_analysis_run_id: Optional[str],
        opportunities: List[EffectOpportunity],
        context: Dict[str, Any]
    ) -> List[EffectInstructionSchema]:
        """
        Uses Gemini to plan effects based on deterministic opportunities.
        """
        if not opportunities:
            return []

        # Choose model: flash by default, pro if escalated in config
        model = context.get("model", self.default_model)
        
        # Build prompt
        opps_data = [opp.model_dump() for opp in opportunities]
        prompt = f"""
        You are an expert stream video editor.
        Review the following effect opportunities and decide what visual or audio effect to apply, if any.
        Opportunities:
        {json.dumps(opps_data, indent=2)}
        
        Respond ONLY with a JSON array of effect decisions matching the required schema.
        Do not over-edit. Use 'none' if no effect is needed.
        """

        # Structured output schema matching EffectInstructionSchema loosely
        # We use a simpler schema for the LLM to output, then map it.
        # For this preflight implementation, we'll request a JSON array of dicts.
        
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                # Ideally we pass response_schema here, but for simplicity of this preflight we trust the prompt
                temperature=0.2,
            )
        )
        
        instructions: List[EffectInstructionSchema] = []
        try:
            decisions = json.loads(response.text)
            if not isinstance(decisions, list):
                decisions = [decisions]
                
            run_id = context.get("run_id", str(uuid.uuid4()))
            
            for i, dec in enumerate(decisions):
                opp = opportunities[i] if i < len(opportunities) else opportunities[-1]
                
                effect_type_str = dec.get("effect_type", "none").lower()
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
                    parameters=dec.get("parameters", {}),
                    confidence=float(dec.get("confidence", 0.8)),
                    priority=EffectPriority.NORMAL,
                    reason=dec.get("reason", "Gemini decision"),
                    evidence_references=[opp.id],
                    provider=f"gemini ({model})"
                )
                
                if eff_type != EffectType.NONE:
                    instructions.append(inst)
                    
        except Exception as e:
            logger.error(f"Failed to parse Gemini effect planning response: {e}")
            # Fallback to empty if parse fails, or raise.
            
        return instructions
