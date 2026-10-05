---
id: ARCH-SYS-001
title: System Overview
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - system
---

# System Overview

StreamEditor AI is a monorepo containing multiple apps and packages.

## Pipeline Topology (Canonical Stages M1 to M9)

StreamEditor AI executes a strictly directed pipeline without backward circular dependencies:

```text
M1: Media Ingest & Proxy Generation
 ↓
M2: Understanding Layer (Speech, Scenes, Audio Events, Lightweight Visual Observations)
 ↓
M3: Candidate Generation & Multi-Dimensional Scoring
 ↓
M4: Story Graph Assembly & Dependency Resolution
 ↓
M5: EditPlan Optimization (Knapsack Beat Selection)
 ↓
M6: Human Review & Interactive Overrides
 ↓
M7: Detailed Visual Understanding (Face Tracking, Saliency, Focus Targets)
 ↓
M8: Effect Planning & Composition
 ↓
M9: Deterministic Video Rendering (FFmpeg & Remotion)
```

> [!IMPORTANT]
> Stage M2 answers *what happened* using lightweight CV without touching Stage M7. Stage M7 answers *where to focus and zoom* strictly downstream after clip selection. M2 must never import or query M7 outputs.

