import pytest
import tempfile
import uuid
from pathlib import Path
from stream_editor.contracts.timeline import TimelineEvent, TimelineEventType
from stream_editor.contracts.editorial import CandidateSegment, CandidateSegmentScores
from stream_editor.contracts.edit_plan import EditPlan, EditPlanVersion, EditClip
from stream_editor.models.mock_provider import MockProvider

@pytest.fixture
def tmp_storage():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def mock_provider():
    return MockProvider()

@pytest.fixture
def sample_timeline_event():
    return TimelineEvent(
        id=uuid.uuid4(),
        project_id="proj_1",
        source="system",
        event_type=TimelineEventType.speech,
        start_seconds=0.0,
        end_seconds=5.0,
        confidence=0.9,
        structured_data={},
        producer="test",
        producer_version="1.0"
    )

@pytest.fixture
def sample_candidate_segment():
    return CandidateSegment(
        id=uuid.uuid4(),
        project_id="proj_1",
        start_seconds=10.0,
        end_seconds=15.0,
        scores=CandidateSegmentScores(humor=0.8, importance=0.9, reaction=0.5, visual_interest=0.7, chat_relevance=0.6, story_value=0.8, repetition_penalty=0.1),
        narrative_context="test",
        selected_timeline_events=[]
    )

@pytest.fixture
def sample_edit_plan():
    return EditPlan(
        id=uuid.uuid4(),
        project_id="proj_1",
        version=1,
        clips=[],
        transitions=[],
        audio_operations=[],
        provenance=EditPlanVersion(version=1, created_at="2024-01-01T00:00:00Z", model_provider="mock", model_name="mock", model_version="1", prompt_version="1"),
        status="draft",
        narrative_dependencies=[]
    )
