---
id: ARCH-SYS-001
title: System Overview
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - system
---

# System Overview

StreamEditor AI is a monorepo containing multiple apps and packages.

## Components
- **Apps:** api, worker, web
- **Packages:** contracts, media, analysis, editorial, research, models, rendering, storage, vault
- **Renderers:** FFmpeg (core ops), Remotion (rich overlays)

```mermaid
graph TD
    UI[Web App UI] <--> API[API Server]
    API --> DB[(PostgreSQL)]
    API --> Queue[(Job Queue)]
    Worker[Worker App] <--> Queue
    Worker --> Packages[Core Packages]
    Packages --> Storage[(File Storage)]
    Packages --> Models[Model Provider]
```
