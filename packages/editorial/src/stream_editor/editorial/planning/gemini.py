import json
import logging
import uuid
from typing import Any

from google import genai
from google.genai import types

from stream_editor.contracts.editorial import CandidateSegmentContract
from stream_editor.contracts.edit_plan import ClipPriority, EditClipContract, EditPlanConfig, EditPlanContract
from stream_editor.contracts.editorial import StoryGraphContract
from stream_editor.api.config import settings

from .interfaces import GlobalEditorialPlanner
from .optimizer import DeterministicDurationOptimizer


logger = logging.getLogger(__name__)

class GeminiGlobalEditorialPlanner(GlobalEditorialPlanner):
    """
    Uses Gemini Pro to plan the final edit.
    Passes a compressed view of the StoryGraph and Candidates to the model,
    asking for a JSON list of candidate IDs to include, and their assigned priority.
    """
    
    def __init__(self) -> None:
        self.client = genai.Client()
        self.model_name = "gemini-2.5-pro" # M5 requires strong reasoning
        
    def generate_plan(
        self,
        project_id: str,
        run_id: str,
        graph: StoryGraphContract,
        candidates: list[CandidateSegmentContract],
        config: EditPlanConfig,
        **kwargs: Any
    ) -> EditPlanContract:
        
        # 1. Compress Context
        # We don't send raw transcripts. We send candidate summaries + scores.
        candidate_catalog = []
        for c in sorted(candidates, key=lambda x: x.start_time):
            score_val = c.score.total_score if c.score else 0.0
            candidate_catalog.append({
                "id": str(c.id),
                "time": f"{c.start_time:.1f} - {c.end_time:.1f}",
                "duration": round(c.duration, 1),
                "summary": c.summary,
                "score": round(score_val, 2)
            })
            
        threads_summary = []
        for t in graph.threads:
            threads_summary.append({
                "id": str(t.id),
                "theme": t.theme,
                "importance": t.importance,
                "node_count": len(t.node_ids)
            })
            
        # 2. Build Prompt
        system_instruction = (
            "You are an expert YouTube Editor (StreamEditor AI). Your goal is to reconstruct the valuable "
            "experience of watching a livestream while removing dead air and preserving narrative comprehension. "
            "You are given a list of story threads and a catalog of available candidate clips. "
            "Select the best candidates to form a cohesive video. Assign a priority to each selected clip.\n\n"
            "Respond ONLY with a JSON array of objects, each containing: "
            '{"candidate_id": "uuid", "priority": "essential|high|medium|low|context_only", "reason": "why"}'
        )
        
        prompt = (
            f"Target Duration: ~{config.target_duration_seconds} seconds\n"
            f"Planning Profile: {config.profile.value}\n\n"
            f"STORY THREADS:\n{json.dumps(threads_summary, indent=2)}\n\n"
            f"CANDIDATE CATALOG:\n{json.dumps(candidate_catalog, indent=2)}\n\n"
            "Build the EditPlan by selecting candidate IDs. Keep the target duration in mind. "
            "Output JSON array only."
        )
        
        logger.info(f"Generating plan with {self.model_name}, passing {len(candidates)} candidates.")
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.4,
                response_mime_type="application/json",
            )
        )
        
        try:
            selections = json.loads(response.text)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {response.text}")
            raise ValueError(f"LLM returned invalid JSON: {e}")
            
        # 3. Build Clips
        selected_clips: list[EditClipContract] = []
        cand_map = {str(c.id): c for c in candidates}
        
        for sel in selections:
            cid = sel.get("candidate_id")
            if not cid or cid not in cand_map:
                continue
                
            cand = cand_map[cid]
            priority_str = sel.get("priority", "medium")
            try:
                priority = ClipPriority(priority_str)
            except ValueError:
                priority = ClipPriority.medium
                
            clip = EditClipContract(
                id=uuid.uuid4(),
                plan_id=uuid.UUID(run_id),
                source_start=cand.start_time,
                source_end=cand.end_time,
                output_start=0.0,
                output_end=cand.duration,
                candidate_id=cid,
                selection_reason=sel.get("reason", ""),
                priority=priority,
                confidence=cand.score.total_score if cand.score else 0.5
            )
            selected_clips.append(clip)
            
        # 4. Enforce Chronological Source
        selected_clips.sort(key=lambda c: c.source_start)
        
        # 5. Optimize and Repack Duration
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
