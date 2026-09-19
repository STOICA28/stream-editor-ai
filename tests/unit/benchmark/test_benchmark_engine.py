"""Synthetic benchmark test suite for M13 Editorial Quality Evaluation."""

import pytest
from datetime import datetime, UTC

from stream_editor.contracts.benchmark import (
    DatasetSplit,
    ClipMatchClassification,
    AISegmentClassification,
    FalseNegativeReason,
    FalsePositiveReason,
    PipelineStage,
    EffectAgreementCategory,
    RetainedInterval,
    HumanReferenceTimeline,
    StreamEditorTimelineSegment,
    StreamEditorTimeline,
    EditorialBenchmarkCase,
)
from stream_editor.research.benchmark.timeline import (
    merge_intervals,
    compute_interval_intersection,
    compute_total_duration,
    build_human_reference_timeline,
    build_streameditor_timeline,
)
from stream_editor.research.benchmark.metrics import (
    calculate_overlap_metrics,
    calculate_quantiles,
    calculate_context_metrics,
    calculate_narrative_metrics,
    calculate_pacing_metrics,
    calculate_effect_metrics,
)
from stream_editor.research.benchmark.classifier import (
    classify_clip_match,
    classify_ai_segment,
    trace_failure_root_cause,
)
from stream_editor.research.benchmark.evaluator import (
    MockEditorialEvaluationProvider,
    SegmentSemanticEvaluation,
)
from stream_editor.research.benchmark.engine import EditorialBenchmarkEngine


@pytest.mark.asyncio
async def test_perfect_agreement():
    """AI timeline exactly matches Human Reference timeline."""
    case = EditorialBenchmarkCase(
        name="test_perfect",
        source_asset_id="src-1",
        human_edit_asset_id="edit-1",
        duration_source=100.0,
        duration_human_edit=30.0,
        split=DatasetSplit.TEST,
    )
    intervals = [
        RetainedInterval(id="h1", source_start=10.0, source_end=20.0),
        RetainedInterval(id="h2", source_start=40.0, source_end=50.0),
        RetainedInterval(id="h3", source_start=70.0, source_end=80.0),
    ]
    human_timeline = HumanReferenceTimeline(
        case_id=case.id,
        retained_intervals=intervals,
        total_retained_duration=30.0,
        total_source_duration=100.0,
    )
    ai_segments = [
        StreamEditorTimelineSegment(id="s1", source_start=10.0, source_end=20.0, output_start=0.0, output_end=10.0, clip_id="c1"),
        StreamEditorTimelineSegment(id="s2", source_start=40.0, source_end=50.0, output_start=10.0, output_end=20.0, clip_id="c2"),
        StreamEditorTimelineSegment(id="s3", source_start=70.0, source_end=80.0, output_start=20.0, output_end=30.0, clip_id="c3"),
    ]
    ai_timeline = StreamEditorTimeline(
        project_id="p1",
        plan_id="plan-1",
        segments=ai_segments,
        total_selected_duration=30.0,
        clip_count=3,
    )

    engine = EditorialBenchmarkEngine(evaluator=MockEditorialEvaluationProvider())
    result, failures = await engine.evaluate_case(
        run_id="run-perfect",
        case=case,
        human_timeline=human_timeline,
        ai_timeline=ai_timeline,
    )

    assert result.overlap_at_10s.precision == 1.0
    assert result.overlap_at_10s.recall == 1.0
    assert result.overlap_at_10s.f1 == 1.0
    assert result.matched_segments_count == 3
    assert result.missed_segments_count == 0
    assert result.ai_only_segments_count == 0
    assert len(failures) == 0


