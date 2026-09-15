# M10: EditDNA Research Engine

This milestone builds the second major brain of StreamEditor AI: **EditDNA**. It enables the system to study real human-edited reference videos, align them against the original VODs, observe editorial decisions (retention, cuts, visual effects, speed), and aggregate these observations into descriptive `StyleProfile`s and `ResearchFinding`s.

## User Review Required
> [!IMPORTANT]
> - This plan introduces a separate `packages/research` module to keep research distinct from production logic.
> - **Input Policy**: Reference media must be user-supplied or otherwise authorized through local `MediaAsset` imports. We will **NOT** implement arbitrary YouTube downloading.
> - **Gemini Escapement & Failure Isolation**: Gemini Flash/Pro are used via a `ReferenceUnderstandingProvider`. Standard CI will rely on a `MockReferenceProvider` and not require Gemini credentials. If Gemini is unavailable, deterministic alignment and locally measurable observations will remain intact.
> - **Long-form Scalability**: Designed for 8h source vs 2–4h edit. Alignment relies on indexed, windowed, chunked processing, actively avoiding O(N²) naive frame comparisons.

## Proposed Changes

---

### Database Models
We will create `apps/api/src/stream_editor/api/models/research.py` and run an Alembic migration.

#### [NEW] apps/api/src/stream_editor/api/models/research.py
Defines SQLAlchemy models:
- `ReferenceProject`: Container for research.
- `ReferenceVideoPair`: Maps `source_asset_id` to `edited_asset_id`.
- `ReferenceAlignmentRun`: Stores configuration, versions, signature, and metrics.
- `AlignmentBlock`: Mappings of source to edited time intervals. Includes rich evidence (`audio_confidence`, `transcript_confidence`, `visual_confidence`, `combined_confidence`, `speed_ratio`, `method`).
- `ObservedEditorialDecision`: Records of retained, omitted, or modified clips.
- `ObservedEffect`: Detected visual/audio transforms (`zoom_face`, `zoom_chat`, `grayscale`, `freeze_frame`, `slow_motion`, `speed_up`, audio changes). Supports manual corrections (effect type, time boundaries, target, false positive, missed effect).
- `StyleProfile`: Aggregated metrics for a project.
- `ResearchFinding`: Governance record. Distinguishes explicitly between `observation`, `inference`, `hypothesis`, and `approved`. Supports rejected / needs-more-data workflow.

---

### Contracts
We will add Pydantic contracts for research structures.

#### [NEW] packages/contracts/src/stream_editor/contracts/research.py
Pydantic equivalents for the DB models to ensure type safety. Maintains strict compatibility with the M8 effect ontology.

---

### Research Engine (Core Algorithms)
We will introduce a new package module.

#### [NEW] packages/research/src/stream_editor/research/alignment/audio.py
`AudioAligner`: A first-class alignment signal using spectral features, chroma, or hashes on candidate windows.

#### [NEW] packages/research/src/stream_editor/research/alignment/transcript.py
`TranscriptAligner`: Performs semantic/phrase sequence matching between the source and edited transcript.

#### [NEW] packages/research/src/stream_editor/research/alignment/visual.py
`VisualAligner`: Compares perceptual hashes / features within boundaries.

#### [NEW] packages/research/src/stream_editor/research/alignment/builder.py
Coordinates multi-signal coarse and fine alignment. Explicitly supports unmatched/unmapped source and edited regions (for intros, title cards, memes, external inserts).
Supports manual alignment correction while preserving the original machine inference.
Defines **deterministic alignment cache signatures**: `hash(source_fingerprint, edited_fingerprint, analysis_versions, alignment_config, algorithm_versions)`.

#### [NEW] packages/research/src/stream_editor/research/observation/cut_detector.py
Derives `ObservedEditorialDecision` and cut boundaries from `AlignmentBlock`s.

