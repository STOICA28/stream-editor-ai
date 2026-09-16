import asyncio
import os
import sys
import uuid
from pydantic import BaseModel

sys.path.insert(0, os.path.abspath('packages/contracts/src'))
sys.path.insert(0, os.path.abspath('packages/models/src'))
sys.path.insert(0, os.path.abspath('packages/editorial/src'))
sys.path.insert(0, os.path.abspath('packages/narrative/src'))
sys.path.insert(0, os.path.abspath('packages/analysis/src'))
sys.path.insert(0, os.path.abspath('packages/research/src'))
sys.path.insert(0, os.path.abspath('apps/api/src'))
sys.path.insert(0, os.path.abspath('apps/worker/src'))

from stream_editor.models.antigravity_client import AntigravityClient
from stream_editor.editorial.planning.antigravity import AntigravityGlobalEditorialPlanner
from stream_editor.research.providers.antigravity import AntigravityReferenceProvider

async def run_tests():
    os.environ["ANTIGRAVITY_BIN"] = r"C:\Users\adria\AppData\Local\agy\bin\agy.exe"
    client = AntigravityClient(timeout=120.0)
    print("--- 7. DOMAIN REAL-INFERENCE MATRIX ---")

    # M5
    print("Testing M5 Global Planning...")
    try:
        m5 = AntigravityGlobalEditorialPlanner(client)
        from stream_editor.contracts.edit_plan import EditPlanConfig
        from stream_editor.contracts.editorial import CandidateSegmentContract, StoryGraphContract
        
        cands = [
            CandidateSegmentContract(id="c1", project_id="proj1", start_time=0.0, end_time=10.0, duration=10.0, summary="intro", score_importance=0.9),
            CandidateSegmentContract(id="c2", project_id="proj1", start_time=10.0, end_time=20.0, duration=10.0, summary="joke", score_importance=0.8),
            CandidateSegmentContract(id="c3", project_id="proj1", start_time=20.0, end_time=30.0, duration=10.0, summary="outro", score_importance=0.5)
        ]
        
        res_m5 = await m5.generate_plan(
            project_id="proj1", 
            run_id=str(uuid.uuid4()), 
            graph=StoryGraphContract(id=str(uuid.uuid4()), project_id="proj1", run_id=str(uuid.uuid4()), version=1, status="active", threads=[], relationships=[]), 
            candidates=cands, 
            config=EditPlanConfig()
        )
        print("M5 Result clips:", len(res_m5.clips))
    except Exception as e:
        print("M5 Failed:", type(e), e)
        
    print("Testing M10 Research...")
    try:
        m10 = AntigravityReferenceProvider(client)
        from stream_editor.contracts.research import AlignmentBlockContract, AlignmentMethod
        # Add a gap to trigger deterministic freeze frame just so length is > 0, proving it doesn't fail.
        b1 = AlignmentBlockContract(id="1", run_id="r1", source_start=10, source_end=15, edit_start=10, edit_end=15, combined_confidence=0.5, speed_ratio=1.0, method=AlignmentMethod.COMBINED)
        b2 = AlignmentBlockContract(id="2", run_id="r1", source_start=15.1, source_end=20, edit_start=16, edit_end=21, combined_confidence=0.9, speed_ratio=1.0, method=AlignmentMethod.COMBINED)
        res_m10 = await m10.detect_effects([b1, b2], "src.mp4", "edit.mp4")
        print("M10 Result length:", len(res_m10))
    except Exception as e:
        print("M10 Failed:", type(e), e)

asyncio.run(run_tests())
