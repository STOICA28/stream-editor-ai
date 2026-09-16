import asyncio
import os
import sys
from pydantic import BaseModel

# Add packages to path
sys.path.insert(0, os.path.abspath('packages/contracts/src'))
sys.path.insert(0, os.path.abspath('packages/models/src'))
sys.path.insert(0, os.path.abspath('packages/editorial/src'))
sys.path.insert(0, os.path.abspath('packages/narrative/src'))
sys.path.insert(0, os.path.abspath('packages/analysis/src'))
sys.path.insert(0, os.path.abspath('packages/research/src'))
sys.path.insert(0, os.path.abspath('apps/api/src'))
sys.path.insert(0, os.path.abspath('apps/worker/src'))

from stream_editor.models.antigravity_client import AntigravityClient
from stream_editor.editorial.providers.antigravity import AntigravityEditorialProvider
from stream_editor.narrative.providers.antigravity import AntigravityNarrativeProvider
from stream_editor.editorial.planning.antigravity import AntigravityGlobalEditorialPlanner
from stream_editor.analysis.providers.visual.antigravity import AntigravityVisualUnderstandingProvider
from stream_editor.analysis.providers.effect.antigravity import AntigravityEffectPlanner, AntigravityEffectCritic
from stream_editor.research.providers.antigravity import AntigravityReferenceProvider

class SmokeTestSchema(BaseModel):
    ok: bool

async def run_tests():
    # Force use of actual binary
    os.environ["ANTIGRAVITY_BIN"] = r"C:\Users\adria\AppData\Local\agy\bin\agy.exe"
    
    print("--- 6. GLOBAL REAL SMOKE TEST ---")
    client = AntigravityClient(timeout=120.0)
    print("Client bin:", client.bin_path)
    print("Client available:", client.is_available)
    print("Client model:", client.model)
    
    try:
        res = await client.generate_structured("Say ok is true", SmokeTestSchema)
        print("Smoke Test Result:", res)
        print("Telemetry after smoke:", client.telemetry)
    except Exception as e:
        print("Smoke Test Failed:", e)

    print("\n--- 7. DOMAIN REAL-INFERENCE MATRIX ---")
    
    # M3
    print("Testing M3 Editorial...")
    try:
        m3 = AntigravityEditorialProvider(client)
        from stream_editor.contracts.editorial import LocalFeatures
        # We need a small transcript
        res_m3 = await m3.analyze_candidate(candidate_id="c1", transcript_excerpt="hello", local_features=LocalFeatures(speaker_count=1), nearby_events=[], local_summary=None, chapter_summary=None, prompt_version="v1")
        print("M3 Result:", res_m3)
    except Exception as e:
        print("M3 Failed:", type(e), e)
        
    # M4
    print("Testing M4 Narrative...")
    try:
        m4 = AntigravityNarrativeProvider(client)
        from stream_editor.contracts.editorial import StoryGraphConfig
        res_m4 = await m4.build_local_graph([{"id": "c1", "start_time": 0.0, "end_time": 1.0}], "chapter sum", [], StoryGraphConfig())
        print("M4 Result length:", len(res_m4.relationships) if hasattr(res_m4, 'relationships') else res_m4)
    except Exception as e:
        print("M4 Failed:", type(e), e)

    # M5
    print("Testing M5 Global Planning...")
    try:
        m5 = AntigravityGlobalEditorialPlanner(client)
        from stream_editor.contracts.edit_plan import EditPlanConfig, StoryNode
        res_m5 = await m5.generate_plan(candidates=[StoryNode(id="c1", label="test", description="test", start_time=0.0, end_time=1.0, score=1.0)], config=EditPlanConfig())
        print("M5 Result:", res_m5)
    except Exception as e:
        print("M5 Failed:", type(e), e)
        
    # M7
    print("Testing M7 Visual...")
    try:
        m7 = AntigravityVisualUnderstandingProvider(client)
        res_m7 = await m7.analyze_window("proj1", "asset1", 0.0, 1.0)
        print("M7 Result:", res_m7)
    except Exception as e:
        print("M7 Failed:", type(e), e)
        
    # M8 Planner
    print("Testing M8 Effect Planner...")
    try:
        m8_planner = AntigravityEffectPlanner(client)
        from stream_editor.contracts.effect_planning import EffectOpportunity, EffectType
        opp = EffectOpportunity(id="o1", type=EffectType.ZOOM_REGION, timestamp=0.0, reasoning="test", confidence=1.0, properties={})
        res_m8p = await m8_planner.propose_effects("proj1", [opp])
        print("M8 Planner Result:", res_m8p)
    except Exception as e:
        print("M8 Planner Failed:", type(e), e)
        
    # M8 Critic
    print("Testing M8 Effect Critic...")
    try:
        m8_critic = AntigravityEffectCritic(client)
        from stream_editor.contracts.effect_planning import EffectPlan
        plan = EffectPlan(id="p1", target_id="c1", target_type="candidate", effects=[])
        res_m8c = await m8_critic.evaluate_plan("proj1", plan)
        print("M8 Critic Result:", res_m8c)
    except Exception as e:
        print("M8 Critic Failed:", type(e), e)

    # M10
    print("Testing M10 Research...")
    try:
        m10 = AntigravityReferenceProvider(client)
        from stream_editor.contracts.research import AlignmentBlockContract
        b = AlignmentBlockContract(
            id="1", pair_id="p1", source_start=0, source_end=1, edit_start=0, edit_end=1,
            transcript_confidence=1.0, visual_confidence=1.0, audio_confidence=1.0, combined_confidence=0.5, speed_ratio=1.0
        )
        res_m10 = await m10.detect_effects([b], "src.mp4", "edit.mp4")
        print("M10 Result:", res_m10)
    except Exception as e:
        print("M10 Failed:", type(e), e)

    print("\n--- 11. AUTH FAILURE TEST ---")
    try:
        os.environ["ANTIGRAVITY_BIN"] = "C:\\invalid\\path\\agy.exe"
        bad_client = AntigravityClient()
        await bad_client.generate_structured("Fail", SmokeTestSchema)
        print("Auth Failure Test: FAILED (did not raise)")
    except Exception as e:
        print(f"Auth Failure Test: PASSED (raised {type(e).__name__})")
        
    print("\n--- 12. CACHE TEST ---")
    os.environ["ANTIGRAVITY_BIN"] = r"C:\Users\adria\AppData\Local\agy\bin\agy.exe"
    cache_client = AntigravityClient()
    await cache_client.generate_structured("Test Cache", SmokeTestSchema)
    print("Cache Hits 1:", cache_client.telemetry["cache_hits"])
    await cache_client.generate_structured("Test Cache", SmokeTestSchema)
    print("Cache Hits 2:", cache_client.telemetry["cache_hits"])
    await cache_client.generate_structured("Test Cache Diff", SmokeTestSchema)
    print("Cache Hits 3:", cache_client.telemetry["cache_hits"])

asyncio.run(run_tests())
