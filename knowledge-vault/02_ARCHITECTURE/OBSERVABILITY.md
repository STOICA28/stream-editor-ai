---
id: ARCH-OBS-001
title: Observability
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - observability
---

# Observability

- **Structured Logging:** JSON logs containing `project_id`, `job_id`, `stage`, `elapsed`, `error`.
- **Model Usage:** Track token usage and costs per project/stage.
- **Job Progress:** Exposed via an API for frontend progress bars.
