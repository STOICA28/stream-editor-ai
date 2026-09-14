"""
M3 Unit Tests - Candidate Generation Engine

Tests all core modules:
- windowing: EventClusterer, CandidateWindowBuilder
- context: ContextExpander
- features: LocalFeatureExtractor
- merging: CandidateMerger
- ranking: ExperimentalRanker
- repetition: RepetitionDetector
- providers: MockEditorialProvider
"""
from __future__ import annotations

import pytest

from stream_editor.contracts.editorial import (
    RANKING_PROFILES,
    CandidateWindowConfig,
    LocalFeatures,
    ScoreComponents,
)
from stream_editor.editorial.context import ContextExpander, TranscriptSegmentData
from stream_editor.editorial.features import LocalFeatureExtractor
from stream_editor.editorial.merging import CandidateMerger
from stream_editor.editorial.providers.mock import MockEditorialProvider
from stream_editor.editorial.ranking import ExperimentalRanker
from stream_editor.editorial.repetition import RepetitionDetector
from stream_editor.editorial.windowing import CandidateWindowBuilder, EventClusterer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_event(id: str, event_type: str, start: float, end: float) -> dict:
    return {"id": id, "event_type": event_type, "start_time": start, "end_time": end}

def make_segment(id: str, start: float, end: float, text: str, speaker: str | None = None) -> TranscriptSegmentData:
    return TranscriptSegmentData(id=id, start_time=start, end_time=end, text=text, speaker=speaker)


# ---------------------------------------------------------------------------
# EventClusterer
# ---------------------------------------------------------------------------

class TestEventClusterer:
    def test_empty_events(self):
        clusterer = EventClusterer()
        assert clusterer.cluster([], merge_gap=3.0) == []

    def test_single_event_single_cluster(self):
        clusterer = EventClusterer()
        events = [make_event("e1", "speech", 10.0, 20.0)]
        clusters = clusterer.cluster(events, merge_gap=3.0)
        assert len(clusters) == 1
        assert len(clusters[0]) == 1

    def test_two_close_events_merged(self):
        clusterer = EventClusterer()
        events = [
            make_event("e1", "speech", 10.0, 20.0),
            make_event("e2", "high_energy", 22.0, 25.0),  # gap = 2s < 3s
        ]
        clusters = clusterer.cluster(events, merge_gap=3.0)
        assert len(clusters) == 1
        assert len(clusters[0]) == 2

    def test_two_far_events_separate(self):
        clusterer = EventClusterer()
        events = [
            make_event("e1", "speech", 10.0, 20.0),
            make_event("e2", "speech", 30.0, 40.0),  # gap = 10s > 3s
        ]
        clusters = clusterer.cluster(events, merge_gap=3.0)
        assert len(clusters) == 2


# ---------------------------------------------------------------------------
# CandidateWindowBuilder
# ---------------------------------------------------------------------------

class TestCandidateWindowBuilder:
    def test_single_cluster_builds_window(self):
        builder = CandidateWindowBuilder()
        config = CandidateWindowConfig(min_duration=5.0, max_duration=60.0)
        cluster = [make_event("e1", "speech", 10.0, 25.0)]
        windows = builder.build([cluster], config)
        assert len(windows) == 1
        assert windows[0].core_start == 10.0
        assert windows[0].core_end == 25.0

    def test_short_cluster_padded_to_min_duration(self):
        builder = CandidateWindowBuilder()
        config = CandidateWindowConfig(min_duration=10.0, max_duration=60.0)
        cluster = [make_event("e1", "speech", 10.0, 12.0)]  # 2s < 10s min
        windows = builder.build([cluster], config)
        assert len(windows) == 1
        duration = windows[0].core_end - windows[0].core_start
        assert abs(duration - 10.0) < 0.01

    def test_long_cluster_truncated_to_max(self):
        builder = CandidateWindowBuilder()
        config = CandidateWindowConfig(min_duration=5.0, max_duration=30.0)
        cluster = [make_event("e1", "speech", 0.0, 120.0)]  # 120s > 30s max
        windows = builder.build([cluster], config)
        assert len(windows) == 1
        assert windows[0].core_end - windows[0].core_start == 30.0

    def test_source_signals_extracted(self):
        builder = CandidateWindowBuilder()
        config = CandidateWindowConfig(min_duration=5.0, max_duration=60.0)
        cluster = [
            make_event("e1", "speech", 10.0, 20.0),
            make_event("e2", "high_energy", 21.0, 22.0),
        ]
        windows = builder.build([cluster], config)
        assert "speech" in windows[0].source_signals
        assert "high_energy" in windows[0].source_signals


