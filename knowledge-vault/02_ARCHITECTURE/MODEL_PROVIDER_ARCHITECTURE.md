---
id: ARCH-MODEL-001
title: Model Provider Architecture
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - models
---

# Model Provider Architecture

- **Interface:** `ModelProvider` class defines the standard API.
- **Adapters:** Implementations for Gemini, Anthropic, and a mandatory Mock provider.
- **Tiering:** Use cheap/fast models for bulk analysis, capable models for narrative/editorial decisions.
- **Hardcoding:** Model names are injected via configuration, never hardcoded in business logic.
