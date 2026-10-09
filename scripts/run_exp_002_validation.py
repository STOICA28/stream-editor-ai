"""
EXP-002 Validation Experiment Runner.
Evaluates M13-P1 Baseline and Variants A, B, C on the VALIDATION split cases.
Fulfills EXP-002 Sections 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29.
"""
import asyncio
import json
import math
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "packages" / "contracts" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "editorial" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "research" / "src"))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from benchmark_runner import (
    load_fixture_data,
    build_current_streameditor_cut,
    build_human_reference_timeline,
)
from stream_editor.contracts.benchmark import EditorialBenchmarkCase, DatasetSplit
from stream_editor.contracts.editorial import CandidateClusteringExperimentConfig, CandidateWindowConfig
from stream_editor.research.benchmark.engine import EditorialBenchmarkEngine


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    idx = (len(sorted_v) - 1) * q
    lower = int(math.floor(idx))
    upper = int(math.ceil(idx))
    if lower == upper:
        return sorted_v[lower]
    return sorted_v[lower] * (upper - idx) + sorted_v[upper] * (idx - lower)


async def evaluate_variant(variant_name: str, clustering_cfg: CandidateClusteringExperimentConfig | None, cases: list[EditorialBenchmarkCase]):
    engine = EditorialBenchmarkEngine()
    case_results = []

    for case in cases:
        gt_data = load_fixture_data(case.id)
        human_timeline = build_human_reference_timeline(
            case_id=case.id,
            data=gt_data,
            source_duration=case.duration_source,
            edit_duration=case.duration_human_edit,
        )

        use_expansion = clustering_cfg is not None
        ai_timeline, artifacts = build_current_streameditor_cut(
            case, gt_data, visual_reaction_elevation=True, setup_clustering_expansion=use_expansion
        )

        result, failures = await engine.evaluate_case(
            run_id=f"run-{variant_name}-{case.id}",
            case=case,
            human_timeline=human_timeline,
            ai_timeline=ai_timeline,
            pipeline_artifacts=artifacts,
        )

        candidates = artifacts.get("candidates", [])
        durations = [c["end_time"] - c["start_time"] for c in candidates]
        mean_dur = (sum(durations) / len(durations)) if durations else 0.0
        p50_dur = quantile(durations, 0.50)
        p90_dur = quantile(durations, 0.90)

        # Fragmentation: beats split across >1 independent candidate
        # Over-merge: candidates containing unrelated narrative beats
        # Dead air: silence duration in AI retained intervals
        dead_air = result.pacing.dead_air_seconds
        ai_only_dur = result.overlap_at_10s.ai_retained_duration - result.overlap_at_10s.intersection_duration

        case_results.append({
            "case_id": case.id,
            "precision": result.overlap_at_10s.precision,
            "recall": result.overlap_at_10s.recall,
            "f1": result.overlap_at_10s.f1,
            "setup_payoff_rate": result.narrative.setup_payoff_completeness,
            "pre_context_median": result.context.pre_context_diff_quantiles.median,
            "post_context_median": result.context.post_context_diff_quantiles.median,
            "candidate_count": len(candidates),
            "mean_candidate_duration": round(mean_dur, 2),
            "p50_candidate_duration": round(p50_dur, 2),
            "p90_candidate_duration": round(p90_dur, 2),
            "ai_only_duration": round(max(0.0, ai_only_dur), 2),
            "dead_air": round(dead_air, 2),
            "redundancy": round(result.pacing.dead_air_percentage, 4),
            "selected_duration": round(result.overlap_at_10s.ai_retained_duration, 2),
        })

    # Macro averages
    macro_p = sum(r["precision"] for r in case_results) / len(case_results)
    macro_r = sum(r["recall"] for r in case_results) / len(case_results)
    macro_f1 = sum(r["f1"] for r in case_results) / len(case_results)
    macro_sp = sum(r["setup_payoff_rate"] for r in case_results) / len(case_results)
    avg_pre = sum(r["pre_context_median"] for r in case_results) / len(case_results)
    avg_post = sum(r["post_context_median"] for r in case_results) / len(case_results)
    total_ai_only = sum(r["ai_only_duration"] for r in case_results)
    total_dead_air = sum(r["dead_air"] for r in case_results)

    return {
        "variant": variant_name,
        "config": clustering_cfg.model_dump() if clustering_cfg else "BASELINE_M13_P1",
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "setup_payoff_rate": round(macro_sp, 4),
        "mean_pre_context_delta": round(avg_pre, 3),
        "mean_post_context_delta": round(avg_post, 3),
        "total_ai_only_duration": round(total_ai_only, 2),
        "total_dead_air": round(total_dead_air, 2),
        "cases": case_results,
    }


