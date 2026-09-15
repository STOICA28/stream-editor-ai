import pytest
from stream_editor.rendering.compiler import TimelineCompiler
from stream_editor.contracts.edit_plan import EditClipContract, ClipPriority
from stream_editor.contracts.effect_planning import EffectInstructionSchema, EffectType, EffectTargetType, EffectPriority
import uuid

def test_timeline_compiler_basic():
    compiler = TimelineCompiler()
    
    clips = [
        EditClipContract(id=uuid.uuid4(), plan_id=uuid.uuid4(), source_start=10.0, source_end=20.0, output_start=0.0, output_end=10.0, selection_reason="", priority=ClipPriority.high),
        EditClipContract(id=uuid.uuid4(), plan_id=uuid.uuid4(), source_start=30.0, source_end=45.0, output_start=10.0, output_end=25.0, selection_reason="", priority=ClipPriority.high)
    ]
    
    effects = [
        EffectInstructionSchema(
            id="eff1",
            effect_plan_run_id="epr1",
            source_start=15.0,
            source_end=35.0,
            effect_type=EffectType.GRAYSCALE,
            target_type=EffectTargetType.FULL_FRAME,
            confidence=0.9,
            priority=EffectPriority.NORMAL,
            provider="test"
        )
    ]
    
    timeline = compiler.compile("proj1", "job1", clips, effects)
    
    assert len(timeline.segments) == 2
    assert timeline.expected_duration == 25.0
    
    seg1 = timeline.segments[0]
    assert seg1.duration == 10.0
    assert seg1.output_start == 0.0
    assert seg1.output_end == 10.0
    assert len(seg1.effects) == 1
    
    e1 = seg1.effects[0]
    assert e1.source_start == 15.0
    assert e1.source_end == 20.0
    assert e1.output_start == 5.0
    assert e1.output_end == 10.0
    
    seg2 = timeline.segments[1]
    assert seg2.duration == 15.0
    assert seg2.output_start == 10.0
    assert seg2.output_end == 25.0
    assert len(seg2.effects) == 1
    
    e2 = seg2.effects[0]
    assert e2.source_start == 30.0
    assert e2.source_end == 35.0
    assert e2.output_start == 10.0
    assert e2.output_end == 15.0
