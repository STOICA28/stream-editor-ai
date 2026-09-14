---
id: ADR-002
title: Structured EditPlan as AI-to-Renderer Interface
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - adr
  - architecture
  - security
  - editorial
---

# ADR-002: Structured EditPlan as AI-to-Renderer Interface

**Status:** Accepted  
**Date:** 2026-09-14  
**Deciders:** Principal Architect

## Context

The system uses LLMs/VLMs to make editorial decisions. A naive implementation would have the model generate FFmpeg commands or shell scripts that are then executed. This approach is:

1. **Dangerous** â€” AI-generated shell commands are arbitrary code execution
2. **Unauditable** â€” There is no structured record of what decision was made and why
3. **Unreproducible** â€” Two runs with the same model may produce different commands
4. **Unversioned** â€” There is no schema to validate or evolve
5. **Unmaintainable** â€” Business logic lives in prompts, not in code

## Decision

All AI editorial decisions are expressed as **validated `EditPlan` objects** defined by a Pydantic v2 schema.

**The principle: AI decides. Deterministic software executes.**

```
LLM/VLM
   â†“
Raw JSON output
   â†“
Pydantic validation (EditPlan schema)  â† FIREWALL
   â†“
Validated EditPlan
   â†“
Renderer (FFmpeg, Remotion)
   â†“
Media output
```

An LLM must NEVER:
- Execute arbitrary FFmpeg commands
- Generate shell strings that get executed
- Invent effect names not in the `EffectType` enum
- Generate file paths directly (only reference assets by ID)
- Modify the rendering pipeline dynamically

### Effect API

Effects are expressed as typed, constrained objects using an **enumerated `EffectType`**. The model cannot invent new effects â€” it can only select from the approved list with validated parameters.

```python
class EffectType(str, Enum):
    zoom_face = "zoom_face"       # scale: 1.2-2.0
    slow_motion = "slow_motion"   # speed: 0.25-0.75
    grayscale = "grayscale"       # intensity: 0.0-1.0
    # ... all effects enumerated
```

If the model returns `"effect_type": "custom_explosion"`, Pydantic raises `ValidationError` and the plan is rejected before it reaches the renderer.

### Structured Output

Model adapters must use structured output (JSON mode or function calling) wherever the provider supports it. The `ModelProvider` interface returns typed Python objects, not raw strings.

### Provenance

Every `EditPlan` records which model, which model version, and which prompt version generated it. This allows:
- Auditing of editorial decisions
- Reproducing a previous edit
- Attribution of bugs to specific model/prompt combinations

## Consequences

### Positive
- Arbitrary code execution by AI is architecturally impossible
- Every editorial decision is auditable and versioned
- Effects are constrained to a safe enumerated set
- Schema evolution is explicit and versioned
- The renderer is completely decoupled from model choices

### Negative
- New effect types require schema changes (EditPlan version bump)
- Some model capabilities cannot be used if they don't fit the schema
- Additional validation overhead on every model response

### Mitigations
- The `EffectType` enum covers all practically needed effects for the editorial use case
- Validation overhead is negligible compared to rendering time
- Schema changes go through ADR process to prevent uncontrolled drift

## References

- `packages/contracts/src/stream_editor/contracts/edit_plan.py` â€” Implementation
- `packages/contracts/src/stream_editor/contracts/effects.py` â€” Effect API
- EDIT_PLAN â€” Full schema specification
- EFFECTS â€” Effect constraints
- [[ADR-005-model-provider-abstraction]] â€” How models are invoked
