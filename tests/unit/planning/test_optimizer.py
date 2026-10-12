import uuid
from stream_editor.contracts.edit_plan import EditClipContract, ClipPriority, EditPlanConfig
from stream_editor.editorial.planning.optimizer import DeterministicDurationOptimizer


def test_optimizer_no_pruning_needed() -> None:
    clips = [
        EditClipContract(
            id=uuid.uuid4(), plan_id=uuid.uuid4(),
            source_start=0.0, source_end=10.0,
            output_start=0.0, output_end=10.0,
            selection_reason="Test", priority=ClipPriority.high, confidence=0.9
        )
    ]
    config = EditPlanConfig(target_duration_seconds=100.0, tolerance_seconds=10.0)
    
    optimized = DeterministicDurationOptimizer.optimize(clips, config)
    assert len(optimized) == 1
    assert optimized[0].output_duration == 10.0


def test_optimizer_pruning() -> None:
    clips = [
        EditClipContract(
            id=uuid.uuid4(), plan_id=uuid.uuid4(),
            source_start=0.0, source_end=50.0,
            output_start=0.0, output_end=50.0,
            selection_reason="Test", priority=ClipPriority.essential, confidence=0.9
        ),
        EditClipContract(
            id=uuid.uuid4(), plan_id=uuid.uuid4(),
            source_start=100.0, source_end=150.0,
            output_start=50.0, output_end=100.0,
            selection_reason="Test", priority=ClipPriority.context_only, confidence=0.1
        )
    ]
    # Total duration is 100. Max duration is 60. Must prune.
    config = EditPlanConfig(target_duration_seconds=50.0, tolerance_seconds=10.0)
    
    optimized = DeterministicDurationOptimizer.optimize(clips, config)
    
    # Should drop the context_only one
    assert len(optimized) == 1
    assert optimized[0].priority == ClipPriority.essential
    
    # Output times should be repacked
    assert optimized[0].output_start == 0.0
    assert optimized[0].output_end == 50.0


def test_editing_goal_presets() -> None:
    from stream_editor.contracts.edit_plan import EditingGoal

    short_cfg = EditPlanConfig.from_goal(EditingGoal.SHORT_HIGHLIGHT)
    assert short_cfg.target_duration_seconds == 120.0
    assert short_cfg.tolerance_seconds == 30.0

    long_cfg = EditPlanConfig.from_goal(EditingGoal.LONG_FORM_SUMMARY)
    assert long_cfg.target_duration_seconds == 900.0
    assert long_cfg.tolerance_seconds == 180.0

    full_cfg = EditPlanConfig.from_goal(EditingGoal.FULL_EDITED_SESSION)
    assert full_cfg.target_duration_seconds == 2400.0
    assert full_cfg.tolerance_seconds == 300.0


def test_narrative_anchor_detector() -> None:
    from stream_editor.editorial.planning.anchors import NarrativeAnchorDetector

    plan_id = uuid.uuid4()
    raw_clips = [
        # Clip at stream beginning (Greeting)
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=15.0, source_end=45.0,
            output_start=0.0, output_end=30.0,
            selection_reason="Opening", priority=ClipPriority.context_only
        ),
        # Clip at game start
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=220.0, source_end=280.0,
            output_start=30.0, output_end=90.0,
            selection_reason="Launch game", priority=ClipPriority.medium
        ),
        # Standard mid-game clip
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=1200.0, source_end=1230.0,
            output_start=90.0, output_end=120.0,
            selection_reason="Grinding", priority=ClipPriority.low
        ),
    ]

    tagged = NarrativeAnchorDetector.tag_anchor_clips(raw_clips, total_source_duration=5000.0)
    assert len(tagged) == 3

    # Greeting is tagged as essential anchor
    assert tagged[0].is_narrative_anchor is True
    assert tagged[0].anchor_type == "STREAM_GREETING"
    assert tagged[0].priority == ClipPriority.essential

    # Game start is tagged as essential anchor
    assert tagged[1].is_narrative_anchor is True
    assert tagged[1].anchor_type == "GAME_START"
    assert tagged[1].priority == ClipPriority.essential

    # Mid-game is NOT an anchor
    assert tagged[2].is_narrative_anchor is False
    assert tagged[2].anchor_type is None


def test_optimizer_preserves_narrative_anchors_under_extreme_pressure() -> None:
    plan_id = uuid.uuid4()
    clips = [
        # Protected greeting anchor
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=10.0, source_end=35.0,
            output_start=0.0, output_end=25.0,
            selection_reason="Streamer greeting", priority=ClipPriority.context_only,
            is_narrative_anchor=True, anchor_type="STREAM_GREETING"
        ),
        # Protected game start anchor
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=250.0, source_end=280.0,
            output_start=25.0, output_end=55.0,
            selection_reason="Game launch", priority=ClipPriority.medium,
            is_narrative_anchor=True, anchor_type="GAME_START"
        ),
        # High-energy mid-game action clip
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=500.0, source_end=560.0,
            output_start=55.0, output_end=115.0,
            selection_reason="Action", priority=ClipPriority.high, confidence=0.95
        ),
        # Unimportant filler clip
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=800.0, source_end=850.0,
            output_start=115.0, output_end=165.0,
            selection_reason="Filler", priority=ClipPriority.low, confidence=0.2
        )
    ]
    # Total duration is 165s. Target budget is 60s (tolerance 10s -> max 70s).
    # Normally context_only (25s) would be pruned first!
    # But greeting is an anchor, so filler (50s) and action (60s) get pruned,
    # preserving the narrative anchor!
    config = EditPlanConfig(
        target_duration_seconds=50.0,
        tolerance_seconds=10.0,
        preserve_narrative_anchors=True
    )

    optimized = DeterministicDurationOptimizer.optimize(clips, config)

    # Verify both anchors survived pruning despite low/medium priority
    anchor_types = [c.anchor_type for c in optimized if c.is_narrative_anchor]
    assert "STREAM_GREETING" in anchor_types
    assert "GAME_START" in anchor_types

    # Total duration fits within budget
    assert sum(c.output_duration for c in optimized) <= 70.0
