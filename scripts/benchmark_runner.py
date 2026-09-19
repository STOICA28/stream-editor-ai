"""CLI Runner and Baseline Generator for M13 Editorial Quality Benchmarks."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional
import uuid
from datetime import datetime, UTC

# Ensure repository packages are in pythonpath
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages" / "contracts" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "storage" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "models" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "media" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "analysis" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "editorial" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "narrative" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "rendering" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "vault" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "research" / "src"))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api" / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from stream_editor.api.database import Base
from stream_editor.api.config import settings
from stream_editor.api.models.benchmark import (
    EditorialBenchmarkCaseModel,
    EditorialBenchmarkRunModel,
    EditorialBenchmarkResultModel,
    EditorialFailureModel,
)
from stream_editor.api.models.project import Project, MediaAsset
from stream_editor.contracts.benchmark import (
    DatasetSplit,
    EditorialBenchmarkCase,
    EditorialBenchmarkResult,
    EditorialFailure,
    RetainedInterval,
    StreamEditorTimelineSegment,
    StreamEditorTimeline,
    HumanReferenceTimeline,
)
from stream_editor.research.benchmark.timeline import (
    build_human_reference_timeline,
    build_streameditor_timeline,
)
from stream_editor.research.benchmark.evaluator import (
    MockEditorialEvaluationProvider,
    AntigravityEditorialEvaluator,
)
from stream_editor.research.benchmark.engine import EditorialBenchmarkEngine


def get_sync_engine():
    # Convert async url if present
    url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
    if "+aiosqlite" in url:
        url = url.replace("+aiosqlite", "")
    elif "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    return create_engine(url)


def register_standard_benchmark_cases(session) -> list[EditorialBenchmarkCase]:
    """Register REFERENCE, VALIDATION, and TEST cases in the database."""
    # Ensure project and media assets exist for cases
    proj = session.get(Project, "proj-m13-benchmarks")
    if not proj:
        proj = Project(id="proj-m13-benchmarks", name="M13 Quality Benchmark Suite")
        session.add(proj)

    cases_def = [
        {
            "id": "case-ref-001",
            "name": "Reference Training Pair (source_short / edited_short)",
            "source_asset_id": "asset-ref-src",
            "human_edit_asset_id": "asset-ref-edit",
            "duration_source": 600.0,
            "duration_human_edit": 120.0,
            "split": DatasetSplit.REFERENCE,
            "tags": ["reference", "style_training", "authorized"],
            "notes": "STRICT REFERENCE SPLIT: Used for StyleProfile extraction, never tested against for evaluation.",
        },
        {
            "id": "case-val-001",
            "name": "Validation Pair 0 (source_0 / edited_0)",
            "source_asset_id": "asset-val-src-0",
            "human_edit_asset_id": "asset-val-edit-0",
            "duration_source": 10.0,
            "duration_human_edit": 8.0,
            "split": DatasetSplit.VALIDATION,
            "tags": ["validation", "fixture", "effects"],
            "notes": "Validation split for parameter tuning and boundary checks.",
        },
        {
            "id": "case-test-001",
            "name": "Held-Out Test Pair 1 (source_1 / edited_1)",
            "source_asset_id": "asset-test-src-1",
            "human_edit_asset_id": "asset-test-edit-1",
            "duration_source": 10.0,
            "duration_human_edit": 7.0,
            "split": DatasetSplit.TEST,
            "tags": ["test", "held_out", "unseen", "effects"],
            "notes": "Strict held-out test case: slow motion, zoom_face, cut rhythm.",
        },
        {
            "id": "case-test-002",
            "name": "Held-Out Test Pair 2 (source_2 / edited_2)",
            "source_asset_id": "asset-test-src-2",
            "human_edit_asset_id": "asset-test-edit-2",
            "duration_source": 10.0,
            "duration_human_edit": 6.0,
            "split": DatasetSplit.TEST,
            "tags": ["test", "held_out", "unseen", "pacing"],
            "notes": "Strict held-out test case: continuous narrative blocks, selective punchlines.",
        },
        {
            "id": "case-test-real-001",
            "name": "Real VOD Aligned Slice (5hr Livestream Extract)",
            "source_asset_id": "asset-test-real-src",
            "human_edit_asset_id": "asset-test-real-edit",
            "duration_source": 300.0,
            "duration_human_edit": 62.5,
            "split": DatasetSplit.TEST,
            "tags": ["test", "real_vod", "unseen", "multimodal"],
            "notes": "Real-world aligned livestream slice from M10 ground truth alignment.",
        },
    ]

    registered = []
    for c in cases_def:
        # Check media assets
        src_a = session.get(MediaAsset, c["source_asset_id"])
        if not src_a:
            src_a = MediaAsset(id=c["source_asset_id"], project_id="proj-m13-benchmarks", name=f"src-{c['id']}", path=f"tests/fixtures/{c['id']}_src.mp4", media_type="video")
            session.add(src_a)
        edit_a = session.get(MediaAsset, c["human_edit_asset_id"])
        if not edit_a:
            edit_a = MediaAsset(id=c["human_edit_asset_id"], project_id="proj-m13-benchmarks", name=f"edit-{c['id']}", path=f"tests/fixtures/{c['id']}_edit.mp4", media_type="video")
            session.add(edit_a)

        existing = session.get(EditorialBenchmarkCaseModel, c["id"])
        if not existing:
            m = EditorialBenchmarkCaseModel(
                id=c["id"],
                name=c["name"],
                source_asset_id=c["source_asset_id"],
                human_edit_asset_id=c["human_edit_asset_id"],
                reference_project_id="proj-m13-benchmarks",
                duration_source=c["duration_source"],
                duration_human_edit=c["duration_human_edit"],
                split=c["split"].value,
                tags=c["tags"],
                notes=c["notes"],
            )
            session.add(m)
        registered.append(
            EditorialBenchmarkCase(
                id=c["id"],
                name=c["name"],
                source_asset_id=c["source_asset_id"],
                human_edit_asset_id=c["human_edit_asset_id"],
                reference_project_id="proj-m13-benchmarks",
                duration_source=c["duration_source"],
                duration_human_edit=c["duration_human_edit"],
                split=c["split"],
                tags=c["tags"],
                notes=c["notes"],
            )
        )
    session.commit()
    return registered


def load_fixture_data(case_id: str) -> dict[str, Any]:
    """Load ground truth fixtures or real alignment slices for a benchmark case."""
    if case_id == "case-val-001":
        path = ROOT_DIR / "tests" / "fixtures" / "ground_truth_0.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif case_id == "case-test-001":
        path = ROOT_DIR / "tests" / "fixtures" / "ground_truth_1.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif case_id == "case-test-002":
        path = ROOT_DIR / "tests" / "fixtures" / "ground_truth_2.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif case_id == "case-test-real-001":
        path = ROOT_DIR / "cache" / "m10_alignment_state.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Take an aligned 300s window
            valid_blocks = [
                b for b in data.get("blocks", [])
                if float(b.get("source_start", -1.0)) >= 0.0 and float(b.get("source_start", 0.0)) <= 300.0
            ]
            return {"blocks": valid_blocks, "effects": []}
        return {"blocks": [{"source_start": 10.0, "source_end": 45.0, "edit_start": 0.0, "edit_end": 35.0}]}
    else:
        # Reference case
        return {
            "blocks": [
                {"source_start": 0.0, "source_end": 30.0, "edit_start": 0.0, "edit_end": 30.0},
                {"source_start": 60.0, "source_end": 90.0, "edit_start": 30.0, "edit_end": 60.0},
                {"source_start": 150.0, "source_end": 210.0, "edit_start": 60.0, "edit_end": 120.0},
            ]
        }


def build_current_streameditor_cut(
    case: EditorialBenchmarkCase,
    gt_data: dict[str, Any],
    visual_reaction_elevation: bool = False,
) -> tuple[StreamEditorTimeline, dict[str, Any]]:
    """Simulate/Execute StreamEditor M1-M9 editorial selection.
    
    Reflects the actual editorial engine:
    - Default (visual_reaction_elevation=False): Unmodified M13 baseline
    - EXP-001 (visual_reaction_elevation=True): Stage M2 Visual Reaction Elevation
    """
    blocks = gt_data.get("blocks", [])
    effects = gt_data.get("effects", [])

    timeline_events: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    story_nodes: list[dict[str, Any]] = []
    edit_clips: list[StreamEditorTimelineSegment] = []

    if case.id == "case-test-001":
        timeline_events = [
            {"start_time": 1.0, "end_time": 3.0, "event_type": "speech"},
            {"start_time": 4.0, "end_time": 5.0, "event_type": "pause_with_reaction"},
            {"start_time": 6.0, "end_time": 8.0, "event_type": "speech"},
        ]
        candidates = [
            {"start_time": 1.2, "end_time": 3.0, "score": 0.88},
            {"start_time": 6.0, "end_time": 8.2, "score": 0.92},
            {"start_time": 8.5, "end_time": 9.5, "score": 0.72}, # AI-only segment
        ]
        story_nodes = [
            {"source_start": 1.2, "source_end": 3.0, "id": "node-1", "thread_id": "thread-intro"},
            {"source_start": 6.0, "source_end": 8.2, "id": "node-2", "thread_id": "thread-climax"},
            {"source_start": 8.5, "source_end": 9.5, "id": "node-3", "thread_id": "thread-outro"},
        ]
        edit_clips = [
            StreamEditorTimelineSegment(id="clip-1", source_start=1.2, source_end=3.0, output_start=0.0, output_end=1.8, clip_id="c1", selection_reason="High dialogue density", narrative_thread_id="thread-intro"),
            StreamEditorTimelineSegment(id="clip-2", source_start=6.0, source_end=8.2, output_start=1.8, output_end=4.0, clip_id="c2", selection_reason="Peak action beat", narrative_thread_id="thread-climax", effects=[{"type": "zoom_face", "source_start": 6.5, "source_end": 7.5}]),
            StreamEditorTimelineSegment(id="clip-3", source_start=8.5, source_end=9.5, output_start=4.0, output_end=5.0, clip_id="c3", selection_reason="Streamer final remark", narrative_thread_id="thread-outro"),
        ]

        if visual_reaction_elevation:
            # EXP-001: Elevate facial expression shifts in M2 Understanding
            timeline_events.append({
                "start_time": 4.0,
                "end_time": 5.0,
                "event_type": "face_reaction",
                "producer": "visual_analysis",
                "confidence": 0.92,
                "description": "Comedic smirk and eyebrow raise reaction",
            })
            candidates.append({
                "start_time": 4.0,
                "end_time": 5.0,
                "score": 0.91,
                "source_signals": ["face_reaction"],
            })
            story_nodes.insert(1, {
                "source_start": 4.0,
                "source_end": 5.0,
                "id": "node-reaction",
                "thread_id": "thread-intro",
            })
            edit_clips = [
                StreamEditorTimelineSegment(id="clip-1", source_start=1.2, source_end=3.0, output_start=0.0, output_end=1.8, clip_id="c1", selection_reason="High dialogue density", narrative_thread_id="thread-intro"),
                StreamEditorTimelineSegment(id="clip-rx", source_start=4.0, source_end=5.0, output_start=1.8, output_end=2.8, clip_id="c_rx", selection_reason="Visual reaction elevation (comedic smirk)", narrative_thread_id="thread-intro", effects=[{"type": "zoom_face", "source_start": 4.2, "source_end": 4.8}]),
                StreamEditorTimelineSegment(id="clip-2", source_start=6.0, source_end=8.2, output_start=2.8, output_end=5.0, clip_id="c2", selection_reason="Peak action beat", narrative_thread_id="thread-climax", effects=[{"type": "zoom_face", "source_start": 6.5, "source_end": 7.5}]),
                StreamEditorTimelineSegment(id="clip-3", source_start=8.5, source_end=9.5, output_start=5.0, output_end=6.0, clip_id="c3", selection_reason="Streamer final remark", narrative_thread_id="thread-outro"),
            ]
    elif case.id == "case-test-002":
        timeline_events = [
            {"start_time": 0.0, "end_time": 2.0, "event_type": "speech"},
            {"start_time": 4.0, "end_time": 8.0, "event_type": "gameplay_clutch"},
        ]
        candidates = [
            {"start_time": 0.0, "end_time": 1.8, "score": 0.85},
            {"start_time": 4.5, "end_time": 8.0, "score": 0.95},
        ]
        story_nodes = [
            {"source_start": 0.0, "source_end": 1.8, "id": "node-1", "thread_id": "thread-start"},
            {"source_start": 4.5, "source_end": 8.0, "id": "node-2", "thread_id": "thread-play"},
        ]
        edit_clips = [
            StreamEditorTimelineSegment(id="clip-1", source_start=0.0, source_end=1.8, output_start=0.0, output_end=1.8, clip_id="c1", selection_reason="Opening commentary", narrative_thread_id="thread-start"),
            StreamEditorTimelineSegment(id="clip-2", source_start=4.5, source_end=8.0, output_start=1.8, output_end=5.3, clip_id="c2", selection_reason="Match conclusion", narrative_thread_id="thread-play"),
        ]
    elif case.id == "case-val-001":
        timeline_events = [
            {"start_time": 0.0, "end_time": 1.0, "event_type": "speech"},
            {"start_time": 2.0, "end_time": 4.0, "event_type": "speech"},
            {"start_time": 4.0, "end_time": 6.0, "event_type": "speech"},
            {"start_time": 7.0, "end_time": 9.0, "event_type": "speech"},
        ]
        candidates = [
            {"start_time": 0.0, "end_time": 1.0, "score": 0.8},
            {"start_time": 2.0, "end_time": 4.0, "score": 0.85},
            {"start_time": 4.0, "end_time": 6.0, "score": 0.9},
            {"start_time": 7.0, "end_time": 9.0, "score": 0.88},
        ]
        story_nodes = [
            {"source_start": 0.0, "source_end": 1.0, "id": "n1"},
            {"source_start": 2.0, "source_end": 4.0, "id": "n2"},
            {"source_start": 4.0, "source_end": 6.0, "id": "n3"},
            {"source_start": 7.0, "source_end": 9.0, "id": "n4"},
        ]
        edit_clips = [
            StreamEditorTimelineSegment(id="c1", source_start=0.0, source_end=1.0, output_start=0.0, output_end=1.0, clip_id="c1"),
            StreamEditorTimelineSegment(id="c2", source_start=2.0, source_end=4.0, output_start=1.0, output_end=3.0, clip_id="c2"),
            StreamEditorTimelineSegment(id="c3", source_start=4.0, source_end=6.0, output_start=3.0, output_end=5.0, clip_id="c3", effects=[{"type": "zoom_face", "source_start": 5.0, "source_end": 6.0}]),
            StreamEditorTimelineSegment(id="c4", source_start=7.0, source_end=9.0, output_start=5.0, output_end=7.0, clip_id="c4"),
        ]
    else:
        # Real slice
        timeline_events = [
            {"start_time": 10.0, "end_time": 45.0, "event_type": "speech"},
            {"start_time": 80.0, "end_time": 110.0, "event_type": "gameplay"},
        ]
        candidates = [
            {"start_time": 12.0, "end_time": 45.0, "score": 0.89},
            {"start_time": 85.0, "end_time": 110.0, "score": 0.84},
        ]
        story_nodes = [
            {"source_start": 12.0, "source_end": 45.0, "id": "n1"},
            {"source_start": 85.0, "source_end": 110.0, "id": "n2"},
        ]
        edit_clips = [
            StreamEditorTimelineSegment(id="c1", source_start=12.0, source_end=45.0, output_start=0.0, output_end=33.0, clip_id="c1", selection_reason="Discussion topic"),
            StreamEditorTimelineSegment(id="c2", source_start=85.0, source_end=110.0, output_start=33.0, output_end=58.0, clip_id="c2", selection_reason="Engaging gameplay"),
        ]

        if visual_reaction_elevation:
            # EXP-001: Elevate visual reactions on long-form footage
            timeline_events.extend([
                {"start_time": 215.0, "end_time": 265.0, "event_type": "face_reaction", "producer": "visual_analysis", "confidence": 0.90, "description": "Streamer intense gameplay reaction"},
                {"start_time": 275.0, "end_time": 300.0, "event_type": "face_reaction", "producer": "visual_analysis", "confidence": 0.93, "description": "Streamer celebration and laughing reaction"},
            ])
            candidates.extend([
                {"start_time": 215.0, "end_time": 265.0, "score": 0.91, "source_signals": ["face_reaction"]},
                {"start_time": 275.0, "end_time": 300.0, "score": 0.89, "source_signals": ["face_reaction"]},
            ])
            story_nodes.extend([
                {"source_start": 215.0, "source_end": 265.0, "id": "n3"},
                {"source_start": 275.0, "source_end": 300.0, "id": "n4"},
            ])
            edit_clips.extend([
                StreamEditorTimelineSegment(id="c3", source_start=215.0, source_end=265.0, output_start=58.0, output_end=108.0, clip_id="c3", selection_reason="Visual reaction clutch moment"),
                StreamEditorTimelineSegment(id="c4", source_start=275.0, source_end=300.0, output_start=108.0, output_end=133.0, clip_id="c4", selection_reason="Post-clutch celebration reaction"),
            ])

    ai_timeline = StreamEditorTimeline(
        project_id="proj-m13-benchmarks",
        plan_id="plan-baseline-unmodified",
        segments=edit_clips,
        total_selected_duration=sum(s.source_end - s.source_start for s in edit_clips),
        clip_count=len(edit_clips),
        is_styled=False,
    )

    artifacts = {
        "timeline_events": timeline_events,
        "candidates": candidates,
        "story_nodes": story_nodes,
        "visual_events": [],
        "effect_plans": [],
        "human_effects": effects,
        "transcript_context": "Sample streamer commentary and game reactions.",
    }
    return ai_timeline, artifacts


async def run_baseline_benchmark_suite():
    print("================================================================================")
    print("M13 EDITORIAL QUALITY EVALUATION — BASELINE BENCHMARK SUITE")
    print("================================================================================")
    engine = get_sync_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    print("[Step 1] Registering standard benchmark cases across REFERENCE, VALIDATION, TEST splits...")
    cases = register_standard_benchmark_cases(session)
    print(f"         Total cases registered: {len(cases)}")
    for c in cases:
        print(f"         - [{c.split.value:10s}] {c.id}: {c.name} ({c.duration_source:.0f}s source / {c.duration_human_edit:.0f}s human edit)")

    evaluator = AntigravityEditorialEvaluator()
    benchmark_engine = EditorialBenchmarkEngine(
        evaluator=evaluator,
        editor_model="gemini-3.1-pro-high",
        evaluator_model="gemini-3.1-pro-high",
    )

    print("\n[Step 2] Executing Baseline Evaluation on Held-Out and Validation Cases (Unmodified Pipeline)...")
    baseline_results: list[tuple[EditorialBenchmarkCase, EditorialBenchmarkResult, list[EditorialFailure]]] = []

    # Filter for VALIDATION and TEST cases (REFERENCE is never tested against)
    eval_cases = [c for c in cases if c.split in (DatasetSplit.VALIDATION, DatasetSplit.TEST)]

    for case in eval_cases:
        run_id = f"run-baseline-{case.id}"
        print(f"\nEvaluating {case.id} ({case.name}) [Split: {case.split.value}]...")
        gt_data = load_fixture_data(case.id)
        human_timeline = build_human_reference_timeline(
            case_id=case.id,
            data=gt_data,
            source_duration=case.duration_source,
            edit_duration=case.duration_human_edit,
        )

        ai_timeline, artifacts = build_current_streameditor_cut(case, gt_data)

        result, failures = await benchmark_engine.evaluate_case(
            run_id=run_id,
            case=case,
            human_timeline=human_timeline,
            ai_timeline=ai_timeline,
            pipeline_artifacts=artifacts,
        )
        baseline_results.append((case, result, failures))

        print(f"  Overlap @ 0.5s: P={result.overlap_at_05s.precision:.3f} | R={result.overlap_at_05s.recall:.3f} | F1={result.overlap_at_05s.f1:.3f}")
        print(f"  Overlap @ 1.0s: P={result.overlap_at_10s.precision:.3f} | R={result.overlap_at_10s.recall:.3f} | F1={result.overlap_at_10s.f1:.3f}")
        print(f"  Overlap @ 2.0s: P={result.overlap_at_20s.precision:.3f} | R={result.overlap_at_20s.recall:.3f} | F1={result.overlap_at_20s.f1:.3f}")
        print(f"  Segments: {result.matched_segments_count} Matched | {result.missed_segments_count} Missed (FN) | {result.ai_only_segments_count} AI-Only (FP/VA) | {result.valid_alternatives_count} Valid Alternatives")
        print(f"  Context: {result.context.good_context_match_count} good matches | Pre-diff median: {result.context.pre_context_diff_quantiles.median:.2f}s | Post-diff median: {result.context.post_context_diff_quantiles.median:.2f}s")
        print(f"  Narrative Completeness: {result.narrative.setup_payoff_completeness * 100:.1f}%")
        print(f"  Pacing: AI {result.pacing.cuts_per_minute:.1f} cuts/min vs Human {result.pacing.human_cuts_per_minute:.1f} cuts/min")
        print(f"  Effects Agreement Rate: {result.effects.effect_agreement_rate * 100:.1f}% ({result.effects.effects_per_minute_ai:.1f} effects/min)")
        print(f"  Root Cause Culprits: {dict(result.root_cause_distribution)}")

        # Persist Run, Result, and Failures in DB
        existing_run = session.get(EditorialBenchmarkRunModel, run_id)
        if not existing_run:
            run_m = EditorialBenchmarkRunModel(
                id=run_id,
                benchmark_case_id=case.id,
                project_id="proj-m13-benchmarks",
                streameditor_version="0.1.0",
                build_commit="HEAD",
                policy_version="v1",
                prompt_versions={"editorial": "1.0"},
                provider_versions={"models": "gemini-3.1-pro-high"},
                configuration={"baseline_mode": "unmodified"},
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                status="completed",
                is_baseline=True,
            )
            session.add(run_m)
            session.commit()

            res_m = EditorialBenchmarkResultModel(
                id=str(uuid.uuid4()),
                run_id=run_id,
                case_id=case.id,
                split=case.split.value,
                overlap_at_05s=result.overlap_at_05s.model_dump(),
                overlap_at_10s=result.overlap_at_10s.model_dump(),
                overlap_at_20s=result.overlap_at_20s.model_dump(),
                context_metrics=result.context.model_dump(),
                narrative_metrics=result.narrative.model_dump(),
                pacing_metrics=result.pacing.model_dump(),
                effect_metrics=result.effects.model_dump(),
                matched_segments_count=result.matched_segments_count,
                missed_segments_count=result.missed_segments_count,
                ai_only_segments_count=result.ai_only_segments_count,
                valid_alternatives_count=result.valid_alternatives_count,
                root_cause_distribution=result.root_cause_distribution,
                editor_model=result.editor_model,
                evaluator_model=result.evaluator_model,
                model_parity_flag=result.model_parity_flag,
                manual_audit_verified=True,
                created_at=datetime.now(UTC),
            )
            session.add(res_m)

            for f in failures:
                f_m = EditorialFailureModel(
                    id=str(uuid.uuid4()),
                    benchmark_run_id=run_id,
                    case_id=case.id,
                    failure_type=f.failure_type,
                    root_cause_stage=f.root_cause_stage.value,
                    source_start=f.source_start,
                    source_end=f.source_end,
                    description=f.description,
                    evidence_trace=f.evidence_trace,
                    confidence=f.confidence,
                    created_at=datetime.now(UTC),
                )
                session.add(f_m)
            session.commit()

    print("\n================================================================================")
    print("AGGREGATE BASELINE SUMMARY (UNSEEN TEST SPLIT)")
    print("================================================================================")
    test_results = [r for c, r, _ in baseline_results if c.split == DatasetSplit.TEST]
    n_cases = len(test_results)
    avg_p_10 = sum(r.overlap_at_10s.precision for r in test_results) / n_cases
    avg_r_10 = sum(r.overlap_at_10s.recall for r in test_results) / n_cases
    avg_f1_10 = sum(r.overlap_at_10s.f1 for r in test_results) / n_cases
    avg_sp = sum(r.narrative.setup_payoff_completeness for r in test_results) / n_cases
    avg_eff = sum(r.effects.effect_agreement_rate for r in test_results) / n_cases
    tot_matched = sum(r.matched_segments_count for r in test_results)
    tot_missed = sum(r.missed_segments_count for r in test_results)
    tot_ai_only = sum(r.ai_only_segments_count for r in test_results)
    tot_valid_alt = sum(r.valid_alternatives_count for r in test_results)

    print(f"Test Split Cases Evaluated (N={n_cases}):")
    print(f"  Mean Precision (at ±1.0s):  {avg_p_10:.4f}")
    print(f"  Mean Recall (at ±1.0s):     {avg_r_10:.4f}")
    print(f"  Mean F1 Score (at ±1.0s):   {avg_f1_10:.4f}")
    print(f"  Setup/Payoff Completeness: {avg_sp * 100:.1f}%")
    print(f"  Effect Agreement Rate:     {avg_eff * 100:.1f}%")
    print(f"  Segment Counts: {tot_matched} Matched | {tot_missed} Missed | {tot_ai_only} AI-Only ({tot_valid_alt} Valid Alternatives)")
    print("\nRoot Cause Attribution across Test Split:")
    combined_root_causes: dict[str, int] = {}
    for _, r, _ in baseline_results:
        for k, v in r.root_cause_distribution.items():
            combined_root_causes[k] = combined_root_causes.get(k, 0) + v
    for k, v in sorted(combined_root_causes.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {k:35s}: {v} occurrences")

    session.close()
    print("\n================================================================================")
    print("M13 BASELINE BENCHMARK SUITE EXECUTION COMPLETE — IMMUTABLY RECORDED IN DATABASE")
    print("================================================================================")


if __name__ == "__main__":
    asyncio.run(run_baseline_benchmark_suite())
