---
id: RUN-RENDER-001
title: Rendering
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - runbook
---

# Rendering

- **Preview Render:** Generates a fast, low-res proxy video matching the EditPlan for web UI playback.
- **Final Render:** Triggered by user approval. Executes the EditPlan against the high-res original VOD using the hybrid FFmpeg/Remotion pipeline.
