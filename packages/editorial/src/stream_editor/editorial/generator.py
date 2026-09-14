"""
CandidateGenerator: orchestrates the full M3 candidate generation pipeline.

Pipeline:
  M2 Evidence
    -> EventClusterer
    -> CandidateWindowBuilder
    -> ContextExpander
    -> CandidateMerger
    -> (for each merged window)
       -> LocalFeatureExtractor
       -> ModelResultCache lookup
       -> EditorialAnalysisProvider.analyze_candidate
       -> RepetitionDetector
       -> ExperimentalRanker
       -> CandidateSegment + CandidateEvidenceLink persist
  -> CandidateRun.status = completed

All operations are idempotent: if a CandidateRun with the same
derivation_signature already exists and is completed, return it immediately.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime

from stream_editor.contracts.editorial import (
    RANKING_PROFILES,
    CandidateWindowConfig,
    EditorialAnalysisProvider,
    LocalFeatures,
    ScoreComponents,
)
from stream_editor.editorial.cache import ModelResultCache
from stream_editor.editorial.context import ContextExpander, SceneData, TranscriptSegmentData
from stream_editor.editorial.features import LocalFeatureExtractor
from stream_editor.editorial.merging import CandidateMerger
from stream_editor.editorial.ranking import ExperimentalRanker
from stream_editor.editorial.repetition import RepetitionDetector
from stream_editor.editorial.windowing import CandidateWindowBuilder, EventClusterer

GENERATOR_VERSION = "1.0.0"
EDITORIAL_RULES_VERSION = "1.2"   # matches KEEP_VS_CUT.md version
FLASH_CONFIDENCE_THRESHOLD = 0.55  # below this -> mark as eligible for escalation


def _candidate_sig(
    project_id: str,
    source_asset_id: str,
    start_time: float,
    end_time: float,
    core_start: float,
    core_end: float,
    generator_version: str,
) -> str:
    data = {
        "project_id": project_id,
        "source_asset_id": source_asset_id,
        "start_time": round(start_time, 3),
        "end_time": round(end_time, 3),
        "core_start": round(core_start, 3),
        "core_end": round(core_end, 3),
        "generator_version": generator_version,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _run_sig(
    project_id: str,
    source_asset_id: str,
    config: CandidateWindowConfig,
    provider_name: str,
    prompt_version: str,
    ranking_profile_name: str,
) -> str:
    data = {
        "project_id": project_id,
        "source_asset_id": source_asset_id,
        "config": config.model_dump(),
        "provider": provider_name,
        "prompt_version": prompt_version,
        "ranking_profile": ranking_profile_name,
        "generator_version": GENERATOR_VERSION,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class CandidateGenerator:
    """Full M3 candidate generation pipeline."""

    def generate(
        self,
        project_id: str,
        source_asset_id: str,
        db: object,   # synchronous SQLAlchemy Session
        provider: EditorialAnalysisProvider,
        config: CandidateWindowConfig | None = None,
        prompt_version: str = "v1",
        ranking_profile_name: str = "balanced",
        provider_name: str = "mock",
    ) -> str:
        """
        Run the full candidate generation pipeline.

        Returns:
            run_id: The CandidateRun ID.
        """
        from stream_editor.api.models.project import (
            CandidateEvidenceLink,
            CandidateRun,
        )
        from stream_editor.api.models.project import (
            CandidateSegment as DBCandidate,
        )

        if config is None:
            config = CandidateWindowConfig()

        ranking_profile = RANKING_PROFILES.get(ranking_profile_name, RANKING_PROFILES["balanced"])
        run_sig = _run_sig(project_id, source_asset_id, config, provider_name, prompt_version, ranking_profile_name)

        # Idempotency check
        existing_run = (
            db.query(CandidateRun)  # type: ignore[attr-defined]
            .filter(CandidateRun.derivation_signature == run_sig)
            .first()
        )
        if existing_run and existing_run.status == "completed":
            return str(existing_run.id)

        # Create or reuse run record
        if not existing_run:
            run = CandidateRun(
                id=str(uuid.uuid4()),
                project_id=project_id,
                source_asset_id=source_asset_id,
                analysis_versions={},
                provider=provider_name,
                generator_version=GENERATOR_VERSION,
                candidate_config=config.model_dump(),
                prompt_version=prompt_version,
                derivation_signature=run_sig,
                status="running",
                created_at=datetime.utcnow(),
            )
            db.add(run)  # type: ignore[attr-defined]
            db.commit()  # type: ignore[attr-defined]
        else:
            run = existing_run
            run.status = "running"
            db.commit()  # type: ignore[attr-defined]

        try:
            run_id = str(run.id)

            # Load M2 evidence from DB
            from stream_editor.api.models.project import (
                Scene as DBScene,
            )
            from stream_editor.api.models.project import (
                TimelineEvent as DBTimelineEvent,
            )
            from stream_editor.api.models.project import (
                TranscriptRun,
            )
            from stream_editor.api.models.project import (
                TranscriptSegment as DBTranscriptSeg,
            )

            timeline_events_db = (
                db.query(DBTimelineEvent)  # type: ignore[attr-defined]
                .filter(DBTimelineEvent.source_asset_id == source_asset_id)
                .all()
            )
            timeline_events = [
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "start_time": e.start_time,
                    "end_time": e.end_time,
                    "data": e.data or {},
                }
                for e in timeline_events_db
            ]

            transcript_run = (
                db.query(TranscriptRun)  # type: ignore[attr-defined]
                .filter(TranscriptRun.source_asset_id == source_asset_id)
                .order_by(TranscriptRun.created_at.desc())
                .first()
            )
            transcript_segments: list[TranscriptSegmentData] = []
            if transcript_run:
                segs_db = (
                    db.query(DBTranscriptSeg)  # type: ignore[attr-defined]
                    .filter(DBTranscriptSeg.transcript_run_id == transcript_run.id)
                    .order_by(DBTranscriptSeg.start_time)
                    .all()
                )
                transcript_segments = [
                    TranscriptSegmentData(
                        id=str(s.id),
                        start_time=s.start_time,
                        end_time=s.end_time,
                        text=s.text,
                        speaker=s.speaker,
                    )
                    for s in segs_db
                ]

            scenes_db = (
                db.query(DBScene)  # type: ignore[attr-defined]
                .filter(DBScene.source_asset_id == source_asset_id)
                .all()
            )
            scenes = [SceneData(id=str(s.id), start_time=s.start_time, end_time=s.end_time) for s in scenes_db]

            # Pipeline: cluster -> window -> expand -> merge
            clusterer = EventClusterer()
            builder = CandidateWindowBuilder()
            expander = ContextExpander()
            merger = CandidateMerger()
            feat_extractor = LocalFeatureExtractor()
            rep_detector = RepetitionDetector()
            ranker = ExperimentalRanker()
            cache = ModelResultCache()

            clusters = clusterer.cluster(timeline_events, config.merge_gap)
            raw_windows = builder.build(clusters, config)
            expanded = [expander.expand(w, transcript_segments, scenes, config) for w in raw_windows]
            merged_windows = merger.merge(expanded, config.overlap_threshold)

            all_texts: list[str] = []  # for repetition scoring
            candidate_count = 0

            for mw in merged_windows:
                deriv_sig = _candidate_sig(
                    project_id, source_asset_id,
                    mw.start_time, mw.end_time,
                    mw.core_start, mw.core_end,
                    GENERATOR_VERSION,
                )

                # Idempotency: skip if already exists
                existing = (
                    db.query(DBCandidate)  # type: ignore[attr-defined]
                    .filter(DBCandidate.derivation_signature == deriv_sig)
                    .first()
                )
                if existing and existing.status in ("analyzed", "pending"):
                    candidate_count += 1
                    continue

                # Transcript excerpt for this window
                window_segs = [
                    s for s in transcript_segments
                    if s.end_time > mw.core_start and s.start_time < mw.core_end
                ]
                transcript_excerpt = " ".join(s.text for s in window_segs)

                # Local features
                surrounding_texts = all_texts[-3:] if all_texts else []
                features = feat_extractor.extract(
                    segments=transcript_segments,
                    events=timeline_events,
                    scenes=scenes,
                    start_time=mw.start_time,
                    end_time=mw.end_time,
                    surrounding_texts=surrounding_texts,
                )

                # Nearby events for context
                nearby_events = [
                    e for e in timeline_events
                    if float(str(e.get("end_time", 0))) > mw.start_time - 30
                    and float(str(e.get("start_time", 0))) < mw.end_time + 30
                ]

                # Cache key input
                cache_input = {
                    "transcript_excerpt": transcript_excerpt[:2000],
                    "features": features.model_dump(),
                    "nearby_events": nearby_events[:10],
                }
                candidate_id = str(uuid.uuid4())

                def _compute_analysis(
                    _te: str = transcript_excerpt,
                    _feats: LocalFeatures = features,
                    _ne: list[dict[str, object]] = nearby_events,
                    _cid: str = candidate_id,
                ) -> dict[str, object]:
                    result = provider.analyze_candidate(
                        candidate_id=_cid,
                        transcript_excerpt=_te,
                        local_features=_feats,
                        nearby_events=_ne,
                        local_summary=None,
                        chapter_summary=None,
                        prompt_version=prompt_version,
                    )
                    return result.model_dump()

                raw_result, hit = cache.get_or_set(
                    db=db,
                    provider=provider_name,
                    model="mock" if provider_name == "mock" else "gemini-2.0-flash",
                    prompt_version=prompt_version,
                    editorial_rules_version=EDITORIAL_RULES_VERSION,
                    input_payload=cache_input,
                    compute_fn=_compute_analysis,
                )

                # Unpack result
                signals_raw = raw_result.get("signals", {})
                if isinstance(signals_raw, dict):
                    signals = ScoreComponents(**{
                        k: v for k, v in signals_raw.items()
                        if k in ScoreComponents.model_fields
                    })
                else:
                    signals = ScoreComponents()

                confidence = float(str(raw_result.get("confidence", 0.5)))

                # Repetition score
                repetition_score = rep_detector.score(transcript_excerpt, all_texts)
                if signals.repetition is None:
                    signals = signals.model_copy(update={"repetition": repetition_score})

                # Visual interest from scene_change_rate
                if signals.visual_interest is None and features.scene_change_rate is not None:
                    # Normalize: >2 changes/min = high, 0 = none. Clamp to [0,1]
                    vi = min(1.0, (features.scene_change_rate or 0.0) / 2.0)
                    signals = signals.model_copy(update={"visual_interest": round(vi, 4)})

                # Experimental rank
                exp_rank = ranker.rank(signals, ranking_profile)

                # Escalation: mark as eligible if confidence below threshold
                escalated = "eligible" if confidence < FLASH_CONFIDENCE_THRESHOLD else None

                # Debug label (NOT canonical)
                if confidence >= 0.70:
                    debug_label = "interesting"
                elif confidence >= 0.40:
                    debug_label = "uncertain"
                else:
                    debug_label = "low-signal"

                cand = DBCandidate(
                    id=candidate_id,
                    run_id=run_id,
                    project_id=project_id,
                    source_asset_id=source_asset_id,
                    core_start=mw.core_start,
                    core_end=mw.core_end,
                    start_time=mw.start_time,
                    end_time=mw.end_time,
                    source_signals=mw.source_signals,
                    transcript_excerpt=transcript_excerpt[:1000] or None,
                    summary=str(raw_result.get("summary", ""))[:500] or None,
                    local_features=features.model_dump(),
                    score_humor=signals.humor,
                    score_reaction=signals.reaction,
                    score_importance=signals.importance,
                    score_visual_interest=signals.visual_interest,
                    score_chat_relevance=signals.chat_relevance,
                    score_novelty=signals.novelty,
                    score_emotional_intensity=signals.emotional_intensity,
                    score_story_value=signals.story_value,
                    score_repetition=signals.repetition,
                    confidence=confidence,
                    reasoning_summary=list(raw_result.get("reasoning_summary", [])),
                    experimental_rank=exp_rank,
                    ranking_profile=ranking_profile_name,
                    analysis_provider=provider_name,
                    analysis_model="mock" if provider_name == "mock" else "gemini-2.0-flash",
                    prompt_version=prompt_version,
                    semantic_cache_hit="hit" if hit else "miss",
                    input_tokens=raw_result.get("input_tokens"),
                    output_tokens=raw_result.get("output_tokens"),
                    analysis_latency_ms=raw_result.get("latency_ms"),
                    escalated=escalated,
                    debug_label=debug_label,
                    derivation_signature=deriv_sig,
                    status="analyzed",
                    created_at=datetime.utcnow(),
                )
                db.add(cand)  # type: ignore[attr-defined]
                db.flush()  # type: ignore[attr-defined]

                # Evidence links
                for eid in mw.evidence_ids:
                    link = CandidateEvidenceLink(
                        id=str(uuid.uuid4()),
                        candidate_id=candidate_id,
                        evidence_type="timeline_event",
                        evidence_id=eid,
                    )
                    db.add(link)  # type: ignore[attr-defined]

                all_texts.append(transcript_excerpt)
                candidate_count += 1

            db.commit()  # type: ignore[attr-defined]

            run.status = "completed"
            run.candidate_count = candidate_count
            run.completed_at = datetime.utcnow()
            db.commit()  # type: ignore[attr-defined]

        except Exception as err:
            run.status = "failed"
            run.error_message = str(err)[:500]
            db.commit()  # type: ignore[attr-defined]
            raise

        return run_id
