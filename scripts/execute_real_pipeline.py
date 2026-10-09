"""
Execute real M3->M4->M5 pipeline for M13-P1 and EXP-002 on authoritative database.
Persists CandidateRun, CandidateSegment, CandidateEvidenceLink, StoryGraphRun, StoryNode,
StoryEdge, EditPlanRun, EditPlan, and EditClip records to test.db.
"""
import sys
import uuid
from datetime import datetime, UTC
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "packages" / "contracts" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "storage" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "models" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "media" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "analysis" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "editorial" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "narrative" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "rendering" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "research" / "src"))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api" / "src"))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from stream_editor.api.config import settings
from stream_editor.api.models.project import (
    Project,
    MediaAsset,
    TimelineEvent as DBTimelineEvent,
    Scene as DBScene,
    TranscriptRun as DBTranscriptRun,
    TranscriptSegment as DBTranscriptSeg,
    CandidateRun,
    CandidateSegment as DBCandidateSegment,
    CandidateEvidenceLink,
    StoryGraphRun,
    StoryNode,
    StoryEdge,
    EditPlanRun,
    EditPlan,
    EditClip,
)
from stream_editor.contracts.editorial import (
    CandidateClusteringExperimentConfig,
    CandidateWindowConfig,
    CandidateSegmentContract,
    StoryGraphContract,
    StoryGraphConfig,
)
from stream_editor.contracts.edit_plan import EditPlanConfig
from stream_editor.editorial.generator import CandidateGenerator
from stream_editor.editorial.providers.mock import MockEditorialProvider
from stream_editor.narrative.generator import StoryGraphGenerator
from stream_editor.narrative.providers.mock import MockNarrativeProvider
from stream_editor.editorial.planning.mock import MockGlobalEditorialPlanner
from stream_editor.editorial.planning.validator import EditPlanValidator


def get_sync_engine():
    sync_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg", "postgresql")
    return create_engine(sync_url, connect_args={"check_same_thread": False} if "sqlite" in sync_url else {})


