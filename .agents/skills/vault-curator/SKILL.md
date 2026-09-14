---
name: vault-curator
description: Maintains the StreamEditor AI Obsidian knowledge vault integrity, consistency, and canonical status of all documents.
version: 1.0
applies_to: knowledge-vault/
---

# Skill: vault-curator

## Purpose

The vault is the single source of truth for StreamEditor AI. This skill ensures the vault remains internally consistent, properly structured, and free of conflicting specifications. Every agent session that touches vault documents should apply this skill before completing.

## When to Apply This Skill

- After adding or modifying any document in `knowledge-vault/`
- After a milestone completes (update status, changelog)
- When asked to "curate vault" or "validate vault"
- Before every commit that touches `knowledge-vault/`

## Step-by-Step Process

### 1. Run the automated checker first

```bash
uv run python scripts/check_vault.py
```

Fix all errors before proceeding. Warnings are advisory — review them.

### 2. Validate frontmatter on every document you touched

Every vault document MUST begin with YAML frontmatter:

```yaml
---
id: UNIQUE_SLUG
title: Human Readable Title
status: draft | research | proposal | canonical | deprecated
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
---
```

**Required fields:** `id`, `title`, `status`
**Optional but recommended:** `created`, `updated`, `tags`, `related`

Valid status values and their meanings:

| Status | Meaning |
|--------|---------|
| `draft` | Work in progress, may be incomplete or wrong |
| `research` | Observation or measurement, not yet validated |
| `proposal` | Structured proposal, awaiting review |
| `canonical` | Approved, affects production behavior |
| `deprecated` | No longer applies, kept for history |

### 3. Check for conflicting specifications

Search for documents that make contradictory claims:

1. Find all documents with `status: canonical`
2. For each canonical claim, verify no other canonical document contradicts it
3. If conflict found: demote one to `proposal` status and create an ADR to resolve
4. NEVER silently pick a winner — flag the conflict explicitly

Example conflict check: if `EDITORIAL_PHILOSOPHY.md` says "cuts must be at sentence boundaries" and `KEEP_VS_CUT.md` says "cuts may be mid-sentence for energy", that is a conflict requiring human resolution.

### 4. Verify ADRs exist for architectural changes

If code changes exist for features not covered by an ADR:

1. Check `knowledge-vault/07_ADR/` for relevant decisions
2. If no ADR: create one with `status: draft` and note it needs human review
3. ADR naming: `ADR-NNN-short-description.md` (next sequential number)

ADR template:
```yaml
---
id: ADR-NNN-slug
title: "ADR NNN: Decision Title"
status: draft
date: YYYY-MM-DD
---

# ADR NNN: Decision Title

## Context
What problem prompted this decision.

## Decision
What was decided.

## Consequences
What this means going forward. Trade-offs accepted.

## Alternatives Considered
What else was evaluated and why it was rejected.
```

### 5. Distinguish research from canonical rules

The vault has a strict evidence hierarchy. NEVER auto-promote findings:

```
OBSERVATION (what we saw, raw)
    ↓ manual review
INFERENCE (what we think it means)
    ↓ analysis + multiple observations
HYPOTHESIS (testable pattern, status: proposal)
    ↓ human approval only
APPROVED RULE (status: canonical, affects production)
```

- `04_RESEARCH/RawFindings/` — status must be `research`, never `canonical`
- `04_RESEARCH/Patterns/` — status must be `proposal` or `hypothesis`
- `03_EDITORIAL_BIBLE/` — status must be `canonical` (or `draft` for in-progress rules)

**Promoting a finding to canonical requires explicit human approval.**
If you see a research finding that looks like it should be canonical, create a promotion proposal document in `04_RESEARCH/Patterns/` and flag it for human review.

### 6. Maintain cross-document links

When you create or rename a document:

1. Search for `[[old-name]]` wikilinks throughout the vault
2. Update all references
3. Run `scripts/check_vault.py` to catch broken links (warns on broken wikilinks)

### 7. Update PROJECT_STATUS.md

Always end a vault curation session by updating:
- `00_HOME/PROJECT_STATUS.md` — current state, what was done, what remains
- `11_CHANGELOG/CHANGELOG.md` — what changed in this session

## Common Errors and Fixes

| Error | Fix |
|-------|-----|
| Missing frontmatter | Add `---` block with id, title, status |
| Invalid status value | Use only: draft, research, proposal, canonical, deprecated |
| Broken wikilink | Update link or create target document |
| Conflicting canonical docs | Demote one to proposal, create ADR |
| Research promoted to canonical | Demote back to proposal, flag for human review |

## Final Check

```bash
uv run python scripts/check_vault.py
# Must exit 0 before completing
```