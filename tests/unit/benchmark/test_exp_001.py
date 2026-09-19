import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import pytest
from stream_editor.contracts.editorial import LocalFeatures, ScoreComponents
from stream_editor.editorial.features import LocalFeatureExtractor
from stream_editor.editorial.context import SceneData, TranscriptSegmentData


def test_local_feature_extractor_counts_visual_reactions() -> None:
    """Verify LocalFeatureExtractor extracts visual reaction and event counts."""
    segments = [
        TranscriptSegmentData(id="s1", start_time=1.0, end_time=3.0, text="hello world", speaker="spk1")
    ]
    events = [
        {"start_time": 1.5, "end_time": 2.0, "event_type": "speech"},
        {"start_time": 3.5, "end_time": 4.5, "event_type": "face_reaction"},
        {"start_time": 4.0, "end_time": 4.5, "event_type": "strong_face_reaction"},
        {"start_time": 5.0, "end_time": 6.0, "event_type": "visual_event"},
        {"start_time": 7.0, "end_time": 8.0, "event_type": "audio_peak"},
    ]
    scenes = [SceneData(id="sc1", start_time=0.0, end_time=10.0)]

    features = LocalFeatureExtractor.extract(
        segments=segments,
        events=events,
        scenes=scenes,
        start_time=0.0,
        end_time=10.0,
    )

    assert features.visual_reaction_count == 2
    assert features.visual_event_count == 3
    assert features.audio_peaks == 1


def test_score_components_supports_reaction_and_humor() -> None:
    """Verify ScoreComponents supports reaction and humor scores for EXP-001."""
    scores = ScoreComponents(
        reaction=0.85,
        humor=0.75,
        visual_interest=0.90,
    )
    dumped = scores.to_dict()
    assert dumped["reaction"] == 0.85
    assert dumped["humor"] == 0.75
    assert dumped["visual_interest"] == 0.90


@pytest.mark.asyncio
async def test_exp_001_simulation_metrics() -> None:
    """Verify EXP-001 evaluation delta against baseline."""
    from scripts.run_exp_001 import execute_exp_001

    verdict, payload = await execute_exp_001()
    assert verdict == "PASSED"
    assert payload["exp_001"]["recall_10"] > 0.70
    assert payload["exp_001"]["precision_10"] >= 0.70
    assert payload["exp_001"]["setup_payoff_completeness"] == 1.0
    assert payload["exp_001"]["m2_misses"] == 0
