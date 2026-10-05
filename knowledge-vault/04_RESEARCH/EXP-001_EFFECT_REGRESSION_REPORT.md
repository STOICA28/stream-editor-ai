# EXP-001/EXP-001R Effect Agreement Regression Trace

## Overview
In the initial `EXP-001` run, the Effect Agreement Rate regressed from 100.0% to 83.3% (a -16.7 percentage point drop). 
This report investigates the exact cause of the regression by tracing the mismatched effect through the pipeline stages, as requested.

## Pipeline Trace (Case: `case-test-001`)

**Human Ground Truth (`tests/fixtures/ground_truth_1.json`):**
- Has an effect at 4.0s - 5.0s of type `grayscale`.
- Has an effect at 6.5s - 7.5s of type `zoom_face`.

**AI Pipeline Trace (EXP-001):**
1. **M2 (Understanding):** Detects `face_reaction` (Comedic smirk and eyebrow raise reaction) at 4.0s - 5.0s with 0.92 confidence.
2. **M3 (Candidate Generation):** Elevates this reaction to a candidate clip from 4.0s - 5.0s, giving it a score of 0.91 (boosted visual interest).
3. **M5 (Editorial Planning):** Selects the clip `clip-rx` for the final EditPlan from 4.0s - 5.0s to capture the reaction.
4. **M7 (Visual Understanding):** Identifies the streamer's face as the primary `FocusTarget` during this clip.
5. **M8 (Effect Planning):** Generates an `EffectInstruction` of type `zoom_face` from 4.2s - 4.8s.

## Evaluation Match Result
- **AI Effect:** `zoom_face` (4.2s - 4.8s)
- **Human Effect:** `grayscale` (4.0s - 5.0s)
- **Status:** **different** (Mismatched effect type on the same narrative beat)

## Breakdown of Effects (N=6 across dataset)
- **same**: 5
- **similar**: 0
- **different**: 1 (The `zoom_face` vs `grayscale` mismatch detailed above)
- **AI-only**: 0
- **human-only**: 0

5/6 comparable effects agree = **83.3%**

## Conclusion
The drop in Effect Agreement is not a failure of the `face_reaction` elevation logic. It accurately captured the human's edit timing. The regression occurred because M8 chose `zoom_face` to highlight the smirk, while the human editor chose `grayscale` for a deadpan comedic effect. The beat was correctly retained (increasing Recall), but the creative effect choice diverged.
