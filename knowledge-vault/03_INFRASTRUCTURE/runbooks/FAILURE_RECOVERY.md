---
id: RUNBOOK-RECOVERY-001
status: canonical
title: Failure Recovery & Job Management
---

# Failure Recovery Runbook

## Overview
StreamEditor jobs use a Lease/Heartbeat model (JobLeaseMixin). 
If a worker crashes, its jobs become stale but stay marked as RUNNING in the DB until the lease expires.

## Recovering Stale Jobs
Celery cks_late=True combined with standard idempotency allows automatic retry.
However, if jobs are stuck in the database without being re-queued:
\\\ash
# Run the lease sweeper to reset stale jobs to QUEUED
uv run python scripts/sweep_stale_jobs.py
\\\

## Disk Exhaustion
If the DATA_DIR fills up, workers will raise IOError due to _check_disk_space.
1. Expand disk or clean up old projects.
2. The failing jobs will retry via Celery bounded retries (up to 3 times).
3. .partial files are automatically cleaned up if a process crashes mid-write.

## Antigravity (Gemini) Outages
The system limits concurrency via ANTIGRAVITY_MAX_CONCURRENCY. 
If Antigravity returns errors, it throws AIProviderExecutionError, triggering a task retry.
