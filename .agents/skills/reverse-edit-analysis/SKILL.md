---
name: reverse-edit-analysis
description: Compares an original source VOD with an editor's derivative output to reconstruct editorial decisions and extract measurable EditDNA patterns.
version: 1.0
applies_to: knowledge-vault/04_RESEARCH/
---

# Skill: reverse-edit-analysis

## Purpose

Given a raw VOD (source) and an edited derivative (output), reconstruct what the editor decided:
- What was kept and what was cut?
- Where were visual transformations applied (zoom, crop, color)?
- What was the editorial rhythm?

This is the most direct path to understanding a creator's EditDNA.

## Prerequisites

- Both source VOD and edited output are available
- Analysis proxies have been generated (1280px width, use video-analysis skill)
- Transcriptions of both files are available or will be generated

## Step-by-Step Process

### 1. Transcribe both files

Transcribe source VOD and edited output independently.
Use Whisper or equivalent — store results as structured TimestampedTranscript:

```
source_transcript.json:
  segments: [{start, end, text, confidence}, ...]

edit_transcript.json:
  segments: [{start, end, text, confidence}, ...]
```

Each segment: start and end in seconds (float), text as string.

### 2. Align transcripts

Use fuzzy string matching to align segments between source and edit:

1. Tokenize both transcripts at the word level
2. Use sequence alignment (Smith-Waterman or similar) to find matching regions
3. Build an alignment map: `{edit_segment_id: source_segment_id | None}`
4. Segments in edit with no source match are either: synthetic content, title cards, or re-recordings
5. Record alignment confidence per segment

Tools to use: `difflib.SequenceMatcher` (Python stdlib) is acceptable for initial alignment. Document the method used.

### 3. Identify retained vs removed sections

From the alignment:

**Retained sections** — present in both edit and source:
- Record: source_start, source_end, edit_start, edit_end, duration_source, duration_edit
- Check if duration differs (could indicate speed change)
- Check if segment is contiguous with previous retained section or has a gap (= cut point)

**Removed sections** — in source but not in edit:
- Record: source_start, source_end, duration, content_summary (first 50 chars of text)
- Tag with probable reason if obvious: silence, off-topic, repetition, setup-without-payoff

**Compute:**
```
retention_rate = sum(retained_durations) / source_duration
cut_count = number of distinct gaps between retained sections
avg_clip_duration = sum(retained_durations) / cut_count
```

### 4. Analyze visual transformations

For each retained section, compare frames between source and edit:

1. Sample one frame per retained section (at midpoint)
2. Compare aspect ratio: same or different?
3. If cropped: estimate crop region. Is the subject still centered? Was it zoomed?
4. Estimate zoom factor: output_height / source_height (if same subject fills more frame = zoom in)
5. Analyze color: compute mean HSV per frame. Difference indicates color grading.

Mark uncertain transformations as `unknown` — never invent a transformation. Better to have an honest gap than a wrong inference.

### 5. Identify context around notable events

For cuts at significant moments (high energy, punchline, dramatic beat):

- Record what came 5-10 seconds BEFORE the cut in source (the setup)
- Record what came 5-10 seconds AFTER the cut point (the recovery)
- Did the editor cut before the event, during it, or after?
- This reveals the editor's "breath" timing

### 6. Store results as structured ResearchFindings

Create a reverse-edit session document:

```yaml
---
id: reverse-edit-CREATOR-YYYY-MM-DD
title: "Reverse Edit Analysis: [Creator] — [Video]"
status: research
created: YYYY-MM-DD
creator: creator-slug
source_duration_s: 7200
edit_duration_s: 1847
retention_rate: 0.257
cut_count: 312
avg_clip_duration_s: 5.9
---
```

Then document each finding using the reference-research skill structure.

### 7. Uncertainty rules

- If you cannot determine whether a transformation happened: mark as `unknown`
- If alignment confidence < 0.7 for a segment: mark as `uncertain`
- If a cut reason is ambiguous: list the top 2 candidates, do not pick one
- Never write "the editor chose X because Y" — write "the edit shows X; a likely reason is Y (confidence: low/medium/high)"

## Common Pitfalls

| Pitfall | Correct approach |
|---------|-----------------|
| Re-recording misidentified as cut | Check if text differs significantly — may be a re-take |
| Music causing transcription errors | Use separate audio track analysis for music sections |
| Speed ramping confused with cut | Compare total word count in segment, not just timestamps |
| Assuming reason for cut | Document as `reason: unknown` if not clear |

## Output Checklist

- [ ] Both transcripts generated and saved
- [ ] Alignment map computed and confidence recorded
- [ ] Retention rate, cut count, avg clip duration calculated
- [ ] Visual transformation analysis complete (mark unknowns honestly)
- [ ] ResearchFindings document created with proper frontmatter
- [ ] No findings promoted to canonical
- [ ] `scripts/check_vault.py` passes