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

## [2026-10-12] (Transcript-First Semantic Editing & Context-Aware Cut Planning — E2E-PILOT)
### Changed
- **Invalidated E2E-002 Editorial Claim:** Formally recorded that `E2E-LONGFORM-REFERENCE-002` failed human editorial acceptance. Human reviewer identified lengthy unimportant stream administration (mic/OBS/volume testing, YouTube upload talk), truncated gameplay onboarding, unexplained 104-minute game-state jumps, and lack of context.
- **Root Cause Forensic Audit:** Demonstrated that E2E-002 executed zero LLM inference on the raw transcript during planning; candidate moments were hardcoded Python timestamps (`[20.0s, 150.0s]`) with pre-baked scores. Heuristics blindly protected administrative chatter while cutting the actual video introduction at `0.0s`.
### Added
- **Semantic Cut Decision Contracts (`packages/contracts/src/stream_editor/contracts/editorial.py`):**
  - Added `SemanticDecisionType` (`KEEP`, `REMOVE`, `CONDENSE`, `KEEP_AS_CONTEXT`, `KEEP_AS_PAYOFF`, `REQUIRES_PREVIOUS_CONTEXT`, `UNCERTAIN`).
  - Added `SemanticCutDecision` and `SemanticRegionCutPlan`.
- **Authentic WhisperX Transcription:**
  - Extracted and transcribed authentic Spanish audio from `source.wav` across 5 diagnostic slices covering Regions A, B, and C using `faster-whisper`.
- **Game-State Continuity Engine (GSCE) & Diagnostic Reports:**
  - `SEMANTIC_EDITORIAL_PIPELINE_AUDIT.md`: Forensic audit of E2E-002 heuristic bypass and stream admin retention.
  - `TRANSCRIPT_CUT_DECISION_PILOT.md`: Comprehensive textual cut plans for Regions A, B, and C with evidence tables and human editor comparison.
  - `NARRATIVE_TRANSITION_FAILURE_ANALYSIS.md`: Deep analysis of the 104-minute jump ($5525\text{s} \to 11810\text{s}$), state disparity matrix, and transition bridging rules.
- **Pilot Renders & Validation:**
  - Rendered neutral-cut video demonstrations for Regions A, B, and C with 10ms audio edge crossfades, validated by `MediaValidator`.

## [2026-10-12] (Long-Form Narrative Reconstruction & Editorial Cut Intelligence — E2E-002)
### Changed
- **Invalidated E2E-001 Editorial Claim:** Formally recorded that `E2E-LONGFORM-REFERENCE-001` failed human editorial acceptance due to truncated greeting onset, omitted game onboarding, and extreme 35-minute transition jump fragmentation. Disclosed that the demonstration utilized a hardcoded candidate list (`candidate_clips = [...]`).
### Added
- **Hierarchical Narrative Contracts (`packages/contracts/src/stream_editor/contracts/editorial.py`):**
  - Added `NarrativeLevel` (`SESSION`, `EPISODE`, `MOMENT`).
  - Added semantic edge types to `EdgeRelationType`: `requires_context`, `introduces_objective`, `establishes_game_state`, `changes_game_state`, `resolves_objective`, `explains_reaction`, and `safe_to_skip`.
  - Added `NarrativeEpisodeContract`, `GameStateSnapshot`, `NarrativeDependency`, and `EnforcementAction`.
- **Narrative Dependency Resolver (`packages/editorial/src/stream_editor/editorial/planning/resolver.py`):**
  - Implemented `NarrativeDependencyResolver.resolve_dependencies()` to traverse narrative edges, automatically pull prerequisite setups when payoffs/action beats are selected, propagate essential priority, and drop unsupported beats.
  - Implemented `NarrativeDependencyResolver.link_episode_continuity()` to bridge tight intra-episode sub-beats ($\le 8.0\text{s}$), eliminating micro-jumpcuts within the same scene.
- **Planner Integration:**
  - Integrated `NarrativeAnchorDetector` and `NarrativeDependencyResolver` into `MockGlobalEditorialPlanner` and `AntigravityGlobalEditorialPlanner`.
- **E2E-LONGFORM-REFERENCE-002 Benchmark (`scripts/run_e2e_longform_reference_002_benchmark.py`):**
  - Built autonomous pipeline generator on 5.19h master livestream (`source.mp4`).
  - Achieved 100% payoff setup retention rate (4/4 setups preserved).
  - Preserved exact greeting onset at 20.0s (unclipped speech) and game premise onboarding ([56.0s – 150.0s]).
  - Bridged the Chapter 16 climax into an unbroken 130.0s raid arc (Alarm + Combat + Victory).
  - Rendered a complete 750.0s (12.50-minute) demonstration MP4 with neutral cuts and verified playability via `MediaValidator`.
