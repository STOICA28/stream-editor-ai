---
id: AGENT-EDITOR-001
title: Editor Agent
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - agents
  - editor
---

# Editor Agent

**Role:** Makes the editorial decisions.
**Responsibilities:**
- Ingest `CandidateSegment` and `StoryGraph` data.
- Consult the `03_EDITORIAL_BIBLE` for rules.
- Produce a validated `EditPlan`.
**Constraints:**
- Must strictly use the `EffectAPI`.
- Only relies on canonical rules.
