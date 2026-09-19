"""Editorial Benchmark Engine orchestrator."""

from typing import Any, Optional
import uuid
from datetime import datetime, UTC

from stream_editor.contracts.benchmark import (
    DatasetSplit,
    ClipMatchClassification,
    AISegmentClassification,
    FalseNegativeReason,
    FalsePositiveReason,
    PipelineStage,
    RetainedInterval,
    HumanReferenceTimeline,
    StreamEditorTimelineSegment,
    StreamEditorTimeline,
    EditorialBenchmarkCase,
    EditorialBenchmarkRun,
    EditorialBenchmarkResult,
    EditorialFailure,
)
from .timeline import (
    compute_total_duration,
)
from .metrics import (
    calculate_overlap_metrics,
    calculate_context_metrics,
    calculate_narrative_metrics,
    calculate_pacing_metrics,
    calculate_effect_metrics,
)
from .classifier import (
    classify_clip_match,
    classify_ai_segment,
    trace_failure_root_cause,
)
from .evaluator import (
    EditorialEvaluationProvider,
    MockEditorialEvaluationProvider,
)


class EditorialBenchmarkEngine:
    """Core scientific evaluation engine for StreamEditor editorial quality."""

    def __init__(
        self,
        evaluator: Optional[EditorialEvaluationProvider] = None,
        editor_model: str = "gemini-3.1-pro-high",
        evaluator_model: str = "gemini-3.1-pro-high",
    ) -> None:
        self.evaluator = evaluator or MockEditorialEvaluationProvider()
        self.editor_model = editor_model
        self.evaluator_model = evaluator_model

    async def evaluate_case(
        self,
        run_id: str,
        case: EditorialBenchmarkCase,
        human_timeline: HumanReferenceTimeline,
        ai_timeline: StreamEditorTimeline,
        pipeline_artifacts: Optional[dict[str, Any]] = None,
    ) -> tuple[EditorialBenchmarkResult, list[EditorialFailure]]:
        """Evaluate a single benchmark case comparing StreamEditor against human reference."""
        artifacts = pipeline_artifacts or {}
        timeline_events = artifacts.get("timeline_events", [])
        candidates = artifacts.get("candidates", [])
        story_nodes = artifacts.get("story_nodes", [])
        visual_events = artifacts.get("visual_events", [])
        effect_plans = artifacts.get("effect_plans", [])
        human_effects = artifacts.get("human_effects", [])

        ai_intervals = [(s.source_start, s.source_end) for s in ai_timeline.segments]
        human_intervals = [
            (h.source_start, h.source_end)
            for h in human_timeline.retained_intervals
            if not h.is_external_insert
        ]

        # 1. Overlap Metrics across tolerances (0.5s, 1.0s, 2.0s)
        overlap_05 = calculate_overlap_metrics(ai_intervals, human_intervals, tolerance_seconds=0.5)
        overlap_10 = calculate_overlap_metrics(ai_intervals, human_intervals, tolerance_seconds=1.0)
        overlap_20 = calculate_overlap_metrics(ai_intervals, human_intervals, tolerance_seconds=2.0)

        # 2. Subsystem Dimensions
        context_m = calculate_context_metrics(
            ai_timeline.segments, human_timeline.retained_intervals, tolerance=1.0
        )
        narrative_m = calculate_narrative_metrics(
            ai_timeline.segments, human_timeline.retained_intervals, story_nodes=story_nodes
        )
        pacing_m = calculate_pacing_metrics(
            ai_timeline.segments,
            human_timeline.retained_intervals,
            total_source_duration=case.duration_source,
            timeline_events=timeline_events,
        )
        effect_m = calculate_effect_metrics(ai_timeline.segments, human_effects=human_effects)

        # 3. Clip Classification and Failure Tracing
        matched_count = 0
        missed_count = 0
        ai_only_count = 0
        valid_alt_count = 0

        failures: list[EditorialFailure] = []
        root_cause_counts: dict[str, int] = {}

        # Evaluate Human intervals (Check for False Negatives)
        for h in human_timeline.retained_intervals:
            if h.is_external_insert:
                continue
            classification = classify_clip_match(h, ai_timeline.segments, tolerance=1.0)
            if classification == ClipMatchClassification.MATCHED:
                matched_count += 1
            elif classification == ClipMatchClassification.MISSED:
                missed_count += 1
                # Trace root cause upstream
                stage, reason, evidence = trace_failure_root_cause(
                    start_time=h.source_start,
                    end_time=h.source_end,
                    is_false_negative=True,
                    timeline_events=timeline_events,
                    candidate_segments=candidates,
                    story_nodes=story_nodes,
                    edit_clips=[s.model_dump() for s in ai_timeline.segments],
                    visual_events=visual_events,
                    effect_plans=effect_plans,
                )
                failure = EditorialFailure(
                    benchmark_run_id=run_id,
                    case_id=case.id,
                    failure_type=reason,
                    root_cause_stage=stage,
                    source_start=h.source_start,
                    source_end=h.source_end,
                    description=f"Human retained interval [{h.source_start:.1f}s - {h.source_end:.1f}s] was missed by StreamEditor. Culprit: {stage.value}",
                    evidence_trace=evidence,
                    confidence=h.confidence,
                )
                failures.append(failure)
                key = f"{stage.value}:{reason}"
                root_cause_counts[key] = root_cause_counts.get(key, 0) + 1

        # Evaluate AI segments (Check for AI-Only / False Positives)
        for seg in ai_timeline.segments:
            support = classify_ai_segment(seg, human_timeline.retained_intervals, tolerance=1.0)
            if support == AISegmentClassification.AI_ONLY:
                ai_only_count += 1
                # Run semantic evaluation
                semantic_eval = await self.evaluator.evaluate_segment(
                    seg.model_dump(),
                    context_transcript=artifacts.get("transcript_context", ""),
                )
                if semantic_eval.is_valid_alternative:
                    valid_alt_count += 1

                stage, reason, evidence = trace_failure_root_cause(
                    start_time=seg.source_start,
                    end_time=seg.source_end,
                    is_false_negative=False,
                    timeline_events=timeline_events,
                    candidate_segments=candidates,
                    story_nodes=story_nodes,
                    edit_clips=[s.model_dump() for s in ai_timeline.segments],
                    visual_events=visual_events,
                    effect_plans=effect_plans,
                    semantic_verdict=semantic_eval.model_dump(),
                )

                failure = EditorialFailure(
                    benchmark_run_id=run_id,
                    case_id=case.id,
                    failure_type=reason,
                    root_cause_stage=stage,
                    source_start=seg.source_start,
                    source_end=seg.source_end,
                    description=f"AI selected segment [{seg.source_start:.1f}s - {seg.source_end:.1f}s] not in human edit. Evaluation: {'Valid Alternative' if semantic_eval.is_valid_alternative else 'False Positive'}",
                    evidence_trace=evidence,
                    confidence=semantic_eval.confidence,
                )
                failures.append(failure)
                key = f"{stage.value}:{reason}"
                root_cause_counts[key] = root_cause_counts.get(key, 0) + 1

        # 4. Construct Immutable Result
        result = EditorialBenchmarkResult(
            run_id=run_id,
            case_id=case.id,
            split=case.split,
            overlap_at_05s=overlap_05,
            overlap_at_10s=overlap_10,
            overlap_at_20s=overlap_20,
            context=context_m,
            narrative=narrative_m,
            pacing=pacing_m,
            effects=effect_m,
            matched_segments_count=matched_count,
            missed_segments_count=missed_count,
            ai_only_segments_count=ai_only_count,
            valid_alternatives_count=valid_alt_count,
            failures=failures,
            root_cause_distribution=root_cause_counts,
            editor_model=self.editor_model,
            evaluator_model=self.evaluator_model,
            model_parity_flag=self.editor_model == self.evaluator_model,
            manual_audit_verified=False,
        )

        return result, failures
