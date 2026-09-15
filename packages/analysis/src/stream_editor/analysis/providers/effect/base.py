from typing import Protocol, List, Dict, Any, Optional
from stream_editor.contracts.effect_planning import EffectOpportunity, EffectInstructionSchema

class EffectPlanningProvider(Protocol):
    async def plan_effects(
        self,
        project_id: str,
        edit_plan_id: str,
        visual_analysis_run_id: Optional[str],
        opportunities: List[EffectOpportunity],
        context: Dict[str, Any]
    ) -> List[EffectInstructionSchema]:
        """
        Evaluate a list of deterministic effect opportunities and return specific effect instructions.
        """
        ...

class EffectPlanCritic(Protocol):
    async def critique(
        self,
        project_id: str,
        instructions: List[EffectInstructionSchema],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate a set of effect instructions and return a list of issues (overediting, conflicts).
        Returns a list of dicts like: {"issue": "...", "severity": "high", "affected_effect_id": "...", "suggestion": "..."}
        """
        ...
