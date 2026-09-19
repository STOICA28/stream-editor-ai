"""Timeline interval reconstruction and harmonization for editorial evaluation."""

from typing import Any, Optional
import math

from stream_editor.contracts.benchmark import (
    RetainedInterval,
    HumanReferenceTimeline,
    StreamEditorTimelineSegment,
    StreamEditorTimeline,
)


def merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Sort and merge overlapping or adjacent intervals."""
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged: list[tuple[float, float]] = []
    current_start, current_end = sorted_intervals[0]

    for start, end in sorted_intervals[1:]:
        if start <= current_end + 1e-4:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end
    merged.append((current_start, current_end))
    return merged


def compute_interval_intersection(
    intervals_a: list[tuple[float, float]],
    intervals_b: list[tuple[float, float]],
    tolerance: float = 0.0,
) -> float:
    """Compute total duration of intersection between two sets of intervals.
    
    If tolerance > 0, interval boundaries in intervals_b are expanded by tolerance
    when testing for overlap with intervals_a.
    """
    merged_a = merge_intervals(intervals_a)
    
    # If tolerance is applied, expand B's intervals
    if tolerance > 0.0:
        expanded_b = [(max(0.0, s - tolerance), e + tolerance) for s, e in intervals_b]
        merged_b = merge_intervals(expanded_b)
    else:
        merged_b = merge_intervals(intervals_b)

    total_intersection = 0.0
    for a_start, a_end in merged_a:
        for b_start, b_end in merged_b:
            overlap_start = max(a_start, b_start)
            overlap_end = min(a_end, b_end)
            if overlap_end > overlap_start:
                total_intersection += (overlap_end - overlap_start)

    # Intersection cannot exceed the smaller total duration of A or tolerance-expanded B
    a_dur = sum(e - s for s, e in merged_a)
    return min(total_intersection, a_dur)


def compute_total_duration(intervals: list[tuple[float, float]]) -> float:
    """Compute total non-overlapping duration of intervals."""
    merged = merge_intervals(intervals)
    return sum(e - s for s, e in merged)


def build_human_reference_timeline(
    case_id: str,
    data: dict[str, Any] | list[dict[str, Any]],
    source_duration: float = 0.0,
    edit_duration: float = 0.0,
) -> HumanReferenceTimeline:
    """Build a HumanReferenceTimeline from ground truth fixtures or alignment data."""
    retained: list[RetainedInterval] = []
    removed: list[RetainedInterval] = []
    transformed: list[RetainedInterval] = []
    external_inserts: list[RetainedInterval] = []

    blocks: list[dict[str, Any]] = []
    if isinstance(data, dict):
        blocks = data.get("blocks", [])
        if not blocks and "retained_intervals" in data:
            blocks = data.get("retained_intervals", [])
    elif isinstance(data, list):
        blocks = data

    for idx, b in enumerate(blocks):
        s_start = float(b.get("source_start", 0.0))
        s_end = float(b.get("source_end", 0.0))
        e_start = float(b["edit_start"]) if b.get("edit_start") is not None else None
        e_end = float(b["edit_end"]) if b.get("edit_end") is not None else None
        speed = float(b.get("speed_ratio", 1.0))
        conf = float(b.get("combined_confidence") or b.get("confidence") or 1.0)
        
        is_trans = speed != 1.0 or b.get("is_transformed", False)
        is_ext = s_start < 0.0 or b.get("is_external_insert", False)
        
        interval = RetainedInterval(
            id=str(b.get("id", f"ref-{idx}")),
            source_start=max(0.0, s_start),
            source_end=max(0.0, s_end),
            edit_start=e_start,
            edit_end=e_end,
            confidence=conf,
            is_transformed=is_trans,
            is_external_insert=is_ext,
            transformation_notes=f"speed_ratio={speed}" if is_trans else None,
            ordering_index=idx,
            tags=b.get("tags", []),
        )

        if is_ext:
            external_inserts.append(interval)
        elif is_trans:
            transformed.append(interval)
            retained.append(interval)
        else:
            retained.append(interval)

    # Sort intervals by source_start
    retained.sort(key=lambda x: x.source_start)

    # Calculate total retained duration
    retained_intervals_tuples = [(i.source_start, i.source_end) for i in retained if not i.is_external_insert]
    total_retained = compute_total_duration(retained_intervals_tuples)

    # Calculate removed intervals (gaps between retained intervals up to source_duration)
    if source_duration > 0.0 and retained_intervals_tuples:
        merged_retained = merge_intervals(retained_intervals_tuples)
        current_cursor = 0.0
        rem_idx = 0
        for r_start, r_end in merged_retained:
            if r_start > current_cursor + 0.1:
                removed.append(
                    RetainedInterval(
                        id=f"rem-{rem_idx}",
                        source_start=current_cursor,
                        source_end=r_start,
                        confidence=1.0,
                        ordering_index=rem_idx,
                    )
                )
                rem_idx += 1
            current_cursor = max(current_cursor, r_end)
        if current_cursor < source_duration - 0.1:
            removed.append(
                RetainedInterval(
                    id=f"rem-{rem_idx}",
                    source_start=current_cursor,
                    source_end=source_duration,
                    confidence=1.0,
                    ordering_index=rem_idx,
                )
            )

    avg_conf = 1.0
    if retained:
        avg_conf = sum(i.confidence for i in retained) / len(retained)

    return HumanReferenceTimeline(
        case_id=case_id,
        retained_intervals=retained,
        removed_intervals=removed,
        transformed_intervals=transformed,
        external_inserts=external_inserts,
        total_retained_duration=total_retained,
        total_source_duration=source_duration,
        total_edit_duration=edit_duration,
        alignment_confidence_avg=avg_conf,
    )


def build_streameditor_timeline(
    project_id: str,
    edit_plan: Any,
    is_styled: bool = False,
    style_policy_id: Optional[str] = None,
) -> StreamEditorTimeline:
    """Build a StreamEditorTimeline from an EditPlanContract or dictionary."""
    plan_id = "unknown-plan"
    clips: list[Any] = []

    if hasattr(edit_plan, "id"):
        plan_id = str(edit_plan.id)
    elif isinstance(edit_plan, dict) and "id" in edit_plan:
        plan_id = str(edit_plan["id"])

    if hasattr(edit_plan, "clips"):
        clips = edit_plan.clips
    elif isinstance(edit_plan, dict) and "clips" in edit_plan:
        clips = edit_plan["clips"]

    segments: list[StreamEditorTimelineSegment] = []
    for idx, c in enumerate(clips):
        if hasattr(c, "source_start"):
            s_start = float(c.source_start)
            s_end = float(c.source_end)
            o_start = float(c.output_start)
            o_end = float(c.output_end)
            clip_id = str(c.id) if hasattr(c, "id") else f"clip-{idx}"
            cand_id = str(c.candidate_id) if getattr(c, "candidate_id", None) else None
            node_id = str(c.story_node_id) if getattr(c, "story_node_id", None) else None
            reason = getattr(c, "selection_reason", None)
            priority = getattr(c, "priority", "medium")
            effects = [e.model_dump() if hasattr(e, "model_dump") else e for e in getattr(c, "effects", [])]
        else:
            s_start = float(c.get("source_start", 0.0))
            s_end = float(c.get("source_end", 0.0))
            o_start = float(c.get("output_start", 0.0))
            o_end = float(c.get("output_end", 0.0))
            clip_id = str(c.get("id", f"clip-{idx}"))
            cand_id = str(c["candidate_id"]) if c.get("candidate_id") else None
            node_id = str(c["story_node_id"]) if c.get("story_node_id") else None
            reason = c.get("selection_reason")
            priority = c.get("priority", "medium")
            effects = c.get("effects", [])

        segment = StreamEditorTimelineSegment(
            id=f"seg-{idx}",
            source_start=s_start,
            source_end=s_end,
            output_start=o_start,
            output_end=o_end,
            clip_id=clip_id,
            candidate_id=cand_id,
            story_node_id=node_id,
            selection_reason=reason,
            priority=priority,
            effects=effects,
        )
        segments.append(segment)

    # Sort segments by source_start
    segments.sort(key=lambda x: x.source_start)
    seg_tuples = [(s.source_start, s.source_end) for s in segments]
    total_selected = compute_total_duration(seg_tuples)

    return StreamEditorTimeline(
        project_id=project_id,
        plan_id=plan_id,
        segments=segments,
        total_selected_duration=total_selected,
        clip_count=len(segments),
        is_styled=is_styled,
        style_policy_id=style_policy_id,
    )
