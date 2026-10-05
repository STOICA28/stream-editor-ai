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

## Stage M2 — Multimodal Understanding
Stage M2 processes the 720p analysis proxy to extract raw chronological evidence:
- **Transcription:** Using WhisperX with word-level timestamps.
- **Scene Detection:** Detecting major visual cuts or game state changes via PySceneDetect.
- **Lightweight Visual Observations (`face_reaction`):** Upstream facecam motion and expression dynamics using `OpenCVVisualObservationProvider` (sampling at 4.0 fps, bounded $O(1)$ memory). Answers: *what happened?*
- **Audio Events:** Detecting laughter, shouting, silence via FFmpeg filters.
- **Chat Analysis:** Processing the stream chat to find high-activity spikes and interactions.

## Strict Architectural Separation from Stage M7
- **M2 (Upstream):** Answers *what happened* in the stream. It outputs lightweight `TimelineEvent(event_type="face_reaction")` feeding Stage M3 candidate generation. M2 has **zero** dependency on Stage M7.
- **M7 (Downstream):** Answers *where should the viewer look, what is visually important, and how should frames be cropped/zoomed*. M7 executes *after* M5 selection on the retained beats, providing detailed face tracking, saliency maps, and `FocusTarget` entities.

