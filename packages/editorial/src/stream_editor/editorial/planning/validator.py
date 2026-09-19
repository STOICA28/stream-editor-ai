from stream_editor.contracts.edit_plan import EditPlanContract


class EditPlanValidator:
    """
    Deterministic validator for EditPlans.
    Ensures that the planned clips are strictly chronological (source_start)
    and do not overlap in source time, unless explicitly intended (for advanced features).
    MVP: Strictly chronological, non-overlapping source.
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
        
        # Sort by output position
        sorted_clips = sorted(plan.clips, key=lambda c: c.output_start)
        
        for i in range(1, len(sorted_clips)):
            prev = sorted_clips[i - 1]
            curr = sorted_clips[i]
            
            # For MVP, source ordering must follow output ordering
            if curr.source_start < prev.source_start:
                errors.append(
                    f"Non-chronological order: Clip {curr.id} (source {curr.source_start}) "
                    f"appears after Clip {prev.id} (source {prev.source_start})"
                )
                
            # For MVP, source clips should not heavily overlap in source time
            # (If they do, they are redundant or duplicate)
            if curr.source_start < (prev.source_end - 0.5):
                errors.append(
                    f"Overlapping source selection: Clip {prev.id} ends at {prev.source_end}, "
                    f"but Clip {curr.id} starts at {curr.source_start}"
                )
                
        return errors
