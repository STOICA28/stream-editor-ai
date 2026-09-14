---
id: ARCH-SEC-001
title: Security
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - security
---

# Security

- **AI Output is Untrusted:** Treat all LLM output as potentially hostile.
- **No Arbitrary Execution:** Never use `shell=True` or `eval()`. Pass explicit arg arrays to FFmpeg.
- **Path Sanitization:** Prevent directory traversal attacks on uploads.
- **Secrets:** Use `.env` variables only.
