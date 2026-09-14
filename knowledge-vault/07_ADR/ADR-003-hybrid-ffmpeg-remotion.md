---
id: ADR-003
title: Hybrid FFmpeg and Remotion Rendering
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - adr
---

# ADR-003: Hybrid FFmpeg and Remotion

**Context:** FFmpeg is fast for cuts and audio, but terrible for dynamic UI elements. Remotion is great for UI but slow/heavy for basic cuts.
**Decision:** Use a hybrid approach: FFmpeg for core media operations, Remotion for rich overlays.
**Consequences:** Two rendering paths to maintain, requires a solid abstraction layer.