- **Forensic & Architectural Documentation:**
  - `E2E_LONGFORM_002_ROOT_CAUSE_REPORT.md` (Forensic transition jump audit and invalidation disclosure).
  - `HUMAN_REFERENCE_CUT_DECISION_AUDIT.md` (Ground truth human edit category allocation and 2,438s reconciliation).
  - `NARRATIVE_CONTINUITY_DESIGN.md` (Hierarchical 3-level narrative model and dependency architecture).
  - `E2E_LONGFORM_REFERENCE_002_REPORT.md` (Benchmark results and comparison matrix).

## [2026-10-12] (Long-Form Editorial Intelligence & Human Reference Alignment)
### Added
- **Long-Form Selection Root-Cause Audit (`LONGFORM_EDITING_ROOT_CAUSE_AUDIT.md`):**
  - Traced the forensic root cause of the previous 43.5s output (`streameditor_e2e_real_edit.mp4`), establishing that it originated from a manual developer demonstration script using a 10-minute slice (`source_short.mp4`), rather than the full 5.19-hour stream (`source.mp4`).
  - Documented that M5 duration pruning prioritized dropping `ClipPriority.context_only` first, which stripped opening greetings and setups.
- **Human Reference Alignment Report (`HUMAN_REFERENCE_ALIGNMENT_REPORT.md`):**
  - Analyzed the master 5.19-hour stream (`source.mp4`, 18675.2s) and 40.6-minute human reference (`edited.mp4`, 2438.4s) using M10 EditDNA.
  - Constructed the **Human Edit Decision Map** (`cache/human_edit_decision_map.json`), revealing an 86.7% retention density in Chapter 0 (greeting & game onboarding), 70.48% conversational content, 20.45% reaction peaks, and 49.26% removed repetition.
- **Long-Form Editorial Improvement Plan (`LONGFORM_EDITORIAL_IMPROVEMENT_PLAN.md`):**
  - Introduced explicit editing presets: `SHORT_HIGHLIGHT` (60–180s), `LONG_FORM_SUMMARY` (600–1200s), and `FULL_EDITED_SESSION` (1800–2700s).
  - Designed `NarrativeAnchorDetector` to protect opening greeting and game launch anchors from duration pruning.
- **Narrative Anchor Protection Architecture:**
  - Implemented `packages/editorial/src/stream_editor/editorial/planning/anchors.py` tagging `STREAM_GREETING`, `GAME_START`, and `OUTRO`.
  - Updated `packages/contracts/src/stream_editor/contracts/edit_plan.py` with `EditingGoal`, `preserve_narrative_anchors`, and anchor fields.
  - Updated `packages/editorial/src/stream_editor/editorial/planning/optimizer.py` to give narrative anchors strict immunity against duration pruning.
- **E2E-LONGFORM-REFERENCE-001 Benchmark & Demonstration (`E2E_LONGFORM_REFERENCE_001_REPORT.md`):**
  - Executed benchmark harness (`scripts/run_e2e_longform_reference_benchmark.py`).
  - Rendered a complete 460.0-second (7.67-minute) demonstration MP4 (`final.mp4`, 153.9 MB) across the 5.19-hour stream with neutral cuts (zero VFX masking).
  - Verified playability and PTS alignment via `MediaValidator` (verdict: `Valid`).
  - Achieved 73.91% direct intersection with the human reference edit while preserving opening social greeting and game start.
### Added
- **Cryptographic & Visual Provenance Audit (`REAL_MEDIA_PROVENANCE_AUDIT.md`):**
  - Audited all media assets across the repository with SHA-256 hashes, exact container and stream durations, codecs, visual frame descriptions, and provenance history.
  - Formally identified and invalidated synthetic oracle diagnostic fixture `source_0.mp4` (red ball & green box `"FACE"` on black canvas generated in M10.2). Invalidated all historical editorial claims derived from it.
  - Confirmed authentic master footage: `source_short.mp4` (SHA-256: `e92c2134...`), uncut 10-minute continuous 1080p60 livestream broadcast of the streamer playing *"Otro Día en el Paraíso"*.
- **Genuine M3 Evaluation Suite (`eval-real-001` through `eval-real-004`):**
  - Generated 4 genuine cases from `source_short.mp4` with unedited source context videos ($30\text{s}–45\text{s}$) alongside blinded randomized A/B comparison clips.
  - Added explicit subsecond delta explanations and targeted narrative questions for each case.
- **Complete End-to-End Pipeline Demonstration (`streameditor_e2e_real_edit.mp4`):**
  - Executed full M1-M9 pipeline on authentic livestream footage to render a $43.79\text{s}$ multi-clip editorial video comprising 4 narrative beats (Intro $\to$ Action $\to$ Reaction $\to$ Outro) with Stage M8 facecam reaction zoom.
- **Interactive Local HTML Review Application (`exp002_ab_review_app.html`):**
  - Built standalone interactive web app with embedded HTML5 video players for context and A/B variants, preference buttons, comment fields, and single-click JSON feedback export (zero manual JSON parsing for human reviewers).
- **Decoupled Blinded Package & Evaluation Key:**
  - Updated `exp002_real_ab_reviewer_package.json` and `exp002_real_ab_evaluation_key.json` with new genuine media fingerprints, video paths, and randomized seed mappings.

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
