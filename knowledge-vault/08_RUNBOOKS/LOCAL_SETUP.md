---
id: RUN-SETUP-001
title: Local Setup
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - runbook
  - setup
---

# Local Setup

**Prerequisites:**
- Docker & docker-compose
- Python 3.12
- Node.js 20+
- FFmpeg (added to PATH)

**Steps:**
1. Clone the repository.
2. `cp .env.example .env` and fill in API keys.
3. Run `docker-compose up -d` to start Postgres and Redis.
4. Run Python migrations: `alembic upgrade head`.
5. Start API: `cd apps/api && uvicorn main:app`.
6. Start Frontend: `cd apps/web && npm run dev`.
