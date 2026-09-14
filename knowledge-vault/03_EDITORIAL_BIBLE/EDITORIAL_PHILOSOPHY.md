---
id: ED-PHIL-001
title: Editorial Philosophy
status: canonical
version: 1.1
last_reviewed: 2026-09-14
tags:
  - editorial
  - philosophy
  - canonical
---

# Editorial Philosophy

> "The target is not 'find the loudest or funniest clips.' The target is 'reconstruct the experience of watching the livestream while removing dead time and enhancing moments where editorial attention improves understanding or comedy.'"

## The Central Principle

StreamEditor AI is a **narrative reconstruction tool**, not a highlight reel generator.

The output of a good edit should feel like the viewer watched the whole stream, but in concentrated form. Someone watching the final video should understand:

- Who the streamer is and how they react
- What happened in the session (story arc, not just moments)
- Why specific moments were funny or significant — not just *that* they were

A string of the top-10 funniest isolated clips is **fatiguing and disorienting**. Narrative context is what makes moments land.

## What We Preserve

| Category | Examples |
|----------|---------|
| **Narrative context** | Setup before a joke, explanation before a complex event |
| **Personality** | Streamer's characteristic reactions, speech patterns, catchphrases |
| **Relationships** | Streamer reading/reacting to chat, recurring in-jokes |
| **Setups and payoffs** | A bet made at 01:12 that resolves at 04:45 |
| **Running jokes** | A callback only works if the original joke was kept |
| **Emotional transitions** | Don't cut from intense grief to instant comedy without breath |
| **Surprising visual details** | A background event the streamer doesn't notice but chat does |
| **Meaningful chat** | When the streamer reads a chat message and it changes the moment |

## What We Remove

| Category | Rationale |
|----------|-----------|
| **Dead air** | Silence >30s with no event, no viewer value |
| **AFK periods** | "brb" through return, unless reaction to something is funny |
| **Stream setup/teardown** | Device checks, game loading, OBS configuration |
| **Repetitive content** | If the same type of event happened 8 times, keep the 2 best |
| **Technical failures** | Unless the streamer's reaction to them is the moment |
| **Filler transitions** | "anyway..." → long silence → opens Discord → checks settings |

## The Effect Principle

Effects (zooms, grayscale, text overlays, freeze frames) **serve the content — they do not create it**.

- A zoom on a face should reveal genuine emotion, not manufacture it.
- Grayscale should mark a meaningful low point, not be used for aesthetics.
- A freeze frame should give the viewer time to process something surprising.
- Do not stack effects. One effect at a time unless there is a clear reason.

**The test:** If you removed the effect and the moment was still good, the effect was optional. If the moment required the effect to be understood, the effect had purpose.

## Editorial Judgment Hierarchy

When in conflict, apply this priority order:

1. **Narrative integrity** — Does this cut break a story dependency?
2. **Emotional continuity** — Does this transition feel wrong tonally?
3. **Humor preservation** — Does this setup → payoff chain remain intact?
4. **Pacing** — Is the overall flow comfortable to watch?
5. **Duration** — Shorter is not always better; length serves the story.

## The "Single Clips" Anti-Pattern

Avoid this failure mode: generating a set of individually high-scoring moments that have no relationship to each other. The Story Graph exists precisely to detect when moments form chains and to ensure those chains are honored.

If a moment scores highly in isolation but its setup was cut and its callback is missing, the editor must decide whether to:
- Include the setup (preferred)
- Omit the callback (if setup is too long)
- Keep neither (if the chain cannot be reconstructed)

Never keep a payoff and silently omit its setup.

## References

- [[KEEP_VS_CUT]] — Specific keep/cut rules
- [[CALLBACKS]] — Dependency chain rules
- [[STORYTELLING]] — Narrative arc principles
- [[HUMOR]] — Comedy-specific rules
- [[CONTEXT_POLICY]] — Minimum context windows
