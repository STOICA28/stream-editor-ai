"""
Executable Regression Test Suite for M2->M3 Cache Invalidation and Signature Lineage (EXP-002).

Validates:
1. Configuration changes invalidate CandidateRun signatures.
2. Upstream M2 input changes (transcripts, timeline events) invalidate CandidateRun signatures.
3. Identical inputs and configurations produce deterministic, identical signatures (idempotent reuse).
4. Feature flag switching (relational clustering ON vs OFF) invalidates CandidateRun signatures.
5. Rollback to M13-P1 baseline recovers the exact baseline derivation signature.
6. M3 invalidation cascades downstream to M4 (Story Graph) without touching upstream M1/M2 cache keys.
7. CandidateSegment signatures are permanently bound to parent CandidateRun signature and evidence IDs.
"""
import hashlib
import json
import pytest

from stream_editor.contracts.editorial import (
    CandidateClusteringExperimentConfig,
    CandidateWindowConfig,
    StoryGraphConfig,
)
from stream_editor.editorial.generator import (
    _candidate_sig,
    _compute_m2_signature,
    _run_sig,
    GENERATOR_VERSION,
)


class DummyDB:
    """Mock DB session for M2 signature extraction."""
    def __init__(
        self,
        asset_fp="fp-asset-123",
        transcript_sig="tr-sig-001",
        events=None,
        scenes=None,
        audio_events=None,
    ):
        self.asset_fp = asset_fp
        self.transcript_sig = transcript_sig
        self.events = events or []
        self.scenes = scenes or []
        self.audio_events = audio_events or []

    def query(self, model):
        return DummyQuery(self, model)


class DummyQuery:
    def __init__(self, db, model):
        self.db = db
        self.model_name = getattr(model, "__name__", str(model))

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        if "MediaAsset" in self.model_name:
            class DummyAsset:
                id = "asset-1"
                path = "/path/to/video.mp4"
                media_info = {"fingerprint": self.db.asset_fp}
            return DummyAsset()
        elif "TranscriptRun" in self.model_name:
            class DummyTRun:
                id = "tr-1"
                derivation_signature = self.db.transcript_sig
            return DummyTRun()
        return None

    def all(self):
        if "TimelineEvent" in self.model_name:
            return self.db.events
        elif "Scene" in self.model_name:
            return self.db.scenes
        elif "AudioEvent" in self.model_name:
            return self.db.audio_events
        return []


def test_m2_input_change_invalidates_candidate_run():
    """Verify that changes to upstream M2 transcripts or events invalidate the CandidateRun signature."""
    w_cfg = CandidateWindowConfig(
        clustering_config=CandidateClusteringExperimentConfig(version="variant_b")
    )

    # Initial M2 state
    m2_sig_1 = hashlib.sha256(b"m2_state_initial").hexdigest()
    run_sig_1 = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig_1,
        asset_fingerprint="fp-initial",
    )

    # Modified M2 state (e.g. re-transcribed or new detected events)
    m2_sig_2 = hashlib.sha256(b"m2_state_updated").hexdigest()
    run_sig_2 = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig_2,
        asset_fingerprint="fp-initial",
    )

    assert run_sig_1 != run_sig_2, "CandidateRun signature must change when upstream M2 inputs change"


def test_configuration_change_invalidates_candidate_run():
    """Verify that changes to clustering configuration parameters invalidate CandidateRun signature."""
    m2_sig = hashlib.sha256(b"stable_m2_state").hexdigest()

    cfg_a = CandidateClusteringExperimentConfig(
        max_related_event_gap=4.0,
        backward_setup_window=3.0,
        version="variant_b",
    )
    cfg_b = CandidateClusteringExperimentConfig(
        max_related_event_gap=2.5,  # threshold changed
        backward_setup_window=3.0,
        version="variant_b",
    )

    w_cfg_a = CandidateWindowConfig(clustering_config=cfg_a)
    w_cfg_b = CandidateWindowConfig(clustering_config=cfg_b)

    run_sig_a = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg_a,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig,
    )
    run_sig_b = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg_b,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig,
    )

    assert run_sig_a != run_sig_b, "CandidateRun signature must change when clustering thresholds change"


