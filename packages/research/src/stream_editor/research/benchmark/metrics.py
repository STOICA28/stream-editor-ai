"""Deterministic metrics calculation for editorial benchmark evaluation."""

from typing import Any, Optional
import math

from stream_editor.contracts.benchmark import (
    SelectionOverlapMetrics,
    QuantileStats,
    ContextMetrics,
    NarrativeMetrics,
    PacingMetrics,
    EffectMetrics,
    EffectComparisonRecord,
    EffectAgreementCategory,
    RetainedInterval,
    StreamEditorTimelineSegment,
)
from .timeline import (
    compute_interval_intersection,
    compute_total_duration,
)


def calculate_quantiles(values: list[float]) -> QuantileStats:
    """Calculate p10, p25, median (p50), p75, p90, mean, and std for a list of values."""
    if not values:
        return QuantileStats()

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def _percentile(p: float) -> float:
        if n == 1:
            return sorted_vals[0]
        k = (n - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return d0 + d1

    mean_val = sum(sorted_vals) / n
    variance = sum((x - mean_val) ** 2 for x in sorted_vals) / n
    std_val = math.sqrt(variance)

    return QuantileStats(
        p10=round(_percentile(0.10), 4),
        p25=round(_percentile(0.25), 4),
        median=round(_percentile(0.50), 4),
        p75=round(_percentile(0.75), 4),
        p90=round(_percentile(0.90), 4),
        mean=round(mean_val, 4),
        std=round(std_val, 4),
    )


def calculate_overlap_metrics(
    ai_intervals: list[tuple[float, float]],
    human_intervals: list[tuple[float, float]],
    tolerance_seconds: float = 1.0,
) -> SelectionOverlapMetrics:
    """Calculate precision, recall, and F1 at a specific boundary tolerance."""
    ai_total = compute_total_duration(ai_intervals)
    human_total = compute_total_duration(human_intervals)
    intersection = compute_interval_intersection(
        ai_intervals, human_intervals, tolerance=tolerance_seconds
    )

    precision = (intersection / ai_total) if ai_total > 0.0 else 0.0
    recall = (intersection / human_total) if human_total > 0.0 else 0.0
    f1 = (
        (2.0 * precision * recall / (precision + recall))
        if (precision + recall) > 0.0
        else 0.0
    )

    return SelectionOverlapMetrics(
        tolerance_seconds=tolerance_seconds,
        precision=round(min(1.0, precision), 4),
        recall=round(min(1.0, recall), 4),
        f1=round(min(1.0, f1), 4),
        intersection_duration=round(intersection, 4),
        human_retained_duration=round(human_total, 4),
        ai_retained_duration=round(ai_total, 4),
        sample_count=len(human_intervals),
    )


def calculate_context_metrics(
    ai_segments: list[StreamEditorTimelineSegment],
    human_intervals: list[RetainedInterval],
    tolerance: float = 1.0,
) -> ContextMetrics:
    """Calculate pre- and post-context discrepancies between AI segments and Human intervals."""
    pre_diffs: list[float] = []
    post_diffs: list[float] = []

    too_short = 0
    too_long = 0
    good_match = 0

    for human in human_intervals:
        if human.is_external_insert:
            continue
        # Find best overlapping AI segment
        best_overlap = 0.0
        best_seg: Optional[StreamEditorTimelineSegment] = None
        for seg in ai_segments:
            ov = max(
                0.0,
                min(human.source_end, seg.source_end)
                - max(human.source_start, seg.source_start),
            )
            if ov > best_overlap:
                best_overlap = ov
                best_seg = seg

        if best_seg is not None and best_overlap > 0.1:
            # Pre-context difference: ai.source_start - human.source_start
            # Positive means AI starts later (missing setup)
            # Negative means AI starts earlier (more setup)
            pre_diff = best_seg.source_start - human.source_start
            # Post-context difference: ai.source_end - human.source_end
            # Positive means AI ends later (more lingering outro)
            # Negative means AI cuts earlier (missing payoff/punchline)
            post_diff = best_seg.source_end - human.source_end

            pre_diffs.append(pre_diff)
            post_diffs.append(post_diff)

            # Classify context adequacy
            if pre_diff > tolerance or post_diff < -tolerance:
                too_short += 1
            elif pre_diff < -2.0 * tolerance or post_diff > 2.0 * tolerance:
                too_long += 1
            else:
                good_match += 1

    return ContextMetrics(
        pre_context_diff_quantiles=calculate_quantiles(pre_diffs),
        post_context_diff_quantiles=calculate_quantiles(post_diffs),
        context_too_short_count=too_short,
        context_too_long_count=too_long,
        good_context_match_count=good_match,
        sample_count=len(pre_diffs),
    )


def calculate_narrative_metrics(
    ai_segments: list[StreamEditorTimelineSegment],
    human_intervals: list[RetainedInterval],
    story_nodes: Optional[list[dict[str, Any]]] = None,
) -> NarrativeMetrics:
    """Calculate setup/payoff completeness, callback retention, and thread coverage."""
    setup_payoff_total = 0
    setup_payoff_intact = 0
    callback_total = 0
    callback_retained = 0

    ai_intervals = [(s.source_start, s.source_end) for s in ai_segments]
    human_tuples = [(h.source_start, h.source_end) for h in human_intervals if not h.is_external_insert]

    ai_threads: set[str] = set()
    human_threads: set[str] = set()
    thread_durations: dict[str, float] = {}

    for s in ai_segments:
        if s.narrative_thread_id:
            ai_threads.add(s.narrative_thread_id)
            thread_durations[s.narrative_thread_id] = thread_durations.get(
                s.narrative_thread_id, 0.0
            ) + (s.source_end - s.source_start)

    if story_nodes:
        # Check node relationships
        for node in story_nodes:
            n_start = float(node.get("source_start", 0.0))
            n_end = float(node.get("source_end", 0.0))
            thread_id = node.get("thread_id") or node.get("story_thread")
            is_setup = node.get("is_setup", False) or node.get("type") == "setup"
            payoff_node_id = node.get("payoff_node_id") or node.get("paired_payoff_id")
            is_callback = node.get("is_callback", False) or "callback" in node.get("tags", [])

            # Check if human retained this node
            h_kept = compute_interval_intersection([(n_start, n_end)], human_tuples) > 0.5 * (n_end - n_start)
            ai_kept = compute_interval_intersection([(n_start, n_end)], ai_intervals) > 0.5 * (n_end - n_start)

            if thread_id and h_kept:
                human_threads.add(thread_id)

            if is_setup and payoff_node_id:
                setup_payoff_total += 1
                # Check if payoff is also retained
                payoff_node = next((n for n in story_nodes if str(n.get("id")) == str(payoff_node_id)), None)
                if payoff_node:
                    p_start = float(payoff_node.get("source_start", 0.0))
                    p_end = float(payoff_node.get("source_end", 0.0))
                    p_h_kept = compute_interval_intersection([(p_start, p_end)], human_tuples) > 0.5 * (p_end - p_start)
                    p_ai_kept = compute_interval_intersection([(p_start, p_end)], ai_intervals) > 0.5 * (p_end - p_start)

                    # If human kept both and AI kept both -> intact
                    if h_kept and p_h_kept and ai_kept and p_ai_kept:
                        setup_payoff_intact += 1
                    elif not h_kept and ai_kept and p_ai_kept:
                        # AI kept valid pair even if human didn't
                        setup_payoff_intact += 1

            if is_callback:
                callback_total += 1
                if ai_kept:
                    callback_retained += 1

    shared_threads = list(ai_threads.intersection(human_threads))
    ai_only = list(ai_threads - human_threads)
    human_only = list(human_threads - ai_threads)

    sp_comp = (setup_payoff_intact / setup_payoff_total) if setup_payoff_total > 0 else 1.0
    cb_rate = (callback_retained / callback_total) if callback_total > 0 else 1.0

    return NarrativeMetrics(
        setup_payoff_total=setup_payoff_total,
        setup_payoff_intact=setup_payoff_intact,
        setup_payoff_completeness=round(sp_comp, 4),
        callback_total=callback_total,
        callback_retained=callback_retained,
        callback_retention_rate=round(cb_rate, 4),
        shared_thread_ids=shared_threads,
        human_only_thread_ids=human_only,
        ai_only_thread_ids=ai_only,
        thread_duration_distribution=thread_durations,
        sample_count=len(story_nodes or []),
    )


def calculate_pacing_metrics(
    ai_segments: list[StreamEditorTimelineSegment],
    human_intervals: list[RetainedInterval],
    total_source_duration: float,
    timeline_events: Optional[list[dict[str, Any]]] = None,
) -> PacingMetrics:
    """Calculate cuts per minute, clip duration quantiles, compression ratio, and dead air."""
    ai_durations = [s.source_end - s.source_start for s in ai_segments if s.source_end > s.source_start]
    human_durations = [
        h.source_end - h.source_start
        for h in human_intervals
        if not h.is_external_insert and h.source_end > h.source_start
    ]

    total_ai_duration = sum(ai_durations)
    total_human_duration = sum(human_durations)

    # Cuts per minute
    ai_cpm = ((len(ai_segments) - 1) / (total_ai_duration / 60.0)) if total_ai_duration > 10.0 else 0.0
    human_cpm = ((len(human_durations) - 1) / (total_human_duration / 60.0)) if total_human_duration > 10.0 else 0.0

    # Time between cuts in AI output
    time_between_cuts_ai: list[float] = []
    sorted_ai = sorted(ai_segments, key=lambda s: s.output_start)
    for i in range(1, len(sorted_ai)):
        gap = sorted_ai[i].output_start - sorted_ai[i - 1].output_end
        time_between_cuts_ai.append(max(0.0, gap))

    # Time between cuts in Human output
    time_between_cuts_human: list[float] = []
    sorted_human = sorted([h for h in human_intervals if h.edit_start is not None], key=lambda h: h.edit_start or 0.0)
    for i in range(1, len(sorted_human)):
        h_prev_end = sorted_human[i - 1].edit_end or 0.0
        h_curr_start = sorted_human[i].edit_start or 0.0
        time_between_cuts_human.append(max(0.0, h_curr_start - h_prev_end))

    # Compression ratios
    comp_ai = (total_ai_duration / total_source_duration) if total_source_duration > 0.0 else 0.0
    comp_human = (total_human_duration / total_source_duration) if total_source_duration > 0.0 else 0.0

    # Content density & Dead air estimation
    dead_air_seconds = 0.0
    active_events_in_ai = 0
    if timeline_events:
        for ev in timeline_events:
            ev_start = float(ev.get("start_time", 0.0))
            ev_end = float(ev.get("end_time", ev_start + 0.1))
            ev_type = ev.get("event_type", "")
            
            # Check if event is in AI selection
            in_ai = any(s.source_start <= ev_start and ev_end <= s.source_end for s in ai_segments)
            if in_ai:
                active_events_in_ai += 1
                if ev_type in ("silence", "dead_air", "pause"):
                    dead_air_seconds += (ev_end - ev_start)

    density = (active_events_in_ai / (total_ai_duration / 60.0)) if total_ai_duration > 0.0 else 0.0
    dead_air_pct = (dead_air_seconds / total_ai_duration) if total_ai_duration > 0.0 else 0.0

    return PacingMetrics(
        cuts_per_minute=round(ai_cpm, 2),
        human_cuts_per_minute=round(human_cpm, 2),
        clip_duration_stats=calculate_quantiles(ai_durations),
        human_clip_duration_stats=calculate_quantiles(human_durations),
        time_between_cuts_stats=calculate_quantiles(time_between_cuts_ai),
        human_time_between_cuts_stats=calculate_quantiles(time_between_cuts_human),
        compression_ratio_ai=round(comp_ai, 4),
        compression_ratio_human=round(comp_human, 4),
        content_density_events_per_min=round(density, 2),
        dead_air_seconds=round(dead_air_seconds, 2),
        dead_air_percentage=round(dead_air_pct, 4),
    )


def calculate_effect_metrics(
    ai_segments: list[StreamEditorTimelineSegment],
    human_effects: list[dict[str, Any]],
) -> EffectMetrics:
    """Calculate effect placement agreement, onset delta quantiles, and frequency."""
    # Flatten AI effects
    ai_effect_records: list[dict[str, Any]] = []
    for s in ai_segments:
        for eff in s.effects:
            eff_type = eff.get("type") or eff.get("effect_type", "unknown")
            eff_start = float(eff.get("source_start", s.source_start))
            eff_end = float(eff.get("source_end", s.source_end))
            ai_effect_records.append({
                "type": eff_type,
                "source_start": eff_start,
                "source_end": eff_end,
                "raw": eff,
            })

    total_ai_effects = len(ai_effect_records)
    total_human_effects = len(human_effects)

    same_count = 0
    similar_count = 0
    different_count = 0
    ai_only_count = 0
    human_only_count = 0

    onset_diffs: list[float] = []
    records: list[EffectComparisonRecord] = []

    matched_human_indices: set[int] = set()

    for ai_eff in ai_effect_records:
        best_match_idx: Optional[int] = None
        min_onset_diff = float("inf")

        for h_idx, h_eff in enumerate(human_effects):
            h_start = float(h_eff.get("source_start", 0.0))
            diff = abs(ai_eff["source_start"] - h_start)
            if diff <= 2.0 and diff < min_onset_diff:
                min_onset_diff = diff
                best_match_idx = h_idx

        if best_match_idx is not None:
            matched_human_indices.add(best_match_idx)
            h_eff = human_effects[best_match_idx]
            h_type = h_eff.get("effect_type") or h_eff.get("type", "unknown")
            a_type = ai_eff["type"]
            onset_diffs.append(min_onset_diff)

            if a_type == h_type:
                category = EffectAgreementCategory.SAME_EFFECT
                same_count += 1
            elif (
                ("zoom" in a_type and "zoom" in h_type)
                or ("speed" in a_type and "speed" in h_type)
                or ("text" in a_type and "text" in h_type)
            ):
                category = EffectAgreementCategory.SIMILAR_EFFECT
                similar_count += 1
            else:
                category = EffectAgreementCategory.DIFFERENT_EFFECT
                different_count += 1

            records.append(
                EffectComparisonRecord(
                    source_start=ai_eff["source_start"],
                    source_end=ai_eff["source_end"],
                    human_effect_type=h_type,
                    ai_effect_type=a_type,
                    category=category,
                    onset_difference_seconds=round(min_onset_diff, 4),
                    is_appropriate=True,
                )
            )
        else:
            ai_only_count += 1
            records.append(
                EffectComparisonRecord(
                    source_start=ai_eff["source_start"],
                    source_end=ai_eff["source_end"],
                    human_effect_type=None,
                    ai_effect_type=ai_eff["type"],
                    category=EffectAgreementCategory.AI_EFFECT_ONLY,
                    is_appropriate=True,
                )
            )

    human_only_count = total_human_effects - len(matched_human_indices)
    for h_idx, h_eff in enumerate(human_effects):
        if h_idx not in matched_human_indices:
            records.append(
                EffectComparisonRecord(
                    source_start=float(h_eff.get("source_start", 0.0)),
                    source_end=float(h_eff.get("source_end", 0.0)),
                    human_effect_type=h_eff.get("effect_type") or h_eff.get("type"),
                    ai_effect_type=None,
                    category=EffectAgreementCategory.HUMAN_EFFECT_ONLY,
                )
            )

    total_comparisons = same_count + similar_count + different_count + ai_only_count + human_only_count
    agreement_rate = (
        ((same_count + similar_count) / (same_count + similar_count + different_count))
        if (same_count + similar_count + different_count) > 0
        else (1.0 if total_comparisons == 0 else 0.0)
    )

    total_ai_duration = sum(s.source_end - s.source_start for s in ai_segments)
    effects_pm_ai = (total_ai_effects / (total_ai_duration / 60.0)) if total_ai_duration > 0.0 else 0.0

    return EffectMetrics(
        total_comparisons=total_comparisons,
        same_effect_count=same_count,
        similar_effect_count=similar_count,
        different_effect_count=different_count,
        ai_effect_only_count=ai_only_count,
        human_effect_only_count=human_only_count,
        effect_agreement_rate=round(agreement_rate, 4),
        onset_diff_stats=calculate_quantiles(onset_diffs),
        effects_per_minute_ai=round(effects_pm_ai, 2),
        effects_per_minute_human=0.0,
        over_effected_flag=effects_pm_ai > 12.0,
        under_effected_flag=effects_pm_ai < 0.5 and total_human_effects > 3,
        records=records,
    )
