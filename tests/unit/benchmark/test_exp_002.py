"""
Unit tests for EXP-002: Stage M3 Setup/Payoff Clustering Window.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from stream_editor.contracts.editorial import CandidateWindowConfig
from stream_editor.editorial.context import ContextExpander, TranscriptSegmentData, SceneData
from stream_editor.editorial.windowing import CandidateWindow
from stream_editor.contracts.benchmark import DatasetSplit, EditorialBenchmarkCase
from scripts.benchmark_runner import build_current_streameditor_cut, load_fixture_data


def test_candidate_window_config_backward_setup_window():
    """Verify CandidateWindowConfig supports backward_setup_window."""
    default_config = CandidateWindowConfig()
    assert default_config.backward_setup_window == 1.5

    custom_config = CandidateWindowConfig(backward_setup_window=2.0)
    assert custom_config.backward_setup_window == 2.0

    sig1 = default_config.get_signature("fingerprint_test")
    sig2 = custom_config.get_signature("fingerprint_test")
    assert sig1 != sig2


def test_context_expander_backward_setup_snapping():
    """Verify ContextExpander backward setup snapping and scene cut boundary guard."""
    expander = ContextExpander()
    config = CandidateWindowConfig(preroll=0.0, postroll=0.0, backward_setup_window=1.5)

    segments = [
        TranscriptSegmentData(id="s1", start_time=4.0, end_time=6.0, text="Watch this clutch setup!"),
        TranscriptSegmentData(id="s2", start_time=6.0, end_time=8.0, text="Boom, headshot!"),
    ]

    # Case A: Candidate starting at 4.5s (0.5s into s1) should snap back to 4.0s (s1 start)
    window_a = CandidateWindow(core_start=4.5, core_end=8.0, source_signals=["clutch"])
    expanded_a = expander.expand(window_a, segments, [], config)
    assert expanded_a.core_start == 4.0
    assert expanded_a.core_end == 8.0

    # Case B: Scene cut at 4.2s should prevent snapping all the way to 4.0s
    scenes = [SceneData(id="sc1", start_time=4.2, end_time=10.0)]
    expanded_b = expander.expand(window_a, segments, scenes, config)
    assert expanded_b.core_start == 4.2


from stream_editor.research.benchmark.engine import EditorialBenchmarkEngine
from scripts.benchmark_runner import build_human_reference_timeline
import pytest


@pytest.mark.asyncio
async def test_exp_002_timeline_boundary_metrics():
    """Verify setup_clustering_expansion improves recall and pre-context alignment on test cases."""
    case = EditorialBenchmarkCase(
        id="case-test-002",
        name="Clutch Moment",
        source_asset_id="asset-test-002-src",
        human_edit_asset_id="asset-test-002-edit",
        reference_project_id="proj-test-002",
        duration_source=10.0,
        duration_human_edit=6.0,
        split=DatasetSplit.TEST,
        tags=["clutch"],
        notes="Test case 2",
    )
    gt_data = load_fixture_data("case-test-002")
    human_timeline = build_human_reference_timeline(
        case_id=case.id,
        data=gt_data,
        source_duration=case.duration_source,
        edit_duration=case.duration_human_edit,
    )

    benchmark_engine = EditorialBenchmarkEngine()

    # Baseline: without setup clustering expansion
    base_ai, base_artifacts = build_current_streameditor_cut(
        case, gt_data, visual_reaction_elevation=False, setup_clustering_expansion=False
    )
    base_res, _ = await benchmark_engine.evaluate_case(
        run_id="run-base-test-2",
        case=case,
        human_timeline=human_timeline,
        ai_timeline=base_ai,
        pipeline_artifacts=base_artifacts,
    )

    # EXP-002: with setup clustering expansion
    exp_ai, exp_artifacts = build_current_streameditor_cut(
        case, gt_data, visual_reaction_elevation=False, setup_clustering_expansion=True
    )
    exp_res, _ = await benchmark_engine.evaluate_case(
        run_id="run-exp-test-2",
        case=case,
        human_timeline=human_timeline,
        ai_timeline=exp_ai,
        pipeline_artifacts=exp_artifacts,
    )

    # Recall at 1.0s should improve from 88.33% to 100.0%
    base_recall = base_res.overlap_at_10s.recall
    exp_recall = exp_res.overlap_at_10s.recall
    assert exp_recall >= base_recall
    assert exp_recall == 1.0

    # Pre-context delta median should be 0.0s
    assert exp_res.context.pre_context_diff_quantiles.median == 0.0

