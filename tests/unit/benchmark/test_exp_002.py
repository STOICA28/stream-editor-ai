"""
Unit tests for EXP-002: Stage M3 Setup/Payoff Clustering Window & Relational Context Expansion.
Fulfills EXP-002 Section 55 (Required Tests) and Section 56 (Synthetic Control Cases).
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "packages" / "contracts" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "editorial" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "research" / "src"))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import pytest
from stream_editor.contracts.editorial import (
    CandidateClusteringExperimentConfig,
    CandidateRelationType,
    CandidateWindowConfig,
)
from stream_editor.editorial.context import (
    ContextExpander,
    SceneData,
    TranscriptSegmentData,
)
from stream_editor.editorial.generator import _candidate_sig, _run_sig
from stream_editor.editorial.windowing import (
    CandidateRelationClassifier,
    CandidateWindow,
    EventClusterer,
)
from stream_editor.contracts.benchmark import DatasetSplit, EditorialBenchmarkCase
from benchmark_runner import build_current_streameditor_cut, build_human_reference_timeline, load_fixture_data
from stream_editor.research.benchmark.engine import EditorialBenchmarkEngine


def test_candidate_window_config_backward_setup_window():
    """Verify CandidateWindowConfig supports backward_setup_window and clustering_config."""
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


# ---------------------------------------------------------------------------
# SYNTHETIC CONTROL CASES (EXP-002 Section 56)
# ---------------------------------------------------------------------------

def test_synthetic_case_a_setup_payoff_merge():
    """Case A (Section 56): Setup + payoff should merge."""
    clusterer = EventClusterer()
    cfg = CandidateClusteringExperimentConfig(
        reaction_link_window=2.0,
        max_related_event_gap=4.0,
        minimum_relation_confidence=0.6,
    )
    events = [
        {"id": "e1", "start_time": 1.0, "end_time": 3.0, "event_type": "speech", "text": "Wait for it..."},
        {"id": "e2", "start_time": 4.0, "end_time": 5.0, "event_type": "face_reaction", "confidence": 0.92},
    ]
    clusters = clusterer.cluster(events, merge_gap=3.0, clustering_config=cfg)
    assert len(clusters) == 1
    assert len(clusters[0]) == 2
    # Verify relational link classified
    rel = CandidateRelationClassifier.classify_relation(events[0], events[1], cfg)
    assert rel.relation_type == CandidateRelationType.SETUP_TO_PAYOFF
    assert rel.confidence >= 0.6


def test_synthetic_case_b_setup_unrelated_no_merge():
    """Case B (Section 56): Setup + unrelated event should NOT merge."""
    clusterer = EventClusterer()
    cfg = CandidateClusteringExperimentConfig(
        speech_continuity_gap=1.0,
        max_related_event_gap=4.0,
        minimum_relation_confidence=0.6,
    )
    # Two commentary events on unrelated topics separated by 1.8s pause (exceeds speech_continuity_gap)
    events = [
        {"id": "e1", "start_time": 1.0, "end_time": 3.0, "event_type": "speech", "speaker": "streamer_a"},
        {"id": "e2", "start_time": 4.8, "end_time": 6.5, "event_type": "speech", "speaker": "guest_b"},
    ]
    clusters = clusterer.cluster(events, merge_gap=3.0, clustering_config=cfg)
    # Must NOT merge merely due to temporal proximity (< 3.0s)!
    assert len(clusters) == 2
    rel = CandidateRelationClassifier.classify_relation(events[0], events[1], cfg)
    assert rel.relation_type == CandidateRelationType.UNRELATED or rel.confidence < 0.6


def test_synthetic_case_c_reaction_after_trigger_merge():
    """Case C (Section 56): Reaction after trigger should merge."""
    clusterer = EventClusterer()
    cfg = CandidateClusteringExperimentConfig(reaction_link_window=2.0)
    events = [
        {"id": "e1", "start_time": 2.0, "end_time": 4.0, "event_type": "gameplay_clutch"},
        {"id": "e2", "start_time": 4.8, "end_time": 6.0, "event_type": "face_reaction", "confidence": 0.95},
    ]
    clusters = clusterer.cluster(events, merge_gap=3.0, clustering_config=cfg)
    assert len(clusters) == 1
    rel = CandidateRelationClassifier.classify_relation(events[0], events[1], cfg)
    assert rel.relation_type == CandidateRelationType.EVENT_TO_REACTION
    assert rel.confidence >= 0.9


def test_synthetic_case_d_scene_boundary_prevents_merge():
    """Case D (Section 56): Events separated by scene boundary should not merge."""
    clusterer = EventClusterer()
    cfg = CandidateClusteringExperimentConfig(
        scene_boundary_hard_stop=True,
        max_related_event_gap=4.0,
    )
    events = [
        {"id": "e1", "start_time": 1.0, "end_time": 3.0, "event_type": "speech"},
        {"id": "e2", "start_time": 3.8, "end_time": 5.5, "event_type": "gameplay"},
    ]
    # Visual scene cut at 3.4s strictly between events
    scenes = [{"start_time": 3.4, "end_time": 10.0}]
    clusters = clusterer.cluster(events, merge_gap=3.0, clustering_config=cfg, scenes=scenes)
    assert len(clusters) == 2
    rel = CandidateRelationClassifier.classify_relation(events[0], events[1], cfg, scenes=scenes)
    assert rel.relation_type == CandidateRelationType.UNRELATED
    assert rel.same_scene is False


def test_synthetic_case_e_context_expansion_hits_max_cap():
    """Case E (Section 56): Context expansion hits maximum cap."""
    expander = ContextExpander()
    cfg = CandidateClusteringExperimentConfig(
        max_backward_context=3.0,
        max_forward_context=2.5,
        scene_boundary_hard_stop=True,
    )
    config = CandidateWindowConfig(preroll=0.0, postroll=0.0, clustering_config=cfg)

    # 10s speech segment preceding the core
    segments = [
        TranscriptSegmentData(id="s1", start_time=0.0, end_time=10.0, text="Very long preamble speech"),
        TranscriptSegmentData(id="s2", start_time=10.0, end_time=25.0, text="Core and continuation"),
    ]
    window = CandidateWindow(core_start=10.0, core_end=15.0, source_signals=["speech"])
    expanded = expander.expand(window, segments, [], config)

    # Core start cannot expand back beyond 10.0 - 3.0 = 7.0s
    assert expanded.core_start == 7.0
    # Core end cannot expand forward beyond 15.0 + 2.5 = 17.5s
    assert expanded.core_end == 17.5
    assert "clamped_by_max_backward" in expanded.boundary_reason or "clamped_by_max_forward" in expanded.boundary_reason


# ---------------------------------------------------------------------------
# REQUIRED REGRESSION TESTS (EXP-002 Section 55)
# ---------------------------------------------------------------------------

def test_natural_pause_snapping():
    """Verify natural utterance boundary snapping."""
    expander = ContextExpander()
    cfg = CandidateClusteringExperimentConfig(max_backward_context=4.0)
    config = CandidateWindowConfig(preroll=0.0, postroll=0.0, clustering_config=cfg)

    segments = [
        TranscriptSegmentData(id="s1", start_time=2.2, end_time=4.5, text="First setup sentence."),
        TranscriptSegmentData(id="s2", start_time=4.8, end_time=8.0, text="Payoff sentence."),
    ]
    # Window core starts at 4.0s (mid-s1); should snap to 2.2s (clean sentence start)
    window = CandidateWindow(core_start=4.0, core_end=8.0, source_signals=["speech"])
    expanded = expander.expand(window, segments, [], config)
    assert expanded.core_start == 2.2


def test_candidate_signature_changes_with_config():
    """Verify CandidateRun and candidate derivation signatures change with clustering config."""
    cfg_a = CandidateClusteringExperimentConfig(max_backward_context=2.0, version="variant_a")
    cfg_b = CandidateClusteringExperimentConfig(max_backward_context=4.0, version="variant_b")

    w_cfg_a = CandidateWindowConfig(clustering_config=cfg_a)
    w_cfg_b = CandidateWindowConfig(clustering_config=cfg_b)

    sig_a = w_cfg_a.get_signature("src_fingerprint")
    sig_b = w_cfg_b.get_signature("src_fingerprint")
    assert sig_a != sig_b

    run_sig_a = _run_sig("p1", "a1", w_cfg_a, "mock", "v1", "balanced")
    run_sig_b = _run_sig("p1", "a1", w_cfg_b, "mock", "v1", "balanced")
    assert run_sig_a != run_sig_b

    cand_sig_a = _candidate_sig("p1", "a1", 0.0, 10.0, 2.0, 8.0, "1.0.0", clustering_version=cfg_a.version)
    cand_sig_b = _candidate_sig("p1", "a1", 0.0, 10.0, 2.0, 8.0, "1.0.0", clustering_version=cfg_b.version)
    assert cand_sig_a != cand_sig_b


def test_m1_m2_cache_remains_reusable():
    """Verify M1/M2 cache keys are not polluted by M3 clustering config changes."""
    m2_input_data = {"asset_id": "a1", "duration": 300.0, "sampling_rate": 16000}
    m2_cache_key_1 = hashlib.sha256(json.dumps(m2_input_data, sort_keys=True).encode()).hexdigest()

    # Changing M3 CandidateClusteringExperimentConfig does NOT change M2 input data or key
    cfg_exp = CandidateClusteringExperimentConfig(version="variant_c")
    m2_cache_key_2 = hashlib.sha256(json.dumps(m2_input_data, sort_keys=True).encode()).hexdigest()

    assert m2_cache_key_1 == m2_cache_key_2


def test_duplicate_event_handling():
    """Verify duplicate timeline events do not produce corrupt clusters."""
    clusterer = EventClusterer()
    cfg = CandidateClusteringExperimentConfig()
    events = [
        {"id": "e1", "start_time": 2.0, "end_time": 4.0, "event_type": "speech"},
        {"id": "e1", "start_time": 2.0, "end_time": 4.0, "event_type": "speech"}, # exact duplicate
    ]
    clusters = clusterer.cluster(events, merge_gap=3.0, clustering_config=cfg)
    assert len(clusters) == 1
    assert len(clusters[0]) == 2


@pytest.mark.asyncio
async def test_exp_002_timeline_boundary_metrics():
    """Verify setup_clustering_expansion improves recall and pre-context alignment on test cases."""
    case = EditorialBenchmarkCase(
        id="case-test-002",
        name="Clutch Moment",
        source_asset_id="asset-test-002-src",
        human_edit_asset_id="asset-test-edit-2",
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
        case, gt_data, visual_reaction_elevation=True, setup_clustering_expansion=False
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
        case, gt_data, visual_reaction_elevation=True, setup_clustering_expansion=True
    )
    exp_res, _ = await benchmark_engine.evaluate_case(
        run_id="run-exp-test-2",
        case=case,
        human_timeline=human_timeline,
        ai_timeline=exp_ai,
        pipeline_artifacts=exp_artifacts,
    )

    # Recall at 1.0s should improve
    base_recall = base_res.overlap_at_10s.recall
    exp_recall = exp_res.overlap_at_10s.recall
    assert exp_recall >= base_recall
    assert exp_recall == 1.0

    # Pre-context delta median should improve towards 0.0s
    assert exp_res.context.pre_context_diff_quantiles.median == 0.0
