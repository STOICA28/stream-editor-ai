---
id: ADR-008
title: UV Workspace and PEP 420 Namespace Packages
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - adr
  - packaging
---

# ADR 008: UV Workspace and PEP 420 Namespace Packages

## Context
StreamEditor AI is a complex system composed of multiple applications (`api`, `worker`, `web`) and packages (`contracts`, `media`, `analysis`, `editorial`, `models`, `rendering`, `storage`, `vault`). We needed a way to manage these dependencies locally without publishing them.

## Decision
- We use **`uv` workspaces** to manage the Python monorepo.
- We use **PEP 420 implicit namespace packages** for the `stream_editor` namespace. 
- All packages expose their modules under `src/stream_editor/<package_name>`.
- To comply with PEP 420 and `uv`/`hatchling` editable installs, **we strictly prohibit the existence of `__init__.py` files in the `src/stream_editor/` directories**.

## Rationale
- `uv` is extremely fast and natively supports workspace `[tool.uv.sources]` configurations, allowing us to link local packages without fighting `pip` editable installs manually.
- PEP 420 namespace packages allow multiple separate packages to share the `stream_editor.*` import namespace, which keeps imports clean (e.g., `from stream_editor.contracts import EditPlan`).
- The strict rule against `__init__.py` files is required because if even a single `__init__.py` exists, Python treats it as a regular package and stops searching the remaining workspace directories, leading to `ModuleNotFoundError` across the workspace.

## Consequences
- Developers must remember NOT to add `__init__.py` to the `src/` or `src/stream_editor/` levels.
- The `pytest` test suite requires a `pythonpath` declaration in `pyproject.toml` pointing to all `packages/*/src` and `apps/*/src` directories to correctly resolve the namespace during test execution.
