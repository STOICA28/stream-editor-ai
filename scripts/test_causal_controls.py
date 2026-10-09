"""
Automated Executable Causal Relation and Negative-Control Validation (EXP-002).
Verifies that bounded clustering joins only causally supported relationships
and rejects unrelated events even when temporally adjacent.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages" / "contracts" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "editorial" / "src"))

from stream_editor.contracts.editorial import (
    CandidateClusteringExperimentConfig,
    CandidateRelationType,
)
from stream_editor.editorial.windowing import (
    CandidateRelationClassifier,
    EventClusterer,
)


def run_all_causal_controls() -> dict[str, str]:
    frozen_cfg = CandidateClusteringExperimentConfig(
        max_backward_context=3.0,
        max_forward_context=3.0,
        max_related_event_gap=4.0,
        reaction_link_window=2.0,
        speech_continuity_gap=1.5,
        pause_snap_threshold=0.3,
        scene_boundary_hard_stop=True,
        minimum_relation_confidence=0.6,
        version="exp002_variant_b",
    )
    clusterer = EventClusterer()
    verdicts = {}

    print("=" * 80)
    print("EXECUTING CAUSAL RELATION NEGATIVE-CONTROL VALIDATION (EXP-002)")
    print("=" * 80)

    # 1. Negative Control 1: Same speaker, pause > 1.5s (gap=2.2s > speech_continuity_gap 1.5s)
    e1_speech_a = {"id": "sp1", "start_time": 10.0, "end_time": 14.0, "event_type": "speech", "speaker": "streamer", "topic": "game_strategy"}
    e2_speech_b = {"id": "sp2", "start_time": 16.2, "end_time": 19.0, "event_type": "speech", "speaker": "streamer", "topic": "reading_donation"}
    rel_1 = CandidateRelationClassifier.classify_relation(e1_speech_a, e2_speech_b, frozen_cfg)
    clusters_1 = clusterer.cluster([e1_speech_a, e2_speech_b], merge_gap=3.0, clustering_config=frozen_cfg)

    assert rel_1.relation_type == CandidateRelationType.UNRELATED, f"Expected UNRELATED, got {rel_1.relation_type}"
    assert rel_1.confidence < frozen_cfg.minimum_relation_confidence, f"Confidence too high: {rel_1.confidence}"
    assert len(clusters_1) == 2, f"Expected 2 clusters (no merge), got {len(clusters_1)}"
    verdicts["control_1_speaker_pause"] = "PASSED"
    print("  [PASS] Control 1: Speaker pause > 1.5s rejected correctly (2 clusters)")

    # 2. Negative Control 2: Gameplay event followed by unrelated facial movement (conf=0.45, gap=2.5s)
    e3_game = {"id": "g1", "start_time": 30.0, "end_time": 33.0, "event_type": "gameplay", "description": "routine resource gathering"}
    e4_face = {"id": "f1", "start_time": 35.5, "end_time": 37.0, "event_type": "face_reaction", "confidence": 0.45, "description": "minor blink/head turn"}
    rel_2 = CandidateRelationClassifier.classify_relation(e3_game, e4_face, frozen_cfg)
    clusters_2 = clusterer.cluster([e3_game, e4_face], merge_gap=3.0, clustering_config=frozen_cfg)

    assert rel_2.confidence < frozen_cfg.minimum_relation_confidence, f"Confidence too high: {rel_2.confidence}"
    assert len(clusters_2) == 2, f"Expected 2 clusters (no merge), got {len(clusters_2)}"
    verdicts["control_2_unrelated_movement"] = "PASSED"
    print("  [PASS] Control 2: Low-confidence/unrelated movement rejected correctly (2 clusters)")

    # 3. Negative Control 3: Speech setup followed by delayed reaction (gap=4.5s > max_related_event_gap 4.0s)
    e5_setup = {"id": "s1", "start_time": 50.0, "end_time": 53.0, "event_type": "speech", "is_trigger": True, "text": "Check out this jump"}
    e6_late_rx = {"id": "f2", "start_time": 57.5, "end_time": 59.0, "event_type": "face_reaction", "confidence": 0.90}
    rel_3 = CandidateRelationClassifier.classify_relation(e5_setup, e6_late_rx, frozen_cfg)
    clusters_3 = clusterer.cluster([e5_setup, e6_late_rx], merge_gap=3.0, clustering_config=frozen_cfg)

    assert rel_3.relation_type == CandidateRelationType.UNRELATED, f"Expected UNRELATED, got {rel_3.relation_type}"
    assert rel_3.confidence == 0.0, f"Expected 0.0 confidence, got {rel_3.confidence}"
    assert len(clusters_3) == 2, f"Expected 2 clusters (no merge), got {len(clusters_3)}"
    verdicts["control_3_delayed_reaction"] = "PASSED"
    print("  [PASS] Control 3: Temporal gap exceeding 4.0s rejected correctly (2 clusters)")

    # 4. Negative Control 4: Related events separated by an ordinary scene transition
    e7_setup = {"id": "s2", "start_time": 70.0, "end_time": 72.0, "event_type": "speech", "text": "Next game starting"}
    e8_reaction = {"id": "f3", "start_time": 72.8, "end_time": 74.5, "event_type": "face_reaction", "confidence": 0.92}
    scenes = [{"start_time": 72.4, "end_time": 80.0}]
    rel_4 = CandidateRelationClassifier.classify_relation(e7_setup, e8_reaction, frozen_cfg, scenes=scenes)
    clusters_4 = clusterer.cluster([e7_setup, e8_reaction], merge_gap=3.0, clustering_config=frozen_cfg, scenes=scenes)

    assert rel_4.same_scene is False, "Expected same_scene=False across scene cut"
    assert rel_4.relation_type == CandidateRelationType.UNRELATED, f"Expected UNRELATED, got {rel_4.relation_type}"
    assert len(clusters_4) == 2, f"Expected 2 clusters (no merge), got {len(clusters_4)}"
    verdicts["control_4_scene_boundary"] = "PASSED"
    print("  [PASS] Control 4: Scene boundary hard stop prevented merge (2 clusters)")

    # 5. Negative Control 5 (5-Second Gap Contradiction Resolution):
    # Real VOD events: speech setup [20.0, 45.0], gameplay clutch [50.0, 65.0], gap = 5.0s
    e_real_1 = {"id": "te-r004-1", "start_time": 20.0, "end_time": 45.0, "event_type": "speech", "speaker": "streamer"}
    e_real_2 = {"id": "te-r004-2", "start_time": 50.0, "end_time": 65.0, "event_type": "gameplay_clutch"}
    rel_5 = CandidateRelationClassifier.classify_relation(e_real_1, e_real_2, frozen_cfg)
    clusters_5 = clusterer.cluster([e_real_1, e_real_2], merge_gap=3.0, clustering_config=frozen_cfg)

    assert rel_5.temporal_gap == 5.0, f"Expected gap=5.0s, got {rel_5.temporal_gap}"
    assert rel_5.relation_type == CandidateRelationType.UNRELATED, f"Expected UNRELATED for 5.0s gap, got {rel_5.relation_type}"
    assert rel_5.confidence == 0.0, f"Expected confidence 0.0, got {rel_5.confidence}"
    assert len(clusters_5) == 2, f"Expected 2 separate clusters (0 merges), got {len(clusters_5)}"
    verdicts["control_5_real_vod_5s_gap"] = "PASSED"
    print("  [PASS] Control 5: Real VOD 5.0s gap strictly exceeds 4.0s bound -> 0 merges executed (2 clusters)")

    # 6. Negative Control 6: Same scene, gap within relation window (1.0s), but different speakers
    e_spk1 = {"id": "spk1", "start_time": 10.0, "end_time": 12.0, "event_type": "speech", "speaker": "player1"}
    e_spk2 = {"id": "spk2", "start_time": 13.0, "end_time": 15.0, "event_type": "speech", "speaker": "player2"}
    rel_6 = CandidateRelationClassifier.classify_relation(e_spk1, e_spk2, frozen_cfg)
    clusters_6 = clusterer.cluster([e_spk1, e_spk2], merge_gap=3.0, clustering_config=frozen_cfg)

    assert rel_6.speaker_continuity is False, "Expected speaker_continuity=False"
    assert rel_6.relation_type == CandidateRelationType.UNRELATED, f"Expected UNRELATED on speaker change, got {rel_6.relation_type}"
    assert len(clusters_6) == 2, f"Expected 2 clusters (no merge), got {len(clusters_6)}"
    verdicts["control_6_speaker_change"] = "PASSED"
    print("  [PASS] Control 6: Speaker change within 1.0s rejected correctly (2 clusters)")

    # 7. Negative Control 7: Same scene, gap within window (1.0s), game action followed by non-reaction speech
    e_act = {"id": "act1", "start_time": 20.0, "end_time": 22.0, "event_type": "game_event"}
    e_spk = {"id": "spk3", "start_time": 23.0, "end_time": 25.0, "event_type": "speech"}
    rel_7 = CandidateRelationClassifier.classify_relation(e_act, e_spk, frozen_cfg)
    clusters_7 = clusterer.cluster([e_act, e_spk], merge_gap=3.0, clustering_config=frozen_cfg)

    assert rel_7.relation_type != CandidateRelationType.EVENT_TO_REACTION, "Should not classify speech as EVENT_TO_REACTION"
    assert len(clusters_7) == 2, f"Expected 2 clusters (no merge), got {len(clusters_7)}"
    verdicts["control_7_action_to_speech"] = "PASSED"
    print("  [PASS] Control 7: Action followed by ordinary speech rejected correctly (2 clusters)")

    # 8. Positive Control: True speech setup + face reaction in same scene within link window (gap=1.0s)
    e9_setup = {"id": "s3", "start_time": 90.0, "end_time": 92.5, "event_type": "speech", "text": "I can hit this"}
    e10_reaction = {"id": "f4", "start_time": 93.5, "end_time": 95.0, "event_type": "face_reaction", "confidence": 0.92}
    rel_8 = CandidateRelationClassifier.classify_relation(e9_setup, e10_reaction, frozen_cfg)
    clusters_8 = clusterer.cluster([e9_setup, e10_reaction], merge_gap=3.0, clustering_config=frozen_cfg)

    assert rel_8.relation_type == CandidateRelationType.SETUP_TO_PAYOFF, f"Expected SETUP_TO_PAYOFF, got {rel_8.relation_type}"
    assert rel_8.confidence >= 0.90, f"Expected confidence >= 0.90, got {rel_8.confidence}"
    assert len(clusters_8) == 1, f"Expected 1 merged cluster, got {len(clusters_8)}"
    verdicts["control_8_positive_setup_payoff"] = "PASSED"
    print("  [PASS] Control 8 (Positive Control): True setup + payoff merged correctly (1 cluster)")

    print("\nALL CAUSAL CONTROLS PASSED AUTOMATED ASSERTIONS SUCCESSFULLY.")
    return verdicts


def test_causal_negative_controls():
    """Pytest entrypoint."""
    verdicts = run_all_causal_controls()
    assert all(v == "PASSED" for v in verdicts.values())


if __name__ == "__main__":
    run_all_causal_controls()
