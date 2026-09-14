---
id: ADR-001
title: Obsidian Vault as Project Source of Truth
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - adr
  - architecture
  - documentation
---

# ADR-001: Obsidian Vault as Project Source of Truth

**Status:** Accepted  
**Date:** 2026-09-14  
**Deciders:** Principal Architect

## Context

StreamEditor AI is a complex system with intricate editorial rules, a multi-stage AI pipeline, and strict security requirements. Development will span many sessions across different AI agents and human developers. Without a persistent, structured knowledge base, decisions made in session N are forgotten by session N+1, leading to:

- Repeated architectural debates
- Contradictory implementations
- Editorial rules that silently drift
- Agents making wrong assumptions about intended behavior

Standard code comments and a flat README are insufficient for a system of this complexity.

## Decision

The `knowledge-vault/` directory at the repository root is the **canonical source of truth** for:

- Product vision and principles
- System architecture decisions
- Editorial rules and philosophy
- Schema specifications
- Agent role definitions
- Operational runbooks
- Research findings (with explicit promotion workflow)

**If implementation and vault documentation disagree, treat the discrepancy as a bug.** The vault wins.

### Document Governance

All important vault documents use YAML frontmatter with:
- `id`: Unique document identifier (e.g., `ARCH-MEDIA-001`)
- `title`: Human-readable title
- `status`: One of `draft`, `research`, `proposal`, `canonical`, `deprecated`
- `version`: Monotonically increasing integer
- `last_reviewed`: ISO date

Only `canonical` documents automatically influence production system behavior.

### Promotion Workflow

```
Research agent generates finding
         â†“
   Research/Proposal status
         â†“
  Human reviews finding
         â†“
  Human explicitly promotes to canonical
         â†“
  Implementation updated to reflect rule
```

Research agents MUST NOT auto-promote findings to canonical.

### Validation

`scripts/check_vault.py` validates:
- Required canonical documents exist
- Frontmatter is present and valid
- Document IDs are unique
- Status values are in the allowed set

This runs in CI and as part of `make test-all`.

## Consequences

### Positive
- Any agent can resume work by reading `AGENTS.md` â†’ vault entry points
- Editorial rules are explicit, versioned, and auditable
- Research findings cannot silently change production behavior
- Architecture decisions have recorded rationale

### Negative
- Documentation maintenance overhead â€” each behavioral change requires a vault update
- Possible drift if agents fail to update docs (caught by check_vault.py)

### Mitigations
- `check_vault.py` runs in CI
- `AGENTS.md` explicitly requires vault updates after behavioral changes
- The Vault Curator agent skill monitors for drift

## References

- See [[AGENT_SYSTEM]] for agent vault update responsibilities
- See vault-curator skill for curation procedures
- `scripts/check_vault.py` for validation implementation