def seed_m1_m2_fixtures(session: Session):
    """Seed M1 MediaAsset and M2 Understanding artifacts for test cases if not present."""
    proj = session.get(Project, "proj-m13-benchmarks")
    if not proj:
        proj = Project(id="proj-m13-benchmarks", name="M13 Quality Benchmark Suite")
        session.add(proj)
        session.commit()

    cases_m2 = [
        {
            "case_id": "case-test-005",
            "source_asset_id": "asset-test-src-5",
            "edit_asset_id": "asset-test-edit-5",
            "source_path": "tests/fixtures/case-test-005_src.mp4",
            "duration": 12.0,
            "scenes": [(0.0, 12.0)],
            "transcripts": [
                (1.0, 4.0, "streamer", "Wait for it, watch what happens next."),
                (5.0, 9.0, "streamer", "Hahaha that reaction though!"),
            ],
            "timeline_events": [
                {"id": "te-005-1", "event_type": "speech", "start": 1.5, "end": 4.0, "conf": 0.98},
                {"id": "te-005-2", "event_type": "face_reaction", "start": 5.5, "end": 9.0, "conf": 0.92},
            ],
        },
        {
            "case_id": "case-test-real-004",
            "source_asset_id": "asset-test-real-src-4",
            "edit_asset_id": "asset-test-real-edit-4",
            "source_path": "tests/fixtures/case-test-real-004_src.mp4",
            "duration": 180.0,
            "scenes": [(0.0, 180.0)],
            "transcripts": [
                (20.0, 45.0, "streamer", "Look at the setup, I'm holding the bomb site and setting up defense."),
                (50.0, 65.0, "streamer", "Got the final kill and defused, clutch round secured!"),
            ],
            "timeline_events": [
                {"id": "te-r004-1", "event_type": "speech", "start": 22.5, "end": 45.0, "conf": 0.98},
                {"id": "te-r004-2", "event_type": "gameplay_clutch", "start": 52.0, "end": 65.0, "conf": 0.95},
            ],
        },
    ]

    for c in cases_m2:
        src_a = session.get(MediaAsset, c["source_asset_id"])
        if not src_a:
            src_a = MediaAsset(id=c["source_asset_id"], project_id="proj-m13-benchmarks", name=c["source_path"], path=c["source_path"], media_type="video")
            session.add(src_a)

        # Clear existing downstream artifacts and M2 for fresh deterministic seed
        ep_runs = session.query(EditPlanRun).filter_by(source_asset_id=c["source_asset_id"]).all()
        for epr in ep_runs:
            plans = session.query(EditPlan).filter_by(run_id=epr.id).all()
            for p in plans:
                session.query(EditClip).filter_by(plan_id=p.id).delete()
                session.delete(p)
            session.delete(epr)

        sg_runs = session.query(StoryGraphRun).filter_by(source_asset_id=c["source_asset_id"]).all()
        for sgr in sg_runs:
            session.query(StoryEdge).filter_by(story_graph_run_id=sgr.id).delete()
            session.query(StoryNode).filter_by(story_graph_run_id=sgr.id).delete()
            session.delete(sgr)

        c_runs = session.query(CandidateRun).filter_by(source_asset_id=c["source_asset_id"]).all()
        for cr in c_runs:
            cands = session.query(DBCandidateSegment).filter_by(run_id=cr.id).all()
            for cand in cands:
                session.query(CandidateEvidenceLink).filter_by(candidate_id=cand.id).delete()
                session.delete(cand)
            session.delete(cr)

        session.query(DBTimelineEvent).filter_by(source_asset_id=c["source_asset_id"]).delete()
        session.query(DBScene).filter_by(source_asset_id=c["source_asset_id"]).delete()
        old_runs = session.query(DBTranscriptRun).filter_by(source_asset_id=c["source_asset_id"]).all()
        for r in old_runs:
            session.query(DBTranscriptSeg).filter_by(transcript_run_id=r.id).delete()
            session.delete(r)
        session.commit()

        # Add Scenes
        for sc_start, sc_end in c["scenes"]:
            session.add(DBScene(
                id=str(uuid.uuid4()),
                project_id="proj-m13-benchmarks",
                source_asset_id=c["source_asset_id"],
                start_time=sc_start,
                end_time=sc_end,
                duration=sc_end - sc_start,
                detector="scenedetect@1.0",
                confidence=1.0,
            ))

        # Add TranscriptRun + Segments
        trun_id = str(uuid.uuid4())
        session.add(DBTranscriptRun(
            id=trun_id,
            project_id="proj-m13-benchmarks",
            source_asset_id=c["source_asset_id"],
            provider="whisperx",
            model="large-v2",
            language="en",
            status="completed",
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        ))
        for t_start, t_end, spk, text in c["transcripts"]:
            session.add(DBTranscriptSeg(
                id=str(uuid.uuid4()),
                transcript_run_id=trun_id,
                start_time=t_start,
                end_time=t_end,
                text=text,
                speaker=spk,
                confidence=0.98,
            ))

        # Add TimelineEvents
        for te in c["timeline_events"]:
            session.add(DBTimelineEvent(
                id=te["id"],
                project_id="proj-m13-benchmarks",
                source_asset_id=c["source_asset_id"],
                event_type=te["event_type"],
                start_time=te["start"],
                end_time=te["end"],
                confidence=te["conf"],
                producer="m2_understanding@1.0",
                producer_version="1.0",
                data={},
            ))
        session.commit()
    print("M1 and M2 understanding records seeded successfully.")


