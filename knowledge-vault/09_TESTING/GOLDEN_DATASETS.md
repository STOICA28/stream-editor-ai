---
id: TEST-GOLDEN-001
title: Golden Datasets
status: canonical
version: 1.0
last_reviewed: 2026-09-14
tags:
  - testing
---

# Golden Datasets

Golden datasets are hand-verified `TimelineEvent`, `CandidateSegment`, and `EditPlan` JSON files. 
They act as the ground truth for regression testing AI logic changes.
If an AI logic change produces an output different from the golden dataset, the test fails, and the developer must explicitly approve the new output if it is an improvement.
