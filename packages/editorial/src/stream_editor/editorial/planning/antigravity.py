import json
import asyncio
import logging
import uuid
from typing import Any

from pydantic import BaseModel, Field

from stream_editor.contracts.editorial import CandidateSegmentContract
from stream_editor.contracts.edit_plan import ClipPriority, EditClipContract, EditPlanConfig, EditPlanContract
from stream_editor.contracts.editorial import StoryGraphContract
from stream_editor.contracts.style import StyledCandidateAssessment
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
        
        style_map = {}
        if styled_candidates:
            style_map = {sc.candidate_id: sc for sc in styled_candidates}
            
        candidate_catalog = []
        for c in sorted(candidates, key=lambda x: x.start_time or 0.0):
            # Using basic scores if `c.score` is refactored, just handle it gracefully
            score_val = getattr(c, "score_importance", 0.0) or 0.0
            
            # Apply StylePolicy overrides or adjustments
            sc = style_map.get(str(c.id))
            style_notes = []
            if sc:
                for inf in sc.influences:
                    if inf.override_action == "FORCE_KEEP":  # type: ignore[attr-defined]
                        style_notes.append("STYLE_POLICY_MANDATES_KEEP")
                    elif inf.override_action == "FORCE_CUT":  # type: ignore[attr-defined]
                        style_notes.append("STYLE_POLICY_MANDATES_CUT")
                    score_val += inf.adjustment  # type: ignore[attr-defined]
                    
            item = {
                "id": str(c.id),
                "time": f"{c.start_time or 0.0:.1f} - {c.end_time or 0.0:.1f}",
                "duration": round(c.duration, 1),
                "summary": c.summary,
                "score": round(score_val, 2)
            }
            if style_notes:
                item["style_policy_overrides"] = style_notes
                
            candidate_catalog.append(item)
            
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
            f"PRECEDENCE RULES:\n"
            f"1. Technical Invariants (Do not select clips outside the original video length)\n"
            f"2. Human Locks (If a user explicitly locked a clip, you MUST KEEP IT)\n"
            f"3. Canonical Rules (No dead air, no audio feedback)\n"
            f"4. Project Preferences (e.g. Target Duration)\n"
            f"5. StylePolicy (STYLE_POLICY_MANDATES_KEEP or STYLE_POLICY_MANDATES_CUT in Candidate Catalog)\n\n"
            f"Target Duration: ~{config.target_duration_seconds} seconds\n"
            f"Planning Profile: {config.profile.value if hasattr(config.profile, 'value') else config.profile}\n\n"
            f"STORY THREADS:\n{json.dumps(threads_summary, indent=2)}\n\n"
            f"CANDIDATE CATALOG:\n{json.dumps(candidate_catalog, indent=2)}\n\n"
            "Build the EditPlan by selecting candidate IDs."
        )
        
        try:
            response = asyncio.run(self.client.generate_structured(prompt, EditPlanResponse))
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

