---
id: ARCH-STORAGE-001
title: Storage
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - storage
---

# Storage

- **Abstraction:** `StorageProvider` (LocalStorageProvider currently).
- **Structure:**
  `data/projects/{project_id}/`
  - `source/`
  - `proxies/`
  - `audio/`
  - `transcripts/`
  - `frames/`
  - `analysis/`
  - `previews/`
  - `renders/`
- **Rule:** Never hardcode paths in the DB; use relative paths mapped by the StorageProvider.
