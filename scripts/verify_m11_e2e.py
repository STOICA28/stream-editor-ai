import asyncio
import os
import uuid
from typing import List

from stream_editor.editorial.style.compiler import StylePolicyCompiler
from stream_editor.editorial.style.candidate_adapter import CandidateStyleAdapter
from stream_editor.editorial.style.effect_adapter import EffectStyleAdapter
from stream_editor.contracts.editorial import CandidateSegmentContract

async def run_e2e():
    print("========================================")
    print("--- Starting M11 E2E Verification ---")
    print("========================================\n")
    
    # 1. Compile Policy from M10 Profile
    compiler = StylePolicyCompiler()
    m10_profile = {
        "id": str(uuid.uuid4()),
        "reference_project_id": "test_ref",
        "version": 1,
        "metrics": {
            "reaction_count": 150,
            "reaction_confidence": 0.95,
            "cuts_per_minute": 15,
            "cut_count": 250,
            "cut_confidence": 0.95,
            "effect_count": 80,
            "effect_confidence": 0.85
        },
        "effects": [
            {
                "effect_type": "zoom_face",
                "observations": 45,
                "confidence": 0.8
            }
        ]
    }
    
    print("1. COMPILING STYLE POLICY")
    policy = compiler.compile(m10_profile, [], project_id="test_proj")
    print(f"   [+] Policy '{policy.name}' created.")
    print(f"   [+] Policy ID: {policy.id}")
    for i, sig in enumerate(policy.signals):
        print(f"       Signal {i+1}: {sig.name} -> {sig.direction} (Stage: {sig.stage})")
    
    # 2. Candidate Style Adapter (M3 -> M5)
    print("\n2. APPLYING CANDIDATE STYLE ADAPTER")
    adapter = CandidateStyleAdapter(policy)
    
    candidates = [
        CandidateSegmentContract(
            id="c1_reaction",
            project_id="test_proj",
            start_time=10.0,
            end_time=12.0,
            transcript="Oh my god!",
            score=0.6,
            score_reaction=0.8,
            reasoning="Strong reaction"
        ),
        CandidateSegmentContract(
            id="c2_boring",
            project_id="test_proj",
            start_time=20.0,
            end_time=21.0,
            transcript="Uhh... let me check...",
            score=0.2,
            score_reaction=0.1,
            reasoning="Dead air"
        ),
        CandidateSegmentContract(
            id="c3_fast_cut",
            project_id="test_proj",
            start_time=30.0,
            end_time=32.0,
            transcript="Boom!",
            score=0.5,
            reasoning="Fast"
        )
    ]
    
    styled_candidates = adapter.adapt(candidates)
    for sc in styled_candidates:
        print(f"   [+] Candidate {sc.candidate_id}:")
        if sc.influences:
            for inf in sc.influences:
                print(f"       -> Influence: {inf.dimension} ({inf.direction}) Strength: {inf.strength:.2f}")
        else:
            print(f"       -> No influences")
            
    # 3. Effect Style Adapter (M8)
    print("\n3. APPLYING EFFECT STYLE ADAPTER")
    effect_adapter = EffectStyleAdapter(policy)
    pref_effects = effect_adapter.get_preferred_effects()
    density = effect_adapter.get_effect_density_modifier()
    print(f"   [+] Preferred Effects: {pref_effects}")
    print(f"   [+] Density Modifier: {density:.2f}")
    
    print("\n========================================")
    print("? M11 E2E VERIFICATION COMPLETED")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_e2e())
