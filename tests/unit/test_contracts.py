"""Unit tests for Pydantic contract schemas."""
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from stream_editor.contracts.edit_plan import EditClip, EditPlan, EditPlanVersion
from stream_editor.contracts.editorial import CandidateSegment, CandidateSegmentScores
from stream_editor.contracts.effects import Effect, EffectType
from stream_editor.contracts.jobs import JobStage, JobStatus
from stream_editor.contracts.timeline import TimelineEvent, TimelineEventType


# ---------------------------------------------------------------------------
# TimelineEvent
# ---------------------------------------------------------------------------

class TestTimelineEvent:
    def test_creation(self, sample_timeline_event: TimelineEvent) -> None:
        assert sample_timeline_event.event_type == TimelineEventType.speech
        assert 0.0 <= sample_timeline_event.confidence <= 1.0

    def test_confidence_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            TimelineEvent(
                id=uuid.uuid4(),
                project_id="proj_1",
                source="test",
                event_type=TimelineEventType.laughter,
                start_seconds=0.0,
                end_seconds=5.0,
                confidence=1.5,  # > 1.0
                structured_data={},
                producer="test",
                producer_version="1.0",
            )

    def test_all_event_types_valid(self) -> None:
        for et in TimelineEventType:
            event = TimelineEvent(
                id=uuid.uuid4(),
                project_id="proj",
                source="test",
                event_type=et,
                start_seconds=0.0,
                end_seconds=1.0,
                confidence=0.8,
                structured_data={},
                producer="test",
                producer_version="1.0",
            )
            assert event.event_type == et

    def test_events_can_overlap(self) -> None:
        """Overlapping events are explicitly allowed — different detectors can overlap."""
        e1 = TimelineEvent(
            id=uuid.uuid4(), project_id="p", source="audio",
            event_type=TimelineEventType.speech,
            start_seconds=0.0, end_seconds=10.0, confidence=0.9,
            structured_data={}, producer="whisper", producer_version="1",
        )
        e2 = TimelineEvent(
            id=uuid.uuid4(), project_id="p", source="audio",
            event_type=TimelineEventType.laughter,
            start_seconds=4.0, end_seconds=8.0, confidence=0.75,
            structured_data={}, producer="audio_classifier", producer_version="1",
        )
        # Both valid — no exception expected
        assert e1.start_seconds < e2.start_seconds < e1.end_seconds


# ---------------------------------------------------------------------------
# CandidateSegment
# ---------------------------------------------------------------------------

class TestCandidateSegment:
    def test_scores_all_zero_to_one(self) -> None:
        scores = CandidateSegmentScores(
            humor=0.0,
            importance=1.0,
            reaction=0.5,
            visual_interest=0.0,
            chat_relevance=0.99,
            story_value=0.01,
            repetition_penalty=0.0,
        )
        for field_name, value in scores.model_dump().items():
            assert 0.0 <= value <= 1.0, f"{field_name} out of range: {value}"

    def test_score_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            CandidateSegmentScores(
                humor=1.5,  # > 1.0
                importance=0.5,
                reaction=0.5,
                visual_interest=0.5,
                chat_relevance=0.5,
                story_value=0.5,
                repetition_penalty=0.5,
            )

    def test_scores_not_collapsed_to_single_value(self) -> None:
        """Individual dimension scores must be preserved, not merged into one opaque score."""
        scores = CandidateSegmentScores(
            humor=0.9, importance=0.2, reaction=0.8,
            visual_interest=0.1, chat_relevance=0.6,
            story_value=0.7, repetition_penalty=0.05,
        )
        dumped = scores.model_dump()
        assert "humor" in dumped
        assert "importance" in dumped
        assert "repetition_penalty" in dumped


# ---------------------------------------------------------------------------
# EditPlan
# ---------------------------------------------------------------------------

def _make_provenance() -> EditPlanVersion:
    return EditPlanVersion(
        version=1,
        created_at=datetime(2026, 9, 14, tzinfo=timezone.utc),
        model_provider="mock",
        model_name="mock-model",
        model_version="1.0",
        prompt_version="editorial-v1.0.0",
    )


def _make_clip(
    source_start: float,
    source_end: float,
    output_position: float,
) -> EditClip:
    return EditClip(
        id=uuid.uuid4(),
        source_asset_id=uuid.uuid4(),
        source_start_seconds=source_start,
        source_end_seconds=source_end,
        output_position_seconds=output_position,
        effects=[],
        narrative_node_ids=[],
        editorial_reason="test clip",
    )


class TestEditPlan:
    def test_valid_plan_with_single_clip(self) -> None:
        plan = EditPlan(
            id=uuid.uuid4(),
            project_id="proj_1",
            version=1,
            clips=[_make_clip(0.0, 30.0, 0.0)],
            transitions=[],
            audio_operations=[],
            provenance=_make_provenance(),
            status="draft",
            narrative_dependencies=[],
        )
        assert plan.version == 1
        assert len(plan.clips) == 1

    def test_overlapping_clips_raises(self) -> None:
        """Clips with overlapping output positions must be rejected."""
        with pytest.raises(ValidationError, match="overlapping output positions"):
            EditPlan(
                id=uuid.uuid4(),
                project_id="proj_1",
                version=1,
                clips=[
                    _make_clip(0.0, 10.0, 0.0),    # occupies output 0-10
                    _make_clip(10.0, 20.0, 5.0),   # starts at 5, overlaps with prev
                ],
                transitions=[],
                audio_operations=[],
                provenance=_make_provenance(),
                status="draft",
                narrative_dependencies=[],
            )

    def test_sequential_clips_are_valid(self) -> None:
        """Non-overlapping sequential clips must be accepted."""
        plan = EditPlan(
            id=uuid.uuid4(),
            project_id="proj_1",
            version=1,
            clips=[
                _make_clip(100.0, 110.0, 0.0),   # output 0-10
                _make_clip(200.0, 215.0, 10.0),  # output 10-25
                _make_clip(300.0, 310.0, 25.0),  # output 25-35
            ],
            transitions=[],
            audio_operations=[],
            provenance=_make_provenance(),
            status="draft",
            narrative_dependencies=[],
        )
        assert len(plan.clips) == 3

    def test_empty_clips_allowed(self) -> None:
        """Empty clips list is allowed (plan is a draft)."""
        plan = EditPlan(
            id=uuid.uuid4(),
            project_id="proj_1",
            version=1,
            clips=[],
            transitions=[],
            audio_operations=[],
            provenance=_make_provenance(),
            status="draft",
            narrative_dependencies=[],
        )
        assert plan.clips == []


# ---------------------------------------------------------------------------
# JobStage ordering
# ---------------------------------------------------------------------------

class TestJobStage:
    def test_ingest_is_first_stage(self) -> None:
        assert JobStage.ingest == "ingest"

    def test_render_final_is_last_stage(self) -> None:
        assert JobStage.render_final == "render_final"

    def test_all_statuses_exist(self) -> None:
        statuses = {s.value for s in JobStatus}
        assert "pending" in statuses
        assert "completed" in statuses
        assert "failed" in statuses
