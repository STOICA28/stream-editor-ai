---
id: SCHEMA-STYLE-001
title: StyleProfile Schema
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - schema
---

# StyleProfile Schema

**Description:** The calculated profile for a specific editor or channel.

```json
{
  "channel_id": "channel1",
  "editor_id": "editor1",
  "metrics": {
    "retention_rate": 0.15,
    "avg_clip_duration_ms": 18000,
    "cut_density": 0.8,
    "zoom_frequency": 0.05
  },
  "evidence_count": 5,
  "confidence": 0.85
}
```