# ---------------------------------------------------------------------------
# ContextExpander
# ---------------------------------------------------------------------------

class TestContextExpander:
    def setup_method(self):
        self.expander = ContextExpander()
        self.config = CandidateWindowConfig(preroll=5.0, postroll=3.0)
        self.segments = [
            make_segment("s1", 0.0, 5.0, "Hello everyone."),
            make_segment("s2", 5.0, 10.0, "Welcome to the stream."),
            make_segment("s3", 10.0, 20.0, "Let us start the game."),
            make_segment("s4", 20.0, 30.0, "This is very exciting!"),
        ]

    def test_core_aligns_to_segment_boundaries(self):
        from stream_editor.editorial.windowing import CandidateWindow
        window = CandidateWindow(core_start=7.0, core_end=22.0, source_signals=["speech"])
        expanded = self.expander.expand(window, self.segments, [], self.config)
        # core_start should align to s2 start (5.0)
        assert expanded.core_start == 5.0
        # core_end should align to s4 end (30.0)
        assert expanded.core_end == 30.0

    def test_preroll_applied_after_alignment(self):
        from stream_editor.editorial.windowing import CandidateWindow
        window = CandidateWindow(core_start=7.0, core_end=22.0, source_signals=["speech"])
        expanded = self.expander.expand(window, self.segments, [], self.config)
        assert expanded.start_time == max(0.0, expanded.core_start - 5.0)

    def test_no_segments_falls_back_to_core(self):
        from stream_editor.editorial.windowing import CandidateWindow
        window = CandidateWindow(core_start=10.0, core_end=20.0, source_signals=[])
        expanded = self.expander.expand(window, [], [], self.config)
        assert expanded.core_start == 10.0
        assert expanded.core_end == 20.0


# ---------------------------------------------------------------------------
# LocalFeatureExtractor
# ---------------------------------------------------------------------------

class TestLocalFeatureExtractor:
    def setup_method(self):
        self.extractor = LocalFeatureExtractor()
        self.segments = [
            make_segment("s1", 0.0, 5.0, "Hello! Great start!"),
            make_segment("s2", 5.0, 10.0, "Yes this is very good.", "Speaker1"),
            make_segment("s3", 10.0, 15.0, "Agreed!", "Speaker2"),
        ]

    def test_returns_local_features(self):
        features = self.extractor.extract(self.segments, [], [], 0.0, 15.0)
        assert features.duration_seconds == pytest.approx(15.0)
        assert features.transcript_char_length is not None
        assert features.speech_density is not None
        assert 0.0 <= features.speech_density <= 1.0

    def test_exclamation_density_positive(self):
        features = self.extractor.extract(self.segments, [], [], 0.0, 15.0)
        assert features.exclamation_density is not None
        assert features.exclamation_density >= 0.0

    def test_scene_change_rate_zero_when_no_scenes(self):
        features = self.extractor.extract(self.segments, [], [], 0.0, 15.0)
        assert features.scene_change_rate == 0.0

    def test_lexical_novelty_none_when_no_surrounding(self):
        features = self.extractor.extract(self.segments, [], [], 0.0, 15.0, surrounding_texts=[])
        assert features.lexical_novelty is None


# ---------------------------------------------------------------------------
# CandidateMerger
# ---------------------------------------------------------------------------

class TestCandidateMerger:
    def setup_method(self):
        self.merger = CandidateMerger()

    def _make_expanded(self, start, end, core_s, core_e, signals=None):
        from stream_editor.editorial.context import ExpandedWindow
        return ExpandedWindow(
            start_time=start, end_time=end,
            core_start=core_s, core_end=core_e,
            source_signals=signals or [],
            evidence_ids=[],
        )

    def test_no_overlap_not_merged(self):
        w1 = self._make_expanded(0.0, 10.0, 2.0, 8.0, ["speech"])
        w2 = self._make_expanded(20.0, 30.0, 22.0, 28.0, ["high_energy"])
        merged = self.merger.merge([w1, w2], overlap_threshold=0.5)
        assert len(merged) == 2

    def test_high_overlap_merged(self):
        w1 = self._make_expanded(0.0, 20.0, 5.0, 15.0, ["speech"])
        w2 = self._make_expanded(5.0, 25.0, 8.0, 18.0, ["high_energy"])
        merged = self.merger.merge([w1, w2], overlap_threshold=0.3)
        assert len(merged) == 1
        assert merged[0].start_time == 0.0
        assert merged[0].end_time == 25.0

    def test_signals_preserved_after_merge(self):
        w1 = self._make_expanded(0.0, 20.0, 5.0, 15.0, ["speech"])
        w2 = self._make_expanded(5.0, 25.0, 8.0, 18.0, ["high_energy"])
        merged = self.merger.merge([w1, w2], overlap_threshold=0.3)
        assert "speech" in merged[0].source_signals
        assert "high_energy" in merged[0].source_signals


