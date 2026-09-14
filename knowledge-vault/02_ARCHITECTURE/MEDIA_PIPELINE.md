---
id: ARCH-MEDIA-001
title: Media Pipeline
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - media
---

# Media Pipeline

**Principle:** Never run expensive AI on full-quality source.

1. **Retain Original:** The original VOD is saved and untouched.
2. **FFprobe:** Extract basic metadata (duration, codecs, res).
3. **Analysis Proxy:** Generate a 720p, reasonably bitrated version for visual models.
4. **Audio Extraction:** Extract 16kHz mono audio for WhisperX.
5. **Frame Sampling:** Extract frames at 1fps for visual analysis.
6. **Final Render:** The resulting EditPlan ALWAYS references the original high-quality VOD for the final export.
