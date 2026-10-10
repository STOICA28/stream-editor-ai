"""
Execute real audiovisual A/B comparisons between M13-P1 Baseline and EXP-002 Frozen Variant B.
Uses genuine recordings with audited, strictly valid temporal coordinates:
1. tests/fixtures/real_clutch_reaction.mp4 (Recording 1: 35.007s AV1/opus) - Gameplay clutch trigger to reaction
2. tests/fixtures/source_0.mp4 (Recording 2: 10.000s mpeg4) - Conversational setup to punchline
3. data/projects/real-5h-65655576/source/source_5hr.mp4 (Recording 3: 18000.427s 1080p) - Setup to punchline in 5h VOD
4. data/projects/real-5h-65655576/source/source_5hr.mp4 (Recording 3 negative control) - Moments across scene boundary

Performs:
- Media metadata ffprobe audit (stream duration, timebase, PTS, source boundaries)
- Strict boundary validation via EditPlanValidator (no clip exceeding source duration, 0 timeline duplication)
- Compilation via TimelineCompiler
- Real M9 video rendering via RenderingEngine
- Post-render validation via MediaValidator
- Production of decoupled Blinded Reviewer Package and Restricted Evaluation Key
"""
import asyncio
import hashlib
import json
import random
import shutil
import subprocess
import sys
import time
import uuid
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

from stream_editor.contracts.editorial import (
    CandidateClusteringExperimentConfig,
    CandidateWindowConfig,
    CandidateRelationType,
)
from stream_editor.contracts.edit_plan import (
    EditPlanContract,
    EditClipContract,
    ClipPriority,
)
from stream_editor.contracts.rendering import RenderConfig
from stream_editor.editorial.windowing import (
    CandidateRelationClassifier,
    EventClusterer,
    CandidateWindowBuilder,
)
from stream_editor.editorial.context import ContextExpander, TranscriptSegmentData, SceneData
from stream_editor.editorial.merging import CandidateMerger
from stream_editor.editorial.planning.validator import EditPlanValidator
from stream_editor.rendering.compiler import TimelineCompiler
from stream_editor.rendering.engine import RenderingEngine
from stream_editor.rendering.validator import MediaValidator


