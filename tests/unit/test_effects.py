import pytest
from pydantic import ValidationError
from stream_editor.contracts.effects import Effect, EffectType, validate_effect

def test_zoom_region_valid():
    effect = Effect(effect_type=EffectType.zoom_region, params={"x":0.5, "y":0.5, "width":0.5, "height":0.5, "scale":2.0, "duration_seconds":1.0}, start_seconds=0, end_seconds=1)
    validate_effect(effect)

def test_zoom_region_invalid_scale():
    effect = Effect(effect_type=EffectType.zoom_region, params={"x":0.5, "y":0.5, "width":0.5, "height":0.5, "scale":5.0, "duration_seconds":1.0}, start_seconds=0, end_seconds=1)
    with pytest.raises(ValidationError):
        validate_effect(effect)

def test_grayscale_valid():
    effect = Effect(effect_type=EffectType.grayscale, params={"duration_seconds": 1.0, "intensity": 0.5}, start_seconds=0, end_seconds=1)
    validate_effect(effect)
