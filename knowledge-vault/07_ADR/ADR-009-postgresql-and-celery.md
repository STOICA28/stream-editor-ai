---
id: ADR-009
title: PostgreSQL and Celery Task Queue
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - adr
  - database
  - async
---

# ADR 009: PostgreSQL and Celery Task Queue

## Context
StreamEditor AI processes massive video files and invokes slow AI models. The pipeline is structured as a DAG of long-running, resumable jobs (e.g., INGEST, PROBE, TRANSCRIBE, GENERATE_CANDIDATES). The system needs a database for state management and an async task queue for execution.

## Decision
- **Database:** PostgreSQL (via SQLAlchemy / asyncpg).
- **Task Queue:** Celery with Redis as the broker.

## Rationale
- **PostgreSQL:** Relational data strongly suits the deeply linked structure of `Project` -> `Job` -> `TimelineEvent` -> `CandidateSegment` -> `EditPlan`. We require ACID compliance to ensure job state consistency.
- **Celery + Redis:** The DAG of media processing jobs can be represented well using Celery chains and chords. Redis provides a fast, reliable broker that is easy to self-host in Docker Compose.

## Consequences
- Requires a running PostgreSQL instance and Redis instance for local development.
- The worker application must be carefully scaled to avoid exhausting PostgreSQL connection pools.
- Long-running ffmpeg or transcription tasks must not block the main Celery worker threads indefinitely without heartbeat mechanisms.
