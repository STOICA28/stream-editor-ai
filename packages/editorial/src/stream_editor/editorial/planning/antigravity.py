import json
import logging
import uuid
from typing import Any

from pydantic import BaseModel, Field

from stream_editor.contracts.editorial import CandidateSegmentContract
from stream_editor.contracts.edit_plan import ClipPriority, EditClipContract, EditPlanConfig, EditPlanContract
from stream_editor.contracts.editorial import StoryGraphContract
from stream_editor.api.config import settings

from stream_editor.models.antigravity_client import AntigravityClient, AIProviderUnavailable

from .interfaces import GlobalEditorialPlanner
from .optimizer import DeterministicDurationOptimizer


logger = logging.getLogger(__name__)

class EditSelection(BaseModel):
    candidate_id: str = Field(...)
    priority: str = Field(..., description="essential, high, medium, low, context_only")
    reason: str = Field(...)

class EditPlanResponse(BaseModel):
    selections: list[EditSelection] = Field(default_factory=list)

class AntigravityGlobalEditorialPlanner(GlobalEditorialPlanner):
    def __init__(self, client: AntigravityClient) -> None:
        self.client = client
        
    async def generate_plan(
        self,
        project_id: str,
        run_id: str,
        graph: StoryGraphContract,
        candidates: list[CandidateSegmentContract],
        config: EditPlanConfig,
        **kwargs: Any
    ) -> EditPlanContract:
        
        candidate_catalog = []
        for c in sorted(candidates, key=lambda x: x.start_time or 0.0):
            # Using basic scores if `c.score` is refactored, just handle it gracefully
            score_val = getattr(c, "score_importance", 0.0) or 0.0
            candidate_catalog.append({
                "id": str(c.id),
                "time": f"{c.start_time or 0.0:.1f} - {c.end_time or 0.0:.1f}",
                "duration": round(c.duration, 1),
                "summary": c.summary,
                "score": round(score_val, 2)
            })
            
        threads_summary = []
        for t in graph.threads:
            threads_summary.append({
                "id": str(t.id),
                "theme": getattr(t, "title", "Thread"),
                "importance": getattr(t, "importance", 1.0),
                "node_count": len(t.node_ids)
            })
            
        system_instruction = (
            "You are an expert YouTube Editor (StreamEditor AI). Your goal is to reconstruct the valuable "
            "experience of watching a livestream while removing dead air and preserving narrative comprehension. "
            "You are given a list of story threads and a catalog of available candidate clips. "
            "Select the best candidates to form a cohesive video. Assign a priority to each selected clip."
        )
        
        prompt = (
            "Analyze only the provided evidence.\n"
            "Return the required structured output.\n"
            "Do not modify repository files.\n"
            "Do not execute commands.\n"
            "Do not invoke tools.\n"
            "Do not change project state.\n\n"
            f"{system_instruction}\n\n"
            f"Target Duration: ~{config.target_duration_seconds} seconds\n"
            f"Planning Profile: {config.profile.value if hasattr(config.profile, 'value') else config.profile}\n\n"
            f"STORY THREADS:\n{json.dumps(threads_summary, indent=2)}\n\n"
            f"CANDIDATE CATALOG:\n{json.dumps(candidate_catalog, indent=2)}\n\n"
            "Build the EditPlan by selecting candidate IDs."
        )
        
        try:
            response = await self.client.generate_structured(prompt, EditPlanResponse)
            selections_data = response.selections
        except AIProviderUnavailable:
            logger.warning("Antigravity unavailable. Returning empty plan.")
            selections_data = []
        except Exception as e:
            logger.error(f"Failed to generate plan via Antigravity: {e}")
            selections_data = []
            
        selected_clips: list[EditClipContract] = []
        cand_map = {str(c.id): c for c in candidates}
        
        for sel in selections_data:
            cid = sel.candidate_id
            if not cid or cid not in cand_map:
                continue
                
            cand = cand_map[cid]
            priority_str = sel.priority
            try:
                priority = ClipPriority(priority_str)
            except ValueError:
                priority = ClipPriority.medium
                
            clip = EditClipContract(
                id=uuid.uuid4(),
                plan_id=uuid.UUID(run_id),
                source_start=cand.start_time or 0.0,
                source_end=cand.end_time or cand.duration,
                output_start=0.0,
                output_end=cand.duration,
                candidate_id=cid,
                selection_reason=sel.reason,
                priority=priority,
                confidence=0.8
            )
            selected_clips.append(clip)
            
        selected_clips.sort(key=lambda c: c.source_start)
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
