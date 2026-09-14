---
id: RES-PAT-001
title: Hypothesized Keep/Cut Rules
status: research
version: 1.0
last_reviewed: 2026-09-14
tags:
  - research
  - hypothesis
  - editorial
---

# Hypothesized Keep/Cut Rules

This document tracks specific editorial hypotheses that were proposed during early implementation but have NOT yet been empirically validated through EditDNA research. These are **unsupported assumptions** and should not be treated as canonical rules.

## Hypothesized "Mandatory Keeps"
- **Lore Establishment**: Keep the first occurrence of a running joke, phrase, or "character". (Hypothesis: Required for callbacks to land).
- **High Emotion Peaks**: Genuine rage, triumph, sadness, or extreme laughter.
- **Consequential Action**: Boss defeated, major plot point, high-stakes decision.
- **Direct Chat Engagement**: Streamer explicitly reads a chat message and responds with a strong opinion/joke.
- **Unexpected Failures**: Glitches, in-game deaths, hardware fails with entertaining reactions.

## Hypothesized "Mandatory Cuts"
- **Low-Energy Chat Reading**: Monotone reading of donations/subs with standard "thank you". (Hypothesis: Harms retention, should be cut mercilessly).
- **Menu Navigation**: Staring at settings or inventory for >10s.
- **AFK / BRB Periods**: Cut if >15s without game action (unless chat is doing something hilarious on screen).
- **Technical Troubleshooting**: Cut unless the streamer goes on a hilarious rant.
- **Repetitive Grinding**: Doing exact same action >3 times (Hypothesis: Should be a montage, not raw cuts).
- **Stream Intros/Outros**: "Starting soon" screen and long goodbyes.

## Hypothesized Scoring Weights
The following formula was proposed for generating `CandidateSegment` scores (`story_value`), but must remain configurable/experimental, NOT canonical:
- `reaction` (30%)
- `humor` (25%)
- `importance` (25%)
- `visual_interest` (10%)
- `chat_relevance` (10%)

## Hypothesized Transformations (The "Gray Area")
- **The Long Walk (Travel Time)**: Do not cut audio, apply B-Roll or a `speed_ramp` (e.g., 200% speed) to the visual layer.
- **The Failed Setup**: Show 1st failure, cut middle failures, show last failure briefly (maybe with `grayscale`), show success in full.
- **The Tangent**: If funny, keep start and punchline, cut middle, use zoom effect.

## Hypothesized Pacing Thresholds
- **Average clip duration:** 15-45 seconds.
- **Maximum uninterrupted silence:** 3 seconds.
- **Speed-up Factor:** 200-400% for boring but necessary progression.
