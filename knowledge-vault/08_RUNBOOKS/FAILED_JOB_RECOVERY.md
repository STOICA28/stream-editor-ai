---
id: RUN-RECOVERY-001
title: Failed Job Recovery
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - runbook
---

# Failed Job Recovery

1. Check logs in the Observability dashboard or `docker logs worker`.
2. Identify the failed stage (e.g., `DETECT_SCENES`).
3. Fix the underlying issue (e.g., FFmpeg crash, API quota limit).
4. Trigger a job resume. The system is idempotent and will resume from the failed stage using cached inputs.
