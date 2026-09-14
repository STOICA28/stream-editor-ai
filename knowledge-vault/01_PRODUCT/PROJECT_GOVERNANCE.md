---
id: GOV-001
title: Project Governance
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - governance
  - rules
---

# Project Governance

This document establishes the official governance structure and knowledge hierarchy for StreamEditor AI.

## Knowledge Hierarchy

From highest authority to lowest:

1. **Product Vision / Product Principles** (e.g., `01_PRODUCT/PRODUCT_VISION.md`, `01_PRODUCT/PRODUCT_PRINCIPLES.md`)
2. **Canonical Architecture + accepted ADRs** (e.g., `02_ARCHITECTURE/`, `07_ADR/`)
3. **Canonical Editorial Bible** (e.g., `03_EDITORIAL_BIBLE/`)
4. **Approved Research Findings** (e.g., `04_RESEARCH/Findings/`)
5. **Research** (e.g., `04_RESEARCH/Patterns/`)
6. **Proposals** (e.g., proposals in the inbox)
7. **Experiments**
8. **Inbox** (`99_INBOX/`)

## Promotion Rule

Research, hypotheses, and agent-generated editorial opinions can ONLY become canonical through an explicit promotion step by the user. 
A coding or research agent must NEVER silently convert its own inference, assumptions, or generated rules into a canonical production rule.

## Conflict Rule

If there is a conflict between the system:

1. **Code vs. Canonical Documentation:** If code conflicts with canonical documentation, treat the conflict as a bug in the code. The canonical documentation is the source of truth.
2. **Research vs. Canonical Documentation:** If research conflicts with canonical documentation, create a proposal/ADR to discuss the conflict rather than silently changing production behavior to match the research.