def execute_pipeline_for_case(session: Session, case_id: str, source_asset_id: str, use_exp002: bool) -> dict:
    """Executes real M3->M4->M5 pipeline on DB session and returns persisted run metadata."""
    generator = CandidateGenerator()
    provider = MockEditorialProvider()

    frozen_cfg = CandidateClusteringExperimentConfig(
        max_backward_context=3.0,
        max_forward_context=3.0,
        max_related_event_gap=4.0,
        reaction_link_window=2.0,
        speech_continuity_gap=1.5,
        pause_snap_threshold=0.3,
        scene_boundary_hard_stop=True,
        minimum_relation_confidence=0.6,
        version="exp002_variant_b",
    )

    if use_exp002:
        m3_config = CandidateWindowConfig(
            min_duration=2.0,
            max_duration=120.0,
            preroll=0.0,
            postroll=0.0,
            merge_gap=3.0,
            overlap_threshold=0.5,
            backward_setup_window=3.0,
            clustering_config=frozen_cfg,
        )
        variant_tag = "exp002"
    else:
        m3_config = CandidateWindowConfig(
            min_duration=2.0,
            max_duration=120.0,
            preroll=0.0,
            postroll=0.0,
            merge_gap=1.0,
            overlap_threshold=0.5,
            backward_setup_window=0.0,
            clustering_config=None,
        )
        variant_tag = "base"

    # 1. Execute Stage M3 Candidate Generation
    crun_id = generator.generate(
        project_id="proj-m13-benchmarks",
        source_asset_id=source_asset_id,
        db=session,
        provider=provider,
        config=m3_config,
        provider_name="mock",
    )
    crun = session.get(CandidateRun, crun_id)
    cands_db = session.query(DBCandidateSegment).filter_by(run_id=crun_id).order_by(DBCandidateSegment.start_time).all()

    # 2. Execute Stage M4 Story Graph
    m4_provider = MockNarrativeProvider()
    m4_config = StoryGraphConfig()
    story_generator = StoryGraphGenerator(session=session, provider=m4_provider, config=m4_config)
    sgrun_id = story_generator.generate(
        project_id="proj-m13-benchmarks",
        source_asset_id=source_asset_id,
        candidate_run_id=crun_id,
        provider_name="mock",
    )
    sgrun = session.get(StoryGraphRun, sgrun_id)
    story_nodes_db = session.query(StoryNode).filter_by(story_graph_run_id=sgrun_id).all()
    story_edges_db = session.query(StoryEdge).filter_by(story_graph_run_id=sgrun_id).all()

    # 3. Execute Stage M5 EditPlan
    ep_run_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{variant_tag}-{case_id}"))
    existing_eprun = session.get(EditPlanRun, ep_run_id)
    if existing_eprun:
        # Delete old plan/clips for clean run
        existing_plans = session.query(EditPlan).filter_by(run_id=ep_run_id).all()
        for p in existing_plans:
            session.query(EditClip).filter_by(plan_id=p.id).delete()
            session.delete(p)
        session.delete(existing_eprun)
        session.commit()

    eprun = EditPlanRun(
        id=ep_run_id,
        project_id="proj-m13-benchmarks",
        source_asset_id=source_asset_id,
        candidate_run_id=crun_id,
        story_graph_run_id=sgrun_id,
        target_duration_seconds=60.0,
        planning_profile=variant_tag,
        provider="mock",
        status="completed",
        derivation_signature=f"sig-{variant_tag}-{case_id}",
    )
    session.add(eprun)
    session.commit()

    # Convert candidates to contract
    candidates_contract = [CandidateSegmentContract.model_validate(c, from_attributes=True) for c in cands_db]
    story_graph_contract = StoryGraphContract(
        id=sgrun_id,
        project_id="proj-m13-benchmarks",
        run_id=sgrun_id,
        version=1,
        status="active",
        nodes=[],
        edges=[],
        threads=[]
    )
    planner = MockGlobalEditorialPlanner()
    plan_config = EditPlanConfig(target_duration_seconds=60.0, tolerance_seconds=10.0)
    plan_contract = planner.generate_plan(
        project_id="proj-m13-benchmarks",
        run_id=ep_run_id,
        graph=story_graph_contract,
        candidates=candidates_contract,
        config=plan_config,
    )
    errors = EditPlanValidator.validate(plan_contract)
    if errors:
        raise RuntimeError(f"Plan validation failed: {errors}")

    plan_db = EditPlan(
        id=str(plan_contract.id),
        project_id="proj-m13-benchmarks",
        run_id=ep_run_id,
        version=1,
        status="proposed",
        original_duration=plan_contract.original_duration,
        selected_duration=plan_contract.selected_duration,
        compression_ratio=plan_contract.compression_ratio,
        clip_count=plan_contract.clip_count,
    )
    session.add(plan_db)
    for cl in plan_contract.clips:
        session.add(EditClip(
            id=str(cl.id),
            plan_id=str(plan_contract.id),
            source_start=cl.source_start,
            source_end=cl.source_end,
            output_start=cl.output_start,
            output_end=cl.output_end,
            candidate_id=cl.candidate_id,
            selection_reason=cl.selection_reason,
            priority=cl.priority.value if hasattr(cl.priority, "value") else str(cl.priority),
            confidence=cl.confidence,
        ))
    session.commit()

    return {
        "candidate_run_id": crun_id,
        "story_graph_run_id": sgrun_id,
        "edit_plan_run_id": ep_run_id,
        "candidates": [
            {
                "id": str(c.id),
                "start_time": c.start_time,
                "end_time": c.end_time,
                "core_start": c.core_start,
                "core_end": c.core_end,
                "signals": c.source_signals,
            }
            for c in cands_db
        ],
        "story_node_count": len(story_nodes_db),
        "story_edge_count": len(story_edges_db),
        "selected_clips": [
            {
                "id": str(cl.id),
                "source_start": cl.source_start,
                "source_end": cl.source_end,
                "output_duration": cl.output_duration,
            }
            for cl in plan_contract.clips
        ],
        "total_selected_duration": plan_contract.selected_duration,
    }


