---
id: ARCH-EDITORIAL-001
title: Editorial Pipeline
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - architecture
  - editorial
---

# Editorial Pipeline

1. **Candidates:** Generate CandidateSegments from TimelineEvents.
2. **Scoring:** Assign multidimensional scores to candidates.
3. **Story Graph:** Build narrative dependencies (setup -> payoff).
4. **EditPlan Generation:** Editor Agent produces an EditPlan.
5. **Critic:** Critic Agent reviews the plan and refines it.
6. **Versioning:** The validated EditPlan is versioned and saved.
