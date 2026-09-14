---
name: rendering
description: Executes a validated EditPlan into a rendered media output using deterministic FFmpeg calls. Never executes model-generated strings.
version: 1.0
applies_to: packages/rendering/
---

# Skill: rendering

## Purpose

Take a validated `EditPlan` and produce actual rendered media output. The renderer is the **only** component that touches FFmpeg. It is deterministic, auditable, and safe.

## Cardinal Rules

1. **Validate EditPlan schema before touching FFmpeg** — no exceptions
2. **All FFmpeg calls use argument lists** — never `shell=True`, never string concatenation
3. **Validate all input paths before use** — must exist, must be within `DATA_DIR`
4. **Create preview render before final render** — catch problems cheaply
5. **Use ffprobe to verify output** — validate codec, duration, dimensions
6. **Log all commands at DEBUG level** — argument list form, not string form
7. **Never execute model-generated strings** — ever

## Step-by-Step Process

### 1. Validate the EditPlan

```python
# Re-validate even if caller claims it's validated
try:
    plan = EditPlan.model_validate(plan_dict)
except ValidationError as exc:
    log.error("render.editplan.invalid", errors=exc.errors(), job_id=job_id)
    raise RenderError(f"EditPlan validation failed: {exc}") from exc
```

### 2. Validate all input paths

Before building any FFmpeg command:

```python
data_dir = Path(settings.DATA_DIR).resolve()

for clip in plan.clips:
    source_path = storage.get_source_path(plan.source_job_id).resolve()
    
    # Path must exist
    if not source_path.exists():
        raise RenderError(f"Source not found: {source_path}")
    
    # Path must be within DATA_DIR (prevent path traversal)
    try:
        source_path.relative_to(data_dir)
    except ValueError:
        raise RenderError(f"Source path outside DATA_DIR: {source_path}")
    
    # Validate clip timestamps
    if clip.source_end_s > source_duration_s:
        raise RenderError(
            f"Clip {clip.id}: source_end_s ({clip.source_end_s}) "
            f"exceeds source duration ({source_duration_s})"
        )
```

### 3. Build FFmpeg argument lists (NOT strings)

Each FFmpeg call must be an explicit list:

```python
# WRONG — never do this
cmd_str = f"ffmpeg -ss {start} -to {end} -i {input} {output}"  # ❌

# RIGHT — always this form
cmd = [
    settings.FFMPEG_PATH,
    "-ss", str(clip.source_start_s),    # seek to start
    "-to", str(clip.source_end_s),       # end time
    "-i", str(source_path),              # input
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "18",
    "-c:a", "aac",
    "-b:a", "192k",
    "-avoid_negative_ts", "make_zero",
    str(clip_output_path),
]
log.debug("ffmpeg.cmd", args=cmd, job_id=job_id, clip_id=clip.id)  # ✅ log it
subprocess.run(cmd, check=True, capture_output=True)
```

### 4. Apply effects via pre-built filter chains

Map `EffectType` to deterministic filter arguments:

```python
EFFECT_FILTER_BUILDERS: dict[EffectType, Callable] = {
    EffectType.zoom_in: build_zoom_in_filter,
    EffectType.fade_in: build_fade_in_filter,
    EffectType.crop: build_crop_filter,
    # etc.
}

def build_zoom_in_filter(effect: Effect, duration_s: float) -> str:
    """Build a zoompan filter string (parameters from validated effect only)."""
    factor = effect.params["factor"]  # already validated: 1.0 ≤ factor ≤ 3.0
    return f"zoompan=z='zoom+0.002':d={int(duration_s * 25)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
```

Never accept a filter string from an LLM. Always build it from validated params.

### 5. Concatenate clips

After rendering individual clips, concatenate:

```python
# Build concat demuxer file (no shell metacharacters)
concat_content = ""
for clip_path in clip_paths:
    concat_content += f"file '{clip_path.as_posix()}'\n"
concat_file = work_dir / "concat.txt"
concat_file.write_text(concat_content, encoding="utf-8")

cmd = [
    settings.FFMPEG_PATH,
    "-f", "concat",
    "-safe", "0",
    "-i", str(concat_file),
    "-c", "copy",
    str(output_path),
]
```

### 6. Create preview render first

Before final render, render a 60-second preview:

```python
preview_path = work_dir / "preview.mp4"
preview_cmd = [
    settings.FFMPEG_PATH,
    "-i", str(full_output_path),
    "-t", "60",
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35",
    "-c:a", "aac", "-b:a", "64k",
    str(preview_path),
]
subprocess.run(preview_cmd, check=True, capture_output=True)
log.info("render.preview.complete", path=str(preview_path), job_id=job_id)
# Preview is available for QA before final render completes
```

### 7. Verify output with ffprobe

After rendering, validate the output:

```python
probe_cmd = [
    settings.FFPROBE_PATH,
    "-v", "quiet",
    "-print_format", "json",
    "-show_format",
    "-show_streams",
    str(output_path),
]
result = subprocess.run(probe_cmd, check=True, capture_output=True, text=True)
probe_data = json.loads(result.stdout)

# Validate
actual_duration = float(probe_data["format"]["duration"])
expected_duration = plan.total_output_duration_s
if abs(actual_duration - expected_duration) > 1.0:  # 1 second tolerance
    log.warning(
        "render.duration.mismatch",
        expected=expected_duration,
        actual=actual_duration,
        delta=abs(actual_duration - expected_duration),
    )
```

### 8. Structured logging

Log every significant step:

```python
log.info("render.start", job_id=job_id, clip_count=len(plan.clips))
log.debug("ffmpeg.cmd", args=cmd, clip_id=clip.id)  # argument list
log.info("render.clip.complete", clip_id=clip.id, elapsed_s=elapsed)
log.info("render.concat.start", clip_count=len(clip_paths))
log.info("render.complete", output_path=str(output_path), duration_s=actual_duration)
```

## Security Checklist

Before every render:

- [ ] EditPlan re-validated with `model_validate()`
- [ ] All source paths checked: exist + within DATA_DIR
- [ ] All timestamps within source duration
- [ ] All effect params from validated schema (not from LLM strings)
- [ ] All FFmpeg cmds are lists (no shell=True, no string format)
- [ ] All commands logged at DEBUG level

## Output Checklist

- [ ] Preview render created and verified
- [ ] Final render complete
- [ ] ffprobe verification passed (duration, codec)
- [ ] Output path recorded in job
- [ ] Render logged (start, complete, duration)