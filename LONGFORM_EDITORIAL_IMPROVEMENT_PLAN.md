# LONG-FORM EDITORIAL SELECTION IMPROVEMENT PLAN
**Document ID:** PLAN-LONGFORM-001  
**Target Milestone:** Long-Form Editorial Intelligence & Reference Alignment  
**Dependencies:** Contracts (`packages/contracts`), Editorial Planning (`packages/editorial`), M10 EditDNA Cache  

---

## 1. Context and Problem Statement

Previous evaluations of StreamEditor AI yielded a 43.5-second snippet (`streameditor_e2e_real_edit.mp4`) that omitted the streamer's opening greeting, dropped the initial game launch, and reduced a 5.2-hour broadcast to four isolated moments.

The root cause audit (`LONGFORM_EDITING_ROOT_CAUSE_AUDIT.md`) established that:
1. The demo runner manually selected 4 clips from a 10-minute slice (`source_short.mp4`) rather than processing the 5.19-hour master stream.
2. In the codebase, M5 duration policies lacked explicit long-form editing goals (`SHORT_HIGHLIGHT`, `LONG_FORM_SUMMARY`, `FULL_EDITED_SESSION`).
3. M5 duration pruning prioritized dropping `ClipPriority.context_only` first, eliminating greetings, explanations, and setups under duration pressure.
4. M4 StoryGraph lacked structural anchor typing for `STREAM_GREETING` and `GAME_START`.

Conversely, the Human Reference Alignment Report (`HUMAN_REFERENCE_ALIGNMENT_REPORT.md`) demonstrated that the human editor:
- Preserved **86.7%** of the first 15 minutes of the broadcast (opening greeting and game launch).
- Structured the 40.6-minute edit primarily around **conversations (70.5%)** and **reactions (20.5%)**.
- Cut over **49.3%** of repetitive mechanical farming loops.

This improvement plan delivers the minimal, staged architectural enhancements required to make StreamEditor produce coherent, full-scale long-form edits.

---

## 2. Staged Implementation Roadmap

```text
[Stage 1: Contracts]
  └─ Define EditingGoal enum (SHORT_HIGHLIGHT, LONG_FORM_SUMMARY, FULL_EDITED_SESSION)
  └─ Add narrative anchor fields to EditClipContract and EditPlanConfig
       │
[Stage 2: Anchor Protection]
  └─ Implement Narrative Anchor Detector (STREAM_GREETING, GAME_START, OUTRO)
  └─ Mark anchors as ClipPriority.essential and is_narrative_anchor=True
       │
[Stage 3: Optimizer Calibration]
  └─ Protect narrative anchors from duration pruning in DeterministicDurationOptimizer
  └─ Support configurable budget allocation by EditingGoal
       │
[Stage 4: Evaluation Benchmark]
  └─ Implement E2E-LONGFORM-REFERENCE-001 evaluation harness
  └─ Compare AI selection vs Human Edit Decision Map across 5.19h timeline
       │
[Stage 5: Long-Form Demonstration Rendering]
  └─ Generate and render long-form EditPlan using neutral cuts
  └─ Validate with MediaValidator
       │
[Stage 6: Quality Gates & Git Push]
  └─ pytest, mypy, check_vault.py
  └─ Commit and push to origin/master
```

---

## 3. Detailed Specifications

### 3.1 Stage 1: Contract Enhancements (`packages/contracts`)
In `packages/contracts/src/stream_editor/contracts/edit_plan.py`:
- Introduce `EditingGoal`:
  ```python
  class EditingGoal(str, Enum):
      SHORT_HIGHLIGHT = "SHORT_HIGHLIGHT"        # Target ~120s (1 - 3 min for Shorts)
      LONG_FORM_SUMMARY = "LONG_FORM_SUMMARY"    # Target ~900s (10 - 20 min episode)
      FULL_EDITED_SESSION = "FULL_EDITED_SESSION" # Target ~2400s (35 - 45 min full edit)
  ```
- Enhance `EditPlanConfig`:
  - `editing_goal: EditingGoal = EditingGoal.LONG_FORM_SUMMARY`
  - `preserve_narrative_anchors: bool = True`
  - Helper method `get_target_duration_for_goal(goal: EditingGoal) -> tuple[float, float]` to compute appropriate target and tolerance.
- Enhance `EditClipContract`:
  - `is_narrative_anchor: bool = False`
  - `anchor_type: str | None = None` (e.g. `"STREAM_GREETING"`, `"GAME_START"`, `"OUTRO"`)

### 3.2 Stage 2: Narrative Anchor Detection (`packages/editorial`)
Create `packages/editorial/src/stream_editor/editorial/planning/anchors.py`:
- `NarrativeAnchorDetector`:
  - Detects `STREAM_GREETING`: The earliest speech segment in the stream (source time `< 120.0s`) where the streamer greets viewers.
  - Detects `GAME_START`: The first transition where game activity commences (source time between `180.0s` and `400.0s`).
  - Detects `OUTRO`: The final conversation segment concluding the stream (within final 5 minutes of stream).
  - Automatically flags matching candidates as `is_narrative_anchor=True` and sets `priority=ClipPriority.essential`.

### 3.3 Stage 3: Calibrated Duration Pruning (`packages/editorial`)
In `packages/editorial/src/stream_editor/editorial/planning/optimizer.py`:
- Update `DeterministicDurationOptimizer`:
  - When pruning candidates to meet the target duration:
    - Never prune any clip with `is_narrative_anchor=True` or `locked=True` or `priority=ClipPriority.essential`.
    - Only prune non-anchor clips from `context_only` -> `low` -> `medium` -> `high`.
    - Re-pack output timestamps maintaining chronological continuity.

### 3.4 Stage 4: Independent Benchmark `E2E-LONGFORM-REFERENCE-001`
Create `scripts/run_e2e_longform_reference_benchmark.py`:
- Measures AI editorial selection against the ground truth Human Edit Decision Map across the complete 5.19-hour timeline.
- Key Metrics:
  - Opening Greeting Preservation (PASS/FAIL)
  - Game Start Preservation (PASS/FAIL)
  - Intersection of Retained Source Intervals (seconds & percentage)
  - Retained Repetition Penalty (avoiding monotonous loops)
  - Output Duration Alignment to declared `EditingGoal`
  - Temporal Distribution across chapters

### 3.5 Stage 5: Long-Form Demonstration Rendering
- Execute end-to-end rendering on `source.mp4` using M9.
- Use restrained/neutral cuts without VFX masks to evaluate cut quality cleanly.
- Verify playback and structural integrity via `MediaValidator`.

---

## 4. Verification and Acceptance Criteria

1. **Unit Tests:**
   - Test `EditingGoal` serialization and budget resolution in `EditPlanConfig`.
   - Test `NarrativeAnchorDetector` correctly flags greeting and game start.
   - Test `DeterministicDurationOptimizer` preserves anchor clips under extreme duration pressure (e.g. budget reduced to 60s).
2. **Quality Gates:**
   - `uv run pytest` passes 100%.
   - `uv run mypy packages apps` passes with zero errors.
   - `python scripts/check_vault.py` passes.
3. **Evidence Artifacts:**
   - `E2E_LONGFORM_REFERENCE_001_REPORT.md` documenting benchmark metrics.
   - Rendered demonstration MP4 and manifest.
