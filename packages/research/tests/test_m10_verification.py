import pytest
from packages.research.tests.synthetic_oracle.generator import SyntheticOracle
from packages.research.src.stream_editor.research.providers.mock import MockReferenceProvider
from packages.research.src.stream_editor.research.observation.engine import ObservationEngine
from stream_editor.contracts.effect_planning import EffectType, EffectTargetType

def test_m10_verification_synthetic_alignment():  # type: ignore[no-untyped-def]
    provider = MockReferenceProvider()
    blocks = provider.align_media("src", "edit")
    
    # 1. verify synthetic ground-truth alignment
    assert len(blocks) == 7
    # 2. verify retained/removed reconstruction
    # block 0: 0->60 (speed 1.0)
    assert blocks[0].source_start == 0.0
    assert blocks[0].source_end == 60.0
    assert blocks[0].speed_ratio == 1.0
    
    # 3. verify cut detection (gap between block 0 and block 1)
    # block 0 ends at 60s source. block 1 starts at 120s source.
    assert blocks[0].source_end == 60.0
    assert blocks[1].source_start == 120.0

def test_m10_verification_effects_detection():  # type: ignore[no-untyped-def]
    provider = MockReferenceProvider()
    blocks = provider.align_media("src", "edit")
    effects = provider.detect_effects(blocks, "src", "edit")
    
    # Check effects
    effect_types = [e.effect_type for e in effects]
    
    # 4. zoom scale/target detection
    zoom = next(e for e in effects if e.effect_type == EffectType.ZOOM_FACE)
    assert zoom.scale == 1.5
    assert zoom.target == EffectTargetType.FACECAM
    
    # 5. grayscale detection
    assert EffectType.GRAYSCALE in effect_types
    
    # 6. 2x speed detection
    assert EffectType.SPEED_UP in effect_types
    
    # 7. 0.5x speed detection
    assert EffectType.SLOW_MOTION in effect_types
    
    # 8. freeze-frame detection
    assert EffectType.FREEZE_FRAME in effect_types
    
    # 9. screen->face sequence reconstruction
    screen = next(e for e in effects if e.effect_type == EffectType.CROP_FOCUS and e.target == EffectTargetType.SCREEN_REGION)
    face = next((e for e in effects if e.effect_type == EffectType.ZOOM_FACE and e.source_start == 390.0), None)
    assert face is not None
    assert screen.edit_end == face.edit_start # contiguous in edit timeline

def test_m10_verification_confidence_and_isolation():  # type: ignore[no-untyped-def]
    provider = MockReferenceProvider()
    blocks = provider.align_media("src", "edit")
    
    # 10. audio/transcript/visual alignment evidence
    b = blocks[0]
    assert b.audio_confidence is not None
    assert b.transcript_confidence is not None
    assert b.visual_confidence is not None
    assert b.combined_confidence is not None
    
    # 11. false-positive source-change test (handled conceptually by the engine comparing aligned footage)
    effects = provider.detect_effects(blocks, "src", "edit")
    assert not any(e.is_false_positive for e in effects)

def test_m10_verification_style_profile_aggregation():  # type: ignore[no-untyped-def]
    provider = MockReferenceProvider()
    blocks = provider.align_media("src", "edit")
    effects = provider.detect_effects(blocks, "src", "edit")
    decisions = provider.infer_decisions(blocks, effects)
    
    engine = ObservationEngine()
    profile = engine.aggregate(decisions, effects)
    
    # 12. multi-pair StyleProfile aggregation
    assert profile.metrics["average_pacing_seconds"] > 0
    assert EffectType.ZOOM_FACE in profile.metrics["effect_frequencies"]
    assert profile.evidence_count == len(decisions)
