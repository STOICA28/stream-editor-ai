---
id: RUNBOOK-OPS-001
status: canonical
title: Standard Operations & Observability
---

# Operations Runbook

## Health & Readiness
The system exposes two standard endpoints:
- GET /api/v1/health: Basic API liveness.
- GET /api/v1/health/ready: Deep check (DB connection verification).
- GET /api/v1/health/ai: Antigravity/Gemini model readiness check.

## Structured Logging
All FastAPI logs are emitted in JSON format via structlog.
A correlation_id (X-Request-ID) is bound to all logs within the context of a request.
Querying logs:
\\\ash
cat stream_editor.log | jq 'select(.request_id == "uuid-here")'
\\\

## Configuration Validation
Configuration is validated eagerly at startup via Pydantic BaseSettings (pps/api/src/stream_editor/api/config.py).
If critical env vars are missing, the process exits with Code 1 immediately.
