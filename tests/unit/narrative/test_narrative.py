import pytest
from stream_editor.narrative.chapters import ChapterGrouper
from stream_editor.narrative.retrieval import LinkCandidateRetriever
from stream_editor.narrative.validator import GraphValidator
from stream_editor.contracts.editorial import ProposedRelationship, EdgeRelationType, DependencyStrength

def test_chapter_grouper_duration_fallback():
    grouper = ChapterGrouper(chapter_duration_seconds=100.0)
    candidates = [
        {"id": "c1", "start_time": 10.0, "end_time": 20.0},
        {"id": "c2", "start_time": 90.0, "end_time": 110.0},
        {"id": "c3", "start_time": 150.0, "end_time": 160.0},
    ]
    chapters = grouper.group(candidates)
    
    assert len(chapters) == 2
    assert chapters[0].index == 0
    assert chapters[0].start_time == 10.0
    assert len(chapters[0].candidates) == 2  # c1, c2
    assert chapters[1].index == 1
    assert chapters[1].start_time == 110.0
    assert len(chapters[1].candidates) == 1  # c3

def test_link_retriever_tfidf():
    retriever = LinkCandidateRetriever(max_k=2, min_similarity=0.1)
    candidates = [
        {"id": "1", "start_time": 10, "transcript_excerpt": "the quick brown fox", "summary": ""},
        {"id": "2", "start_time": 20, "transcript_excerpt": "hello world", "summary": ""},
        {"id": "3", "start_time": 30, "transcript_excerpt": "a brown fox jumps", "summary": "quick fox"},
    ]
    pairs = retriever.retrieve_pairs(candidates)
    
    assert len(pairs) == 1
    assert pairs[0].source_id == "1"
    assert pairs[0].target_id == "3"
    assert pairs[0].similarity > 0.1

def test_validator_rejects_self_link():
    validator = GraphValidator()
    rel = ProposedRelationship(
        source_candidate="c1",
        target_candidate="c1",
        relation=EdgeRelationType.same_thread,
        confidence=0.9,
        dependency_strength=DependencyStrength.helpful,
        dependency_strength_score=0.5,
        evidence_summary="test",
    )
    result = validator.validate_edge(rel, {"c1": {}}, [])
    assert not result.passed
    assert "Self-link" in result.errors[0]

def test_validator_temporal_direction():
    validator = GraphValidator()
    # callback_to: source must appear AFTER target.
    # If source is at 10s and target is at 50s, this is invalid.
    rel = ProposedRelationship(
        source_candidate="c1",
        target_candidate="c2",
        relation=EdgeRelationType.callback_to,
        confidence=0.9,
        dependency_strength=DependencyStrength.helpful,
        dependency_strength_score=0.5,
        evidence_summary="test",
    )
    registry = {
        "c1": {"start_time": 10.0},
        "c2": {"start_time": 50.0},
    }
    result = validator.validate_edge(rel, registry, [])
    assert not result.passed
    assert "Temporal violation" in result.errors[0]
