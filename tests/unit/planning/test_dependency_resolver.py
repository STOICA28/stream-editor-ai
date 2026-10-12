"""Unit tests for NarrativeDependencyResolver."""

from uuid import uuid4

from stream_editor.contracts.edit_plan import (
    ClipPriority,
    EditClipContract,
    EditPlanConfig,
)
from stream_editor.contracts.editorial import (
    CandidateSegmentContract,
    DependencyStrength,
    EdgeRelationType,
    StoryEdgeContract,
    StoryGraphContract,
    StoryNodeContract,
    StoryNodeType,
)
from stream_editor.editorial.planning.resolver import NarrativeDependencyResolver


def test_resolve_dependencies_missing_prerequisite_pulled() -> None:
    plan_id = uuid4()
    cand_a_id = str(uuid4())
    cand_b_id = str(uuid4())

    cand_a = CandidateSegmentContract(
        id=cand_a_id,
        project_id="p1",
        start_time=10.0,
        end_time=30.0,
        summary="Streamer introduces game objective",
    )
    cand_b = CandidateSegmentContract(
        id=cand_b_id,
        project_id="p1",
        start_time=45.0,
        end_time=70.0,
        summary="Streamer achieves the objective with big payoff",
    )

    # Graph shows B depends on A
    node_a = StoryNodeContract(
        id="node_a",
        story_graph_run_id="run1",
        node_type=StoryNodeType.setup,
        start_time=10.0,
        end_time=30.0,
        candidate_id=cand_a_id,
        confidence=0.9,
        provider="mock",
    )
    node_b = StoryNodeContract(
        id="node_b",
        story_graph_run_id="run1",
        node_type=StoryNodeType.payoff,
        start_time=45.0,
        end_time=70.0,
        candidate_id=cand_b_id,
        confidence=0.9,
        provider="mock",
    )
    edge = StoryEdgeContract(
        id="edge_1",
        story_graph_run_id="run1",
        source_node_id="node_b",
        target_node_id="node_a",
        relation_type=EdgeRelationType.requires_context,
        confidence=0.95,
        dependency_strength=DependencyStrength.critical,
        provider="mock",
    )
    graph = StoryGraphContract(
        id="g1",
        project_id="p1",
        run_id="run1",
        version=1,
        status="completed",
        nodes=[node_a, node_b],
        edges=[edge],
    )

    # Only B was initially selected
    clip_b = EditClipContract(
        id=uuid4(),
        plan_id=plan_id,
        source_start=45.0,
        source_end=70.0,
        output_start=0.0,
        output_end=25.0,
        candidate_id=cand_b_id,
        selection_reason="Payoff highlight",
        priority=ClipPriority.high,
    )

    resolved = NarrativeDependencyResolver.resolve_dependencies(
        selected_clips=[clip_b],
        all_candidates=[cand_a, cand_b],
        story_graph=graph,
    )

    # Both A and B should now be in the plan
    assert len(resolved) == 2
    cand_ids = [c.candidate_id for c in resolved]
    assert cand_a_id in cand_ids
    assert cand_b_id in cand_ids
    # Chronologically ordered
    assert resolved[0].candidate_id == cand_a_id
    assert resolved[1].candidate_id == cand_b_id


def test_resolve_dependencies_missing_prerequisite_dropped_if_unavailable() -> None:
    plan_id = uuid4()
    cand_b_id = str(uuid4())
    missing_a_id = str(uuid4())

    node_a = StoryNodeContract(
        id="node_a",
        story_graph_run_id="run1",
        node_type=StoryNodeType.setup,
        start_time=10.0,
        end_time=30.0,
        candidate_id=missing_a_id,
        confidence=0.9,
        provider="mock",
    )
    node_b = StoryNodeContract(
        id="node_b",
        story_graph_run_id="run1",
        node_type=StoryNodeType.payoff,
        start_time=45.0,
        end_time=70.0,
        candidate_id=cand_b_id,
        confidence=0.9,
        provider="mock",
    )
    edge = StoryEdgeContract(
        id="edge_1",
        story_graph_run_id="run1",
        source_node_id="node_b",
        target_node_id="node_a",
        relation_type=EdgeRelationType.requires_context,
        confidence=0.95,
        dependency_strength=DependencyStrength.critical,
        provider="mock",
    )
    graph = StoryGraphContract(
        id="g1",
        project_id="p1",
        run_id="run1",
        version=1,
        status="completed",
        nodes=[node_a, node_b],
        edges=[edge],
    )

    clip_b = EditClipContract(
        id=uuid4(),
        plan_id=plan_id,
        source_start=45.0,
        source_end=70.0,
        output_start=0.0,
        output_end=25.0,
        candidate_id=cand_b_id,
        selection_reason="Payoff highlight without setup",
        priority=ClipPriority.high,
    )

    # Candidate catalog does NOT have missing_a
    resolved = NarrativeDependencyResolver.resolve_dependencies(
        selected_clips=[clip_b],
        all_candidates=[],  # missing
        story_graph=graph,
    )

    # Clip B must be dropped because its critical prerequisite is missing
    assert len(resolved) == 0