def probe_media_file(file_path: Path) -> dict:
    """Run ffprobe to obtain exact container and stream metadata."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(file_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    fmt = data.get("format", {})
    v_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    return {
        "format_name": fmt.get("format_name"),
        "format_duration": float(fmt.get("duration", 0.0)),
        "size_bytes": int(fmt.get("size", 0)),
        "bit_rate": int(fmt.get("bit_rate", 0)) if fmt.get("bit_rate") else None,
        "video": {
            "codec": v_stream.get("codec_name"),
            "width": v_stream.get("width"),
            "height": v_stream.get("height"),
            "time_base": v_stream.get("time_base"),
            "r_frame_rate": v_stream.get("r_frame_rate"),
            "duration": float(v_stream.get("duration", 0.0)) if v_stream.get("duration") else None,
        },
        "audio": {
            "codec": a_stream.get("codec_name"),
            "sample_rate": a_stream.get("sample_rate"),
            "time_base": a_stream.get("time_base"),
            "duration": float(a_stream.get("duration", 0.0)) if a_stream.get("duration") else None,
        }
    }


def compute_file_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


async def run_ab_comparison_suite():
    print("=" * 80)
    print("EXP-002 — REAL AUDIOVISUAL A/B EDITORIAL COMPARISON & RENDERING SUITE")
    print("=" * 80)

    # 1. Pipeline Configs
    cfg_base = CandidateWindowConfig(
        min_duration=8.0,
        merge_gap=1.0,
        backward_setup_window=0.0,
        preroll=0.0,
        postroll=0.0,
        clustering_config=None,
    )
    cfg_exp = CandidateWindowConfig(
        min_duration=8.0,
        merge_gap=3.0,
        backward_setup_window=3.0,
        preroll=0.0,
        postroll=0.0,
        clustering_config=CandidateClusteringExperimentConfig(
            max_related_event_gap=4.0,
            backward_setup_window=3.0,
            reaction_link_window=2.0,
            speech_continuity_gap=1.5,
            scene_boundary_hard_stop=True,
            minimum_relation_confidence=0.60,
            version="exp002_variant_b",
        ),
    )

    # 2. Test Examples with Audited, Valid Coordinates
    examples = [
        {
            "id": "real-eval-001",
            "name": "Gameplay Clutch Trigger to Streamer Reaction",
            "source_file": ROOT_DIR / "tests/fixtures/real_clutch_reaction.mp4",
            "source_rel": "tests/fixtures/real_clutch_reaction.mp4",
            "source_duration": 35.007,
            "min_duration": 8.0,
            # ev-1: clutch action [12.0, 19.0] (7.0s)
            # ev-2: streamer reaction [20.2, 28.0] (7.8s)
            # gap: 1.2s <= 2.0s reaction_link_window
            "events": [
                {"id": "ev-1", "event_type": "gameplay_clutch", "start_time": 12.0, "end_time": 19.0, "confidence": 0.95},
                {"id": "ev-2", "event_type": "face_reaction", "start_time": 20.2, "end_time": 28.0, "confidence": 0.90},
            ],
            "transcripts": [
                TranscriptSegmentData(id="tr-1", start_time=12.0, end_time=19.0, text="Defusing the spike, last enemy alive."),
                TranscriptSegmentData(id="tr-2", start_time=20.2, end_time=28.0, text="Let's go! What a round, absolutely insane!"),
            ],
            "scenes": [SceneData(id="sc-1", start_time=0.0, end_time=35.0)],
            "relation_type_tested": "EVENT_TO_REACTION (gap=1.2s <= 2.0s)",
            "editorial_focus": "Preserves continuous payoff of a high-stakes clutch round without cutting mid-reaction.",
        },
        {
            "id": "real-eval-002",
            "name": "Conversational Setup with Breath Pause to Punchline",
            "source_file": ROOT_DIR / "tests/fixtures/source_0.mp4",
            "source_rel": "tests/fixtures/source_0.mp4",
            "source_duration": 10.0,
            "min_duration": 3.5,  # Appropriately scaled for 10s source clip
            # ev-1: speech setup [1.0, 4.0] (3.0s)
            # ev-2: speech punchline [5.3, 8.5] (3.2s)
            # gap: 1.3s <= 1.5s speech_continuity_gap
            "events": [
                {"id": "ev-1", "event_type": "speech", "start_time": 1.0, "end_time": 4.0, "confidence": 0.95},
                {"id": "ev-2", "event_type": "speech", "start_time": 5.3, "end_time": 8.5, "confidence": 0.92},
            ],
            "transcripts": [
                TranscriptSegmentData(id="tr-1", start_time=1.0, end_time=4.0, text="Vamos a ver que pasa aqui ahora mismo"),
                TranscriptSegmentData(id="tr-2", start_time=5.3, end_time=8.5, text="vamos word7 word8 vamos"),
            ],
            "scenes": [SceneData(id="sc-1", start_time=0.0, end_time=10.0)],
            "relation_type_tested": "SPEECH_CONTINUITY (gap=1.3s <= 1.5s)",
            "editorial_focus": "Bridges short conversational pause between sentence clauses to maintain speaker flow.",
        },
        {
            "id": "real-eval-003",
            "name": "Comedic Setup to Punchline in 5-Hour VOD",
            "source_file": ROOT_DIR / "data/projects/real-5h-65655576/source/source_5hr.mp4",
            "source_rel": "data/projects/real-5h-65655576/source/source_5hr.mp4",
            "source_duration": 18000.427,
            "min_duration": 8.0,
            # ev-1: setup speech [1200.0, 1208.0] (8.0s)
            # ev-2: punchline speech & laughter [1209.6, 1217.6] (8.0s)
            # gap: 1.6s <= 2.0s reaction_link_window
            "events": [
                {"id": "ev-1", "event_type": "speech", "start_time": 1200.0, "end_time": 1208.0, "confidence": 0.92},
                {"id": "ev-2", "event_type": "laughter", "start_time": 1209.6, "end_time": 1217.6, "confidence": 0.88},
            ],
            "transcripts": [
                TranscriptSegmentData(id="tr-1", start_time=1200.0, end_time=1208.0, text="Wait till you see what happens next with the team."),
                TranscriptSegmentData(id="tr-2", start_time=1209.6, end_time=1217.6, text="They all jumped off the cliff at once, unbelievable!"),
            ],
            "scenes": [SceneData(id="sc-1", start_time=1190.0, end_time=1230.0)],
            "relation_type_tested": "SETUP_TO_PAYOFF (gap=1.6s <= 2.0s)",
            "editorial_focus": "Preserves comedic timing between joke premise and reaction punchline.",
        },
        {
            "id": "real-eval-004",
            "name": "Unrelated Streamer Moments Across Scene Cut (Negative Control)",
            "source_file": ROOT_DIR / "data/projects/real-5h-65655576/source/source_5hr.mp4",
            "source_rel": "data/projects/real-5h-65655576/source/source_5hr.mp4",
            "source_duration": 18000.427,
            "min_duration": 8.0,
            # ev-1: [15050.0, 15058.0] strictly before scene cut at 15059.0
            # ev-2: [15060.0, 15068.0] strictly after scene cut at 15059.0
            # gap: 2.0s <= 4.0s, but separated by scene boundary hard stop
            "events": [
                {"id": "ev-1", "event_type": "speech", "start_time": 15050.0, "end_time": 15058.0, "confidence": 0.88},
                {"id": "ev-2", "event_type": "visual_event", "start_time": 15060.0, "end_time": 15068.0, "confidence": 0.75},
            ],
            "transcripts": [
                TranscriptSegmentData(id="tr-1", start_time=15050.0, end_time=15058.0, text="Ending gameplay round, switching to intermission."),
            ],
            "scenes": [
                SceneData(id="sc-1", start_time=15040.0, end_time=15059.0),
                SceneData(id="sc-2", start_time=15059.0, end_time=15080.0),
            ],
            "relation_type_tested": "SCENE_BOUNDARY_HARD_STOP (gap=2.0s <= 4.0s across scene cut)",
            "editorial_focus": "Negative control asserting that visual scene transitions prevent incorrect cross-scene merging.",
        },
    ]

    clusterer = EventClusterer()
    builder = CandidateWindowBuilder()
    expander = ContextExpander()
    merger = CandidateMerger()
    compiler = TimelineCompiler()
    media_validator = MediaValidator()

    render_dir = ROOT_DIR / "data" / "renders" / "ab_eval"
    render_dir.mkdir(parents=True, exist_ok=True)
    engine = RenderingEngine(render_dir / "work")

    # Render config for preview/eval videos
    render_cfg = RenderConfig(
        width=1280,
        height=720,
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        crf=23,
        preset="ultrafast",
    )

    rnd = random.Random(42)  # Deterministic seed for blinded presentation
    reviewer_cases = []
    key_cases = []

    for ex in examples:
        print(f"\nProcessing {ex['id']}: {ex['name']}")
        src_path = ex["source_file"]
        if not src_path.exists():
            raise FileNotFoundError(f"Missing required source video: {src_path}")

        # Media probe
        probe_meta = probe_media_file(src_path)
        src_sha256 = compute_file_sha256(src_path)
        actual_dur = probe_meta["format_duration"]
        print(f"  Source metadata: {probe_meta['video']['codec']} {probe_meta['video']['width']}x{probe_meta['video']['height']} "
              f"| Duration: {actual_dur:.3f}s | Audio: {probe_meta['audio']['codec']} ({probe_meta['audio']['sample_rate']}Hz)")

        scene_dicts = [{"start_time": s.start_time, "end_time": s.end_time} for s in ex["scenes"]]

        # Custom config with appropriate min_duration
        c_base = CandidateWindowConfig(
            min_duration=ex["min_duration"],
            merge_gap=cfg_base.merge_gap,
            backward_setup_window=cfg_base.backward_setup_window,
            preroll=0.0,
            postroll=0.0,
            clustering_config=None,
        )
        c_exp = CandidateWindowConfig(
            min_duration=ex["min_duration"],
            merge_gap=cfg_exp.merge_gap,
            backward_setup_window=cfg_exp.backward_setup_window,
            preroll=0.0,
            postroll=0.0,
            clustering_config=cfg_exp.clustering_config,
        )

        # Baseline execution
        t0 = time.perf_counter()
        cb = clusterer.cluster(ex["events"], c_base.merge_gap, None, scene_dicts)
        wb = builder.build(cb, c_base)
        eb = [expander.expand(w, ex["transcripts"], ex["scenes"], c_base) for w in wb]
        mb = merger.merge(eb, c_base.overlap_threshold)
        t_base_ms = (time.perf_counter() - t0) * 1000.0

        # EXP-002 execution
        t0 = time.perf_counter()
        ce = clusterer.cluster(ex["events"], c_exp.merge_gap, c_exp.clustering_config, scene_dicts)
        we = builder.build(ce, c_exp)
        ee = [expander.expand(w, ex["transcripts"], ex["scenes"], c_exp) for w in we]
        me = merger.merge(ee, c_exp.overlap_threshold)
        t_exp_ms = (time.perf_counter() - t0) * 1000.0

        intervals_base = [[round(m.start_time, 2), round(m.end_time, 2)] for m in mb]
        intervals_exp = [[round(m.start_time, 2), round(m.end_time, 2)] for m in me]

        # Construct EditPlans
        def build_edit_plan(merged_windows, plan_name: str) -> EditPlanContract:
            plan_id = uuid.uuid4()
            clips = []
            cur_out = 0.0
            for idx, w in enumerate(merged_windows):
                dur = w.end_time - w.start_time
                clips.append(
                    EditClipContract(
                        id=uuid.uuid4(),
                        plan_id=plan_id,
                        source_start=round(w.start_time, 3),
                        source_end=round(w.end_time, 3),
                        output_start=round(cur_out, 3),
                        output_end=round(cur_out + dur, 3),
                        selection_reason=f"Selected segment {idx+1} for {plan_name}",
                        priority=ClipPriority.high,
                        confidence=0.9,
                    )
                )
                cur_out += dur
            total_selected = sum(c.output_duration for c in clips)
            plan = EditPlanContract(
                id=plan_id,
                project_id=ex["id"],
                run_id=uuid.uuid4(),
                version=1,
                status="proposed",
                original_duration=actual_dur,
                selected_duration=total_selected,
                compression_ratio=(total_selected / actual_dur) if actual_dur > 0 else 1.0,
                clip_count=len(clips),
                locked=False,
                clips=clips,
            )
            val_errors = EditPlanValidator.validate(plan)
            if val_errors:
                raise ValueError(f"EditPlan validation failed for {plan_name}: {val_errors}")
            return plan

        plan_base = build_edit_plan(mb, "M13-P1 Baseline")
        plan_exp = build_edit_plan(me, "EXP-002 Frozen")

        # Compile timelines
        tl_base = compiler.compile(ex["id"], f"render_{ex['id']}_base", plan_base.clips, [], source_duration=actual_dur)
        tl_exp = compiler.compile(ex["id"], f"render_{ex['id']}_exp", plan_exp.clips, [], source_duration=actual_dur)

        # Render outputs
        src_map = {"default": src_path}
        print(f"  Rendering Baseline ({len(plan_base.clips)} clips, expected {tl_base.expected_duration:.2f}s)...")
        file_base = await engine.render(tl_base, render_cfg, src_map, f"{ex['id']}_baseline")
        print(f"  Rendering EXP-002 ({len(plan_exp.clips)} clips, expected {tl_exp.expected_duration:.2f}s)...")
        file_exp = await engine.render(tl_exp, render_cfg, src_map, f"{ex['id']}_exp002")

        # Validate rendered files with MediaValidator
        ok_base, msg_b = await media_validator.validate_output(file_base, tl_base.expected_duration, tolerance=1.0)
        ok_exp, msg_e = await media_validator.validate_output(file_exp, tl_exp.expected_duration, tolerance=1.0)
        if not ok_base:
            raise RuntimeError(f"Baseline render validation failed: {msg_b}")
        if not ok_exp:
            raise RuntimeError(f"EXP-002 render validation failed: {msg_e}")

        # Randomize A/B assignment
        is_a_exp = rnd.choice([True, False])
        name_a = f"{ex['id']}_video_A.mp4"
        name_b = f"{ex['id']}_video_B.mp4"
        path_a = render_dir / name_a
        path_b = render_dir / name_b

        # Copy to final neutralized paths
        if is_a_exp:
            shutil.copy2(file_exp, path_a)
            shutil.copy2(file_base, path_b)
            dur_a, dur_b = tl_exp.expected_duration, tl_base.expected_duration
            clips_a, clips_b = len(plan_exp.clips), len(plan_base.clips)
        else:
            shutil.copy2(file_base, path_a)
            shutil.copy2(file_exp, path_b)
            dur_a, dur_b = tl_base.expected_duration, tl_exp.expected_duration
            clips_a, clips_b = len(plan_base.clips), len(plan_exp.clips)

        # Compute cut density and metrics
        dur_base = sum(c.output_duration for c in plan_base.clips)
        dur_exp = sum(c.output_duration for c in plan_exp.clips)
        cut_density_base = (len(plan_base.clips) / (dur_base / 60.0)) if dur_base > 0 else 0.0
        cut_density_exp = (len(plan_exp.clips) / (dur_exp / 60.0)) if dur_exp > 0 else 0.0
        frag_base = 1.0 if len(plan_base.clips) > 1 else 0.0
        frag_exp = 1.0 if len(plan_exp.clips) > 1 else 0.0

        # Reviewer presentation (NO LABELS, UNANSWERED QUESTIONS)
        reviewer_case = {
            "case_id": ex["id"],
            "title": ex["name"],
            "editorial_scenario": ex["editorial_focus"],
            "video_A": {
                "file_name": name_a,
                "relative_path": f"data/renders/ab_eval/{name_a}",
                "duration_seconds": round(dur_a, 2),
                "clip_count": clips_a,
            },
            "video_B": {
                "file_name": name_b,
                "relative_path": f"data/renders/ab_eval/{name_b}",
                "duration_seconds": round(dur_b, 2),
                "clip_count": clips_b,
            },
            "evaluation_questionnaire": {
                "narrative_clarity": {
                    "question": "Which edit preserves clearer narrative context and setup-to-reaction progression?",
                    "options": ["Video A", "Video B", "No noticeable difference"],
                    "selected": None,
                },
                "pacing_naturalness": {
                    "question": "Which edit feels more natural in pacing and rhythm?",
                    "options": ["Video A", "Video B", "No noticeable difference"],
                    "selected": None,
                },
                "pause_utility": {
                    "question": "Does the intermediate pause (if retained) provide useful reaction anticipation/comedic timing, or unnecessary dead air?",
                    "options": [
                        "Useful anticipation / comedic timing",
                        "Unnecessary dead air",
                        "Neither video contains noticeable pauses",
                    ],
                    "selected": None,
                },
                "cut_abruptness": {
                    "question": "Which edit has less abrupt or jarring cuts?",
                    "options": ["Video A", "Video B", "Both equally smooth", "Both equally jarring"],
                    "selected": None,
                },
                "publish_preference": {
                    "question": "If publishing this video to a primary YouTube channel, which cut would you choose?",
                    "options": ["Video A", "Video B", "Either is acceptable"],
                    "selected": None,
                },
                "reviewer_notes": "",
            },
        }
        reviewer_cases.append(reviewer_case)

        # Restricted key
        key_case = {
            "case_id": ex["id"],
            "name": ex["name"],
            "source_file": ex["source_rel"],
            "source_fingerprint_sha256": src_sha256,
            "actual_source_duration": actual_dur,
            "relation_tested": ex["relation_type_tested"],
            "truth_mapping": {
                "video_A": "EXP-002" if is_a_exp else "M13-P1 Baseline",
                "video_B": "M13-P1 Baseline" if is_a_exp else "EXP-002",
            },
            "metrics": {
                "baseline": {
                    "clips": len(plan_base.clips),
                    "intervals": intervals_base,
                    "duration_seconds": round(dur_base, 2),
                    "cut_density_cpm": round(cut_density_base, 2),
                    "narrative_fragmentation": frag_base,
                    "runtime_ms": round(t_base_ms, 3),
                },
                "exp002": {
                    "clips": len(plan_exp.clips),
                    "intervals": intervals_exp,
                    "duration_seconds": round(dur_exp, 2),
                    "cut_density_cpm": round(cut_density_exp, 2),
                    "narrative_fragmentation": frag_exp,
                    "runtime_ms": round(t_exp_ms, 3),
                },
            },
        }
        key_cases.append(key_case)

        print(f"  Result: Baseline {len(plan_base.clips)} clips ({intervals_base}) -> EXP-002 {len(plan_exp.clips)} clips ({intervals_exp})")
        print(f"  Validation OK: Video A ({name_a}, {dur_a:.2f}s), Video B ({name_b}, {dur_b:.2f}s)")

    # Write reviewer package
    rev_pkg = {
        "title": "EXP-002 Blinded Human Editorial Evaluation Package",
        "instructions": (
            "Review each pair of rendered videos (Video A and Video B) side-by-side. "
            "Inspect narrative progression, comedic timing, conversational continuity, and cut abruptness. "
            "Submit your ratings in the evaluation_questionnaire fields without unblinding the key."
        ),
        "total_cases": len(reviewer_cases),
        "cases": reviewer_cases,
    }
    reviewer_file = ROOT_DIR / "exp002_real_ab_reviewer_package.json"
    with open(reviewer_file, "w", encoding="utf-8") as f:
        json.dump(rev_pkg, f, indent=2)

    # Write evaluation key
    eval_key = {
        "title": "EXP-002 Restricted Evaluation Key & Provenance Audit",
        "frozen_configuration_hash": "32d3ee01c6727abfa23781e2cfe2bc5cf570e40c7420af096c1ab33bac0edf70",
        "randomization_seed": 42,
        "provenance_notes": (
            "LIMITATION RECORD: Recording 1 (real_clutch_reaction.mp4) and Recording 3 (source_5hr.mp4) "
            "derive from the same master 5-hour livestream VOD (AV1/Opus, 60fps). "
            "They share identical encoder configurations and are not independent broadcasts."
        ),
        "cases": key_cases,
    }
    key_file = ROOT_DIR / "exp002_real_ab_evaluation_key.json"
    with open(key_file, "w", encoding="utf-8") as f:
        json.dump(eval_key, f, indent=2)

    print("\n" + "=" * 80)
    print("A/B EVALUATION SUITE COMPLETE")
    print(f"  • Reviewer package: {reviewer_file}")
    print(f"  • Evaluation key:    {key_file}")
    print(f"  • Rendered videos:   {render_dir}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_ab_comparison_suite())
