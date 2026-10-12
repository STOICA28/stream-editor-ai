"""Transcript-First Semantic Editorial Reasoner using AntigravityClient (gemini-3.1-pro-high).

Performs authentic LLM reasoning over genuine Whisper transcripts across diagnostic pilot regions.
Generates structured SemanticCutDecision contracts and validated textual cut plans.
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages" / "contracts" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "models" / "src"))

from stream_editor.contracts.editorial import (
    SemanticDecisionType,
    SemanticCutDecision,
    SemanticRegionCutPlan,
)
from stream_editor.models.antigravity_client import AntigravityClient

CACHE_DIR = Path("cache/pilot_transcripts")
OUTPUT_DIR = Path("cache/pilot_semantic_plans")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class SegmentEvaluation(BaseModel):
    segment_id: str = Field(description="Unique block identifier e.g. blk_1")
    source_start: float = Field(description="Start timestamp in seconds")
    source_end: float = Field(description="End timestamp in seconds")
    decision: str = Field(description="One of: KEEP, REMOVE, CONDENSE, KEEP_AS_CONTEXT, KEEP_AS_PAYOFF, REQUIRES_PREVIOUS_CONTEXT, UNCERTAIN")
    reason: str = Field(description="Editorial justification for decision")
    narrative_importance: float = Field(ge=0.0, le=1.0, description="0.0 (worthless admin/dead air) to 1.0 (crucial narrative)")
    category: str = Field(description="Category e.g. stream_administration, premise_setup, gameplay_intro, gameplay_progression, repetitive_loop, banter, reaction")
    required_context: Optional[str] = Field(default=None, description="Explanation of context required if viewer might be disoriented")
    game_state_before: Optional[str] = Field(default=None, description="Game state before this moment")
    game_state_after: Optional[str] = Field(default=None, description="Game state after this moment")
    omitted_events: Optional[str] = Field(default=None, description="Events that occurred between previous clip and this clip if skipped")

class RegionEvaluationResponse(BaseModel):
    region_id: str
    evaluations: List[SegmentEvaluation]
    continuity_audit_summary: str
    editorial_verdict: str

EDITORIAL_SYSTEM_PROMPT = """You are the Lead Master Editor for StreamEditor AI.
Your objective is to produce a coherent, entertaining long-form YouTube video from a raw livestream.
You must analyze the authentic transcript and gameplay context with meticulous editorial judgment.

CRITICAL EDITORIAL PRINCIPLES:
1. DISTINGUISH ESSENTIAL FROM ADMIN:
   - Stream administration (checking OBS, adjusting game audio/music volume sliders, asking chat if microphone works, talking about YouTube thumbnails or whether the stream will be uploaded to YouTube) MUST BE MARKED 'REMOVE' with 0.0-0.1 importance.
   - Core premise (explaining the game, the premise of the satire simulator, setting up the shop name 'Pacofi', establishing character motivation) MUST BE MARKED 'KEEP' or 'KEEP_AS_CONTEXT' with 0.8-1.0 importance.
2. DISTINGUISH PROGRESSION FROM REPETITIVE GRIND:
   - Routine repetitive actions (waiting for customers, grinding weed in grinder, silent menu wandering) MUST BE 'REMOVE' or 'CONDENSE'.
   - Progression milestones (making the first sale, planting the first seed, paying off the debt, hiring an employee) MUST BE 'KEEP' or 'KEEP_AS_CONTEXT'.
3. CONTINUITY AND CONTEXT AWARENESS:
   - If a scene shows the streamer in a radically different situation (e.g. 100-minute time warp where employees now run the store), explain what context the viewer needs!
   - Detail state before, omitted events, and state after.
4. VALID DECISION VALUES:
   - KEEP
   - REMOVE
   - CONDENSE
   - KEEP_AS_CONTEXT
   - KEEP_AS_PAYOFF
   - REQUIRES_PREVIOUS_CONTEXT
   - UNCERTAIN
"""

def chunk_segments(segments: list, max_window_sec: float = 45.0) -> list[dict]:
    """Group granular Whisper segments into coherent editorial blocks (20-45s)."""
    blocks = []
    current_block = []
    block_start = segments[0]["source_start"] if segments else 0.0
    
    for s in segments:
        if not current_block:
            current_block.append(s)
            block_start = s["source_start"]
            continue
        
        if (s["source_end"] - block_start) > max_window_sec:
            blocks.append(current_block)
            current_block = [s]
            block_start = s["source_start"]
        else:
            current_block.append(s)
            
    if current_block:
        blocks.append(current_block)
        
    formatted_blocks = []
    for idx, b in enumerate(blocks):
        b_start = b[0]["source_start"]
        b_end = b[-1]["source_end"]
        formatted_blocks.append({
            "block_id": f"blk_{idx+1}",
            "source_start": b_start,
            "source_end": b_end,
            "duration": round(b_end - b_start, 2),
            "transcript_text": " ".join([s["text"] for s in b]),
        })
    return formatted_blocks

async def evaluate_region(client: AntigravityClient, region_id: str, title: str, transcript_data: list) -> SemanticRegionCutPlan:
    print(f"\n=======================================================")
    print(f"Evaluating Region: {region_id} ({title})")
    print(f"Total Whisper segments: {len(transcript_data)}")
    print(f"=======================================================")
    
    blocks = chunk_segments(transcript_data, max_window_sec=45.0)
    print(f"Formatted into {len(blocks)} editorial blocks for single-pass holistic reasoning.")
    
    blocks_text = "\n".join([
        f"- Block [{b['block_id']}] ({b['source_start']}s -> {b['source_end']}s, dur={b['duration']}s):\n  \"{b['transcript_text']}\""
        for b in blocks
    ])
    
    prompt = f"""{EDITORIAL_SYSTEM_PROMPT}

