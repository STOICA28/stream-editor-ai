# M9 — DETERMINISTIC RENDERING ENGINE Implementation Plan

The M8 Preflight Gate has been successfully passed. The repository contains real `GeminiEffectPlanner` and `GeminiEffectCritic` components.

## Goal
Implement a deterministic rendering engine that takes an approved `EditPlan`, a validated `EffectPlan`, and source media to produce a rendered `.mp4`. 

## User Review Required
Please review the detailed architecture below for M9, including cache structures, validation rules, and the boundary between FFmpeg and Remotion. Do not proceed to execution until approved.

## Proposed Changes

### 1. Rendering Architecture & Source Quality
- **Separate Paths**:
  - `preview`: Uses the 720p analysis proxy asset. Fast codec presets.
  - `final`: Strictly uses the original source media asset. High quality presets.
- **Timestamp Precision & VFR**: 
  - Do not rely on `frame = timestamp * fps`. Media timestamps (milliseconds or accurate decimal seconds) will be the source of truth to avoid floating-point drift across 100+ cuts.
  - FFmpeg's timebase and PTS/DTS will be preserved. Variable Frame Rate (VFR) sources will be handled via `-vsync vfr` or equivalent PTS matching to keep exact media timestamps.
- **Audio Continuity**:
  - Implement short crossfades (e.g. 10ms) around hard cuts to avoid audio pops/clicks, without altering editorial timing.
- **Multi-Source & Multi-Audio**:
  - Preserve M1.1 support for `EditPlans` containing multiple source assets.
  - Deterministically select the default audio stream (index 0 or explicit config) when multiple audio streams are present.

### 2. Job Isolation & Resumability
- **Isolated Directories**: 
  - Each job gets a dedicated path: `data/projects/<id>/renders/<render-job-id>/`.
  - Subdirectories: `segments/` and `work/`. Output uses `output.partial.mp4`.
- **Atomic Outputs**: 
  - All outputs write to `.partial`. Only upon full success and FFprobe validation is the file promoted to `final.mp4`.
- **Resumable Rendering**:
  - Renders are segment-based (cache-first). An interrupted or crashed job will leave completed segments in the cache. Retries will skip successfully rendered segments and resume where it failed.

### 3. Segment Caching & Signatures
- **Cache Signatures**: Each segment computes a deterministic hash of:
  `source fingerprint + source range + effects + RenderConfig + renderer version`
- **Cache Reuse & Invalidation**:
  - Modifying one clip in an `EditPlan` changes its signature, but unchanged clips hit the cache.
  - Changing `RenderConfig` (codec, resolution) alters the signature, invalidating the entire cache.
- **Corrupt Cache Handling**:
  - Cache hits must be verified (file exists, valid size). Corrupt segments or outputs are detected, deleted, and regenerated.

### 4. Models & Database
#### [MODIFY] apps/api/src/stream_editor/api/models/project.py
Add `RenderJob` model:
- `id`, `project_id`, `source_asset_id`, `edit_plan_id`, `effect_plan_run_id` (optional, supports content-only renders).
- `render_config`, `derivation_signature`, `renderer_version`.
- `status` (pending, preparing, rendering, validating, completed, failed, cancelled, interrupted).
- `progress` (float 0-100), `output_asset_id`, `error_message`, `started_at`, `completed_at`.

*Successful renders create a `MediaAsset` of type `preview_render` or `final_render`, storing full provenance.*

### 5. Contracts (Schemas)
#### [NEW] packages/contracts/src/stream_editor/contracts/rendering.py
- `RenderConfig`: mode (preview/final), width, height, fps, video/audio codecs, pixel format, CRF, sample rate, container, hw_accel.
- `CompiledSegment`: source_start, source_end, output_start, output_end, applicable_effects.
- `CompiledTimeline`: ordered `CompiledSegments`, expected_duration.
- `RenderManifest`: Machine-readable JSON output detailing inputs, renderer version, segments used, config, and output hash.

### 6. Timeline Compilation & Effect Boundaries
#### [NEW] packages/rendering/src/stream_editor/rendering/compiler.py
- Transforms `EditPlan` + `EffectPlan` into a `CompiledTimeline`.
- Supports content-only (no EffectPlan) fallback.
- **Effect State Leakage**: State resets to base at segment boundaries unless explicitly held.

### 7. Engine & Handlers (FFmpeg / Remotion Boundary)
#### [NEW] packages/rendering/src/stream_editor/rendering/engine.py
- **FFmpeg Domain**: trims, concat, audio gain/ducking, speed changes, grayscale, basic zoom transforms, muxing.
- **Remotion Domain**: Rich animated overlays, future text/meme graphics.
  - **No JSX Injection**: We output a strongly typed `RemotionRenderSpec` JSON. We *never* execute AI-generated arbitrary React code.
- **Structured Handlers**: Instead of arbitrary string concats, use an `EffectRendererRegistry` (e.g., `ZoomRenderer`, `GrayscaleRenderer`) to build validated FFmpeg filter nodes.

### 8. FFprobe Validation & Telemetry
#### [NEW] packages/rendering/src/stream_editor/rendering/validator.py
- Post-render validation asserts: parsable media, presence of video/audio streams, correct dimensions, expected codecs, nontrivial size, and duration matching `CompiledTimeline.expected_duration` (within a documented tolerance).
- Detects corrupt final outputs.
- **Telemetry**: Records wall-clock duration, output duration, realtime factor, cache hits/misses, encoder used, and output bytes.

### 9. Progress, Cancellation & API
#### [NEW] apps/api/src/stream_editor/api/routers/renders.py
- `POST /projects/{id}/renders` (starts job)
- `GET /renders/{render_id}`
- `POST /renders/{render_id}/cancel` (terminates subprocess, leaves valid segments, removes `.partial`)
- `POST /renders/{render_id}/retry`
- Progress parsing uses FFmpeg's `-progress pipe:` to reliably update the DB.

### 10. Frontend UI
#### [NEW] apps/web/src/app/projects/[id]/renders/page.tsx
- Render UI showing Status, Progress %, Clip X/Y, Output Time.
- Integration from the M8 Debugger: "Render Preview" button.

## Verification Plan

### Automated Tests
- **Content-Only**: 3 selected clips, no effects (verifies cut accuracy and duration).
- **A/V Sync**: Verify sync does not drift across multiple cuts.
- **Scale Simulation**: 100-150 clip timeline simulation to verify no timeline gaps or cumulative drift.
- **Effect Leakage**: Clip A has zoom, Clip B has none. Verify B is rendered correctly without leaked state.
- **Cache Invalidation**:
  - Modify 1 clip -> only 1 segment misses cache.
  - Modify RenderConfig -> all segments miss cache.
- **Corrupt States**:
  - Delete/corrupt a cached segment -> regenerates.
  - Corrupt final `.partial` -> fails validation, regenerates.
- **Interruption/Retry**: Simulate job cancellation midway, assert valid cache remains and retry succeeds.
- **Specific Effects**: `zoom_region`, `zoom_face`, `zoom_chat`, `screen→face` sequence (golden test), `grayscale`, `freeze_frame`, `speed changes`, `audio_gain`, mixed conflicts.

### Manual Verification
- Render a 2–5 minute authorized real video using the frontend UI.
- Inspect visually:
  - Exact cut accuracy at boundaries.
  - A/V Sync.
  - Zoom geometry mapping perfectly without black borders.
  - Screen → Face transitions.
  - Return-to-base behavior on following clips.
  - Grayscale toggling correctly.
  - FFprobe output matching expected specifications.
