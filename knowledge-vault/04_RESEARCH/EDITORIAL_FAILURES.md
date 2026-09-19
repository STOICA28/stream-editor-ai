---
id: RES-FAILURES-001
title: Editorial Failure Taxonomy & Root Cause Analysis
status: canonical
version: 1.0
last_reviewed: 2026-09-19
tags:
  - research
  - failure_taxonomy
  - benchmark
---

# Editorial Failure Taxonomy & Root Cause Analysis

To drive scientific improvement rather than ad-hoc tinkering, StreamEditor AI categorizes every editorial disagreement into a standardized taxonomy mapped to pipeline stages.

## 1. False Negative Taxonomy (Human Retained, AI Missed)

| Failure Code | Description | Typical Upstream Stage |
| :--- | :--- | :--- |
| `MISSED_HUMOR` | Subtle or deadpan comedic remark missed | M2 / M3 |
| `MISSED_REACTION` | Facial expression or streamer reaction without speech | M7 / M3 |
| `MISSED_IMPORTANT_EVENT` | Game clutch, kill, or narrative plot beat omitted | M2 |
| `MISSING_CONTEXT` | Pre-event context truncated too aggressively | M5 / M3 |
| `MISSING_SETUP` | Payoff retained, but preceding setup dropped | M4 / M5 |
| `MISSING_PAYOFF` | Setup retained, but punchline dropped | M4 / M5 |
| `MISSED_CALLBACK` | Recurring joke or callback omitted in later acts | M4 |
| `MISSING_CHAT_CONTEXT` | Streamer responding to chat message not incorporated | M2 |
| `MISSING_VISUAL_EVENT` | Game UI pop-up, scoreboard, or visual gag missed | M7 |
| `LOW_SCORE` | Score below candidate threshold due to quiet delivery | M3 |
| `BUDGET_EXCLUSION` | Valid moment dropped by knapsack duration constraint | M5 |
| `REDUNDANCY_EXCLUSION` | Candidate erroneously marked redundant with earlier beat | M3 / M5 |
| `DEPENDENCY_FAILURE` | Node isolated in Story Graph due to missing edge | M4 |
| `UNKNOWN` | Uncategorized disagreement requiring human audit | Audit |

---

## 2. False Positive Taxonomy (AI Retained, Human Omitted)

| Failure Code | Description | Typical Upstream Stage |
| :--- | :--- | :--- |
| `DEAD_AIR` | Silence, pause, or idle waiting retained | M2 / M3 / M5 |
| `REPETITIVE` | Repeated sentence, action, or redundant phrase | M3 / M5 |
| `LOW_INFORMATION` | Meaningless gameplay traverse or inventory checking | M3 / M5 |
| `UNNECESSARY_CONTEXT` | Excessive preamble before the actual beat | M3 / M5 |
| `WEAK_REACTION` | Mild twitch or breath misclassified as dramatic | M7 / M3 |
| `FAILED_HUMOR` | Attempted joke that fell flat in stream context | M3 |
| `OFF_TOPIC` | Distracting tangent disconnected from main stream thread | M4 / M5 |
| `OVERLONG_SETUP` | Setup exceeds 2.5x the human standard duration | M3 / M5 |
| `OVERLONG_PAYOFF` | Lingering outro after streamer punchline | M3 / M5 |
| `VALID_ALTERNATIVE` | High-quality moment that human editor omitted for time | Acceptable Alternative |
| `HUMAN_REFERENCE_UNCERTAIN` | Ambiguous human edit boundary or stylistic whim | Reference Noise |
| `UNKNOWN` | Uncategorized disagreement | Audit |

---

## 3. Root Cause Investigation Procedure

When an experiment is designed to improve a metric:
1. Identify the primary failure code in the baseline run (e.g., `M2:MISSED_IMPORTANT_EVENT`).
2. Verify with the Root-Cause Stage Tracer whether the event was absent in M2, filtered in M3, isolated in M4, or pruned in M5.
3. Formulate a targeted hypothesis targeting ONLY the responsible stage.
4. Execute the experiment against the held-out test split.
5. Require positive delta in F1 / Completeness without regression in precision.