def test_resolve_dependencies_essential_priority_inheritance() -> None:
    plan_id = uuid4()
    cand_a_id = str(uuid4())
    cand_b_id = str(uuid4())

    cand_a = CandidateSegmentContract(
        id=cand_a_id,
        project_id="p1",
        start_time=5.0,
        end_time=20.0,
        summary="Crucial setup",
    )
    cand_b = CandidateSegmentContract(
        id=cand_b_id,
        project_id="p1",
        start_time=30.0,
        end_time=50.0,
        summary="Climax payoff",
    )

    node_a = StoryNodeContract(
        id="node_a",
        story_graph_run_id="run1",
        node_type=StoryNodeType.setup,
        start_time=5.0,
        end_time=20.0,
        candidate_id=cand_a_id,
        confidence=0.9,
        provider="mock",
    )
    node_b = StoryNodeContract(
        id="node_b",
        story_graph_run_id="run1",
        node_type=StoryNodeType.payoff,
        start_time=30.0,
        end_time=50.0,
        candidate_id=cand_b_id,
        confidence=0.9,
        provider="mock",
    )
    edge = StoryEdgeContract(
        id="edge_1",
        story_graph_run_id="run1",
        source_node_id="node_b",
        target_node_id="node_a",
        relation_type=EdgeRelationType.payoff_of,
        confidence=0.95,
        dependency_strength=DependencyStrength.critical,
        provider="mock",
    )
    graph = StoryGraphContract(
        id="g1",
        project_id="p1",
        run_id="run1",
        version=1,
        status="completed",
        nodes=[node_a, node_b],
        edges=[edge],
    )

    clip_b = EditClipContract(
        id=uuid4(),
        plan_id=plan_id,
        source_start=30.0,
        source_end=50.0,
        output_start=0.0,
        output_end=20.0,
        candidate_id=cand_b_id,
        selection_reason="Essential climax",
        priority=ClipPriority.essential,
    )

    resolved = NarrativeDependencyResolver.resolve_dependencies(
        selected_clips=[clip_b],
        all_candidates=[cand_a, cand_b],
        story_graph=graph,
    )

    assert len(resolved) == 2
    # Prerequisite A should inherit essential priority so duration optimizer doesn't prune it!
    assert resolved[0].candidate_id == cand_a_id
    assert resolved[0].priority == ClipPriority.essential


def test_link_episode_continuity_bridges_small_gaps() -> None:
    plan_id = uuid4()
    clip1 = EditClipContract(
        id=uuid4(),
        plan_id=plan_id,
        source_start=100.0,
        source_end=120.0,
        output_start=0.0,
        output_end=20.0,
        selection_reason="Part 1",
        priority=ClipPriority.high,
    )
    clip2 = EditClipContract(
        id=uuid4(),
        plan_id=plan_id,
        source_start=123.5,  # 3.5s gap
        source_end=150.0,
        output_start=20.0,
        output_end=46.5,
        selection_reason="Part 2",
        priority=ClipPriority.high,
    )

    bridged = NarrativeDependencyResolver.link_episode_continuity(
        [clip1, clip2], max_bridging_gap_seconds=5.0
    )

    assert len(bridged) == 1
    assert bridged[0].source_start == 100.0
    assert bridged[0].source_end == 150.0


def test_link_episode_continuity_preserves_large_gaps() -> None:
    plan_id = uuid4()
    clip1 = EditClipContract(
        id=uuid4(),
        plan_id=plan_id,
        source_start=100.0,
        source_end=120.0,
        output_start=0.0,
        output_end=20.0,
        selection_reason="Part 1",
        priority=ClipPriority.high,
    )
    clip2 = EditClipContract(
        id=uuid4(),
        plan_id=plan_id,
        source_start=200.0,  # 80s gap
        source_end=240.0,
        output_start=20.0,
        output_end=60.0,
        selection_reason="Part 2",
        priority=ClipPriority.high,
    )

    bridged = NarrativeDependencyResolver.link_episode_continuity(
        [clip1, clip2], max_bridging_gap_seconds=5.0
    )

    assert len(bridged) == 2
