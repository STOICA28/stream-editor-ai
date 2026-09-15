from uuid import uuid4

from stream_editor.contracts.edit_plan import ClipPriority, EditClipContract, EditPlanConfig


class DeterministicDurationOptimizer:
    """
    Trims an over-budget EditPlan deterministically by removing the lowest priority clips
    until the plan fits within target_duration + tolerance.
    """
    
    # Pruning order from first to prune to last to prune
    PRUNE_ORDER = [
        ClipPriority.context_only,
        ClipPriority.low,
        ClipPriority.medium,
        ClipPriority.high,
    ]

    @classmethod
    def optimize(
        cls,
        clips: list[EditClipContract],
        config: EditPlanConfig
    ) -> list[EditClipContract]:
        """
        Returns a new list of clips that fits the duration constraint,
        recalculating output times to close any gaps left by pruned clips.
        """
        if not clips:
            return clips
            
        max_duration = config.target_duration_seconds + config.tolerance_seconds
        
        # Sort clips purely by output_start
        current_clips = sorted(clips, key=lambda c: c.output_start)
        
        # Total duration is just sum of (output_end - output_start) of all clips 
        # (Assuming no gaps in MVP rough cut, or just use the sum directly)
        total_dur = sum(c.output_duration for c in current_clips)
        
        if total_dur <= max_duration:
            return cls._repack_output_times(current_clips)
            
        # We need to prune.
        for priority_to_prune in cls.PRUNE_ORDER:
            # Iteratively remove the lowest confidence clip of this priority
            # until we are under budget, or run out of clips of this priority.
            while total_dur > max_duration:
                # Find all clips of this priority that are NOT locked
                candidates = [c for c in current_clips if c.priority == priority_to_prune and not c.locked]
                if not candidates:
                    break # No more clips of this priority to prune
                    
                # Pick the one with the lowest confidence (or random/first if None)
                # Sort by confidence ascending (None counts as 0 for pruning purposes)
                candidates.sort(key=lambda c: c.confidence if c.confidence is not None else 0.0)
                
                victim = candidates[0]
                current_clips.remove(victim)
                total_dur -= victim.output_duration
                
            if total_dur <= max_duration:
                break
                
        # Repack the output times so there are no gaps
        return cls._repack_output_times(current_clips)

    @staticmethod
    def _repack_output_times(clips: list[EditClipContract]) -> list[EditClipContract]:
        """
        Recalculates output_start and output_end so clips play consecutively starting from 0.0
        """
        repacked = []
        current_time = 0.0
        for clip in clips:
            dur = clip.output_duration
            
            # create a new clip with adjusted output times
            new_clip = clip.model_copy()
            new_clip.output_start = current_time
            new_clip.output_end = current_time + dur
            
            repacked.append(new_clip)
            current_time += dur
            
        return repacked
