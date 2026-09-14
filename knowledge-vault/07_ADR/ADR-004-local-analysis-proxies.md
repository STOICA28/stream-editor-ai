---
id: ADR-004
title: Local Analysis Proxies
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - adr
---

# ADR-004: Local Analysis Proxies

**Context:** Running AI models on 1080p60fps 50mbps VODs is incredibly expensive and slow.
**Decision:** Generate low-res, low-bitrate analysis proxies locally before uploading to AI services.
**Consequences:** Adds initial processing time and local storage overhead, but drastically reduces cloud AI costs.
