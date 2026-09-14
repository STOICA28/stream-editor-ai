---
name: video-analysis
description: Runs the StreamEditor AI analysis pipeline on media files to produce structured TimelineEvents. Handles proxy generation, transcription, scene detection, and energy analysis.
version: 1.0
applies_to: packages/analysis/
---

# Skill: video-analysis

## Purpose

Transform raw media into structured `TimelineEvent` objects that the editorial planner can reason about. This skill covers the complete analysis pipeline: proxy generation → transcription → scene detection → energy analysis → event consolidation.

## Cardinal Rules

1. **Always use the analysis proxy** — never run AI analysis on full-quality source
2. **Cache everything** — never re-run a completed analysis stage
3. **Check idempotency** — check job step status before starting any stage
4. **Produce TimelineEvents** — not raw detector output; validated schema only
5. **Log every step** — structured logging with stage name, job_id, timing

## Pipeline Stages

```
Source Media
    ↓
[Stage 1] Proxy Generation    → {job_id}_proxy.mp4 (1280px wide, H.264)
    ↓
[Stage 2] Audio Extraction    → {job_id}_audio.wav (16kHz mono)
    ↓
[Stage 3] Transcription       → TranscriptSegment[]
    ↓
[Stage 4] Scene Detection     → SceneChangeEvent[]
    ↓
[Stage 5] Energy Analysis     → AudioEnergyEvent[]
    ↓
[Stage 6] Consolidation       → TimelineEvent[] (canonical output)
```

## Step-by-Step Process

### Stage 1: Proxy Generation

Before any analysis, generate a proxy:

```python
# Check if proxy already exists
proxy_path = storage.get_proxy_path(job_id)
if proxy_path.exists():
    log.info("proxy.exists", job_id=job_id)
else:
    # Generate: exact argument list, no shell=True
    cmd = [
        ffmpeg_path,
        "-i", str(source_path),
        "-vf", f"scale={proxy_width}:-2",  # 1280px wide, maintain AR
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-an",  # no audio in proxy (separate audio stage)
        str(proxy_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
```

Proxy width is set by `ANALYSIS_PROXY_WIDTH` env var (default: 1280).

### Stage 2: Audio Extraction

Extract audio at the standard sample rate:

```python
cmd = [
    ffmpeg_path,
    "-i", str(source_path),
    "-vn",               # no video
    "-ar", "16000",      # 16kHz (AUDIO_SAMPLE_RATE)
    "-ac", "1",          # mono
    "-c:a", "pcm_s16le", # WAV
    str(audio_path),
]
```

### Stage 3: Transcription

- Transcribe the extracted audio (not the video)
- Store as `TranscriptSegment[]` with: start, end, text, confidence, speaker (if diarized)
- Cache the transcript JSON — do not re-transcribe if cached
- If transcription fails: log error, set stage status to `failed`, do not continue

### Stage 4: Scene Detection

Use PySceneDetect or equivalent on the proxy:
- Detect scene changes (content-aware threshold, not hash-based)
- Record: `{timestamp: float, score: float, detector: str, detector_version: str}`
- Store raw detector output separately from TimelineEvents

### Stage 5: Energy Analysis

Compute audio energy envelope:
- Window size: 0.5s with 0.25s overlap
- Metric: RMS energy, normalized 0–1
- Identify peaks (local maxima > threshold)
- Store peaks as: `{timestamp: float, energy: float, is_peak: bool}`

### Stage 6: Consolidation → TimelineEvents

Convert raw detector output to `TimelineEvent` schema:

```python
TimelineEvent(
    id="evt-{job_id}-{sequence:05d}",
    source="transcription" | "scene_detect" | "energy_analysis",
    type=TimelineEventType.SPEECH | SCENE_CHANGE | ENERGY_PEAK | ...,
    start_s=float,      # seconds from media start
    end_s=float,        # seconds from media start
    confidence=float,   # 0.0 – 1.0
    producer="stream_editor.analysis.transcription",
    producer_version="1.0",
    metadata={...},     # source-specific fields
)
```

**Validation rules for each event:**
- `start_s < end_s` (for ranged events)
- `confidence` in [0.0, 1.0]
- `end_s <= source_duration_s`
- `type` must be a valid `TimelineEventType` enum value
- All IDs unique within a job

### Idempotency

Before each stage, check the job step status in the database:
```python
step = await job_repo.get_step(job_id, stage_name)
if step and step.status == "completed":
    log.info("stage.skip.already_complete", stage=stage_name, job_id=job_id)
    return step.output
```

Never re-run a completed stage without explicit user request to re-analyze.

### Structured Logging

Every stage must emit structured logs:

```python
log.info(
    "stage.start",
    job_id=job_id,
    stage="transcription",
    source_duration_s=duration,
)
# ... work ...
log.info(
    "stage.complete",
    job_id=job_id,
    stage="transcription",
    segments_count=len(segments),
    elapsed_s=elapsed,
)
```

## Error Handling

- If a stage fails: set job step status to `failed`, log the error with full context
- Do not silently swallow exceptions in the pipeline
- On partial failure: store successfully completed stages, fail the job, allow resume

## Output Checklist

- [ ] Proxy generated (or confirmed existing)
- [ ] Audio extracted at 16kHz mono
- [ ] Transcript produced and cached
- [ ] Scene changes detected
- [ ] Energy analysis complete
- [ ] All TimelineEvents pass schema validation
- [ ] All events have `producer` and `producer_version` set
- [ ] Structured logs emitted for each stage