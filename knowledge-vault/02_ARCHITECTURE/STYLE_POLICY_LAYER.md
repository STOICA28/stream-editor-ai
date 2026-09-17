---
id: ARCH-STYLE-001
title: Style Policy Layer Architecture
status: canonical
version: 1.0
last_reviewed: 2026-09-17
tags:
  - architecture
  - m11
  - style
---

# Style Policy Layer

The Style Policy Layer (M11) connects the raw research output (EditDNA / StyleProfile) with the deterministic production pipelines (M3, M5, M8). 

## Core Principle
**Style is a scoped prior, not canonical truth.**
The base evidence layers (understanding, narrative graph, visual layout) are completely style-neutral. Style profiles do NOT overwrite facts; they provide weighted preferences for decision-making.

## Data Flow
1. **StyleProfile**: Descriptive research data ("how this human edited").
2. **StylePolicyCompiler**: A deterministic compilation engine that translates the Profile + Approved Research + Canonical Constraints into an immutable EditorialStylePolicy.
3. **EditorialStylePolicy**: A versioned, traceable instruction set containing bounds, distribution targets, and influence weights.
4. **CandidateStyleAdapter (M3)**: Wraps raw M3 candidates in a StyledCandidateAssessment. Generates influence values (e.g., reaction_retention +0.2) based on the policy, preserving the original base scores.
5. **Selection (M5) & Effects (M8)**: Consume the styled assessments. Decisions reflect a balance of narrative value, technical limits, and style priors.

## Precedence Hierarchy
When generating edit plans, precedence is strictly enforced:
1. Technical / Renderer / Schema Invariants (e.g., duration must be > 0)
2. Explicit Human Locked Decisions (M6 overrides)
3. Canonical Editorial Bible rules
4. Explicit Project-Level Human Preferences
5. Selected Approved StylePolicy
6. Default Planner Heuristics

## Governance and Application
*   **Experimental Mode**: A research-level StyleProfile can only be applied if the project explicitly enables experimental_style = true.
*   **Provenance**: Every style-induced change (scoring bump, effect suggestion) must trace back to a specific rule, source metric, N (sample size), and confidence score.
*   **Dry Run**: Style can be tested via a dry run, producing a StyleImpactReport that compares the default outcome with the styled outcome, mutating no database state.
*   **Branding Protection**: Transformed source content and recurring overlays observed in research must NEVER leak literal strings, logos, or copyrighted music into new edits.
