---
id: SCHEMA-TIMELINE-001
title: TimelineEvent Schema
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - schema
---

# TimelineEvent Schema

**Description:** Represents a discrete occurrence in the VOD. Events can and will overlap.

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "source_media_id": "uuid",
  "type": "speech | silence | laughter | shout | scene_change | face_reaction | chat_message | chat_read | visual_event | game_event | music | emotion | topic_change | callback | reference",
  "start_time_ms": 1000,
  "end_time_ms": 5000,
  "confidence": 0.95,
  "structured_data": {},
  "producer": "whisperx",
  "producer_version": "1.0"
}
```
