---
id: ARCH-BENCHMARK-001
title: Editorial Benchmark System Architecture
status: canonical
version: 1.0
last_reviewed: 2026-09-19
tags:
  - architecture
  - benchmark
  - evaluation
---

# Editorial Benchmark System Architecture

```text
                      ┌──────────────────────────────────────┐
                      │          Benchmark Cases DB          │
                      │  (REFERENCE / VALIDATION / TEST)     │
                      └──────────────────┬───────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
                 ▼                                               ▼
   ┌───────────────────────────┐                   ┌───────────────────────────┐
   │   Human Reference Cut     │                   │  StreamEditor Pipeline    │
   │  (Ground Truth Fixtures)  │                   │  (Unmodified M1-M9 Run)   │
   └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                 │                                               │
                 │   HumanReferenceTimeline                      │  StreamEditorTimeline
                 └───────────────────────┬───────────────────────┘
                                         │
                                         ▼
                      ┌─────────────────────────────────────┐
                      │      EditorialBenchmarkEngine       │
                      │                                     │
                      │  1. Overlap Metrics (±0.5, 1.0, 2.0)│
                      │  2. Context Quantiles (Pre/Post)    │
                      │  3. Narrative Completeness (Setup)  │
                      │  4. Pacing & Density Quantiles      │
                      │  5. Effect Placement Agreement      │
                      │  6. Upstream Root Cause Tracer      │
                      └──────────────────┬──────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
                 ▼                                               ▼
   ┌───────────────────────────┐                   ┌───────────────────────────┐
   │  PostgreSQL Persistence   │                   │  Next.js Benchmark UI     │
   │  - benchmark_runs         │                   │  - KPI Scorecards         │
   │  - benchmark_results      │                   │  - Dual-Track Timeline    │
   │  - benchmark_failures     │                   │  - Root Cause Inspector   │
   │  - benchmark_experiments  │                   │  - Experiment Tracker     │
   └───────────────────────────┘                   └───────────────────────────┘
```

## Core Components
- `packages/contracts/src/stream_editor/contracts/benchmark.py`: Strict Pydantic contracts for datasets, metrics, and failures.
- `packages/research/src/stream_editor/research/benchmark/`: Evaluation engine, metrics calculators, classifier, and semantic evaluator.
- `apps/api/src/stream_editor/api/routers/benchmark.py`: REST API endpoints for automated benchmark execution and reporting.
- `apps/web/src/app/benchmarks/`: Web dashboard for comparative visual inspection.