@pytest.mark.asyncio
async def test_overselection_low_precision():
    """AI selects all human moments plus 40s of unwanted filler."""
    case = EditorialBenchmarkCase(
        name="test_overselection",
        source_asset_id="src-1",
        human_edit_asset_id="edit-1",
        duration_source=100.0,
        duration_human_edit=20.0,
        split=DatasetSplit.TEST,
    )
    human_timeline = HumanReferenceTimeline(
        case_id=case.id,
        retained_intervals=[
            RetainedInterval(id="h1", source_start=10.0, source_end=20.0),
            RetainedInterval(id="h2", source_start=50.0, source_end=60.0),
        ],
        total_retained_duration=20.0,
        total_source_duration=100.0,
    )
    # AI selects human intervals plus 2 extra intervals [25-45] and [70-90]
    ai_segments = [
        StreamEditorTimelineSegment(id="s1", source_start=10.0, source_end=20.0, output_start=0.0, output_end=10.0, clip_id="c1"),
        StreamEditorTimelineSegment(id="s2", source_start=25.0, source_end=45.0, output_start=10.0, output_end=30.0, clip_id="c2"),
        StreamEditorTimelineSegment(id="s3", source_start=50.0, source_end=60.0, output_start=30.0, output_end=40.0, clip_id="c3"),
        StreamEditorTimelineSegment(id="s4", source_start=70.0, source_end=90.0, output_start=40.0, output_end=60.0, clip_id="c4"),
    ]
    ai_timeline = StreamEditorTimeline(
        project_id="p1",
        plan_id="plan-1",
        segments=ai_segments,
        total_selected_duration=60.0,
        clip_count=4,
    )

    mock_eval = MockEditorialEvaluationProvider(default_valid_alternative=False)
    engine = EditorialBenchmarkEngine(evaluator=mock_eval)
    result, failures = await engine.evaluate_case(
        run_id="run-overselect",
        case=case,
        human_timeline=human_timeline,
        ai_timeline=ai_timeline,
    )

    assert result.overlap_at_10s.recall == 1.0
    assert result.overlap_at_10s.precision == round(20.0 / 60.0, 4)  # ~0.3333
    assert result.matched_segments_count == 2
    assert result.ai_only_segments_count == 2
    assert len(failures) == 2


@pytest.mark.asyncio
async def test_missing_content_low_recall():
    """AI selects only 1 of 4 human moments (low recall, high precision)."""
    case = EditorialBenchmarkCase(
        name="test_missing",
        source_asset_id="src-1",
        human_edit_asset_id="edit-1",
        duration_source=100.0,
        duration_human_edit=40.0,
        split=DatasetSplit.TEST,
    )
    human_timeline = HumanReferenceTimeline(
        case_id=case.id,
        retained_intervals=[
            RetainedInterval(id="h1", source_start=10.0, source_end=20.0),
            RetainedInterval(id="h2", source_start=30.0, source_end=40.0),
            RetainedInterval(id="h3", source_start=50.0, source_end=60.0),
            RetainedInterval(id="h4", source_start=70.0, source_end=80.0),
        ],
        total_retained_duration=40.0,
        total_source_duration=100.0,
    )
    # AI only selects [10-20]
    ai_segments = [
        StreamEditorTimelineSegment(id="s1", source_start=10.0, source_end=20.0, output_start=0.0, output_end=10.0, clip_id="c1"),
    ]
    ai_timeline = StreamEditorTimeline(
        project_id="p1",
        plan_id="plan-1",
        segments=ai_segments,
        total_selected_duration=10.0,
        clip_count=1,
    )

    engine = EditorialBenchmarkEngine(evaluator=MockEditorialEvaluationProvider())
    result, failures = await engine.evaluate_case(
        run_id="run-missing",
        case=case,
        human_timeline=human_timeline,
        ai_timeline=ai_timeline,
    )

    assert result.overlap_at_10s.precision == 1.0
    assert result.overlap_at_10s.recall == 0.25
    assert result.matched_segments_count == 1
    assert result.missed_segments_count == 3
    assert len(failures) == 3


