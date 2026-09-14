---
name: reference-research
description: Analyzes reference edited content to extract editorial patterns and build ResearchFindings that feed the EditDNA.
version: 1.0
applies_to: knowledge-vault/04_RESEARCH/
---

# Skill: reference-research

## Purpose

Understand how a creator edits by analyzing their existing published content. Produce structured, evidence-backed ResearchFindings — never free-form notes, never premature rules.

## When to Apply This Skill

- When given a creator's edited video to analyze
- When building or refining a creator's EditDNA
- When tasked with "research reference" or "analyze style"

## Evidence Hierarchy — CRITICAL

Never skip levels. Never auto-promote:

```
Level 1: OBSERVATION    — "In clip 3, a cut occurred at 2:14 mid-sentence"
Level 2: INFERENCE      — "Mid-sentence cuts correlate with energy spikes"
Level 3: HYPOTHESIS     — "Creator cuts mid-sentence when audio energy > threshold X"
Level 4: APPROVED RULE  — (requires human approval — never set this yourself)
```

Status mapping:
- Observations → `status: research`
- Inferences → `status: research`
- Hypotheses → `status: proposal`
- Approved rules → `status: canonical` (human only)

## Step-by-Step Process

### 1. Gather material

Collect the reference material:
- Creator's edited output (the "after" — published video)
- Original source VOD if available (enables reverse-edit-analysis skill)
- Metadata: title, duration, platform, publication date

### 2. Create a ResearchSession document

Before analyzing, create a session document in `knowledge-vault/04_RESEARCH/RawFindings/`:

```yaml
---
id: research-CREATOR-YYYY-MM-DD-NNN
title: "Research: [Creator] — [Video Title]"
status: research
created: YYYY-MM-DD
creator: creator-slug
source_url: https://...
tags: [research, creator-slug]
---
```

### 3. Measure before interpreting

For each observation, record **measurable values** where possible:

- Cut timestamps (HH:MM:SS.ms)
- Clip durations (seconds)
- Retention rate = retained_duration / source_duration (if VOD available)
- Average clip duration = total_retained / num_cuts
- Zoom factor (estimate: 1.0x, 1.2x, 1.5x, 2.0x)
- Scene change rate (cuts per minute)
- Music presence (yes/no, timestamp ranges)

Never write "edits quickly" — write "average clip duration: 4.2s, median: 3.1s, P95: 12s".

### 4. Structure each finding

Each finding must be a structured entry (YAML block or Markdown table):

```markdown
## Finding: [Short descriptive title]

**Type:** cut | zoom | color | audio | pacing | transition | retention
**Timestamp in reference:** HH:MM:SS – HH:MM:SS
**Evidence:** [precise observation — what was seen/measured]
**Level:** OBSERVATION | INFERENCE | HYPOTHESIS
**Confidence:** low | medium | high
**Notes:** [any caveats or ambiguities]
```

### 5. Separate observations from interpretations

In each finding, clearly separate:
- **Evidence** (what was measured/observed — objective)
- **Interpretation** (what you think it means — subjective)

Mark interpretations explicitly: "INTERPRETATION: This suggests..."

### 6. Aggregate into patterns

After collecting raw findings, create a pattern document in `knowledge-vault/04_RESEARCH/Patterns/`:

```yaml
---
id: pattern-CREATOR-short-name
title: "Pattern: [Creator] — [Pattern Name]"
status: proposal
created: YYYY-MM-DD
creator: creator-slug
evidence_count: N
supporting_findings: [research-CREATOR-..., ...]
tags: [pattern, creator-slug]
---
```

A pattern needs at minimum 3 supporting observations before it can be proposed.

### 7. NEVER do these things

- ❌ Create a canonical rule without human approval
- ❌ Write "always" or "never" based on a single observation
- ❌ Store findings as free-form prose without structure
- ❌ Assume a cut style applies globally from one segment
- ❌ Use a pattern as a production rule before it is canonical

## Output Checklist

Before completing a research session:

- [ ] ResearchSession document created with proper frontmatter
- [ ] All findings are structured (not free-form prose)
- [ ] Evidence separated from interpretation
- [ ] Measurable statistics calculated where possible
- [ ] No research findings promoted to canonical
- [ ] Pattern document created if 3+ supporting observations
- [ ] `scripts/check_vault.py` passes