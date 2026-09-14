---
id: SCHEMA-STORY-001
title: StoryGraph Schema
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - schema
---

# StoryGraph Schema

**Description:** Maps narrative dependencies.

- **NarrativeNode:** Represents a segment.
  - Types: setup, event, character_intro, joke, callback, payoff, explanation, decision, consequence.
- **NarrativeEdge:** Represents the relationship between nodes.
  - Types: depends_on, callback_to, explains, caused_by, follows, contrasts_with.

```json
{
  "nodes": [{"id": "node1", "type": "setup", "segment_id": "seg1"}],
  "edges": [{"from": "node2", "to": "node1", "type": "depends_on"}]
}
```
