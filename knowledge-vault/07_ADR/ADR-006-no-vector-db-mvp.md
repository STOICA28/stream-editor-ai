---
id: ADR-006
title: No Vector DB for MVP
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - adr
---

# ADR-006: No Vector DB for MVP

**Context:** Setting up Pinecone/Milvus adds infrastructure complexity.
**Decision:** No vector database for the MVP. We will use SQLite FTS5 for vault indexing and exact matching.
**Consequences:** Simpler stack to deploy. Semantic search will have to be added post-MVP.
