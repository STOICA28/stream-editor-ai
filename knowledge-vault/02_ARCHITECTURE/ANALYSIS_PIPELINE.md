---
id: ARCH-ANALYSIS-001
title: Analysis Pipeline
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - analysis
---

# Analysis Pipeline

The analysis subsystems generate [[05_SCHEMAS/TIMELINE_EVENT|TimelineEvents]]. These events can overlap.

- **Transcription:** Using WhisperX with word-level timestamps.
- **Scene Detection:** Detecting major visual cuts or game state changes.
- **Visual Events:** Detecting face reactions, UI elements.
- **Audio Events:** Detecting laughter, shouting, silence.
- **Chat Analysis:** Processing the stream chat to find high-activity spikes and interactions.
