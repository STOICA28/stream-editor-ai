from abc import ABC, abstractmethod
from typing import Any

from stream_editor.contracts.editorial import CandidateSegmentContract
from stream_editor.contracts.edit_plan import EditPlanConfig, EditPlanContract
from stream_editor.contracts.editorial import StoryGraphContract


class GlobalEditorialPlanner(ABC):
    """
    Core abstraction for planning the final edit.
    Takes the structured story graph and the raw candidates, and builds
    a rough cut (EditPlan) obeying the given configuration.
    """
    
    @abstractmethod
    def generate_plan(
        self,
        project_id: str,
        run_id: str,
        graph: StoryGraphContract,
        candidates: list[CandidateSegmentContract],
        config: EditPlanConfig,
        **kwargs: Any
    ) -> EditPlanContract:
        """
        Generate a global edit plan.
        """
        ...
