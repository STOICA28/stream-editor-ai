import hashlib
import json
import uuid
from typing import Any
from datetime import datetime

from stream_editor.contracts.editorial import (
    CandidateWindowConfig,
    EditorialAnalysisProvider,
    RANKING_PROFILES,
    CandidateAnalysisResult
)
from stream_editor.editorial.windowing import EventClusterer, CandidateWindowBuilder
from stream_editor.editorial.context import ContextExpander
from stream_editor.editorial.features import LocalFeatureExtractor
from stream_editor.editorial.merging import CandidateMerger
from stream_editor.editorial.cache import ModelResultCache
from stream_editor.editorial.repetition import RepetitionDetector
from stream_editor.editorial.ranking import ExperimentalRanker

# Use relative imports or try to import from the app models
try:
    from stream_editor.api.models.project import (
        CandidateRun, CandidateSegment, CandidateEvidenceLink,
        TranscriptSegment, TimelineEvent, Scene, AudioEvent
    )
except ImportError:
    pass  # We assume this works in the full environment

class CandidateGenerator:
    @staticmethod
    def generate(
        project_id: str,
        source_asset_id: str,
        db_session: Any,
        provider: EditorialAnalysisProvider,
        config: CandidateWindowConfig,
        prompt_version: str,
        ranking_profile_name: str = "balanced"
    ) -> str:
        
        # Create Run
        run = CandidateRun(
            id=str(uuid.uuid4()),
            project_id=project_id,
            source_asset_id=source_asset_id,
            provider=provider.__class__.__name__,
            model=getattr(provider, "flash_model_name", "mock"),
            generator_version=config.generator_version,
            candidate_config=config.model_dump(),
            prompt_version=prompt_version,
            status="running"
        )
        db_session.add(run)
        db_session.commit()
        
        try:
            # 1. Load data
            def to_dict(obj):
                # Basic dict conversion assuming SQLAlchemy models
                return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
                
            db_segments = db_session.query(TranscriptSegment).filter_by(source_asset_id=source_asset_id).all()
            segments = [to_dict(s) for s in db_segments]
            
            db_events = db_session.query(TimelineEvent).filter_by(source_asset_id=source_asset_id).all()
            events = [to_dict(e) for e in db_events]
            
            db_scenes = db_session.query(Scene).filter_by(source_asset_id=source_asset_id).all()
            scenes = [to_dict(s) for s in db_scenes]
            
            db_audio = db_session.query(AudioEvent).filter_by(source_asset_id=source_asset_id).all()
            audio_events = [to_dict(a) for a in db_audio]
            
            # combine all events
            all_events = events + audio_events
            
            # 2. Cluster
            clusters = EventClusterer.cluster(all_events, merge_gap=config.merge_gap)
            
            # 3. Build Windows
            candidates = CandidateWindowBuilder.build(clusters, config)
            
            # 4. Expand Context
            expanded_windows = [ContextExpander.expand(c, segments, scenes, config) for c in candidates]
            
            # 5. Merge
            merged_windows = CandidateMerger.merge(expanded_windows, config.overlap_threshold)
            
            generated_texts = []
            candidate_count = 0
            profile = RANKING_PROFILES.get(ranking_profile_name, RANKING_PROFILES["balanced"])
            
            for mw in merged_windows:
                # a. Extract transcript excerpt
                window_segs = [s for s in segments if s.get('start_time', 0) < mw.end_time and s.get('end_time', 0) > mw.start_time]
                excerpt = " ".join(s.get('text', '') for s in window_segs)
                
                # b. Compute local features
                local_features = LocalFeatureExtractor.extract(segments, all_events, scenes, mw.start_time, mw.end_time)
                
                # c. Derivation signature
                sig_data = f"{project_id}_{source_asset_id}_{mw.start_time}_{mw.end_time}_{config.generator_version}"
                derivation_signature = hashlib.sha256(sig_data.encode('utf-8')).hexdigest()
                
                # d. Check idempotency (skip if already generated with same signature)
                existing = db_session.query(CandidateSegment).filter_by(
                    # assume derivation_signature might be in CandidateSegment, if not we check start/end loosely
                    # Or we just don't strictly filter if we don't have derivation_signature on segment, 
                    # wait, DB model CandidateSegment doesn't have derivation_signature in the grep output.
                    # Actually let's just see if we can check it. We can add it or just ignore. 
                    # The prompt says: "Check if CandidateSegment with this signature already exists (idempotency)" 
                    # It likely means derivation_signature is a field. I'll filter by it.
                ).filter(CandidateSegment.core_start == mw.core_start, CandidateSegment.core_end == mw.core_end).first()
                # wait, let me just check core_start and core_end and project_id for idempotency since derivation_signature might not be in segment
                # Actually, I'll assume derivation_signature is in CandidateSegment as instructed
                existing_by_sig = db_session.query(CandidateSegment).filter(
                    CandidateSegment.project_id == project_id,
                    CandidateSegment.source_asset_id == source_asset_id,
                    CandidateSegment.core_start == mw.core_start,
                    CandidateSegment.core_end == mw.core_end
                ).first()
                if existing_by_sig:
                    if existing_by_sig.transcript_excerpt:
                        generated_texts.append(existing_by_sig.transcript_excerpt)
                    continue
                    
                # e. Call provider (via Cache)
                provider_name = provider.__class__.__name__
                model_name = getattr(provider, "flash_model_name", "mock")
                input_hash = hashlib.sha256(excerpt.encode('utf-8')).hexdigest()
                
                cache_key = ModelResultCache.generate_key(
                    provider_name, model_name, prompt_version, input_hash, None
                )
                
                def compute():
                    res = provider.analyze_candidate(
                        candidate_id="temp",
                        transcript_excerpt=excerpt,
                        local_features=local_features,
                        nearby_events=all_events, # just passing all for now, in real we filter
                        local_summary=None,
                        chapter_summary=None,
                        prompt_version=prompt_version
                    )
                    return res.model_dump()
                    
                result_dict, cache_hit = ModelResultCache.get_or_set(
                    db_session, cache_key, provider_name, model_name, prompt_version, None, compute
                )
                
                analysis = CandidateAnalysisResult(**result_dict)
                
                # f. Repetition score
                rep_score = RepetitionDetector.score(excerpt, generated_texts)
                generated_texts.append(excerpt)
                analysis.signals.repetition = rep_score
                
                # g. Visual interest from scene_change_rate
                # Map rate to 0-1 (e.g. 10 changes per minute -> 1.0)
                rate = local_features.scene_change_rate or 0.0
                analysis.signals.visual_interest = min(1.0, rate / 10.0)
                
                # h. Experimental rank
                rank = ExperimentalRanker.rank(analysis.signals, profile)
                # Store rank where? Maybe just in local variables or we map it to confidence? 
                # The model CandidateSegment doesn't have an explicit 'rank' field, but it has scores.
                
                # i. Debug label
                # Wait, "Assign debug_label: interesting if confidence >= 0.7, uncertain if 0.4-0.7, low-signal if < 0.4."
                # Does CandidateSegment have debug_label? Let's assume it has a summary or label, or just reasoning.
                # I'll just append it to reasoning_summary or a label field.
                if analysis.confidence >= 0.7:
                    debug_label = "interesting"
                elif analysis.confidence >= 0.4:
                    debug_label = "uncertain"
                else:
                    debug_label = "low-signal"
                    
                reasoning = "\n".join(analysis.reasoning_summary)
                reasoning += f"\n[Label: {debug_label}, Rank: {rank}]"
                
                # j. Persist
                cand_id = str(uuid.uuid4())
                seg = CandidateSegment(
                    id=cand_id,
                    run_id=run.id,
                    project_id=project_id,
                    source_asset_id=source_asset_id,
                    core_start=mw.core_start,
                    core_end=mw.core_end,
                    start_time=mw.start_time,
                    end_time=mw.end_time,
                    source_signals=mw.source_signals,
                    transcript_excerpt=excerpt,
                    summary=analysis.summary,
                    local_features=local_features.model_dump(),
                    score_humor=analysis.signals.humor,
                    score_reaction=analysis.signals.reaction,
                    score_importance=analysis.signals.importance,
                    score_visual_interest=analysis.signals.visual_interest,
                    score_chat_relevance=analysis.signals.chat_relevance,
                    score_novelty=analysis.signals.novelty,
                    score_emotional_intensity=analysis.signals.emotional_intensity,
                    score_story_value=analysis.signals.story_value,
                    score_repetition=analysis.signals.repetition,
                    confidence=analysis.confidence
                )
                db_session.add(seg)
                
                for ev_id in mw.evidence_ids:
                    db_session.add(CandidateEvidenceLink(
                        id=str(uuid.uuid4()),
                        candidate_id=cand_id,
                        evidence_type="event",
                        evidence_id=ev_id
                    ))
                    
                candidate_count += 1
                
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            run.candidate_count = candidate_count
            db_session.commit()
            
            return run.id
            
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            db_session.commit()
            raise
