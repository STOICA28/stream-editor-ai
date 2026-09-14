---
name: validation
description: Runs the full validation suite (tests, linting, vault consistency, media validation) and reports all failures with precise locations.
version: 1.0
applies_to: tests/, scripts/
---

# Skill: validation

## Purpose

Ensure all code, documentation, and media outputs meet StreamEditor AI's quality standards before any work is marked complete.

## When to Apply This Skill

- Before marking any task complete
- Before every commit
- After making changes to any package
- When asked to "validate", "check", or "run tests"
- After generating any media output

## Full Validation Suite

Run in this order — stop at any failure and fix before proceeding:

### Step 1: Unit and Integration Tests

```bash
make test
# equivalent: uv run pytest tests/ -v
```

**All tests must pass.** No skips without a documented reason in the test itself.

If tests fail, report:
- Exact test name
- File and line number
- Error message
- Whether this is a pre-existing failure or introduced by recent changes

### Step 2: Type Checking (mypy strict)

```bash
uv run mypy packages/ apps/
```

mypy is configured in `pyproject.toml` with `strict = true`. All type errors must be resolved.

Common mypy issues and fixes:

| Issue | Fix |
|-------|-----|
| `Missing return type annotation` | Add `-> ReturnType` |
| `Incompatible return value type` | Check Pydantic model usage — use `model_validate()` |
| `Item has no attribute "x"` | Check Optional types — use `if obj.x is not None` |
| `Untyped def` | Add type annotations to all function parameters |

### Step 3: Linting (ruff)

```bash
uv run ruff check .
```

Auto-fix safe issues:
```bash
uv run ruff check --fix .
uv run ruff format .
```

Do NOT auto-fix and commit without reviewing the diff.

### Step 4: Vault Consistency

```bash
make check-vault
# equivalent: uv run python scripts/check_vault.py
```

If vault check fails:
- `MISSING required document` → create the document with proper frontmatter
- `frontmatter missing field` → add the missing field
- `invalid status` → use only: draft, research, proposal, canonical, deprecated
- `broken wikilink` (warning) → update link or create target

### Step 5: EditPlan Validation (when applicable)

When an EditPlan has been generated, validate it explicitly:

```python
from stream_editor.contracts.edit_plan import EditPlan
from pydantic import ValidationError

try:
    plan = EditPlan.model_validate(plan_dict)
except ValidationError as exc:
    print(f"EditPlan validation errors: {exc.errors()}")
```

Check additionally:
- All `source_start_s` < `source_end_s`
- All `source_end_s` ≤ `source_duration_s`
- All clip IDs are unique
- All `narrative_deps` reference clip IDs within the plan
- All effect types are valid `EffectType` enum values
- Clip `order` values are sequential (no gaps, no duplicates)

### Step 6: Media Validation (when media was generated)

For any rendered media output, validate with ffprobe:

```python
import subprocess
import json

def validate_media(path: str) -> dict:
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)

probe = validate_media("output.mp4")

# Check duration is within 1 second of expected
actual = float(probe["format"]["duration"])
assert abs(actual - expected_duration_s) < 1.0, f"Duration mismatch: {actual} vs {expected_duration_s}"

# Check codec
video_streams = [s for s in probe["streams"] if s["codec_type"] == "video"]
assert video_streams, "No video stream found"
assert video_streams[0]["codec_name"] == "h264", f"Wrong codec: {video_streams[0]['codec_name']}"
```

### Step 7: API Validation (when API changes were made)

Run integration tests:
```bash
uv run pytest tests/integration/ -v -m api
```

Check endpoint contracts match the OpenAPI schema:
```bash
# Generate schema and diff against committed version
uv run python -c "from stream_editor.api.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > /tmp/current_schema.json
diff knowledge-vault/05_SCHEMAS/openapi_snapshot.json /tmp/current_schema.json
```

## Failure Reporting Format

When reporting validation failures, always include:

```
FAILURE: [test|mypy|ruff|vault|editplan|media|api]
  File: path/to/file.py (or vault/path.md)
  Line: N (when applicable)
  Issue: exact error message
  Severity: ERROR | WARNING
  Introduced by: [this session | pre-existing]
```

## Passing Criteria

Validation passes when ALL of the following are true:

- [ ] `make test` exits 0 (all tests pass, no unexpected skips)
- [ ] `uv run mypy packages/ apps/` exits 0 (no type errors)
- [ ] `uv run ruff check .` exits 0 (no lint errors)
- [ ] `make check-vault` exits 0 (all required docs present and valid)
- [ ] Any EditPlan generated this session passes `model_validate()`
- [ ] Any media generated this session passes ffprobe validation
- [ ] `PROJECT_STATUS.md` updated
- [ ] `CHANGELOG.md` updated