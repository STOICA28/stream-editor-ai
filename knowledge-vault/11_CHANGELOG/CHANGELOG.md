---
id: CHANGELOG-001
title: Changelog
status: canonical
version: 1.1
last_reviewed: 2026-09-14
tags:
  - changelog
---

# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- Planning for M2 (Transcript and Scene Analysis)

## [2026-09-14] (M1 Completion)
### Added
- **M1 Media Foundation Completed.**
- `StorageProvider` supports large file ingestion via `copy_in()` bypassing RAM buffering.
- Type-safe Python wrappers for FFprobe and FFmpeg without using `shell=True`.
- Atomic writes for generated media using `.partial` extensions to guarantee idempotency.
- Fast deterministic media fingerprinting using size, mtime, and partial sha256.
- Database CRUD endpoints in `apps/api/src/stream_editor/api/routers/projects.py`.
- Eager-compatible Celery DAG traversing `INGEST -> PROBE -> CREATE_PROXY -> EXTRACT_AUDIO`.
- End-to-End CLI test tool (`scripts/process_media.py`) utilizing `synthetic_test.mp4`.

## [2026-09-14] (M0.1 & M0.2)
### Governance & Type Safety (M0.1 & M0.2)
- **M0.2 Type Safety Gate Passed:** Restored strict mypy checking. Typed Celery tasks, FastAPI routers, SQLAlchemy 2.0 DeclarativeBase, and Pydantic models.
- Configured pytest to properly suppress only targeted warnings.
- Performed M0.1 Governance Audit.
- Reverted unvalidated editorial assumptions from KEEP_VS_CUT.md and PACING.md to a new research document.
- Created PROJECT_GOVERNANCE.md establishing the knowledge hierarchy and promotion rules.
- Added Anti-Drift Rule to AGENTS.md.
- Documented missing ADRs (ADR-008 for uv workspaces and namespace packages, ADR-009 for PostgreSQL and Celery).

### Added
- **M0 Foundation Completed.**
- Complete Obsidian knowledge vault (`knowledge-vault/`) acting as the canonical source of truth.
- Core schema contracts in `packages/contracts/` using Pydantic v2 (TimelineEvent, EditPlan, CandidateSegment, etc.).
- Abstractions for `StorageProvider` and `ModelProvider`.
- FastAPI backend scaffold (`apps/api`).
- Celery worker scaffold with pipeline DAG stages (`apps/worker`).
- Next.js frontend scaffold (`apps/web`).
- Docker Compose and `Makefile` for infrastructure setup.
- `AGENTS.md` and agent skills to enforce AI-decides-deterministic-executes principles.
- `check_vault.py` consistency checker running cleanly.

### Security
- Fixed a vulnerability in `probe_media` that previously used `eval()` on ffprobe string outputs.

### Changed
- Configured `uv` workspace and pyproject.toml files to correctly resolve namespace packages (`stream_editor.*`) without `__init__.py` conflicts.
- `pytest` configuration updated to ignore `StarletteDeprecationWarning` regarding `httpx2` to ensure a green test suite.
