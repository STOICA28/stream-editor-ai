---
id: ARCH-JOB-001
title: Job System
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - jobs
---

# Job System

The processing pipeline is a DAG:
`INGEST -> PROBE_MEDIA -> CREATE_ANALYSIS_PROXY -> EXTRACT_AUDIO -> TRANSCRIBE -> DETECT_SCENES -> DETECT_VISUAL_EVENTS -> ANALYZE_AUDIO_EVENTS -> IMPORT_OR_ANALYZE_CHAT -> GENERATE_CANDIDATES -> SCORE_CANDIDATES -> BUILD_STORY_GRAPH -> GENERATE_EDIT_PLAN -> RENDER_PREVIEW -> HUMAN_REVIEW -> RENDER_FINAL`

Each step stores state in the DB, including input/output hashes, algorithm version, timestamps, and errors.
