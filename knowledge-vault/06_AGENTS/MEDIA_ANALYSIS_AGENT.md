---
id: AGENT-MEDIA-001
title: Media Analysis Agent
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - agents
  - media
---

# Media Analysis Agent

**Role:** Processes raw VOD data into structured events.
**Responsibilities:**
- Run WhisperX transcription.
- Execute scene detection algorithms.
- Perform visual and audio analysis via models.
- Output deterministic `TimelineEvent` objects.
