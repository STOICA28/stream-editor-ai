"""
Diagnostic Script: Audit existing M3 gaps and candidate fragmentation across VALIDATION cases.
Fulfills EXP-002 Section 9 and Section 10 requirements.
"""
import json
import math
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages" / "contracts" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "editorial" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "research" / "src"))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from benchmark_runner import load_fixture_data, build_current_streameditor_cut
from stream_editor.contracts.benchmark import EditorialBenchmarkCase, DatasetSplit


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


def compute_quantiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {"p10": 0.0, "p25": 0.0, "median": 0.0, "p75": 0.0, "p90": 0.0, "max": 0.0}
    return {
        "p10": round(quantile(values, 0.10), 3),
        "p25": round(quantile(values, 0.25), 3),
        "median": round(quantile(values, 0.50), 3),
        "p75": round(quantile(values, 0.75), 3),
        "p90": round(quantile(values, 0.90), 3),
        "max": round(max(values), 3),
    }


def audit_validation_cases():
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

    print("=" * 80)
    print("M13-P1 CANDIDATE & GAP AUDIT (VALIDATION CASES)")
    print("=" * 80)

    # Categories for gap distribution
    gaps_by_type = {
        "speech_to_event": [],
        "event_to_reaction": [],
        "speech_to_reaction": [],
        "reaction_to_payoff": [],
        "chat_to_reaction": [],
        "inter_candidate_gaps": [],
    }

    per_case_audit = []

    for case in validation_cases:
        gt_data = load_fixture_data(case.id)
        # Operational baseline M13-P1 has visual_reaction_elevation=True, setup_clustering_expansion=False
        timeline, artifacts = build_current_streameditor_cut(
            case, gt_data, visual_reaction_elevation=True, setup_clustering_expansion=False
        )

        events = artifacts.get("timeline_events", [])
        candidates = artifacts.get("candidates", [])
        story_nodes = artifacts.get("story_nodes", [])
        human_blocks = gt_data.get("blocks", [])

        # Measure inter-candidate gaps
        sorted_cand = sorted(candidates, key=lambda c: c["start_time"])
        case_inter_gaps = []
        for i in range(len(sorted_cand) - 1):
            gap = sorted_cand[i + 1]["start_time"] - sorted_cand[i]["end_time"]
            if gap > 0:
                case_inter_gaps.append(gap)
                gaps_by_type["inter_candidate_gaps"].append(gap)

        # Measure adjacent event relations
        sorted_ev = sorted(events, key=lambda e: e["start_time"])
        for i in range(len(sorted_ev) - 1):
            ev1 = sorted_ev[i]
            ev2 = sorted_ev[i + 1]
            gap = ev2["start_time"] - ev1["end_time"]
            t1 = ev1.get("event_type", "")
            t2 = ev2.get("event_type", "")

            if t1 == "speech" and t2 in ("gameplay", "gameplay_clutch", "event"):
                gaps_by_type["speech_to_event"].append(max(0.0, gap))
            elif t1 in ("gameplay", "gameplay_clutch", "event") and t2 in ("face_reaction", "pause_with_reaction"):
                gaps_by_type["event_to_reaction"].append(max(0.0, gap))
            elif t1 == "speech" and t2 in ("face_reaction", "pause_with_reaction"):
                gaps_by_type["speech_to_reaction"].append(max(0.0, gap))
            elif t1 in ("face_reaction", "pause_with_reaction") and t2 == "speech":
                gaps_by_type["reaction_to_payoff"].append(max(0.0, gap))
            elif t1 in ("chat_message", "chat_read") and t2 in ("face_reaction", "speech"):
                gaps_by_type["chat_to_reaction"].append(max(0.0, gap))

        # Check narrative fragmentation (beats split across multiple candidates)
        # e.g., in case-test-001, speech at 1-3s and reaction at 4-5s are separate candidates (c1: 1.2-3.0, c_rx: 4.0-5.0)
        # in case-test-002, setup at 0-2s and clutch at 4.5-8s are separate candidates
        case_info = {
            "case_id": case.id,
            "events_count": len(events),
            "candidates_count": len(candidates),
            "candidates": [(c["start_time"], c["end_time"], c.get("score")) for c in candidates],
            "human_blocks": [(b["source_start"], b["source_end"]) for b in human_blocks],
            "inter_candidate_gaps": case_inter_gaps,
        }
        per_case_audit.append(case_info)

        print(f"\n--- Case: {case.id} ({case.name}) ---")
        print(f"Timeline Events: {len(events)}")
        for ev in events:
            print(f"  Event: [{ev['start_time']:.1f}s - {ev['end_time']:.1f}s] {ev.get('event_type')}")
        print(f"M13-P1 Candidates: {len(candidates)}")
        for c in candidates:
            print(f"  Candidate: [{c['start_time']:.1f}s - {c['end_time']:.1f}s] score={c.get('score')}")
        print(f"Human Reference Blocks: {len(human_blocks)}")
        for b in human_blocks:
            print(f"  Human: [{b['source_start']:.1f}s - {b['source_end']:.1f}s]")
        print(f"Inter-candidate gaps: {case_inter_gaps}")

    print("\n" + "=" * 80)
    print("GAP DISTRIBUTIONS (EXP-002 Section 10)")
    print("=" * 80)
    for cat, vals in gaps_by_type.items():
        q = compute_quantiles(vals)
        print(f"{cat:<25} (N={len(vals):<2}): p10={q['p10']:<5} p25={q['p25']:<5} med={q['median']:<5} p75={q['p75']:<5} p90={q['p90']:<5} max={q['max']:<5}")

    # Write output to json for reporting
    out_path = ROOT_DIR / "m3_gap_audit_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "cases": per_case_audit,
            "gap_distributions": {cat: compute_quantiles(vals) for cat, vals in gaps_by_type.items()},
            "gap_samples": gaps_by_type,
        }, f, indent=2)
    print(f"\nSaved audit results to {out_path}")


if __name__ == "__main__":
    audit_validation_cases()