def test_boundary_tolerances_expansion():
    """Test boundary tolerances (0.5s, 1.0s, 2.0s) monotonic expansion."""
    human_intervals = [(10.0, 20.0)]
    # AI cut is slightly shifted [10.8, 20.8]
    ai_intervals = [(10.8, 20.8)]

    m05 = calculate_overlap_metrics(ai_intervals, human_intervals, tolerance_seconds=0.5)
    m10 = calculate_overlap_metrics(ai_intervals, human_intervals, tolerance_seconds=1.0)
    m20 = calculate_overlap_metrics(ai_intervals, human_intervals, tolerance_seconds=2.0)

    # Monotonic improvement with tolerance expansion
    assert m05.intersection_duration <= m10.intersection_duration
    assert m10.intersection_duration <= m20.intersection_duration
    assert m20.precision == 1.0


def test_external_inserts_and_speedup():
    """Test that external inserts are excluded from source evaluation and speedup is tracked."""
    data = {
        "blocks": [
            {
                "id": "b-ext",
                "source_start": -10.0,
                "source_end": -5.0,
                "edit_start": 0.0,
                "edit_end": 5.0,
                "is_external_insert": True,
            },
            {
                "id": "b-speed",
                "source_start": 20.0,
                "source_end": 30.0,
                "edit_start": 5.0,
                "edit_end": 10.0,
                "speed_ratio": 2.0,
            },
            {
                "id": "b-norm",
                "source_start": 40.0,
                "source_end": 50.0,
                "edit_start": 10.0,
                "edit_end": 20.0,
                "speed_ratio": 1.0,
            },
        ]
    }
    timeline = build_human_reference_timeline("case-test", data, source_duration=60.0)

    assert len(timeline.external_inserts) == 1
    assert len(timeline.transformed_intervals) == 1
    assert len(timeline.retained_intervals) == 2  # speed + norm
    assert timeline.total_retained_duration == 20.0  # 10s + 10s


def test_narrative_setup_payoff_completeness():
    """Test setup/payoff completeness calculation."""
    human_intervals = [
        RetainedInterval(id="h1", source_start=10.0, source_end=20.0),
        RetainedInterval(id="h2", source_start=50.0, source_end=60.0),
    ]
    story_nodes = [
        {
            "id": "node-setup",
            "source_start": 10.0,
            "source_end": 20.0,
            "is_setup": True,
            "payoff_node_id": "node-payoff",
            "thread_id": "thread-1",
        },
        {
            "id": "node-payoff",
            "source_start": 50.0,
            "source_end": 60.0,
            "type": "payoff",
            "thread_id": "thread-1",
        },
    ]

    # Case A: AI keeps both setup and payoff
    ai_both = [
        StreamEditorTimelineSegment(id="s1", source_start=10.0, source_end=20.0, output_start=0.0, output_end=10.0, clip_id="c1", narrative_thread_id="thread-1"),
        StreamEditorTimelineSegment(id="s2", source_start=50.0, source_end=60.0, output_start=10.0, output_end=20.0, clip_id="c2", narrative_thread_id="thread-1"),
    ]
    nm_both = calculate_narrative_metrics(ai_both, human_intervals, story_nodes=story_nodes)
    assert nm_both.setup_payoff_completeness == 1.0
    assert nm_both.setup_payoff_intact == 1

    # Case B: AI keeps only payoff and drops setup
    ai_payoff_only = [
        StreamEditorTimelineSegment(id="s2", source_start=50.0, source_end=60.0, output_start=0.0, output_end=10.0, clip_id="c2", narrative_thread_id="thread-1"),
    ]
    nm_payoff = calculate_narrative_metrics(ai_payoff_only, human_intervals, story_nodes=story_nodes)
    assert nm_payoff.setup_payoff_completeness == 0.0
    assert nm_payoff.setup_payoff_intact == 0


