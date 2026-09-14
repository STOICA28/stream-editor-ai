---
id: SCHEMA-EDITPLAN-001
title: EditPlan Schema
status: canonical
version: 1.1
last_reviewed: 2026-09-14
tags:
  - schema
  - editorial
  - canonical
related_code: packages/contracts/src/stream_editor/contracts/edit_plan.py
---

# EditPlan Schema

The `EditPlan` is the **sole interface** between AI editorial decisions and the deterministic renderer. An LLM produces only validated `EditPlan`-compatible JSON. The renderer accepts only validated `EditPlan` objects. Nothing else is ever executed.

> **Security principle:** The renderer must never accept a raw LLM string as a command. The `EditPlan` is the firewall.

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier for this plan |
| `project_id` | UUID | The project this plan belongs to |
| `version` | int | Monotonically increasing version number |
| `status` | str | `draft`, `approved`, `rendering`, `rendered`, `failed` |
| `clips` | list[EditClip] | Ordered list of clips (see below) |
| `transitions` | list[Transition] | Transition effects between clips |
| `audio_operations` | list[AudioOp] | Global audio adjustments |
| `narrative_dependencies` | list[NarrativeEdge] | Dependency graph preserved in this plan |
| `provenance` | EditPlanVersion | Which model/prompt generated this plan |

## EditClip Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique clip identifier |
| `source_asset_id` | UUID | Foreign key to MediaAsset |
| `source_start_seconds` | float | Start time in source media |
| `source_end_seconds` | float | End time in source media |
| `output_position_seconds` | float | Where this clip appears in the output timeline |
| `effects` | list[Effect] | Effects applied to this clip (from EffectType enum only) |
| `narrative_node_ids` | list[UUID] | NarrativeNodes this clip satisfies |
| `editorial_reason` | str | Human-readable reason for inclusion |

## EditPlanVersion (Provenance)

| Field | Type | Description |
|-------|------|-------------|
| `version` | int | Schema version |
| `created_at` | datetime | Generation timestamp |
| `model_provider` | str | e.g., `gemini`, `anthropic`, `mock` |
| `model_name` | str | e.g., `gemini-1.5-pro` |
| `model_version` | str | Specific version string |
| `prompt_version` | str | Version hash of the prompt template used |

## Validation Rules

The following must all be true for an `EditPlan` to be valid:

1. `clips` must not be empty
2. Total output duration must be > 0
3. Clips must not have overlapping `output_position_seconds` ranges
4. All `source_start_seconds` < `source_end_seconds` for each clip
5. All effect `effect_type` values must be members of `EffectType` enum
6. All effect params must validate against the corresponding param model
7. All referenced `source_asset_id` values must exist in the project
8. All `narrative_node_ids` must reference existing `NarrativeNode` records

## Example

```json
{
  "id": "9f4c2a1e-...",
  "project_id": "b3d8f0cc-...",
  "version": 1,
  "status": "draft",
  "clips": [
    {
      "id": "clip-001",
      "source_asset_id": "asset-abc",
      "source_start_seconds": 610.0,
      "source_end_seconds": 643.5,
      "output_position_seconds": 0.0,
      "effects": [
        {
          "effect_type": "zoom_face",
          "params": {
            "scale": 1.4,
            "duration_seconds": 2.0,
            "interpolation": "ease_in_out"
          },
          "start_seconds": 628.0,
          "end_seconds": 630.0
        }
      ],
      "narrative_node_ids": ["node-setup-018"],
      "editorial_reason": "Streamer reacts to unexpected boss phase with genuine shock. Setup for running death-joke callback."
    }
  ],
  "transitions": [
    {"from_clip_id": "clip-001", "to_clip_id": "clip-002", "type": "cut"}
  ],
  "audio_operations": [],
  "narrative_dependencies": [
    {"from_node_id": "node-setup-018", "to_node_id": "node-callback-044", "edge_type": "callback_to"}
  ],
  "provenance": {
    "version": 1,
    "created_at": "2026-09-14T14:00:00Z",
    "model_provider": "gemini",
    "model_name": "gemini-1.5-pro",
    "model_version": "001",
    "prompt_version": "editorial-v1.0.0"
  }
}
```

## Version History

| Version | Change |
|---------|--------|
| 1.0 | Initial schema |
| 1.1 | Added `narrative_dependencies` to top-level; clarified validation rules |

## Related Documents

- [[EFFECTS]] — Legal effect types and their constraints
- [[STORY_GRAPH]] — NarrativeNode and NarrativeEdge schemas
- [[CANDIDATE_SEGMENT]] — Input to EditPlan generation
- [[ADR-002-structured-edit-plan]] — Why this architecture exists
