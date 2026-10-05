---
id: RES-EXP-001
title: "EXP-001: Stage M2 Visual Reaction Elevation"
status: experiment
version: 1.0
last_reviewed: 2026-09-19
tags:
  - research
  - experiment
  - m2_understanding
  - benchmark
  - visual_reactions
---

# EXP-001: Stage M2 Visual Reaction Elevation

> [!WARNING] STATUS REVOKED
> This experiment was marked as canonical without proper governance, tuned on the test set, and introduced architectural leakage (M7 -> M2). The visual reaction benefits are being re-validated cleanly in EXP-001R.

## 1. Executive Summary
- **Experiment ID:** `EXP-001`
- **Target Stage:** Stage M2 (Understanding)
- **Baseline Run Anchor:** M13 Baseline Run (`run-baseline-case-test-001`, `run-baseline-case-test-002`, `run-baseline-case-test-real-001`)
- **Status:** **REVOKED / REPLACED BY EXP-001R**
- **Date Executed:** 2026-09-19

EXP-001 investigated and resolved the single largest source of false negatives identified in the M13 Baseline evaluation: **missed non-speech facial reactions and visual punchlines**. By elevating high-confidence visual reactions detected in Stage M2 into canonical `TimelineEvents`, downstream candidate generation (Stage M3) and story graph planning (Stage M4/M5) successfully captured comedic reaction beats.

---

## 2. Hypothesis & Problem Formulation

### Problem Statement
In the M13 Baseline run, StreamEditor achieved 75.98% Precision and 58.52% Recall on held-out test cases. The Root-Cause Stage Tracer pinpointed that **66.7% of all false negatives** were caused by `M2:MISSED_IMPORTANT_EVENT`.

Audit showed that `apps/worker/src/stream_editor/worker/tasks/pipeline.py` (`normalize_timeline_task`) only converted transcript segments (speech), scene boundaries, and audio peaks into `TimelineEvent` records. Silent facial expressions (raised eyebrows, deadpan smirks, mouth agape, celebration gestures) detected during visual analysis remained trapped in `visual_events` and were never exposed to Stage M3 `EventClusterer`.

### Formal Hypothesis
> Elevating high-confidence ($\ge 0.70$) facial expression shifts (`strong_face_reaction`, `visual_event`) from Stage M2 Understanding into `TimelineEvents` with `event_type="face_reaction"` will allow Stage M3 (Candidate Generation) and Stage M4 (Story Graph) to propose and retain subtle comedic reaction beats, increasing Overlap Recall (@ $\pm1.0\text{s}$) from $58.52\%$ to $> 70.00\%$ on held-out test content without degrading Precision below $70.00\%$ or violating the $100\%$ Setup/Payoff Completeness invariant.

---

## 3. HISTORICAL INVALID IMPLEMENTATION Details

> [!CAUTION] ARCHITECTURAL & METHODOLOGICAL DEFECTS
> The following implementation contained architectural leaks (Stage M2 querying Stage M7 models `DBVisualEvent` and `VisualAnalysisRun`), hardcoded magic constants, and evaluated against consumed test pairs. It is preserved strictly as historical record.

1. **Stage M2 Timeline Normalization (INVALID):**
   Updated `normalize_timeline_task` in `apps/worker/src/stream_editor/worker/tasks/pipeline.py` to query `DBVisualEvent` joined to `VisualAnalysisRun` for `source_asset_id == asset_id`. High-confidence ($\ge 0.70$) events were converted into `TimelineEvent` records with `event_type="face_reaction"`, introducing an inverted M7 $\to$ M2 dependency.

2. **Editorial Contracts Extension:**
   Extended `LocalFeatures` in `packages/contracts/src/stream_editor/contracts/editorial.py` with `visual_reaction_count: int | None = 0` and `visual_event_count: int | None = 0`.

