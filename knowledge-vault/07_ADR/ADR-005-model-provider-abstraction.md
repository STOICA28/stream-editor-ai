---
id: ADR-005
title: Model Provider Abstraction
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - adr
---

# ADR-005: Model Provider Abstraction

**Context:** We need to use Gemini for long context, Anthropic for reasoning, and avoid vendor lock-in.
**Decision:** All model access must go through a `ModelProvider` interface.
**Consequences:** Requires writing adapters. A `MockProvider` is mandatory for testing.