REGION TO EVALUATE: {region_id} - {title}
The region consists of the following {len(blocks)} consecutive blocks:

{blocks_text}

INSTRUCTIONS:
1. Provide a SegmentEvaluation for EVERY block listed above ({len(blocks)} total).
2. Explicitly classify stream administration talk as 'REMOVE' with near-zero importance.
3. Explicitly classify premise/intro/game setup/progression as 'KEEP' or 'KEEP_AS_CONTEXT'.
4. Include continuity audit and overall editorial verdict.
Return the structured RegionEvaluationResponse.
"""
    print(f"Invoking AntigravityClient (gemini-3.1-pro-high)...")
    eval_resp: RegionEvaluationResponse = await client.generate_structured(prompt, RegionEvaluationResponse)
    print(f"Response received! Evaluations count: {len(eval_resp.evaluations)}")
    print(f"Editorial Verdict: {eval_resp.editorial_verdict[:100]}...")

    all_decisions: list[SemanticCutDecision] = []
    for ev in eval_resp.evaluations:
        try:
            d_type = SemanticDecisionType(ev.decision.strip())
        except ValueError:
            d_type = SemanticDecisionType.KEEP if "KEEP" in ev.decision else SemanticDecisionType.REMOVE
            
        dur = round(ev.source_end - ev.source_start, 2)
        # Find matching block text
        matching_block = next((b for b in blocks if b["block_id"] == ev.segment_id or abs(b["source_start"] - ev.source_start) < 2.0), None)
        excerpt = matching_block["transcript_text"] if matching_block else ""

        cut_decision = SemanticCutDecision(
            id=f"{region_id}_{ev.segment_id}",
            source_start=ev.source_start,
            source_end=ev.source_end,
            duration=dur,
            transcript_excerpt=excerpt,
            decision=d_type,
            reason=ev.reason,
            narrative_importance=ev.narrative_importance,
            category=ev.category,
            required_context=ev.required_context,
            game_state_before=ev.game_state_before,
            game_state_after=ev.game_state_after,
            omitted_events=ev.omitted_events,
        )
        all_decisions.append(cut_decision)
        print(f"  [{ev.segment_id}] {ev.source_start}s-{ev.source_end}s -> {d_type.value} ({ev.category}) | imp={ev.narrative_importance} | {ev.reason[:60]}...")

    total_source = round(all_decisions[-1].source_end - all_decisions[0].source_start, 2) if all_decisions else 0.0
    retained_dur = round(sum(d.duration for d in all_decisions if d.decision in (SemanticDecisionType.KEEP, SemanticDecisionType.KEEP_AS_CONTEXT, SemanticDecisionType.KEEP_AS_PAYOFF)), 2)
    retention_pct = round((retained_dur / total_source * 100.0), 2) if total_source > 0 else 0.0

    plan = SemanticRegionCutPlan(
        region_id=region_id,
        region_title=title,
        source_range_start=all_decisions[0].source_start if all_decisions else 0.0,
        source_range_end=all_decisions[-1].source_end if all_decisions else 0.0,
        total_source_seconds=total_source,
        total_retained_seconds=retained_dur,
        retention_ratio=retention_pct,
        decisions=all_decisions,
        continuity_audit={"audit_summary": eval_resp.continuity_audit_summary},
        editorial_summary=eval_resp.editorial_verdict,
    )
    
    out_file = OUTPUT_DIR / f"{region_id}_plan.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"Saved {region_id} plan to {out_file}\n")
    return plan

async def main():
    client = AntigravityClient(model="gemini-3.1-pro-high", timeout=120.0)
    
    # 1. Region A: Introduction & Onboarding (0s - 360s)
    with open(CACHE_DIR / "region_a_intro.json", "r", encoding="utf-8") as f:
        trans_a = json.load(f)
    await evaluate_region(client, "Region_A_Introduction", "Session Onboarding & Game Launch", trans_a)
    
    # 2. Region B: Broken Transition (Police 5440s-5550s & Store 11800s-11920s)
    with open(CACHE_DIR / "region_b_police.json", "r", encoding="utf-8") as f:
        trans_b_pol = json.load(f)
    with open(CACHE_DIR / "region_b_store_jump.json", "r", encoding="utf-8") as f:
        trans_b_jump = json.load(f)
    await evaluate_region(client, "Region_B_Transition_Before", "Debt Payoff & Police Check", trans_b_pol)
    await evaluate_region(client, "Region_B_Transition_After", "Dispensary Employee Restock (Post-Jump)", trans_b_jump)
    
    # 3. Region C: Repetitive vs Progression
    with open(CACHE_DIR / "region_c_customer_loop.json", "r", encoding="utf-8") as f:
        trans_c_cust = json.load(f)
    with open(CACHE_DIR / "region_c_cultivation.json", "r", encoding="utf-8") as f:
        trans_c_grow = json.load(f)
    await evaluate_region(client, "Region_C_Customer_Loop", "Counter Sales & Contact List", trans_c_cust)
    await evaluate_region(client, "Region_C_Cultivation", "Basement Grow-Op Installation", trans_c_grow)
    
    print("\n=======================================================")
    print("All Diagnostic Pilot Regions Successfully Evaluated by LLM!")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