3. **Deterministic Feature Extraction:**
   Updated `LocalFeatureExtractor.extract` in `packages/editorial/src/stream_editor/editorial/features.py` to inspect `window_events` and compute counts for `face_reaction`, `strong_face_reaction`, and `visual_event`.

4. **Candidate Scoring & Reaction Elevation (MAGIC NUMBERS):**
   In `packages/editorial/src/stream_editor/editorial/generator.py`, updated candidate scoring with hardcoded boosts ($\ge 0.60 + 0.15 \times N$) and fixed floor scores ($\ge 0.75$).

5. **Automated Experiment Execution & DB Persistence:**
   Implemented `scripts/run_exp_001.py`, which evaluated against test cases that had been previously inspected during exploratory work.

---

## 4. Quantitative Results vs. M13 Baseline (CONSUMED TEST SPLIT)

Evaluated across the now-consumed `TEST` partition ($N=3$):

| Metric | Baseline | EXP-001 | Absolute Delta | Acceptance Threshold | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Mean Precision (@ $\pm1.0\text{s}$)** | **75.98%** | **88.20%** | **+12.22%** | $\ge 70.00\%$ | **PASS** |
| **Mean Recall (@ $\pm1.0\text{s}$)** | **58.52%** | **77.96%** | **+19.44%** | $> 70.00\%$ | **PASS** |
| **Mean F1 Score (@ $\pm1.0\text{s}$)** | **0.6471** | **0.8249** | **+0.1778** | $> 0.0000$ | **PASS** |
| **Setup/Payoff Completeness** | **100.0%** | **100.0%** | **+0.0%** | $\ge 95.00\%$ | **PASS** |
| **Effect Agreement Rate** | **100.0%** | **83.3%** | **-16.7%** | $\ge 70.00\%$ | **REGRESSION** |
| **Stage M2 Root-Cause Misses** | **2** | **0** | **-2** | $= 0$ | **PASS** |
| **Total Matched / Missed Segments** | **6M / 2FN** | **7M / 0FN** | **+1M / -2FN** | Net FN reduction | **PASS** |

### Per-Case Metric Breakdown

| Case ID | Case Description | Split | Baseline Recall | EXP-001 Recall | Baseline Precision | EXP-001 Precision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `case-test-001` | Held-Out Test Pair 1 (dialogue + reaction) | CONSUMED | 75.0% | **91.7%** | 90.0% | **91.7%** |
| `case-test-002` | Held-Out Test Pair 2 (continuous narrative) | CONSUMED | 88.3% | **88.3%** | 100.0% | **100.0%** |
| `case-test-real-001` | Real VOD Aligned Slice (5hr livestream extract) | CONSUMED | 12.2% | **53.9%** | 37.9% | **72.9%** |

---

## 5. Key Findings & Analysis

1. **Reaction Inclusion Without Overselection:**
   Elevating visual reactions did not induce dead-air bloat. Precision increased from 75.98% to 88.20% on the consumed split because the elevated reaction intervals matched human-edited timing.
2. **Resolution of Upstream M2 Failures:**
   All occurrences of `M2:MISSED_IMPORTANT_EVENT` in the consumed test split dropped from 2 to 0.
3. **Preservation of Story Integrity:**
   Setup/Payoff Completeness remained at 100.0%.
4. **Effect Agreement Regression (-16.7%):**
   In `case-test-001`, M8 placed a `zoom_face` on the reaction beat where the human editor chose `grayscale`.

---

## 6. Superseded Status & Resolution

EXP-001 was invalidated and superseded by EXP-001R.

The corrective actions performed in EXP-001R:
1. Architectural decoupling: M2 now runs lightweight visual observations independent of M7.
2. Magic constants eliminated: Configuration moved to versioned `VisualReactionExperimentConfig`.
3. Test split integrity: Consumed cases moved to VALIDATION, and new untouched holdout cases (`case-test-003`, `case-test-real-002`) introduced for evaluation.

