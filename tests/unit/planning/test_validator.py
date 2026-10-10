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


def test_validator_clip_exceeds_source_duration_rejected() -> None:
    """Regression test: clips exceeding declared source duration must be rejected."""
    plan_id = uuid.uuid4()
    # real-eval-001 scenario: source duration is 35.007s, clip ends at 35.75s
    clips = [
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=18.0, source_end=28.0,
            output_start=0.0, output_end=10.0,
            selection_reason="Clutch trigger", priority=ClipPriority.high, confidence=0.9
        ),
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=28.0, source_end=35.75,  # Exceeds 35.007s!
            output_start=10.0, output_end=17.75,
            selection_reason="Payoff with invalid padding", priority=ClipPriority.high, confidence=0.9
        )
    ]
    plan = EditPlanContract(
        id=plan_id,
        project_id="real-eval-001",
        run_id=uuid.uuid4(),
        version=1,
        status="proposed",
        original_duration=35.007,
        selected_duration=17.75,
        compression_ratio=0.5,
        clip_count=2,
        locked=False,
        clips=clips
    )
    errors = EditPlanValidator.validate(plan)
    assert len(errors) > 0
    assert any("Clip exceeds source duration" in e for e in errors)


def test_validator_sequential_source_overlap_timeline_duplication_rejected() -> None:
    """Regression test: overlapping sequential source intervals causing timeline duplication must be rejected."""
    plan_id = uuid.uuid4()
    # real-eval-001 overlap scenario: [18.0, 28.0] and [27.75, 35.0] overlap by 0.25s
    clips = [
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=18.0, source_end=28.0,
            output_start=0.0, output_end=10.0,
            selection_reason="Clutch trigger", priority=ClipPriority.high, confidence=0.9
        ),
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=27.75, source_end=35.0,  # Starts 0.25s before previous ends!
            output_start=10.0, output_end=17.25,
            selection_reason="Duplicate speech segment", priority=ClipPriority.high, confidence=0.9
        )
    ]
    plan = EditPlanContract(
        id=plan_id,
        project_id="real-eval-001",
        run_id=uuid.uuid4(),
        version=1,
        status="proposed",
        original_duration=35.007,
        selected_duration=17.25,
        compression_ratio=0.49,
        clip_count=2,
        locked=False,
        clips=clips
    )
    errors = EditPlanValidator.validate(plan)
    assert len(errors) > 0
    assert any("Overlapping source selection (timeline duplication)" in e for e in errors)


def test_validator_negative_source_start_rejected() -> None:
    """Regression test: clips with negative source_start must be rejected."""
    plan_id = uuid.uuid4()
    clips = [
        EditClipContract(
            id=uuid.uuid4(), plan_id=plan_id,
            source_start=-1.5, source_end=5.0,
            output_start=0.0, output_end=6.5,
            selection_reason="Underflow padding", priority=ClipPriority.high, confidence=0.9
        )
    ]
    plan = EditPlanContract(
        id=plan_id,
        project_id="negative-test",
        run_id=uuid.uuid4(),
        version=1,
        status="proposed",
        original_duration=10.0,
        selected_duration=6.5,
        compression_ratio=0.65,
        clip_count=1,
        locked=False,
        clips=clips
    )
    errors = EditPlanValidator.validate(plan)
    assert len(errors) > 0
    assert any("negative source_start" in e for e in errors)
