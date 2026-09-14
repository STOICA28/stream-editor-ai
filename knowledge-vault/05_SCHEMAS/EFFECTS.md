---
id: SCHEMA-EFFECTS-001
title: Effects Schema
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - schema
---

# Effects Schema

**Description:** The enumerated EffectAPI.

**Legal Effects:**
`cut, zoom_region, zoom_face, zoom_chat, crop, grayscale, freeze_frame, slow_motion, speed_up, text_overlay, subtitle, image_overlay, audio_gain, audio_duck, fade, blur, highlight_region`

Each effect must strictly type-check against its defined constraints (ranges, overlaps).
