---
id: SCHEMA-FEEDBACK-001
title: FeedbackEvent Schema
status: canonical
version: 1.1
last_reviewed: 2026-09-15
tags:
  - schema
---

# FeedbackEvent Schema

## Definition
A `FeedbackEvent` represents a single atomic, immutable action performed by a human reviewer on an `EditPlan` or `EditClip`. It serves as the primary data structure for capturing human editorial judgment so that it can be later analyzed by the `EditDNA` research pipeline.

## Principles
1. **Immutability:** Events are append-only. They are never modified or deleted.
2. **Context Preservation:** The event must capture exactly what was changed (previous value, new value).
3. **Traceability:** It must link to the original `CandidateSegment` or `NarrativeNode` to allow upstream AI adjustment.

## Schema
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "source_asset_id": "uuid",
  "edit_plan_id": "uuid",
  "edit_clip_id": "uuid | null",
  "feedback_type": "string", // accept, reject, modify_start, modify_end, lock
  "previous_value": {},
  "new_value": {},
  "reason_category": "string | null",
  "reason_text": "string | null",
  "candidate_id": "uuid | null",
  "story_node_ids": ["uuid"],
  "created_at": "timestamp"
}
```

## Lifecycle
1. Generated during `POST /clips/{id}/feedback` in `planning.py`.
2. Stored in `feedback_events` table.
3. Queried by `review.py` for stats and analytics.
4. Used by `EditDNA` to build training/prompt data.
