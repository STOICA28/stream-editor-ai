---
id: SCHEMA-CANDIDATE-001
title: CandidateSegment Schema
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - schema
---

# CandidateSegment Schema

**Description:** A potential clip.

**Rule:** Never reduce a candidate to a single opaque score. Use multidimensional scoring.

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "start_time_ms": 10000,
  "end_time_ms": 45000,
  "scores": {
    "humor": 0.8,
    "importance": 0.9,
    "reaction": 0.5,
    "visual_interest": 0.3,
    "chat_relevance": 0.7,
    "story_value": 0.9,
    "repetition_penalty": 0.0
  },
  "justification": "Sets up the main goal for the stream."
}
```
