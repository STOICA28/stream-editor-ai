---
id: ADR-007
title: No LangChain for MVP
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - adr
---

# ADR-007: No LangChain for MVP

**Context:** LangChain/LangGraph often introduce hidden magic and difficult-to-debug abstraction layers.
**Decision:** Direct model API calls with custom orchestration.
**Consequences:** More boilerplate code to write, but full control over prompts, validation, and error handling.
