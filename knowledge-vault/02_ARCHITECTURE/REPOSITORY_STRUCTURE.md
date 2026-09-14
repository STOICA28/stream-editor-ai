---
id: ARCH-REPO-001
title: Repository Structure
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - repo
---

# Repository Structure

- `apps/api`: FastAPI backend
- `apps/worker`: Celery or arq worker for background jobs
- `apps/web`: Next.js frontend
- `packages/contracts`: Pydantic schemas (EditPlan, etc.)
- `packages/media`: FFprobe/FFmpeg wrappers
- `packages/analysis`: WhisperX, Scene detection logic
- `packages/editorial`: Candidate scoring, Story Graph
- `packages/research`: EditDNA extraction
- `packages/models`: ModelProvider adapters
- `packages/rendering`: FFmpeg and Remotion execution
- `packages/storage`: StorageProvider (Local, S3)
- `packages/vault`: Obsidian vault interface
- `knowledge-vault`: This folder
