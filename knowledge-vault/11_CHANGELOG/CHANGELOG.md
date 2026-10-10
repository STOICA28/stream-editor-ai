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

## [2026-10-10] (EXP-002 Promotion Blockers Resolved & Blinded Media Packaging)
### Changed
- **Stage M3 Upstream Cache Dependency Direction:**
  - Removed downstream Stage M7 `VisualAnalysisRun` from M3 signature calculation in `_compute_m2_signature`.
  - M3 signatures now strictly depend on upstream M1/M2 entities (`MediaAsset`, `TranscriptRun`, `TimelineEvents`, `Scene`, `AudioEvent`).
- **Boundary Validation & Anti-Duplication Enforcement:**
  - Enhanced `EditPlanValidator` to validate clip intervals against source bounds (`source_end <= original_duration`) and reject overlapping sequential source intervals (`curr.source_start < prev.source_end - 0.001`, timeline duplication).
  - Updated `TimelineCompiler` to enforce `source_duration` constraints and reject intervals exceeding source duration.
- **Windows Atomic Promotion:**
  - Updated `RenderingEngine` to use `os.replace` instead of `Path.rename` for cross-platform atomic promotion of `.partial` render files.

### Added
- **Audiovisual A/B Media Rendering & Verification:**
  - Rendered 8 genuine playable `.mp4` comparison videos for 4 audited evaluation cases using `RenderingEngine` and validated with `MediaValidator`.
  - Audited and corrected source-relative temporal coordinates for `real-eval-001` and `real-eval-002`.
- **Decoupled Blinded Review Packaging:**
  - Created `exp002_real_ab_reviewer_package.json` with randomized labels (A/B), neutral IDs, and zero fabricated/simulated votes across 5 editorial dimensions.
  - Created `exp002_real_ab_evaluation_key.json` containing ground truth mappings, run signatures, and explicit disclosure of shared master VOD provenance between Recordings 1 and 3.
- **PostgreSQL Integration Suite:**
  - Added `tests/integration/test_exp_002_postgres.py` validating schema creation, idempotency, and rollback handling.
- **Governance Review Documentation:**
  - Updated `EXP-002_PROMOTION_REVIEW.md`, `PROP-M3-SETUP-PAYOFF-CLUSTERING.md`, and `PROJECT_STATUS.md` confirming status as `EXP-002 PROMOTION CONDITIONAL — HUMAN EDITORIAL REVIEW PENDING`.


## [2026-10-09] (EXP-002 Verification)
### Added
- **EXP-002 Setup/Payoff Clustering & Context Windowing (M13 Evaluation):**
  - Implemented multi-signal relational clustering in Stage M3 (`CandidateRelationClassifier`, `CandidateRelationEvidence`, `CandidateClusteringExperimentConfig`).
  - Added support for explicit narrative relations (`SETUP_TO_EVENT`, `EVENT_TO_REACTION`, `SETUP_TO_PAYOFF`, `CHAT_TO_REACTION`, `REACTION_CONTINUATION`, `SAME_BEAT`).
  - Integrated natural pause boundary snapping with strict hard scene cut barriers.
  - Frozen configuration signature: `32d3ee01c6727abfa23781e2cfe2bc5cf570e40c7420af096c1ab33bac0edf70`.
  - Evaluated on untouched holdout cases (`case-test-005` and `case-test-real-004`):
    - Macro Recall: 0.8723 -> 1.0000 (+12.77% observed holdout delta)
    - Macro Precision: 1.0000 -> 1.0000 (0.0% precision loss)
    - Macro F1: 0.9318 -> 1.0000 (+0.0682)
    - Micro Recall: 0.8830 -> 1.0000 (+11.70%)
    - Real Case (`case-test-real-004`) F1: 0.9404 -> 1.0000 (+0.0596)
    - Pre-context error median: +1.375s -> +0.000s
    - Fragmentation rate: 100% -> 0% (eliminated)
    - 0.0s dead air, 0.0s overselection, 0 false merges.
  - Governance Verdict: **EXP-002 VERIFIED — READY FOR PROMOTION REVIEW**.



## [2026-10-05] (EXP-001R.1 Verification)
### Added
- **EXP-001R.1 Real Detector & Discriminative Holdout Proof:**
  - Implemented and verified production `OpenCVVisualObservationProvider` on real authorized media (`real_clutch_reaction.mp4`) with zero mocks in the execution pipeline.
  - Verified strict M2/M7 architectural isolation (`VisualAnalysisRun count before M3 = 0`).
  - Added untouched discriminative holdout cases `case-test-004` (synthetic) and `case-test-real-003` (real 5h VOD slice).
  - Evaluated Baseline vs EXP-001R:
    - Macro Recall: 0.6667 -> 1.0000 (+33.33%)
    - Macro F1: 0.8000 -> 1.0000 (+20.00%)
    - Real Case (`case-test-real-003`) F1: 0.8000 -> 1.0000 (+20.00%)
    - Effect Agreement Rate: 0.0% (0/1) -> 100.0% (1/1)
    - 0.0s dead air, 0.0s overselection, 0 false reactions.
  - Preserved immutable config hash `e619767e08a73d55c41d306f83652a0785ba4435dd770719e3f7e2e7454c3d2e`.
  - Governance Verdict: **EXP-001R VERIFIED — READY FOR PROMOTION REVIEW**.

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