#### [NEW] packages/research/src/stream_editor/research/observation/effect_detector.py
Deduces speed changes and visual effects from the alignment mapping and frame differences. **Effect detection always compares aligned edited content relative to aligned source**, avoiding false positives from natural source changes.
Supports detecting effect sequences, particularly `screen focus -> face focus -> normal`.
Defines **effect-detection cache signatures**: `hash(alignment_run, analyzed_window, detector_versions, gemini_provider/model, prompt_version, effect_ontology_version)`.

#### [NEW] packages/research/src/stream_editor/research/providers/provider.py
Defines `ReferenceUnderstandingProvider` with `MockReferenceProvider` and `GeminiReferenceProvider`.

#### [NEW] packages/research/src/stream_editor/research/style_profile.py
`StyleProfileBuilder`: Aggregates the observations incrementally. Adding Pair #4 analyzes Pair #4 and recomputes aggregation without unnecessarily reprocessing Pairs #1–#3.
Metrics preserve sample counts, distributions, evidence/confidence, cross-video consistency, and outliers. Conditional style patterns retain their numerator/denominator evidence.

---

### API Endpoints
We will expose these capabilities via FastAPI.

#### [NEW] apps/api/src/stream_editor/api/routers/research.py
REST endpoints:
- `POST /reference-projects`, `GET /reference-projects`
- `POST /reference-projects/{id}/pairs`
- `POST /reference-pairs/{id}/analyze`
- `GET /reference-pairs/{id}/alignment`
- `GET /reference-pairs/{id}/decisions`
- `GET /reference-pairs/{id}/effects`
- `GET /reference-projects/{id}/style-profile`
- `GET /reference-projects/{id}/findings`
- `POST /research-findings/{id}/approve`, `POST /research-findings/{id}/reject`
- Exposes telemetry: local windows processed, Flash/Pro requests, tokens, latency, cache hits, ambiguous regions.
- Diagnostic endpoints: mapped edited percentage, retained source duration, unmatched edited duration, block confidence distribution, low-confidence mappings, continuity errors.

---

### Frontend UI
We will build the research interface in the web app.

#### [NEW] apps/web/src/app/research/page.tsx
List of Reference Projects.

#### [NEW] apps/web/src/app/research/projects/[id]/page.tsx
Dashboard for a single Reference Project.

#### [NEW] apps/web/src/app/research/pairs/[id]/page.tsx
Detailed view for a specific ReferenceVideoPair with the **Side-By-Side Player** component for synchronized source/edit playback, alignment mapping, and observed effects.

---

### CLI
#### [NEW] scripts/analyze_reference_pair.py
A CLI utility to trigger and debug the entire M10 pipeline. Generates per-pair research artifacts conceptually equivalent to `alignment.json`, `retained-regions.json`, `cuts.json`, `effects.json`, and `editorial-report.md`.

---

### Vault Documentation
#### [MODIFY] knowledge-vault/00_HOME/PROJECT_STATUS.md
Update milestone progress to M10.
#### [NEW] knowledge-vault/04_RESEARCH/EDITDNA.md
Detailed breakdown of EditDNA architecture, Style Profiles, and the strict distinction between observations and canonical rules.

## Verification Plan
1. **Synthetic Ground-Truth E2E**: Programmatically generate an edited derivative video from a synthetic original video containing known cuts, retained regions, `zoom_region`, `zoom_face`, `grayscale`, `2x speed`, `0.5x speed`, `freeze frame`, and `screen->face` sequence. EditDNA must recover these transformations without being given the correct alignment. Includes metrics for alignment timing error, precision/recall, zoom-scale error, etc.
2. **False-Positive Synthetic Test**: Verify that natural source changes do not falsely trigger editor-added transform detections.
3. **Multi-Pair Synthetic Aggregation Test**: Aggregate Pair 1, 2, and 3 into a StyleProfile, verifying sample counts and incremental aggregation.
4. **Real Authorized Reference Test**: Using a ~10-30 min real source and edited derivative to manually verify alignment and observed edits.
5. **Database & API Integration**: Test endpoints for CRUD operations and alignment execution tasks.
6. **Vault & Quality Gates**: `npm run build`, strict `mypy`, and documentation updates.