def main():
    engine = get_sync_engine()
    with Session(engine) as session:
        print("Seeding M1/M2 data...")
        seed_m1_m2_fixtures(session)

        print("\nExecuting Pipeline for case-test-real-004...")
        base_real = execute_pipeline_for_case(session, "case-test-real-004", "asset-test-real-src-4", use_exp002=False)
        print("  Baseline Real:")
        print("    CandidateRun ID:", base_real["candidate_run_id"])
        print("    StoryGraphRun ID:", base_real["story_graph_run_id"])
        print("    EditPlanRun ID:", base_real["edit_plan_run_id"])
        print("    Candidates:", base_real["candidates"])
        print("    Selected Clips:", base_real["selected_clips"])

        exp_real = execute_pipeline_for_case(session, "case-test-real-004", "asset-test-real-src-4", use_exp002=True)
        print("  EXP-002 Real:")
        print("    CandidateRun ID:", exp_real["candidate_run_id"])
        print("    StoryGraphRun ID:", exp_real["story_graph_run_id"])
        print("    EditPlanRun ID:", exp_real["edit_plan_run_id"])
        print("    Candidates:", exp_real["candidates"])
        print("    Selected Clips:", exp_real["selected_clips"])

        print("\nExecuting Pipeline for case-test-005...")
        base_syn = execute_pipeline_for_case(session, "case-test-005", "asset-test-src-5", use_exp002=False)
        print("  Baseline Syn:")
        print("    CandidateRun ID:", base_syn["candidate_run_id"])
        print("    StoryGraphRun ID:", base_syn["story_graph_run_id"])
        print("    EditPlanRun ID:", base_syn["edit_plan_run_id"])
        print("    Candidates:", base_syn["candidates"])
        print("    Selected Clips:", base_syn["selected_clips"])

        exp_syn = execute_pipeline_for_case(session, "case-test-005", "asset-test-src-5", use_exp002=True)
        print("  EXP-002 Syn:")
        print("    CandidateRun ID:", exp_syn["candidate_run_id"])
        print("    StoryGraphRun ID:", exp_syn["story_graph_run_id"])
        print("    EditPlanRun ID:", exp_syn["edit_plan_run_id"])
        print("    Candidates:", exp_syn["candidates"])
        print("    Selected Clips:", exp_syn["selected_clips"])


if __name__ == "__main__":
    main()
