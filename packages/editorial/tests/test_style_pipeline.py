import pytest
from datetime import datetime
from stream_editor.contracts.style import StyleSignal, EditorialStylePolicyContract
from stream_editor.editorial.style.compiler import StylePolicyCompiler
from stream_editor.editorial.style.candidate_adapter import CandidateStyleAdapter
from stream_editor.contracts.editorial import CandidateSegmentContract
from stream_editor.editorial.style.cache import get_style_cache_key

def test_style_policy_compiler_low_n_omission():
    compiler = StylePolicyCompiler(n_threshold_low=3)
    
    # Needs to match what StylePolicyCompiler expects from profile
    profile_data = {
        "id": "prof_1",
        "reference_project_id": "ref_1",
        "version": 1,
        "pacing": {
            "avg_segment_duration": 5.0,
            "observations": 2,
            "confidence": 0.9
        },
        "effects": []
    }
    
    contract = compiler.compile(profile_data, [], "proj_1")
    # All signals should be skipped or 0 confidence because N=2 < 3
    assert all(s.confidence == 0.0 for s in contract.signals)

def test_candidate_style_adapter():
    policy = EditorialStylePolicyContract(
        id="pol_1",
        name="Test",
        description="Test Policy",
        source_reference_project_id="ref_1",
        source_style_profile_id="prof_1",
        policy_version=1,
        created_at=datetime.utcnow(),
        created_by="test",
        status="active",
        signals=[
            StyleSignal(
                name="test_signal",
                stage="M5",
                direction="increase",
                strength=0.5,
                confidence=1.0,
                sample_size=10,
                source_profile_metric="pacing.avg_segment_duration"
            )
        ]
    )
    
    adapter = CandidateStyleAdapter(policy)
    
    base = CandidateSegmentContract(
        id="c1",
        project_id="proj_1",
        start_time=0.0, 
        end_time=1.0, 
        transcript="haha", 
        score=0.4,
        reasoning="Funny"
    )
    
    assert adapter.policy == policy

def test_cache_key_generation():
    key1 = get_style_cache_key("v1", "pol_1", 1, dry_run=False)
    key2 = get_style_cache_key("v1", "pol_2", 1, dry_run=False)
    key3 = get_style_cache_key("v1", "pol_1", 2, dry_run=False)
    key_dry = get_style_cache_key("v1", "pol_1", 1, dry_run=True)
    
    assert key1 != key2
    assert key1 != key3
    assert key1 != key_dry
