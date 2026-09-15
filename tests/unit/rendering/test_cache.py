import pytest
from stream_editor.rendering.cache import RenderSegmentCache
from stream_editor.contracts.rendering import CompiledSegment, RenderConfig, CompiledEffect
from stream_editor.contracts.effect_planning import EffectType

def test_cache_signature():
    cache = RenderSegmentCache()
    config = RenderConfig(width=1280, height=720, fps=30)
    
    seg1 = CompiledSegment(
        segment_index=0,
        source_asset_id="asset1",
        source_start=10.0,
        source_end=20.0,
        output_start=0.0,
        output_end=10.0,
        duration=10.0,
        effects=[]
    )
    
    sig1 = cache.compute_signature("fingerprint1", seg1, config)
    
    # Same data, same sig
    sig2 = cache.compute_signature("fingerprint1", seg1, config)
    assert sig1 == sig2
    
    # Different config
    config_diff = RenderConfig(width=1920, height=1080, fps=30)
    sig3 = cache.compute_signature("fingerprint1", seg1, config_diff)
    assert sig1 != sig3
    
    # Add effect
    seg1.effects.append(
        CompiledEffect(
            effect_id="eff1",
            effect_type=EffectType.GRAYSCALE,
            source_start=10.0,
            source_end=15.0,
            output_start=0.0,
            output_end=5.0
        )
    )
    sig4 = cache.compute_signature("fingerprint1", seg1, config)
    assert sig1 != sig4

def test_effect_leakage_isolation():
    # Effects in one segment should not affect the signature of another segment without effects
    cache = RenderSegmentCache()
    config = RenderConfig()
    
    seg1 = CompiledSegment(
        segment_index=0,
        source_asset_id="asset1",
        source_start=10.0,
        source_end=20.0,
        output_start=0.0,
        output_end=10.0,
        duration=10.0,
        effects=[CompiledEffect(effect_id="e", effect_type=EffectType.GRAYSCALE, source_start=10, source_end=20, output_start=0, output_end=10)]
    )
    
    seg2 = CompiledSegment(
        segment_index=1,
        source_asset_id="asset1",
        source_start=20.0,
        source_end=30.0,
        output_start=10.0,
        output_end=20.0,
        duration=10.0,
        effects=[]
    )
    
    sig2_with_prev_effect = cache.compute_signature("fingerprint1", seg2, config)
    
    # Ensure it matches exactly what it would be if seg1 never existed
    sig2_isolated = cache.compute_signature("fingerprint1", CompiledSegment(
        segment_index=1,
        source_asset_id="asset1",
        source_start=20.0,
        source_end=30.0,
        output_start=10.0,
        output_end=20.0,
        duration=10.0,
        effects=[]
    ), config)
    
    assert sig2_with_prev_effect == sig2_isolated
