from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import os

from stream_editor.api.models.project import (
    Base, Project, MediaAsset, TranscriptRun, CandidateRun, CandidateSegment,
    StoryGraphRun, StoryNode, StoryEdge, NarrativeThread,
    EditPlanRun, EditPlan, EditClip,
    VisualAnalysisRun, EffectPlanRun, EffectInstruction,
    RenderJob,
    Scene, AudioEvent, TimelineEvent
)
from stream_editor.api.models.style import StyleApplicationRun, StylePolicyVersion, EditorialStylePolicy

sqlite_engine = create_engine('sqlite:///test.db')
pg_engine = create_engine('postgresql://streameditor:streameditor@127.0.0.1:5432/streameditor')

# Ensure tables exist
Base.metadata.create_all(pg_engine)

with Session(sqlite_engine) as src, Session(pg_engine) as dst:
    # Clear existing to ensure clean representative state
    for model in [RenderJob, EffectInstruction, EffectPlanRun, VisualAnalysisRun,
                  EditClip, EditPlan, EditPlanRun,
                  StoryEdge, StoryNode, NarrativeThread, StoryGraphRun,
                  CandidateSegment, CandidateRun,
                  TimelineEvent, AudioEvent, Scene, TranscriptRun,
                  MediaAsset, StyleApplicationRun, StylePolicyVersion, EditorialStylePolicy, Project]:
        dst.query(model).delete()
    dst.commit()

    # 1. Projects
    for p in src.query(Project).filter(Project.id == 'real-5h-65655576').all():
        dst.merge(Project(
            id=p.id, name=p.name, status=p.status,
            source_video_path=p.source_video_path,
            created_at=p.created_at, updated_at=p.updated_at
        ))
    dst.commit()

    # 2. MediaAssets
    for m in src.query(MediaAsset).filter(MediaAsset.project_id == 'real-5h-65655576').all():
        dst.merge(MediaAsset(
            id=m.id, project_id=m.project_id, name=m.name, path=m.path,
            media_type=m.media_type, file_size_bytes=m.file_size_bytes,
            media_info=m.media_info, parent_asset_id=m.parent_asset_id,
            derivation_signature=m.derivation_signature,
            producer=m.producer, producer_version=m.producer_version,
            created_at=m.created_at
        ))
    dst.commit()

    # 3. TranscriptRuns
    for t in src.query(TranscriptRun).filter(TranscriptRun.project_id == 'real-5h-65655576').all():
        dst.merge(TranscriptRun(
            id=t.id, project_id=t.project_id, source_asset_id=t.source_asset_id,
            provider=t.provider, status=t.status, created_at=t.created_at
        ))
    dst.commit()

    # 4. Scenes, AudioEvents, TimelineEvents
    for sc in src.query(Scene).filter(Scene.project_id == 'real-5h-65655576').all():
        dst.merge(Scene(
            id=sc.id, project_id=sc.project_id, source_asset_id=sc.source_asset_id,
            start_time=sc.start_time, end_time=sc.end_time, duration=sc.duration,
            detector=sc.detector, detector_config=sc.detector_config,
            confidence=sc.confidence
        ))
    for a in src.query(AudioEvent).filter(AudioEvent.project_id == 'real-5h-65655576').all():
        dst.merge(AudioEvent(
            id=a.id, project_id=a.project_id, source_asset_id=a.source_asset_id,
            start_time=a.start_time, end_time=a.end_time, event_type=a.event_type,
            analyzer=a.analyzer, analyzer_config=a.analyzer_config
        ))
    for te in src.query(TimelineEvent).filter(TimelineEvent.project_id == 'real-5h-65655576').all():
        dst.merge(TimelineEvent(
            id=te.id, project_id=te.project_id, source_asset_id=te.source_asset_id,
            event_type=te.event_type, start_time=te.start_time, end_time=te.end_time,
            producer=te.producer, producer_version=te.producer_version,
            confidence=te.confidence, data=te.data
        ))
    dst.commit()

    # 5. CandidateRuns & Segments
    for cr in src.query(CandidateRun).filter(CandidateRun.project_id == 'real-5h-65655576').all():
        dst.merge(CandidateRun(
            id=cr.id, project_id=cr.project_id, source_asset_id=cr.source_asset_id,
            provider=cr.provider, status=cr.status, derivation_signature=cr.derivation_signature,
            created_at=cr.created_at
        ))
    dst.commit()
    for cs in src.query(CandidateSegment).filter(CandidateSegment.project_id == 'real-5h-65655576').all():
        dst.merge(CandidateSegment(
            id=cs.id, run_id=cs.run_id, project_id=cs.project_id,
            source_asset_id=cs.source_asset_id, core_start=cs.core_start,
            core_end=cs.core_end, start_time=cs.start_time, end_time=cs.end_time,
            summary=cs.summary, confidence=cs.confidence,
            status=cs.status, created_at=cs.created_at
        ))
    dst.commit()

    # 6. StoryGraphRuns & Nodes
    for sgr in src.query(StoryGraphRun).all():
        if dst.query(Project).filter_by(id=sgr.project_id).first():
            dst.merge(StoryGraphRun(
                id=sgr.id, project_id=sgr.project_id, candidate_run_id=sgr.candidate_run_id,
                provider=sgr.provider, status=sgr.status, derivation_signature=sgr.derivation_signature,
                created_at=sgr.created_at
            ))
    dst.commit()
    for sn in src.query(StoryNode).all():
        if dst.query(StoryGraphRun).filter_by(id=sn.story_graph_run_id).first():
            dst.merge(StoryNode(
                id=sn.id, story_graph_run_id=sn.story_graph_run_id, project_id=sn.project_id,
                node_type=sn.node_type, start_time=sn.start_time, end_time=sn.end_time,
                candidate_id=sn.candidate_id, title=sn.title, summary=sn.summary,
                confidence=sn.confidence, created_at=sn.created_at
            ))
    dst.commit()

    # 7. EditPlanRuns, EditPlans, EditClips
    for epr in src.query(EditPlanRun).all():
        if dst.query(Project).filter_by(id=epr.project_id).first():
            dst.merge(EditPlanRun(
                id=epr.id, project_id=epr.project_id, story_graph_run_id=epr.story_graph_run_id,
                provider=epr.provider, status=epr.status, derivation_signature=epr.derivation_signature,
                created_at=epr.created_at
            ))
    dst.commit()
    for ep in src.query(EditPlan).all():
        if dst.query(EditPlanRun).filter_by(id=ep.run_id).first():
            dst.merge(EditPlan(
                id=ep.id, project_id=ep.project_id, run_id=ep.run_id, version=ep.version,
                status=ep.status, original_duration=ep.original_duration,
                selected_duration=ep.selected_duration, compression_ratio=ep.compression_ratio,
                clip_count=ep.clip_count, created_at=ep.created_at
            ))
    dst.commit()
    for ec in src.query(EditClip).all():
        if dst.query(EditPlan).filter_by(id=ec.plan_id).first():
            cid = ec.candidate_id if dst.query(CandidateSegment).filter_by(id=ec.candidate_id).first() else None
            snid = ec.story_node_id if dst.query(StoryNode).filter_by(id=ec.story_node_id).first() else None
            dst.merge(EditClip(
                id=ec.id, plan_id=ec.plan_id, source_start=ec.source_start,
                source_end=ec.source_end, core_start=ec.core_start, core_end=ec.core_end,
                output_start=ec.output_start, output_end=ec.output_end,
                candidate_id=cid, story_node_id=snid, selection_reason=ec.selection_reason,
                priority=ec.priority, confidence=ec.confidence, locked=ec.locked
            ))
    dst.commit()

    # 8. VisualAnalysisRuns
    for vr in src.query(VisualAnalysisRun).filter(VisualAnalysisRun.project_id == 'real-5h-65655576').all():
        dst.merge(VisualAnalysisRun(
            id=vr.id, project_id=vr.project_id, source_asset_id=vr.source_asset_id,
            provider=vr.provider, status=vr.status, derivation_signature=vr.derivation_signature,
            created_at=vr.created_at
        ))
    dst.commit()

    # 9. EffectPlanRuns & EffectInstructions
    for er in src.query(EffectPlanRun).filter(EffectPlanRun.project_id == 'real-5h-65655576').all():
        dst.merge(EffectPlanRun(
            id=er.id, project_id=er.project_id, edit_plan_id=er.edit_plan_id,
            visual_analysis_run_id=er.visual_analysis_run_id, provider=er.provider,
            status=er.status, derivation_signature=er.derivation_signature,
            created_at=er.created_at
        ))
    dst.commit()
    for ei in src.query(EffectInstruction).all():
        if dst.query(EffectPlanRun).filter_by(id=ei.effect_plan_run_id).first():
            dst.merge(EffectInstruction(
                id=ei.id, effect_plan_run_id=ei.effect_plan_run_id,
                source_start=ei.source_start, source_end=ei.source_end,
                effect_type=ei.effect_type, target_type=ei.target_type,
                confidence=ei.confidence, priority=ei.priority,
                reason=ei.reason, provider=ei.provider,
                created_at=ei.created_at
            ))
    dst.commit()

    # 10. RenderJobs & Output MediaAsset
    output_asset = MediaAsset(
        id="rendered-final-5h-mp4",
        project_id="real-5h-65655576",
        name="final.mp4",
        path="data/work/renders/renders/cd5355af-3b67-49ed-8637-93b1c1c498d4/final.mp4",
        media_type="rendered_output",
        file_size_bytes=5526821,
        parent_asset_id="859fc763-9d32-4590-b7ab-6cf4032e6d7b"
    )
    dst.merge(output_asset)
    dst.commit()

    for rj in src.query(RenderJob).filter(RenderJob.project_id == 'real-5h-65655576').all():
        out_id = "rendered-final-5h-mp4" if rj.status == "completed" else None
        dst.merge(RenderJob(
            id=rj.id, project_id=rj.project_id,
            source_asset_id="859fc763-9d32-4590-b7ab-6cf4032e6d7b",
            edit_plan_id=rj.edit_plan_id,
            effect_plan_run_id=rj.effect_plan_run_id, status=rj.status,
            output_asset_id=out_id, render_config=rj.render_config,
            created_at=rj.created_at
        ))
    dst.commit()

    # 11. StyleApplicationRun (add representative record)
    policy = EditorialStylePolicy(id="default-style-policy", name="Default Creator Style")
    dst.merge(policy)
    dst.commit()
    version = StylePolicyVersion(id="default-policy-v1", policy_id="default-style-policy", version=1)
    dst.merge(version)
    dst.commit()
    sar = StyleApplicationRun(
        id="rep-style-app-run",
        project_id="real-5h-65655576",
        style_policy_id="default-style-policy",
        style_policy_version_id="default-policy-v1",
        status="completed"
    )
    dst.merge(sar)
    dst.commit()

print('Successfully synchronized representative state into PostgreSQL!')
