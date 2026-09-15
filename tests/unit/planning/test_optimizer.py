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