def test_root_cause_stage_tracer():
    """Verify Root-Cause Stage Tracer accurately pinpoints upstream failure origins."""
    # 1. Missing in M2 (no TimelineEvents)
    stage, reason, ev = trace_failure_root_cause(
        start_time=10.0,
        end_time=20.0,
        is_false_negative=True,
        timeline_events=[],  # Empty M2
    )
    assert stage == PipelineStage.M2
    assert reason == FalseNegativeReason.MISSED_IMPORTANT_EVENT.value
    assert ev["stage_culprit"] == "M2_UNDERSTANDING"

    # 2. Detected in M2, but filtered out in M3 (no candidate)
    stage, reason, ev = trace_failure_root_cause(
        start_time=10.0,
        end_time=20.0,
        is_false_negative=True,
        timeline_events=[{"start_time": 12.0, "end_time": 18.0, "event_type": "speech"}],
        candidate_segments=[],  # Empty M3
    )
    assert stage == PipelineStage.M3
    assert reason == FalseNegativeReason.LOW_SCORE.value
    assert ev["stage_culprit"] == "M3_CANDIDATE_GENERATION"

    # 3. Candidate in M3, but dropped in M4 (no StoryNode)
    stage, reason, ev = trace_failure_root_cause(
        start_time=10.0,
        end_time=20.0,
        is_false_negative=True,
        timeline_events=[{"start_time": 12.0, "end_time": 18.0, "event_type": "speech"}],
        candidate_segments=[{"start_time": 10.0, "end_time": 20.0, "score": 0.85}],
        story_nodes=[],  # Empty M4
    )
    assert stage == PipelineStage.M4
    assert reason == FalseNegativeReason.DEPENDENCY_FAILURE.value
    assert ev["stage_culprit"] == "M4_STORY_GRAPH"

    # 4. In StoryGraph (M4), but pruned by Knapsack / Duration Budget (M5)
    stage, reason, ev = trace_failure_root_cause(
        start_time=10.0,
        end_time=20.0,
        is_false_negative=True,
        timeline_events=[{"start_time": 12.0, "end_time": 18.0, "event_type": "speech"}],
        candidate_segments=[{"start_time": 10.0, "end_time": 20.0, "score": 0.85}],
        story_nodes=[{"source_start": 10.0, "source_end": 20.0, "id": "n1"}],
        edit_clips=[],  # Pruned in M5
    )
    assert stage == PipelineStage.M5
    assert reason == FalseNegativeReason.BUDGET_EXCLUSION.value
    assert ev["stage_culprit"] == "M5_GLOBAL_EDITORIAL_SELECTION"


@pytest.mark.asyncio
async def test_semantic_valid_alternative_classification():
    """Test that AI-only segments identified as valid alternatives are categorized accurately."""
    case = EditorialBenchmarkCase(
        name="test_valid_alt",
        source_asset_id="src-1",
        human_edit_asset_id="edit-1",
        duration_source=100.0,
        duration_human_edit=20.0,
        split=DatasetSplit.TEST,
    )
    human_timeline = HumanReferenceTimeline(
        case_id=case.id,
        retained_intervals=[
            RetainedInterval(id="h1", source_start=10.0, source_end=30.0),
        ],
        total_retained_duration=20.0,
        total_source_duration=100.0,
    )
    # AI selected human interval [10-30] plus an additional hilarious gameplay moment [60-80]
    ai_segments = [
        StreamEditorTimelineSegment(id="s1", source_start=10.0, source_end=30.0, output_start=0.0, output_end=20.0, clip_id="c1"),
        StreamEditorTimelineSegment(id="s2", source_start=60.0, source_end=80.0, output_start=20.0, output_end=40.0, clip_id="c2", selection_reason="Epic clutch play"),
    ]
    ai_timeline = StreamEditorTimeline(
        project_id="p1",
        plan_id="plan-1",
        segments=ai_segments,
        total_selected_duration=40.0,
        clip_count=2,
    )

    mock_eval = MockEditorialEvaluationProvider(default_valid_alternative=True)
    engine = EditorialBenchmarkEngine(evaluator=mock_eval)
    result, failures = await engine.evaluate_case(
        run_id="run-valid-alt",
        case=case,
        human_timeline=human_timeline,
        ai_timeline=ai_timeline,
    )

    assert result.ai_only_segments_count == 1
    assert result.valid_alternatives_count == 1
    assert any(f.failure_type == FalsePositiveReason.VALID_ALTERNATIVE.value for f in failures)
