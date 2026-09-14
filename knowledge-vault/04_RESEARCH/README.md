---
id: RES-README-001
title: Research System
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - research
---

# Research System

The Research System is responsible for analyzing human-edited reference videos to extract patterns (EditDNA) and improve the AI's editing rules.

## Evidence Hierarchy
1. **OBSERVATION:** "The editor cut the 5 seconds before the punchline."
2. **INFERENCE:** "The editor prefers tight pacing around jokes."
3. **HYPOTHESIS:** "If a clip contains a joke, pre-context should be < 2s."
4. **APPROVED RULE:** Promoted to the Editorial Bible by the Vault Curator.

## Process
Research findings are deposited in the `99_INBOX`. The Vault Curator reviews them. They are never promoted automatically.
