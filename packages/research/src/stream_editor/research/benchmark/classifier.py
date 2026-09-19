"""Classification rules and Root-Cause Stage Tracer for editorial benchmark evaluation."""

from typing import Any, Optional

from stream_editor.contracts.benchmark import (
    ClipMatchClassification,
    AISegmentClassification,
    FalseNegativeReason,
    FalsePositiveReason,
    PipelineStage,
    RetainedInterval,
    StreamEditorTimelineSegment,
    EditorialFailure,
)


def classify_clip_match(
    human_interval: RetainedInterval,
    ai_segments: list[StreamEditorTimelineSegment],
    tolerance: float = 1.0,
) -> ClipMatchClassification:
    """Classify human retained interval against StreamEditor selections."""
    h_start = human_interval.source_start
    h_end = human_interval.source_end
    h_dur = max(0.001, h_end - h_start)

    total_overlap = 0.0
    for seg in ai_segments:
        ov_start = max(h_start, seg.source_start)
        ov_end = min(h_end, seg.source_end)
        if ov_end > ov_start:
            total_overlap += (ov_end - ov_start)

    # If overlap covers >= 70% of human interval or gap is within tolerance
    if total_overlap >= 0.70 * h_dur or (h_dur - total_overlap) <= tolerance:
        return ClipMatchClassification.MATCHED
    elif total_overlap > 0.0:
        return ClipMatchClassification.PARTIALLY_MATCHED
    else:
        return ClipMatchClassification.MISSED


def classify_ai_segment(
    ai_segment: StreamEditorTimelineSegment,
    human_intervals: list[RetainedInterval],
    tolerance: float = 1.0,
) -> AISegmentClassification:
    """Classify AI timeline segment against human reference intervals."""
    a_start = ai_segment.source_start
    a_end = ai_segment.source_end
    a_dur = max(0.001, a_end - a_start)

    total_overlap = 0.0
    for h in human_intervals:
        if h.is_external_insert:
            continue
        ov_start = max(a_start, h.source_start)
        ov_end = min(a_end, h.source_end)
        if ov_end > ov_start:
            total_overlap += (ov_end - ov_start)

    if total_overlap >= 0.70 * a_dur or (a_dur - total_overlap) <= tolerance:
        return AISegmentClassification.REFERENCE_SUPPORTED
    elif total_overlap > 0.0:
        return AISegmentClassification.PARTIALLY_SUPPORTED
    else:
        return AISegmentClassification.AI_ONLY