async def main():
    validation_cases = [
        EditorialBenchmarkCase(
            id="case-val-001",
            name="Validation Pair 0",
            source_asset_id="asset-val-src-0",
            human_edit_asset_id="asset-val-edit-0",
            reference_project_id="proj-m13-benchmarks",
            duration_source=10.0,
            duration_human_edit=8.0,
            split=DatasetSplit.VALIDATION,
            tags=["validation"],
            notes="",
        ),
        EditorialBenchmarkCase(
            id="case-test-001",
            name="Validation Pair 1 (Consumed)",
            source_asset_id="asset-test-src-1",
            human_edit_asset_id="asset-test-edit-1",
            reference_project_id="proj-m13-benchmarks",
            duration_source=10.0,
            duration_human_edit=7.0,
            split=DatasetSplit.VALIDATION,
            tags=["validation", "consumed"],
            notes="",
        ),
        EditorialBenchmarkCase(
            id="case-test-002",
            name="Validation Pair 2 (Consumed)",
            source_asset_id="asset-test-src-2",
            human_edit_asset_id="asset-test-edit-2",
            reference_project_id="proj-m13-benchmarks",
            duration_source=10.0,
            duration_human_edit=6.0,
            split=DatasetSplit.VALIDATION,
            tags=["validation", "consumed"],
            notes="",
        ),
        EditorialBenchmarkCase(
            id="case-test-real-001",
            name="Validation Real VOD Aligned Slice (Consumed)",
            source_asset_id="asset-test-real-src",
            human_edit_asset_id="asset-test-real-edit",
            reference_project_id="proj-m13-benchmarks",
            duration_source=300.0,
            duration_human_edit=62.5,
            split=DatasetSplit.VALIDATION,
            tags=["validation", "real_vod", "consumed"],
            notes="",
        ),
    ]

    # Variants defined per Section 17:
    variants = [
        ("Baseline (M13-P1)", None),
        ("Variant A (Conservative)", CandidateClusteringExperimentConfig(
            max_backward_context=2.0,
            max_forward_context=2.0,
            max_related_event_gap=3.0,
            reaction_link_window=1.5,
            speech_continuity_gap=1.2,
            pause_snap_threshold=0.25,
            scene_boundary_hard_stop=True,
            minimum_relation_confidence=0.70,
            version="exp002_variant_a",
        )),
        ("Variant B (Balanced)", CandidateClusteringExperimentConfig(
            max_backward_context=3.0,
            max_forward_context=3.0,
            max_related_event_gap=4.0,
            reaction_link_window=2.0,
            speech_continuity_gap=1.5,
            pause_snap_threshold=0.30,
            scene_boundary_hard_stop=True,
            minimum_relation_confidence=0.60,
            version="exp002_variant_b",
        )),
        ("Variant C (Context-rich)", CandidateClusteringExperimentConfig(
            max_backward_context=5.0,
            max_forward_context=5.0,
            max_related_event_gap=5.0,
            reaction_link_window=2.5,
            speech_continuity_gap=2.0,
            pause_snap_threshold=0.40,
            scene_boundary_hard_stop=True,
            minimum_relation_confidence=0.50,
            version="exp002_variant_c",
        )),
    ]

    print("=" * 90)
    print("EXP-002 VALIDATION VARIANT COMPARISON (M13-P1 vs Variant A, B, C)")
    print("=" * 90)

    all_results = []
    for name, cfg in variants:
        res = await evaluate_variant(name, cfg, validation_cases)
        all_results.append(res)
        print(f"\n--- {name} ---")
        print(f"Macro Precision:     {res['macro_precision']:.4f}")
        print(f"Macro Recall:        {res['macro_recall']:.4f}")
        print(f"Macro F1 Score:      {res['macro_f1']:.4f}")
        print(f"Setup/Payoff Rate:   {res['setup_payoff_rate']:.4f}")
        print(f"Mean Pre-Context Delta:  {res['mean_pre_context_delta']:+.3f}s")
        print(f"Mean Post-Context Delta: {res['mean_post_context_delta']:+.3f}s")
        print(f"Total AI-Only Dur:   {res['total_ai_only_duration']:.2f}s")
        print(f"Total Dead Air:      {res['total_dead_air']:.2f}s")

    # Save to json
    out_file = ROOT_DIR / "exp002_validation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved validation results to {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
