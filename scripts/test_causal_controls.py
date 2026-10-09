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

print("=" * 80)
print("CAUSAL RELATION NEGATIVE-CONTROL VALIDATION (EXP-002)")
print("=" * 80)

# 1. Same speaker but different topic (or pause > 1.5s)
e1_speech_a = {"id": "sp1", "start_time": 10.0, "end_time": 14.0, "event_type": "speech", "speaker": "streamer", "topic": "game_strategy"}
e2_speech_b = {"id": "sp2", "start_time": 16.2, "end_time": 19.0, "event_type": "speech", "speaker": "streamer", "topic": "reading_donation"}
# Gap = 2.2s (> 1.5s speech_continuity_gap)
rel_1 = CandidateRelationClassifier.classify_relation(e1_speech_a, e2_speech_b, frozen_cfg)
clusters_1 = clusterer.cluster([e1_speech_a, e2_speech_b], merge_gap=3.0, clustering_config=frozen_cfg)

print(f"\nTest 1: Same speaker, topic switch / pause > 1.5s (gap=2.2s)")
print(f"  Relation: {rel_1.relation_type.value} | Confidence: {rel_1.confidence:.2f} | Notes: {rel_1.evidence_notes}")
print(f"  Clusters count: {len(clusters_1)} (Expected: 2 clusters, NO MERGE)")

# 2. Gameplay event followed by unrelated facial movement (e.g., ordinary face / low confidence reaction / delay > 2.0s)
e3_game = {"id": "g1", "start_time": 30.0, "end_time": 33.0, "event_type": "gameplay", "description": "routine resource gathering"}
e4_face = {"id": "f1", "start_time": 35.5, "end_time": 37.0, "event_type": "face_reaction", "confidence": 0.45, "description": "minor blink/head turn"}
# Gap = 2.5s (> 2.0s reaction_link_window) and confidence < 0.60
rel_2 = CandidateRelationClassifier.classify_relation(e3_game, e4_face, frozen_cfg)
clusters_2 = clusterer.cluster([e3_game, e4_face], merge_gap=3.0, clustering_config=frozen_cfg)

print(f"\nTest 2: Gameplay event followed by unrelated movement (gap=2.5s, conf=0.45)")
print(f"  Relation: {rel_2.relation_type.value} | Confidence: {rel_2.confidence:.2f} | Notes: {rel_2.evidence_notes}")
print(f"  Clusters count: {len(clusters_2)} (Expected: 2 clusters, NO MERGE)")

# 3. Speech setup followed by unrelated reaction (gap > 4.0s)
e5_setup = {"id": "s1", "start_time": 50.0, "end_time": 53.0, "event_type": "speech", "is_trigger": True, "text": "Check out this jump"}
e6_late_rx = {"id": "f2", "start_time": 57.5, "end_time": 59.0, "event_type": "face_reaction", "confidence": 0.90}
# Gap = 4.5s (> 4.0s max_related_event_gap)
rel_3 = CandidateRelationClassifier.classify_relation(e5_setup, e6_late_rx, frozen_cfg)
clusters_3 = clusterer.cluster([e5_setup, e6_late_rx], merge_gap=3.0, clustering_config=frozen_cfg)

print(f"\nTest 3: Speech setup followed by delayed/unrelated reaction (gap=4.5s)")
print(f"  Relation: {rel_3.relation_type.value} | Confidence: {rel_3.confidence:.2f} | Notes: {rel_3.evidence_notes}")
print(f"  Clusters count: {len(clusters_3)} (Expected: 2 clusters, NO MERGE)")

# 4. Related events separated by an ordinary scene transition
e7_setup = {"id": "s2", "start_time": 70.0, "end_time": 72.0, "event_type": "speech", "text": "Next game starting"}
e8_reaction = {"id": "f3", "start_time": 72.8, "end_time": 74.5, "event_type": "face_reaction", "confidence": 0.92}
# Gap = 0.8s, BUT scene cut at 72.4s
scenes = [{"start_time": 72.4, "end_time": 80.0}]
rel_4 = CandidateRelationClassifier.classify_relation(e7_setup, e8_reaction, frozen_cfg, scenes=scenes)
clusters_4 = clusterer.cluster([e7_setup, e8_reaction], merge_gap=3.0, clustering_config=frozen_cfg, scenes=scenes)

print(f"\nTest 4: Related events separated by scene cut (gap=0.8s, cut at 72.4s)")
print(f"  Relation: {rel_4.relation_type.value} | Confidence: {rel_4.confidence:.2f} | Same Scene: {rel_4.same_scene} | Notes: {rel_4.evidence_notes}")
print(f"  Clusters count: {len(clusters_4)} (Expected: 2 clusters, NO MERGE)")

# 5. True Positive Control: Valid setup and reaction in same scene within window
e9_setup = {"id": "s3", "start_time": 90.0, "end_time": 92.5, "event_type": "speech", "text": "I can hit this"}
e10_reaction = {"id": "f4", "start_time": 93.5, "end_time": 95.0, "event_type": "face_reaction", "confidence": 0.92}
rel_5 = CandidateRelationClassifier.classify_relation(e9_setup, e10_reaction, frozen_cfg)
clusters_5 = clusterer.cluster([e9_setup, e10_reaction], merge_gap=3.0, clustering_config=frozen_cfg)

print(f"\nTest 5 (Positive Control): True setup + reaction in same scene (gap=1.0s)")
print(f"  Relation: {rel_5.relation_type.value} | Confidence: {rel_5.confidence:.2f} | Notes: {rel_5.evidence_notes}")
print(f"  Clusters count: {len(clusters_5)} (Expected: 1 cluster, MERGED)")
