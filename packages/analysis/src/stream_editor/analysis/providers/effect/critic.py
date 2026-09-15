import json
import logging
from typing import List, Dict, Any
from google import genai
from google.genai import types

from stream_editor.contracts.effect_planning import EffectInstructionSchema
from .base import EffectPlanCritic

logger = logging.getLogger(__name__)

class GeminiEffectCritic(EffectPlanCritic):
    def __init__(self, api_key: str, default_model: str = "gemini-2.5-pro"):
        self.client = genai.Client(api_key=api_key)
        self.default_model = default_model

    async def critique(
        self,
        project_id: str,
        instructions: List[EffectInstructionSchema],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        if not instructions:
            return []

        model = context.get("model", self.default_model)
        
        inst_data = [i.model_dump(mode="json") for i in instructions]
        
        prompt = f"""
        You are an expert stream video editor acting as an Effect Critic.
        Review the following planned effect instructions for over-editing, jarring transitions, or conflicting effects.
        
        Instructions:
        {json.dumps(inst_data, indent=2)}
        
        Respond ONLY with a JSON array of issue objects. 
        Each issue must have: "issue" (string), "severity" (high/medium/low), "affected_effect_id" (string or null), "suggestion" (string).
        If there are no issues, return an empty array [].
        """

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            issues = json.loads(response.text)
            if not isinstance(issues, list):
                issues = [issues]
            return issues
        except Exception as e:
            logger.error(f"Failed to parse Gemini effect critic response: {e}")
            return []
