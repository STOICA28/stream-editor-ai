---
id: ARCH-RENDER-001
title: Rendering Pipeline
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - rendering
---

# Rendering Pipeline

Hybrid system:
- **FFmpeg Executor:** Handles trim, concat, basic audio operations, cropping, and codec encoding.
- **Remotion Executor:** Handles rich overlays, animations, complex text, and UI elements.

**Security Rule:** Never execute model-generated strings directly in the shell. Effects must be defined in the [[05_SCHEMAS/EFFECTS|EffectAPI]].