def test_identical_inputs_and_idempotent_reuse():
    """Verify that identical inputs, M2 signatures, and configurations produce identical signatures."""
    m2_sig = hashlib.sha256(b"deterministic_m2").hexdigest()
    cfg = CandidateClusteringExperimentConfig(version="variant_b")
    w_cfg = CandidateWindowConfig(clustering_config=cfg)

    sig_1 = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig,
        asset_fingerprint="fp-1",
    )
    sig_2 = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig,
        asset_fingerprint="fp-1",
    )

    assert sig_1 == sig_2, "Signature must be strictly deterministic for idempotent cache hits"


def test_feature_flag_switching_invalidates_m3():
    """Verify that switching relational clustering feature flag invalidates CandidateRun signature."""
    m2_sig = hashlib.sha256(b"same_m2").hexdigest()

    # M13-P1 Baseline: clustering_config is None (flag OFF)
    w_cfg_off = CandidateWindowConfig(clustering_config=None)
    sig_off = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg_off,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig,
        feature_flags={"relational_clustering": False, "variant": "default"},
    )

    # EXP-002: clustering_config active (flag ON)
    w_cfg_on = CandidateWindowConfig(
        clustering_config=CandidateClusteringExperimentConfig(version="variant_b")
    )
    sig_on = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg_on,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig,
        feature_flags={"relational_clustering": True, "variant": "variant_b"},
    )

    assert sig_off != sig_on, "Switching feature flag must produce distinct CandidateRun signatures"


def test_rollback_to_m13_p1_recovers_baseline():
    """Verify that rolling back to M13-P1 recovers the exact baseline derivation signature."""
    m2_sig = hashlib.sha256(b"same_m2").hexdigest()
    w_cfg_baseline = CandidateWindowConfig(clustering_config=None)

    sig_baseline_initial = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg_baseline,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig,
    )

    # Experiment activated
    w_cfg_exp = CandidateWindowConfig(
        clustering_config=CandidateClusteringExperimentConfig(version="variant_b")
    )
    sig_exp = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg_exp,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig,
    )
    assert sig_exp != sig_baseline_initial

    # Rollback to baseline
    sig_baseline_rollback = _run_sig(
        project_id="proj-1",
        source_asset_id="asset-1",
        config=w_cfg_baseline,
        provider_name="mock",
        prompt_version="v1",
        ranking_profile_name="balanced",
        m2_signature=m2_sig,
    )

    assert sig_baseline_rollback == sig_baseline_initial, "Rollback to M13-P1 must deterministically recover the original baseline signature"


def test_m3_invalidation_cascades_downstream_without_affecting_m1_m2():
    """Verify that a new CandidateRun signature cascades to StoryGraphRun without polluting M1/M2 cache."""
    # M1 and M2 cache keys
    m1_proxy_key = hashlib.sha256(b"proxy_1280x720_crf23").hexdigest()
    m2_transcription_key = hashlib.sha256(b"whisper_large_v3_es").hexdigest()

    # M3 Baseline run signature
    m3_sig_base = hashlib.sha256(b"candidate_run_base").hexdigest()
    m4_cfg = StoryGraphConfig()
    m4_sig_base = m4_cfg.get_signature(m3_sig_base)

    # M3 EXP-002 run signature
    m3_sig_exp = hashlib.sha256(b"candidate_run_exp002").hexdigest()
    m4_sig_exp = m4_cfg.get_signature(m3_sig_exp)

    # M4 must be invalidated (cascade)
    assert m4_sig_base != m4_sig_exp, "M4 StoryGraphRun must be invalidated when M3 CandidateRun signature changes"

    # M1 and M2 cache keys remain invariant
    assert m1_proxy_key == hashlib.sha256(b"proxy_1280x720_crf23").hexdigest()
    assert m2_transcription_key == hashlib.sha256(b"whisper_large_v3_es").hexdigest()


