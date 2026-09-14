# Candidate Segment (M3)

The `CandidateSegment` is a temporal window of source media that has been identified as a potential highlight, scored against editorial dimensions, and persisted for human review or automated Story Graph assembly (M4).

## Definition

```python
class CandidateSegment:
    id: str
    run_id: str
    project_id: str
    source_asset_id: str

    # Core Boundaries
    core_start: float
    core_end: float

    # Expanded Boundaries (with pre/post-roll, snapped to utterances)
    start_time: float
    end_time: float

    source_signals: list[str]
    transcript_excerpt: str | None
    summary: str | None
    local_features: dict[str, Any]

    # Scores
    score_humor: float | None
    score_reaction: float | None
    score_importance: float | None
    score_visual_interest: float | None
    score_chat_relevance: float | None
    score_novelty: float | None
    score_emotional_intensity: float | None
    score_story_value: float | None
    score_repetition: float | None

    confidence: float
    reasoning_summary: list[str]

    experimental_rank: float | None
    ranking_profile: str
    debug_label: str

    escalated: str | None
```

## Generation Pipeline (M3)

The pipeline uses `CandidateGenerator` to build segments:

1. **Clustering:** Timeline events closer than `merge_gap` are clustered.
2. **Windowing:** Clusters become windows padded to `min_duration` and truncated to `max_duration`.
3. **Context Expansion:** Windows snap to utterance boundaries and add `preroll`/`postroll`.
4. **Merging:** Overlapping windows merge (using `overlap_threshold`).
5. **Local Features:** Non-LLM signal extraction (speech density, scene changes).
6. **Model Analysis:** Cached calls to Gemini/Mock evaluate the snippet against editorial scores.
7. **Repetition:** TF-IDF checks against prior candidates in the same run.
8. **Ranking & Persistence:** Calculates experimental rank, applies `debug_label` (purely diagnostic, not canonical), and persists.

## Idempotency and Caching

- `CandidateRun` is idempotent based on `derivation_signature`.
- Model outputs are heavily cached in `ModelResultCache` via SHA-256 of excerpt and prompts.
