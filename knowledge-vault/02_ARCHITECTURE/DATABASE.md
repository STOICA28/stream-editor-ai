---
id: ARCH-DB-001
title: Database
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - database
---

# Database

PostgreSQL accessed via SQLAlchemy.

**Core Entities:**
Project, MediaAsset, ProcessingJob, JobStep, TranscriptSegment, Scene, TimelineEvent, CandidateSegment, CandidateScore, NarrativeNode, NarrativeEdge, EditPlan, EditPlanVersion, EditClip, FeedbackEvent, ReferenceProject, ReferenceVideo, ResearchFinding, StylePattern.

*Note: No binary media blobs are stored in the DB.*