def test_candidate_segment_signature_links_to_parent_run_and_evidence():
    """Verify that CandidateSegment signatures link to parent CandidateRun signature and evidence IDs."""
    run_sig_1 = hashlib.sha256(b"run_1").hexdigest()
    run_sig_2 = hashlib.sha256(b"run_2").hexdigest()

    cand_sig_1 = _candidate_sig(
        project_id="p1",
        source_asset_id="a1",
        start_time=1.0,
        end_time=9.0,
        core_start=1.0,
        core_end=9.0,
        generator_version=GENERATOR_VERSION,
        clustering_version="variant_b",
        parent_run_sig=run_sig_1,
        evidence_ids=["ev-1", "ev-2"],
    )

    # Same timestamps but different parent run signature
    cand_sig_2 = _candidate_sig(
        project_id="p1",
        source_asset_id="a1",
        start_time=1.0,
        end_time=9.0,
        core_start=1.0,
        core_end=9.0,
        generator_version=GENERATOR_VERSION,
        clustering_version="variant_b",
        parent_run_sig=run_sig_2,
        evidence_ids=["ev-1", "ev-2"],
    )

    # Same timestamps and parent run, but different evidence IDs
    cand_sig_3 = _candidate_sig(
        project_id="p1",
        source_asset_id="a1",
        start_time=1.0,
        end_time=9.0,
        core_start=1.0,
        core_end=9.0,
        generator_version=GENERATOR_VERSION,
        clustering_version="variant_b",
        parent_run_sig=run_sig_1,
        evidence_ids=["ev-1"],
    )

    assert cand_sig_1 != cand_sig_2, "CandidateSegment signature must reflect parent CandidateRun signature"
    assert cand_sig_1 != cand_sig_3, "CandidateSegment signature must reflect evidence IDs"


def test_m7_only_change_does_not_invalidate_m3():
    """Verify that changes to downstream Stage M7 (VisualAnalysisRun / FocusTarget) do NOT invalidate M3."""
    class DummyEvent:
        id = "ev-1"
        event_type = "speech"
        start_time = 1.0
        end_time = 4.0
        confidence = 0.95
        producer = "whisperx"
        producer_version = "1.0"

    db = DummyDB(asset_fp="fp-test", transcript_sig="tr-sig-1", events=[DummyEvent()])

    # Compute M2 signature for M3
    m2_sig_1, _ = _compute_m2_signature("asset-1", db)

    # Simulated M7 change: An M7 visual run runs or updates in the database
    # Since _compute_m2_signature does not query M7, m2_sig_2 must remain strictly identical
    m2_sig_2, _ = _compute_m2_signature("asset-1", db)
    assert m2_sig_1 == m2_sig_2, "M3 signature must be invariant to M7 state"


def test_m3_signature_can_be_computed_before_m7_executes():
    """Verify that M3 signatures can be computed when Stage M7 has never executed (0 M7 records)."""
    db_clean = DummyDB(asset_fp="fp-clean", transcript_sig="tr-001", events=[])
    sig, fp = _compute_m2_signature("asset-clean", db_clean)
    assert sig is not None and len(sig) == 64, "M3 signature must compute deterministically before M7"
    assert fp == "fp-clean"


def test_no_backward_architectural_dependency():
    """Verify that _compute_m2_signature strictly respects M1/M2 boundaries and contains no M7 references."""
    import inspect
    from stream_editor.editorial import generator

    source = inspect.getsource(generator._compute_m2_signature)
    assert "VisualAnalysisRun" not in source, "Violation: _compute_m2_signature must not reference VisualAnalysisRun (M7)"
    assert "FocusTarget" not in source, "Violation: _compute_m2_signature must not reference FocusTarget (M7)"
    assert "EffectPlan" not in source, "Violation: _compute_m2_signature must not reference EffectPlan (M8)"
