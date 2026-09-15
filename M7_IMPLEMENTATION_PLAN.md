# M7 - Visual Understanding & Focus

This milestone introduces the visual understanding layer to StreamEditor AI. It answers the questions: What is visible? Where is it? What changed? What is visually important? Where should a viewer look?

## Proposed Changes

### Database Architecture
Add the following models to `apps/api/src/stream_editor/api/models/project.py`:
- `VisualAnalysisRun`: Tracks run metadata (config, status, provider, metrics).
- `VisualRegion`: A tracked bounding box representing an object (facecam, chat, content) with normalized coordinates.
- `StreamLayout`: A temporal segment describing the screen layout composition.
- `VisualEvent`: An event linking visual changes (e.g., layout_change, facecam_appears) for indexing with TimelineEvents.
- `FocusTarget`: Represents a recommended visual attention target (e.g., facecam, screen_region) with start/end bounds and relation mappings (e.g., screen_event -> reaction).

### Backend Implementation
#### 1. Core Visual Domain and Schemas
- Add Pydantic schemas in `packages/contracts/src/stream_editor/contracts/visual_analysis.py` (`VisualRegionConfig`, `FocusTargetSchema`, etc.).
- Update `packages/contracts` to support visual event logging.

#### 2. Visual Understanding Providers
- Create `packages/analysis/src/stream_editor/analysis/providers/visual/base.py` defining the `VisualUnderstandingProvider` protocol.
- Create `MockVisualProvider` providing deterministic visual scenarios (Scenario A to F from requirements).
- Create `GeminiVisualProvider` providing the architecture for Gemini Flash/Pro multimodal reasoning, including frame sampling windows.

#### 3. Task Execution
- Add `visual_analysis_task` in `apps/worker` to orchestrate frame sampling, layout classification, region tracking, and focus sequence generation.
- The pipeline will employ hierarchical routing: Local CV (Mocked) -> Gemini Flash -> Gemini Pro.

#### 4. API Endpoints
- Create `apps/api/src/stream_editor/api/routers/visual.py` providing endpoints for:
  - `POST /projects/{id}/visual-analysis`
  - `GET /projects/{id}/visual-analysis`
  - `GET /visual-analysis/{run_id}/layouts`
  - `GET /visual-analysis/{run_id}/regions`
  - `GET /visual-analysis/{run_id}/events`
  - `GET /visual-analysis/{run_id}/focus-targets`
- Register the router in `main.py`.

### Frontend Implementation
- Create a visual debugging tool at `apps/web/src/app/projects/[id]/visual-analysis/page.tsx`
- Implement a video player component with SVG overlay boxes for bounding boxes (normalized coordinates translated to video dimensions).
- Implement list views for detected Focus Targets, Layouts, and Visual Events.

## Verification Plan

### Automated Tests
- Scaffold DB-backed unit tests in `tests/unit/analysis/test_visual_analysis.py` asserting schema correctness, run caching, and relationships.
- Run `uv run pytest` to ensure pipeline consistency.
- Test MockVisualProvider deterministic output.

### Manual Verification
- Deploy UI locally.
- Test `MockVisualProvider` output over the synthetic test video. Ensure coordinates render correctly over the video proxy.
- Ensure `M7 VERIFIED` checklist criteria (layout, facecam, chat, sequences, routing, UI) are met.
