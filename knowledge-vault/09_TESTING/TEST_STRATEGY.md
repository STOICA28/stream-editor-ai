---
id: TEST-STRATEGY-001
title: Test Strategy
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - testing
---

# Test Strategy

- **Unit Tests:** Core logic, Pydantic schema validation, time range overlaps, effect constraints, candidate merging, story dependencies.
- **Integration Tests:** Database CRUD, Celery queues, Media probing, Analysis proxy generation, rendering pipeline.
- **Golden Tests:** Comparing AI outputs against known-good JSON schemas.
- **E2E Tests:** Full pipeline run using synthetic test media scripts.
- **Mandatory:** `MockProvider` must be used in CI to avoid real API costs.
