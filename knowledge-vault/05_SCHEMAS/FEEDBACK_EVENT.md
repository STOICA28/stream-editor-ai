---
id: SCHEMA-FEEDBACK-001
title: FeedbackEvent Schema
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - schema
---

# FeedbackEvent Schema

**Description:** Records human changes to the EditPlan.

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "original_proposal": {},
  "human_modification": {},
  "surrounding_context": {},
  "reason": "Trimmed dead air at start",
  "editorial_style_version": "1.0"
}
```