def trace_failure_root_cause(
    start_time: float,
    end_time: float,
    is_false_negative: bool,
    timeline_events: Optional[list[dict[str, Any]]] = None,
    candidate_segments: Optional[list[dict[str, Any]]] = None,
    story_nodes: Optional[list[dict[str, Any]]] = None,
    edit_clips: Optional[list[dict[str, Any]]] = None,
    visual_events: Optional[list[dict[str, Any]]] = None,
    effect_plans: Optional[list[dict[str, Any]]] = None,
    semantic_verdict: Optional[dict[str, Any]] = None,
) -> tuple[PipelineStage, str, dict[str, Any]]:
    """Trace the earliest upstream stage responsible for an editorial disagreement.
    
    Returns:
        (PipelineStage, failure_reason_string, evidence_trace_dict)
    """
    evidence: dict[str, Any] = {
        "start_time": start_time,
        "end_time": end_time,
        "is_false_negative": is_false_negative,
    }

    if is_false_negative:
        # HUMAN RETAINED, AI MISSED
        # 1. Check Stage M2 (Understanding / TimelineEvents)
        overlapping_events = []
        if timeline_events:
            for ev in timeline_events:
                e_start = float(ev.get("start_time", 0.0))
                e_end = float(ev.get("end_time", e_start + 0.1))
                if max(start_time, e_start) < min(end_time, e_end):
                    overlapping_events.append(ev)

        evidence["m2_events_count"] = len(overlapping_events)
        if not overlapping_events:
            return (
                PipelineStage.M2,
                FalseNegativeReason.MISSED_IMPORTANT_EVENT.value,
                {
                    **evidence,
                    "stage_culprit": "M2_UNDERSTANDING",
                    "explanation": "M2 Understanding pipeline produced no TimelineEvents or speech segments in this interval.",
                },
            )

        # 2. Check Stage M3 (Candidate Generation)
        overlapping_candidates = []
        if candidate_segments:
            for cand in candidate_segments:
                c_start = float(cand.get("start_time", cand.get("source_start", 0.0)))
                c_end = float(cand.get("end_time", cand.get("source_end", 0.0)))
                if max(start_time, c_start) < min(end_time, c_end):
                    overlapping_candidates.append(cand)

        evidence["m3_candidates_count"] = len(overlapping_candidates)
        if not overlapping_candidates:
            # Check if there were visual events that M3 failed to elevate
            v_events = [
                v for v in (visual_events or [])
                if max(start_time, float(v.get("start_time", 0.0))) < min(end_time, float(v.get("end_time", 0.0)))
            ]
            if v_events:
                return (
                    PipelineStage.M3,
                    FalseNegativeReason.MISSING_VISUAL_EVENT.value,
                    {
                        **evidence,
                        "stage_culprit": "M3_CANDIDATE_GENERATION",
                        "explanation": "Visual events were detected by M7/M2, but M3 did not elevate them into candidate segments.",
                    },
                )
            return (
                PipelineStage.M3,
                FalseNegativeReason.LOW_SCORE.value,
                {
                    **evidence,
                    "stage_culprit": "M3_CANDIDATE_GENERATION",
                    "explanation": "Timeline events were detected, but M3 candidate generation filtered out or scored this segment below threshold.",
                },
            )

        # 3. Check Stage M4 (Story Graph)
        overlapping_story_nodes = []
        if story_nodes:
            for node in story_nodes:
                n_start = float(node.get("source_start", node.get("start_time", 0.0)))
                n_end = float(node.get("source_end", node.get("end_time", 0.0)))
                if max(start_time, n_start) < min(end_time, n_end):
                    overlapping_story_nodes.append(node)

        evidence["m4_story_nodes_count"] = len(overlapping_story_nodes)
        if not overlapping_story_nodes:
            return (
                PipelineStage.M4,
                FalseNegativeReason.DEPENDENCY_FAILURE.value,
                {
                    **evidence,
                    "stage_culprit": "M4_STORY_GRAPH",
                    "explanation": "Candidate segment existed in M3, but was dropped or excluded during M4 Story Graph construction.",
                },
            )

        # 4. Check Stage M5 (Global Editorial Selection / EditPlan)
        # Node existed in Story Graph, but was pruned in EditPlan
        return (
            PipelineStage.M5,
            FalseNegativeReason.BUDGET_EXCLUSION.value,
            {
                **evidence,
                "stage_culprit": "M5_GLOBAL_EDITORIAL_SELECTION",
                "explanation": "Candidate was present in StoryGraph, but pruned by M5 knapsack/duration budget optimizer.",
            },
        )

    else:
        # AI RETAINED, HUMAN OMITTED (AI-ONLY)
        if semantic_verdict and semantic_verdict.get("is_valid_alternative"):
            return (
                PipelineStage.M5,
                FalsePositiveReason.VALID_ALTERNATIVE.value,
                {
                    **evidence,
                    "stage_culprit": "M5_ACCEPTABLE_ALTERNATIVE",
                    "explanation": "AI selected a high-quality segment that human editor omitted due to stylistic preference or time budget.",
                    "semantic_verdict": semantic_verdict,
                },
            )

        # Check for dead air or uninteresting gameplay
        if semantic_verdict and semantic_verdict.get("reason"):
            reason_str = str(semantic_verdict.get("reason")).upper()
            if "DEAD_AIR" in reason_str or "SILENCE" in reason_str:
                return (PipelineStage.M5, FalsePositiveReason.DEAD_AIR.value, evidence)
            if "REPETITIVE" in reason_str:
                return (PipelineStage.M5, FalsePositiveReason.REPETITIVE.value, evidence)

        return (
            PipelineStage.M5,
            FalsePositiveReason.LOW_INFORMATION.value,
            {
                **evidence,
                "stage_culprit": "M5_EDITORIAL_SELECTION",
                "explanation": "AI included a segment not retained by human editor that provides marginal narrative value.",
            },
        )
