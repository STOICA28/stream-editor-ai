---
id: RES-PROP-TRANSCRIPT-FIRST-001
title: Transcript-First Semantic Editing & Game-State Continuity Architecture
status: proposal
author: Antigravity Editorial Architecture
created: 2026-10-12
tags: [research, proposal, editorial, semantic, transcripts, continuity]
---

# Proposal: Transcript-First Semantic Cut Planning & Game-State Continuity Engine

## 1. Executive Context & Invalidation of Legacy Approaches

Following human editorial evaluation, both [[EXP-002_SETUP_PAYOFF_CLUSTERING|EXP-002]] and [[EDITORIAL_BENCHMARKING|E2E-LONGFORM-REFERENCE-002]] were rejected. The human reviewer identified that heuristic algorithms (such as fixed duration anchors, audio energy thresholds, and proximity grouping) produce superficial highlight reels rather than coherent narrative edits. Specifically:
1. **Administrative Chatter Retained:** 135+ seconds of volume tweaking and YouTube upload banter were preserved because heuristics mistook them for "introductory speech".
2. **True Video Start Cut:** The video greeting beginning at `0.0s` was sliced mid-sentence because audio energy thresholds delayed onset to `20.0s`.
3. **Severe Game-State Discontinuities:** 104-minute skips occurred with zero bridge context, jumping from a bankrupt solo dealer to an automated dispensary with hired clerks.
4. **Hallucinated Progression:** Heuristic tags categorized character customization as "grow light setup".

The solution is **Transcript-First Semantic Editorial Reasoning**, where an LLM parses the verbatim transcript before any cut boundaries or candidate selections are generated.

---

## 2. The Semantic Decision Contract

Defined in `packages/contracts/src/stream_editor/contracts/editorial.py`:

```python
class SemanticDecisionType(str, Enum):
    KEEP = "KEEP"                                    # Crucial narrative, premise, or entertaining highlight
    REMOVE = "REMOVE"                                # Unnecessary stream admin, audio test, redundant banter, dead air
    CONDENSE = "CONDENSE"                            # Action/dialogue is relevant but drawn out; trim to essentials
    KEEP_AS_CONTEXT = "KEEP_AS_CONTEXT"              # Required setup, rule explanation, or character motivation
    KEEP_AS_PAYOFF = "KEEP_AS_PAYOFF"                # Culmination or reaction that completes an earlier setup
    REQUIRES_PREVIOUS_CONTEXT = "REQUIRES_PREVIOUS_CONTEXT"  # Needs prior scene grounding to be intelligible
    UNCERTAIN = "UNCERTAIN"                          # Ambiguous moment requiring human review or secondary analysis
```

Every temporal window is represented as a `SemanticCutDecision` containing:
- Verbatim transcript quote
- Exact source timestamps
- Category classification (`stream_administration`, `premise_setup`, `gameplay_intro`, `gameplay_progression`, `repetitive_loop`, etc.)
- Narrative importance score ($0.0 \dots 1.0$)
- Prior and posterior game state description
- Explicit required context dependencies

---

## 3. Grounded Pilot Demonstrations

Tested against authentic Spanish WhisperX transcripts from the 5.19-hour master livestream:

1. **Region A (Intro & Onboarding: `0.0s – 360.0s`):**
   - Eliminated 100% of the 135.7s administrative audio/OBS testing and YouTube schedule banter.
   - Restored the exact `0.0s` opening hook (*"Vamos a empezar en este canal un juego..."*).
   - Preserved organization naming (*"Pacofi"*) and initial dispensary arrival.
   - Rendered video: `data/work/renders_pilot/region_a_onboarding_final.mp4` (174.34s, Validated).

2. **Region B (Broken Transition Audit: `5440.0s – 5550.0s` to `11800.0s – 11920.0s`):**
   - Intercepted the 104.75-minute game state jump.
   - Flagged the arrival of the hired clerk as `REQUIRES_PREVIOUS_CONTEXT`.
   - Prevented disorienting jump-cuts by enforcing narrative bridge insertion.
   - Rendered video: `data/work/renders_pilot/region_b_transition_final.mp4` (80.02s, Validated).

3. **Region C (Gameplay Loops & Progression: `920.0s – 1050.0s` & `1820.0s – 1930.0s`):**
   - Differentiated repetitive street dealing (condensed) from phone contact progression (kept).
   - Correctly recognized barber shop character customization instead of hallucinating agricultural tasks.
   - Rendered video: `data/work/renders_pilot/region_c_progression_final.mp4` (142.02s, Validated).

---

## 4. Architectural Integration & Roadmap

To scale this system across full 6-to-8 hour streams:
1. **Batch Transcription Chunker:** Transcribe 15-minute chapters with 30s overlap using `faster-whisper`.
2. **Transcript-First Editorial Chunker:** Analyze chapters with the Antigravity Model Provider (`agy`) producing `SemanticRegionCutPlan` objects.
3. **Game-State Continuity Engine (GSCE):** Chain state differentials across chapter boundaries to ensure every scene change is earned or bridged.
4. **Deterministic Assembly:** Compile validated `SemanticCutDecision` lists into standard `EditPlan` structures for rendering with 10ms audio edge crossfades.

Related documents:
- [[EDITORIAL_PHILOSOPHY]] — The foundational editorial rules.
- [[KEEP_VS_CUT]] — Guidelines on eliminating dead air and stream setup.
- [[CONTEXT_POLICY]] — Rules on pre-roll, post-roll, and narrative context preservation.
- [[PROJECT_STATUS]] — Current system state and benchmark records.
