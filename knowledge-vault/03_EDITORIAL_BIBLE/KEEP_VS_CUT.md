---
id: ED-KEEP-CUT-001
title: Keep vs Cut Rules
status: canonical
version: 1.2
last_reviewed: 2026-09-14
tags:
  - editorial
  - rules
  - retention
---

# Keep vs Cut Guidelines

**Goal:** Transform unedited livestreams into high-retention, narrative-driven content. The AI must make deterministic choices about what to retain based on these validated product principles.

## Canonical Principles (Product Level)

1. **Preserve Narrative Context:** A reaction or punchline must not be isolated from its necessary setup.
2. **Preserve Setup/Payoff Relationships:** Do not cut the setup if the payoff is kept. 
3. **Preserve Callbacks:** Maintain callbacks when they are required for comprehension or humor.
4. **Remove Dead Material:** Genuinely dead or unnecessary material must be removed to improve pacing.
5. **Effects Must Serve Content:** Visual and audio effects must only be applied to serve the content, not just for the sake of editing.
6. **No "Highlight" Generation:** Do not reduce editing to merely selecting isolated high-score highlights. The overall video must feel coherent.
7. **Human in Control:** AI recommendations must remain reviewable by a human.

## Note on Implementation
Any specific rule regarding what to cut (e.g., "menu navigation") or how to weight candidate scores must remain configurable and experimental until empirically validated through EditDNA research. Do not hardcode arbitrary rules. See `04_RESEARCH/Patterns/` for currently hypothesized rules.
