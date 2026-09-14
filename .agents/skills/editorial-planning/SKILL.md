---
name: editorial-planning
description: Generates a validated EditPlan from TimelineEvents and canonical Editorial Bible rules. The LLM produces decisions; Pydantic validates them; the renderer executes them.
version: 1.0
applies_to: packages/editorial/
---

# Skill: editorial-planning

## Purpose

Transform `TimelineEvent[]` + canonical editorial rules into a validated `EditPlan`. The editorial planner is where the LLM's judgment is applied — but the output must be a validated schema, not free text.

## Cardinal Rules

1. **ALWAYS retrieve canonical rules first** — never plan without them
2. **Only use `status: canonical` documents** — never `draft`, `research`, or `proposal`
3. **Output ONLY validated EditPlan structures** — no free-text edit instructions
4. **Never generate effect names not in `EffectType` enum** — schema defines what exists
5. **Never produce timestamps exceeding source duration** — validate all boundaries
6. **Mark uncertain dependencies explicitly** — never silently omit a narrative link

## Step-by-Step Process

### 1. Retrieve canonical Editorial Bible rules

Before any planning, retrieve all canonical rules via VaultIndex:

```python
vault_index = VaultIndex(db_session)
rules = await vault_index.search(
    query="keep cut editorial rule",
    status_filter="canonical",
    section_filter="03_EDITORIAL_BIBLE",
    limit=50,
)
```

If no canonical rules found: **stop**. Do not plan without rules. Log a warning and surface the issue.

Also retrieve creator-specific EditDNA if available:
```python
dna_rules = await vault_index.search(
    query=f"creator:{creator_slug}",
    status_filter="canonical",
    limit=20,
)
```

### 2. Understand the source structure

Before planning, build a mental model of the source:

- Total duration
- Transcript segments (what was said, when)
- Scene changes (structural boundaries)
- Energy peaks (emotional/comedic moments)
- Identify: setups, payoffs, callbacks, running jokes

**Narrative dependency mapping:**
For any moment that is a PAYOFF or CALLBACK, identify its SETUP:
```
setup_at: 00:12:34  "I bet this won't work"
payoff_at: 00:45:12 "It didn't work"
dependency: payoff requires setup, or payoff loses context
```

### 3. Apply keep/cut decisions

For each candidate section, apply canonical rules:

- Check `03_EDITORIAL_BIBLE/KEEP_VS_CUT.md` for criteria
- Check `03_EDITORIAL_BIBLE/EDITORIAL_PHILOSOPHY.md` for pacing constraints
- Apply creator-specific rules (from EditDNA) if available

Never remove a SETUP if its PAYOFF is retained. This is a hard constraint, not a preference.

### 4. Generate the EditPlan structure

Structure the EditPlan — validated against `EditPlan` Pydantic schema:

```python
EditPlan(
    id="plan-{job_id}",
    version="1.0",
    source_job_id=job_id,
    source_duration_s=total_duration,
    created_at=datetime.utcnow(),
    rules_applied=[rule.id for rule in rules],
    clips=[
        EditClip(
            id="clip-{n:04d}",
            source_start_s=float,
            source_end_s=float,
            order=int,
            effects=[...],
            narrative_role="setup" | "payoff" | "standalone" | "transition",
            narrative_deps=["clip-0003"],  # IDs this clip depends on
        )
    ],
    total_output_duration_s=sum(clip.duration_s for clip in clips),
)
```

### 5. Validate all constraints before outputting

Run these checks before producing the final EditPlan:

```python
# Timestamp sanity
assert clip.source_start_s >= 0
assert clip.source_end_s <= source_duration_s
assert clip.source_start_s < clip.source_end_s

# Clip ordering
for i in range(1, len(clips)):
    assert clips[i].order > clips[i-1].order

# Narrative dependency integrity
all_clip_ids = {c.id for c in clips}
for clip in clips:
    for dep_id in clip.narrative_deps:
        assert dep_id in all_clip_ids, f"Clip {clip.id} depends on {dep_id} which is not in plan"

# Effect validation
for effect in clip.effects:
    assert effect.type in EffectType.__members__
    # Check effect params against effect-specific constraints
```

### 6. Handle uncertainty explicitly

If uncertain about a narrative dependency:

```python
# WRONG — silently omit the dependency
clip.narrative_deps = []

# RIGHT — mark uncertainty explicitly
clip.narrative_deps = ["clip-0003"]
clip.narrative_dependency_uncertain = True
clip.narrative_dependency_note = "Setup at 00:12:34 may relate to this payoff; verify manually"
```

Never silently omit a dependency. An uncertain dependency that is flagged can be reviewed. A silently omitted one creates a broken edit.

### 7. Log the planning decision

```python
log.info(
    "editorial.plan.complete",
    job_id=job_id,
    source_duration_s=source_duration,
    output_duration_s=plan.total_output_duration_s,
    retention_rate=plan.total_output_duration_s / source_duration,
    clip_count=len(plan.clips),
    rules_applied_count=len(plan.rules_applied),
    uncertain_deps_count=sum(1 for c in plan.clips if c.narrative_dependency_uncertain),
)
```

## Effect Validation Reference

Only use effects defined in `EffectType` enum (see `packages/contracts`):

| Effect Type | Key Parameters | Constraints |
|------------|---------------|-------------|
| `zoom_in` | `factor`, `duration_s` | factor: 1.0–3.0 |
| `zoom_out` | `factor`, `duration_s` | factor: 1.0–3.0 |
| `fade_in` | `duration_s` | duration: 0.1–5.0s |
| `fade_out` | `duration_s` | duration: 0.1–5.0s |
| `color_grade` | `preset` | preset must be in ColorGradePreset enum |
| `speed_ramp` | `factor` | factor: 0.25–4.0 |
| `crop` | `x`, `y`, `w`, `h` | all relative (0–1) |

## Output Checklist

- [ ] Canonical rules retrieved from VaultIndex (status=canonical only)
- [ ] Narrative dependencies mapped (setup → payoff)
- [ ] All timestamps within source duration
- [ ] All clip orderings sequential
- [ ] All narrative deps point to clips IN the plan
- [ ] All effect types are valid `EffectType` enum values
- [ ] Uncertain deps flagged explicitly (not silently omitted)
- [ ] EditPlan passes `EditPlan.model_validate()` without errors
- [ ] Planning decision logged with retention_rate and clip_count