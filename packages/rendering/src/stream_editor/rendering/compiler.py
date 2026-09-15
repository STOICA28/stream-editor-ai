import logging
from typing import List, Dict, Any, Optional
from stream_editor.contracts.rendering import CompiledTimeline, CompiledSegment, CompiledEffect
from stream_editor.contracts.edit_plan import EditClipContract
from stream_editor.contracts.effect_planning import EffectInstructionSchema

logger = logging.getLogger(__name__)

class TimelineCompiler:
    def __init__(self) -> None:
        pass

    def compile(
        self,
        project_id: str,
        render_job_id: str,
        clips: List[EditClipContract],
        effects: List[EffectInstructionSchema]
    ) -> CompiledTimeline:
        """
        Compiles an EditPlan and EffectPlan into a deterministic CompiledTimeline.
        Uses integer microseconds internally to avoid floating point drift across hundreds of cuts.
        """
        
        # Sort clips by their output_start if present, or just chronologically if they are ordered
        # M5 produces chronological clips. Let's assume they are already sorted by source_start
        # Wait, M6 allows human reordering? Let's sort by their natural order in the list.
        
        segments: List[CompiledSegment] = []
        current_output_us: int = 0
        
        for idx, clip in enumerate(clips):
            source_start_us = int(clip.source_start * 1_000_000)
            source_end_us = int(clip.source_end * 1_000_000)
            
            if source_start_us >= source_end_us:
                logger.warning(f"Clip {clip.id} has invalid duration (start >= end). Skipping.")
                continue
                
            duration_us = source_end_us - source_start_us
            
            output_start_us = current_output_us
            output_end_us = output_start_us + duration_us
            
            # Find effects that overlap with this clip's source time
            clip_effects = []
            for eff in effects:
                eff_source_start_us = int(eff.source_start * 1_000_000)
                eff_source_end_us = int(eff.source_end * 1_000_000)
                
                # Check overlap
                overlap_start = max(source_start_us, eff_source_start_us)
                overlap_end = min(source_end_us, eff_source_end_us)
                
                if overlap_start < overlap_end:
                    # Effect applies to this segment
                    # Calculate relative output times
                    eff_output_start_us = output_start_us + (overlap_start - source_start_us)
                    eff_output_end_us = output_start_us + (overlap_end - source_start_us)
                    
                    clip_effects.append(CompiledEffect(
                        effect_id=eff.id,
                        effect_type=eff.effect_type,
                        source_start=overlap_start / 1_000_000.0,
                        source_end=overlap_end / 1_000_000.0,
                        output_start=eff_output_start_us / 1_000_000.0,
                        output_end=eff_output_end_us / 1_000_000.0,
                        target_box=eff.target_box,
                        parameters=eff.parameters or {}
                    ))
            
            segments.append(CompiledSegment(
                segment_index=idx,
                source_asset_id="default",
                source_start=source_start_us / 1_000_000.0,
                source_end=source_end_us / 1_000_000.0,
                output_start=output_start_us / 1_000_000.0,
                output_end=output_end_us / 1_000_000.0,
                duration=duration_us / 1_000_000.0,
                effects=clip_effects
            ))
            
            current_output_us = output_end_us
            
        return CompiledTimeline(
            project_id=project_id,
            render_job_id=render_job_id,
            segments=segments,
            expected_duration=current_output_us / 1_000_000.0
        )
