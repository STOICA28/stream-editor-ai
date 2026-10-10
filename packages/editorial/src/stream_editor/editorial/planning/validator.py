from stream_editor.contracts.edit_plan import EditPlanContract


class EditPlanValidator:
    """
    Deterministic validator for EditPlans.
    Ensures that the planned clips:
    1. Have valid non-negative start times (source_start >= 0.0)
    2. Have positive durations (source_end > source_start)
    3. Do not exceed source original duration if provided (source_end <= original_duration)
    4. Are strictly chronological (source_start)
    5. Do not overlap in source time in sequential playback, which causes timeline duplication.
    """

    @classmethod
    def validate(cls, plan: EditPlanContract) -> list[str]:
        """
        Returns a list of error strings. Empty list means valid.
        Note: Output overlaps are already caught by the Pydantic model itself.
        """
        errors = []  # type: ignore[var-annotated]
        if not plan.clips:
            return errors
        
        # Check individual clip boundaries
        for clip in plan.clips:
            if clip.source_start < 0.0:
                errors.append(
                    f"Invalid boundary: Clip {clip.id} has negative source_start ({clip.source_start})"
                )
            if clip.source_end <= clip.source_start:
                errors.append(
                    f"Invalid duration: Clip {clip.id} has source_start ({clip.source_start}) >= source_end ({clip.source_end})"
                )
            if plan.original_duration > 0.0 and clip.source_end > (plan.original_duration + 0.001):
                errors.append(
                    f"Clip exceeds source duration: Clip {clip.id} ends at {clip.source_end}, "
                    f"exceeding original_duration {plan.original_duration} (by {clip.source_end - plan.original_duration:.3f}s)"
                )
        
        # Sort by output position
        sorted_clips = sorted(plan.clips, key=lambda c: c.output_start)
        
        for i in range(1, len(sorted_clips)):
            prev = sorted_clips[i - 1]
            curr = sorted_clips[i]
            
            # Source ordering must follow output ordering
            if curr.source_start < prev.source_start:
                errors.append(
                    f"Non-chronological order: Clip {curr.id} (source {curr.source_start}) "
                    f"appears after Clip {prev.id} (source {prev.source_start})"
                )
                
            # Prevent sequential source overlap (timeline duplication)
            if curr.source_start < (prev.source_end - 0.001):
                overlap = prev.source_end - curr.source_start
                errors.append(
                    f"Overlapping source selection (timeline duplication): Clip {prev.id} ends at {prev.source_end}, "
                    f"but Clip {curr.id} starts at {curr.source_start} (overlap: {overlap:.3f}s)"
                )
                
        return errors
