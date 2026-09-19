---
id: TEST-BENCHMARK-001
title: Editorial Quality Evaluation & Real-World Benchmarking (M13)
status: canonical
version: 1.0
last_reviewed: 2026-09-19
tags:
  - testing
  - benchmarking
  - editorial_quality
  - ground_truth
---

# Editorial Quality Evaluation & Real-World Benchmarking (M13)

## 1. Overview and Core Philosophy

Milestone 13 (M13) transitions StreamEditor from asking *"Can the system run and render?"* (proven in M1–M12) to the fundamental scientific question:

```text
DOES STREAMEDITOR ACTUALLY EDIT WELL?
```

We evaluate editorial decisions by comparing StreamEditor's automated edits against human-edited YouTube releases from the same source livestream footage (VODs).

### Critical Distinction: Reference Agreement vs. Editorial Quality
A human editor's cut represents **one high-quality editorial path** through the footage, not the sole valid path:
- **Reference Agreement**: Precision, Recall, and F1 at specific temporal boundary tolerances (±0.5s, ±1.0s, ±2.0s). Measures direct overlap with the human editor.
- **Editorial Quality**: Evaluated through narrative completeness (Setup/Payoff pairs, running jokes), pacing rhythms, content density, and semantic assessment of AI-only segments to detect **Valid Alternatives** vs. **False Positives** (dead air, repetitive filler).

---

## 2. Dataset Partitions and Strict Anti-Leakage Protocol

To ensure rigorous scientific validity, the benchmark suite enforces strict partition boundaries:

1. **`REFERENCE` (Training Split)**:
   - Example: `source_short.mp4` (600s) & `edited_short.mp4` (120s).
   - Used *exclusively* for EditDNA extraction and StyleProfile learning.
   - **STRICT PROHIBITION**: Never evaluated as a test pair.
2. **`VALIDATION` (Tuning Split)**:
   - Example: `tests/fixtures/source_0.mp4` & `tests/fixtures/edited_0.mp4` (`ground_truth_0.json`).
   - Used for hyperparameter optimization and boundary tolerance verification.
3. **`TEST` (Held-Out Unseen Benchmark Pairs)**:
   - Example 1: `tests/fixtures/source_1.mp4` & `tests/fixtures/edited_1.mp4` (`ground_truth_1.json`).
   - Example 2: `tests/fixtures/source_2.mp4` & `tests/fixtures/edited_2.mp4` (`ground_truth_2.json`).
   - Example 3: Real long-form livestream aligned slice (`cache/m10_alignment_state.json`).
   - Evaluated *strictly on unseen content* without prior model exposure.

---

## 3. Evaluation Dimensions & Mathematical Formulation

### 3.1 Interval Selection Overlap
For AI intervals \(A = \bigcup [s_{a,i}, e_{a,i}]\) and human intervals \(H = \bigcup [s_{h,j}, e_{h,j}]\):

$$\text{Precision}(\tau) = \frac{\mu(A \cap_\tau H)}{\mu(A)}$$
$$\text{Recall}(\tau) = \frac{\mu(A \cap_\tau H)}{\mu(H)}$$
$$F_1(\tau) = \frac{2 \cdot \text{Precision}(\tau) \cdot \text{Recall}(\tau)}{\text{Precision}(\tau) + \text{Recall}(\tau)}$$

Where \(\tau \in \{0.5\text{s}, 1.0\text{s}, 2.0\text{s}\}\) accounts for natural human reaction time and micro-boundary shifts.

### 3.2 Context Quantiles
- **Pre-Context Delta**: \(t_{\text{start, AI}} - t_{\text{start, Human}}\). Quantiles \(p_{10}, p_{25}, p_{50}, p_{75}, p_{90}\).
- **Post-Context Delta**: \(t_{\text{end, AI}} - t_{\text{end, Human}}\). Measures lingering outros vs. premature cut-offs.

### 3.3 Narrative Completeness
$$\text{Completeness} = \frac{N_{\text{Setup-Payoff Intact}}}{N_{\text{Setup-Payoff Total}}}$$

### 3.4 Pacing & Rhythms
- **Cut Frequency**: Cuts per minute compared directly between Human and AI.
- **Dead Air Ratio**: Silence duration divided by total output duration.

### 3.5 Effect Agreement
$$\text{Agreement Rate} = \frac{N_{\text{Same Effect}} + N_{\text{Similar Effect}}}{N_{\text{Total Effects}}}$$

---

## 4. Upstream Root-Cause Stage Tracer

Every editorial disagreement (False Negative or False Positive) is programmatically traced to its earliest pipeline origin:
1. **Stage M2 (Understanding)**: Was a TimelineEvent or speech segment detected? If not \(\rightarrow\) `M2:MISSED_IMPORTANT_EVENT`.
2. **Stage M3 (Candidate Generation)**: Did M3 propose a candidate? If not \(\rightarrow\) `M3:LOW_SCORE` or `M3:MISSING_VISUAL_EVENT`.
3. **Stage M4 (Story Graph)**: Was the node connected and given narrative weight? If isolated \(\rightarrow\) `M4:DEPENDENCY_FAILURE`.
4. **Stage M5 (Global Selection)**: Was it pruned by the knapsack optimizer? If dropped for budget \(\rightarrow\) `M5:BUDGET_EXCLUSION`.
5. **Stage M7 / M8**: Visual reaction or effect planning omissions.

---

## 5. M13 Baseline Benchmark Results (Unseen Test Split)

| Metric | Baseline Value | Interpretation |
| :--- | :--- | :--- |
| **Cases Evaluated (N)** | **3** | Held-Out Test Split |
| **Precision (@ ±1.0s)** | **75.98%** | AI selections are predominantly human-supported or valid |
| **Recall (@ ±1.0s)** | **58.52%** | Room for improvement in capturing subtle reaction beats |
| **F1 Score (@ ±1.0s)** | **0.6471** | **Immutable baseline anchor for future experiments** |
| **Setup/Payoff Completeness** | **100.0%** | All paired narrative beats retained intact |
| **Effect Agreement Rate** | **100.0%** | Zoom-face and speed-ramp placement match human intent |
| **Segment Counts** | **6 Matched / 2 Missed / 0 AI-Only** | Root cause of 2 misses: `M2:MISSED_IMPORTANT_EVENT` |

All baseline runs are immutably persisted in `benchmark_runs` and `benchmark_results`.
