import uuid
from stream_editor.contracts.edit_plan import EditClipContract, ClipPriority, EditPlanContract
from stream_editor.editorial.planning.validator import EditPlanValidator


def test_validator_chronological() -> None:
    plan_id = uuid.uuid4()
    clips = [
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=0.0, source_end=10.0,
            output_start=0.0, output_end=10.0,
            selection_reason="Test", priority=ClipPriority.high, confidence=0.9
        ),
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=20.0, source_end=30.0,
            output_start=10.0, output_end=20.0,
            selection_reason="Test", priority=ClipPriority.high, confidence=0.9
        )
    ]
    
    plan = EditPlanContract(
        id=plan_id,
        project_id="test-proj",
        run_id=uuid.uuid4(),
        version=1,
        status="proposed",
        original_duration=100.0,
        selected_duration=20.0,
        compression_ratio=0.2,
        clip_count=2,
        locked=False,
        clips=clips
    )
    
    errors = EditPlanValidator.validate(plan)
    assert not errors


def test_validator_non_chronological() -> None:
    plan_id = uuid.uuid4()
    clips = [
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=50.0, source_end=60.0,
            output_start=0.0, output_end=10.0,
            selection_reason="Test", priority=ClipPriority.high, confidence=0.9
        ),
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=10.0, source_end=20.0,
            output_start=10.0, output_end=20.0,
            selection_reason="Test", priority=ClipPriority.high, confidence=0.9
        )
    ]
    
    plan = EditPlanContract(
        id=plan_id,
        project_id="test-proj",
        run_id=uuid.uuid4(),
        version=1,
        status="proposed",
        original_duration=100.0,
        selected_duration=20.0,
        compression_ratio=0.2,
        clip_count=2,
        locked=False,
        clips=clips
    )
    
    errors = EditPlanValidator.validate(plan)
    assert len(errors) > 0
    assert any("Non-chronological order" in e for e in errors)
