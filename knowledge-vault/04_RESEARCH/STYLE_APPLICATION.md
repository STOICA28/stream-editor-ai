---
id: RES-STYLE-001
title: Style Application & EditDNA
status: canonical
version: 1.0
last_reviewed: 2026-09-17
tags:
  - research
  - m11
  - editdna
---

# Style Application

Research yields observations about external reference videos. For example, we may observe that an editor frequently zooms in on a face during moments of high audio intensity, or that they maintain a very fast pacing (many cuts per minute).

## Transition from Observation to Instruction
To use these observations:
1. They must be validated as abstract patterns, independent of the reference's literal context.
2. They are aggregated into a StyleProfile.
3. They must be compiled into an EditorialStylePolicy before they can affect production.

## Confidence and N (Sample Size)
A core rule of style application is weighting by evidence:
*   Observations with low N (e.g., a specific cut happened only twice) must have their influence drastically scaled down or omitted entirely.
*   Observations with high N and high confidence heavily influence the default priors of the automated editor.

## The TRANSFORMED_SOURCE Signal
When audio perfectly matches but visual alignment fails geometrically (due to zooms, memes, overlays, or color grading), the system flags the region as TRANSFORMED_SOURCE. 
*   **Inference**: This indicates an editorial visual action occurred.
*   **Application**: The policy can infer an increased "effect_density" prior, but MUST NOT blindly assign an effect (e.g., zoom_face) unless M7 (visual understanding) explicitly supports that a face exists and is the logical target of a zoom.
