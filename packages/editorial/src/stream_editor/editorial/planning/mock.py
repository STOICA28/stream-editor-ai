import uuid
from typing import Any

from stream_editor.contracts.editorial import CandidateSegmentContract
from stream_editor.contracts.style import StyledCandidateAssessment
from stream_editor.contracts.edit_plan import ClipPriority, EditClipContract, EditPlanConfig, EditPlanContract
from stream_editor.contracts.editorial import StoryGraphContract

from .interfaces import GlobalEditorialPlanner
from .optimizer import DeterministicDurationOptimizer


class MockGlobalEditorialPlanner(GlobalEditorialPlanner):
    """
    Mock implementation that builds an EditPlan by greedily selecting the best scoring
    candidates until the target duration is reached.
    """
    
    def generate_plan(
        self,
        project_id: str,
        run_id: str,
        graph: StoryGraphContract,
        candidates: list[CandidateSegmentContract],
        config: EditPlanConfig,
        styled_candidates: list[StyledCandidateAssessment] | None = None,
        **kwargs: Any
    ) -> EditPlanContract:
        
        # Sort candidates by combined score, descending
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (c.score_importance or 0.0) + (c.score_story_value or 0.0),
            reverse=True
        )
        
        selected_clips: list[EditClipContract] = []
        
        for cand in sorted_candidates:
            # Map candidate to clip
            clip = EditClipContract(
                id=uuid.uuid4(),
                plan_id=uuid.UUID(run_id),
                source_start=cand.start_time,
                source_end=cand.end_time,
                output_start=0.0, # Will be repacked by optimizer
                output_end=cand.duration,
                candidate_id=str(cand.id),
                selection_reason="Mock top-K selection",
                priority=ClipPriority.high, # Give them high priority
                confidence=(cand.score_importance or 0.0) + (cand.score_story_value or 0.0)
            )
            selected_clips.append(clip)
            
        # Repack to make them chronological in source
        selected_clips.sort(key=lambda c: c.source_start)
        
        # Use optimizer to enforce duration and pack output times
        final_clips = DeterministicDurationOptimizer.optimize(selected_clips, config)
        
        original_dur = sum(c.duration for c in candidates) if candidates else 0.0
        selected_dur = sum(c.output_duration for c in final_clips)
        
        return EditPlanContract(
            id=uuid.uuid4(),
            project_id=project_id,
            run_id=uuid.UUID(run_id),
            version=1,
            status="proposed",
            original_duration=original_dur,
            selected_duration=selected_dur,
            compression_ratio=(selected_dur / original_dur) if original_dur > 0 else 1.0,
            clip_count=len(final_clips),
            locked=False,
            clips=final_clips
        )

