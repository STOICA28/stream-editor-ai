---
id: RES-EXP-002
title: "EXP-002: Stage M3 Setup/Payoff Clustering Window"
status: canonical
version: 1.0
last_reviewed: 2026-09-19
tags:
  - research
  - experiment
  - m3_candidate_generation
  - benchmark
  - setup_payoff
---

# EXP-002: Stage M3 Setup/Payoff Clustering Window

## 1. Executive Summary
- **Experiment ID:** `EXP-002`
- **Target Stage:** Stage M3 (Candidate Generation & Windowing)
- **Baseline Run Anchor:** M13 Baseline Run (`run-baseline-case-test-001`, `run-baseline-case-test-002`, `run-baseline-case-test-real-001`)
- **Status:** **PASSED**
- **Date Executed:** 2026-09-19

EXP-002 investigated and resolved the primary cause of lead-in clipping identified in the M13 Baseline: **pre-context truncation ($\Delta_{\text{pre}} > 0$)**. By expanding backward clustering windows by $1.5\text{s}$ and snapping candidate boundaries to preceding conversational/narrative setup anchors, candidate generation preserves complete setup-payoff units without over-extending into dead air.

---

## 2. Hypothesis & Problem Formulation

### Problem Statement
In livestream editing, high-intensity moments (clutches, jokes, reactions) require preceding conversational context to be intelligible and entertaining. When candidate generation bounds intervals strictly to peak signal triggers:
- Punchlines lose their setup.
- Dialogue starts with cut-off syllables.
- Pre-context error median was $+0.10\text{s}$ to $+0.25\text{s}$ on short clips, and $-18.00\text{s}$ on long-form footage.

### Hypothesis
> Expanding backward clustering windows by $1.5\text{s}$ (`backward_setup_window`) and snapping candidate lead-in boundaries to preceding narrative/speech onset anchors in Stage M3 eliminates setup truncation, improving Pre-Context error by $\ge 50\%$ towards $0.00\text{s}$ and driving Multi-Tolerance Recall (@ $\pm1.0\text{s}$) beyond $80.0\%$ while keeping Setup/Payoff Completeness at $100.0\%$.

---

## 3. Architecture & Algorithmic Changes

### 3.1 Contract Parameterization (`packages/contracts`)
`CandidateWindowConfig` now includes:
```python
backward_setup_window: float = 1.5  # seconds - scan backward for narrative/speech setup
```

### 3.2 Backward Snapping with Scene Protection (`packages/editorial`)
In `ContextExpander.expand`:
1. Identifies immediately preceding transcript segments within `backward_setup_window`.
2. Extends `core_start` backward to encapsulate the full setup dialogue.
3. Guards against crossing hard visual scene cuts (`new_core_start < sc.start_time <= window.core_start`).

---

## 4. Empirical Evaluation Results

### 4.1 Benchmark Comparison on Held-Out Test Split ($N=3$)

| Metric Dimension | M13 Baseline | EXP-001 | EXP-002 | Cumulative Delta |
| :--- | :--- | :--- | :--- | :--- |
| **Mean Recall (@ $\pm1.0\text{s}$)** | $58.52\%$ | $77.96\%$ | **83.89%** | **+25.37%** |
| **Mean Precision (@ $\pm1.0\text{s}$)** | $75.98\%$ | $88.20\%$ | **88.27%** | **+12.29%** |
| **Mean F1 Score (@ $\pm1.0\text{s}$)** | $0.6471$ | $0.8249$ | **0.8573** | **+0.2102** |
| **Pre-Context Error \|Delta\|** | $6.117\text{s}$ | $6.100\text{s}$ | **1.667s** | **-72.8%** |
| **Setup/Payoff Completeness** | $100.0\%$ | $100.0\%$ | **100.0%** | $+0.0\%$ |

### 4.2 Case Breakdown

- **`case-test-001` (Comedic Dialogue + Reaction):**
  - Recall (@ 1.0s): $75.0\% \to \mathbf{95.0\%}$
  - Precision (@ 1.0s): $\mathbf{91.9\%}$ | F1: $\mathbf{0.9344}$
  - Pre-Context Delta: $+0.10\text{s} \to \mathbf{+0.00\text{s}}$ (100% eliminated)
- **`case-test-002` (Gameplay Clutch):**
  - Recall (@ 1.0s): $88.3\% \to \mathbf{100.0\%}$
  - Precision (@ 1.0s): $\mathbf{100.0\%}$ | F1: $\mathbf{1.0000}$
  - Pre-Context Delta: $+0.25\text{s} \to \mathbf{+0.00\text{s}}$ (100% eliminated)
- **`case-test-real-001` (5-hour Real Stream Slice):**
  - Recall (@ 1.0s): $12.2\% \to \mathbf{56.7\%}$
  - Precision (@ 1.0s): $\mathbf{72.9\%}$ | F1: $\mathbf{0.6375}$
  - Pre-Context Delta: $-18.00\text{s} \to \mathbf{+5.00\text{s}}$ (72.2% reduction)

---

## 5. Verification Gates Sign-Off

- **Gate 1 (Recall > 80.00%):** **PASS** ($83.89\%$)
- **Gate 2 (Precision >= 75.00%):** **PASS** ($88.27\%$)
- **Gate 3 (Completeness == 100.0%):** **PASS** ($100.0\%$)
- **Gate 4 (Pre-Context Error Reduction >= 50%):** **PASS** ($72.8\%$)
- **Gate 5 (Regression Tests):** **PASS** (70/70 unit tests passing)
- **Gate 6 (Type Safety):** **PASS** (0 errors across 99 files)
- **Gate 7 (Database State):** **PASS** (`status='PASSED'` in `benchmark_experiments`)

---

## 6. Next Research Step
- **[[EXP-003_PACING_CONTINUITY_SMOOTHING|EXP-003: Stage M5 Pacing Continuity Smoothing]]:** Snap rapid consecutive dialogue cuts separated by $< 0.4\text{s}$ of audio silence into unified continuous clips to eliminate micro-jumpcuts.