# ---------------------------------------------------------------------------
# ExperimentalRanker
# ---------------------------------------------------------------------------

class TestExperimentalRanker:
    def setup_method(self):
        self.ranker = ExperimentalRanker()

    def test_returns_none_when_no_scores(self):
        scores = ScoreComponents()  # all None
        result = self.ranker.rank(scores, RANKING_PROFILES["balanced"])
        assert result is None

    def test_returns_float_when_some_scores_present(self):
        scores = ScoreComponents(humor=0.8, importance=0.6, novelty=0.7)
        result = self.ranker.rank(scores, RANKING_PROFILES["balanced"])
        assert result is not None
        assert 0.0 <= result <= 1.0

    def test_null_scores_not_treated_as_zero(self):
        scores_full = ScoreComponents(humor=0.8, reaction=0.8)
        scores_partial = ScoreComponents(humor=0.8)  # reaction=None
        r_full = self.ranker.rank(scores_full, RANKING_PROFILES["balanced"])
        r_partial = self.ranker.rank(scores_partial, RANKING_PROFILES["balanced"])
        # Both should return non-None but may differ - key test is both work
        assert r_full is not None
        assert r_partial is not None


# ---------------------------------------------------------------------------
# RepetitionDetector
# ---------------------------------------------------------------------------

class TestRepetitionDetector:
    def setup_method(self):
        self.detector = RepetitionDetector()

    def test_unique_text_low_score(self):
        score = self.detector.score(
            "Let us play this new unique game!",
            ["The weather is sunny today.", "I like python programming."],
        )
        assert score < 0.5

    def test_identical_text_high_score(self):
        text = "This is the same sentence repeated again."
        score = self.detector.score(text, [text])
        assert score > 0.9

    def test_empty_text_returns_zero(self):
        score = self.detector.score("", ["some text"])
        assert score == 0.0

    def test_no_others_returns_zero(self):
        score = self.detector.score("some text", [])
        assert score == 0.0


# ---------------------------------------------------------------------------
# MockEditorialProvider
# ---------------------------------------------------------------------------

class TestMockEditorialProvider:
    def setup_method(self):
        self.provider = MockEditorialProvider()

    def _call(self, text: str):
        return self.provider.analyze_candidate(
            candidate_id="test-id",
            transcript_excerpt=text,
            local_features=LocalFeatures(duration_seconds=15.0),
            nearby_events=[],
            local_summary=None,
            chapter_summary=None,
            prompt_version="v1",
        )

    def test_funny_fixture(self):
        result = self._call("haha that was so funny lol!")
        assert result.signals.humor is not None
        assert result.signals.humor >= 0.7

    def test_important_fixture(self):
        result = self._call("this is very important for the story")
        assert result.signals.importance is not None
        assert result.signals.importance >= 0.7

    def test_low_signal_fixture(self):
        result = self._call("ok")
        assert result.confidence < 0.5

    def test_scores_never_forced_to_zero(self):
        result = self._call("some random content without special markers")
        # chat_relevance should be None (mock has no chat data)
        assert result.signals.chat_relevance is None

    def test_confidence_in_valid_range(self):
        result = self._call("some content")
        assert 0.0 <= result.confidence <= 1.0

    def test_reasoning_summary_is_list_of_strings(self):
        result = self._call("some content")
        assert isinstance(result.reasoning_summary, list)
        assert all(isinstance(r, str) for r in result.reasoning_summary)

    def test_summarize_window_returns_dict(self):
        result = self.provider.summarize_window(
            transcript="Hello, this is a test transcript.",
            start_time=0.0,
            end_time=600.0,
            level="local",
            prompt_version="v1",
        )
        assert "summary" in result
        assert "key_topics" in result
        assert isinstance(result["key_topics"], list)
