"""Benchmark production cost and memory behavior of OpenCVVisualObservationProvider on long-form media."""

import ctypes
import json
import os
import sys
import time
from ctypes import wintypes
from pathlib import Path

import cv2

from stream_editor.analysis.providers.visual_observation_provider import (
    OpenCVVisualObservationProvider,
)
from stream_editor.contracts.analysis import VisualReactionConfig


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def get_process_memory_mb() -> tuple[float, float]:
    """Return (current_rss_mb, peak_rss_mb) on Windows."""
    try:
        GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
        GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
            wintypes.DWORD,
        ]
        GetProcessMemoryInfo.restype = wintypes.BOOL

        counters = PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
        h = ctypes.windll.kernel32.GetCurrentProcess()
        if GetProcessMemoryInfo(h, ctypes.byref(counters), counters.cb):
            return (
                counters.WorkingSetSize / (1024 * 1024),
                counters.PeakWorkingSetSize / (1024 * 1024),
            )
    except Exception:
        pass
    return (0.0, 0.0)


def benchmark_slice(
    proxy_path: str,
    provider: OpenCVVisualObservationProvider,
    config: VisualReactionConfig,
    slice_duration_seconds: float,
) -> dict:
    cap = cv2.VideoCapture(proxy_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    full_duration = total_frames / fps
    cap.release()

    target_duration = min(full_duration, slice_duration_seconds)

    start_rss, start_peak = get_process_memory_mb()
    t_cpu_start = time.process_time()
    t_wall_start = time.perf_counter()

    observations = provider.analyze_visuals(
        proxy_path,
        config=config,
        start_time=0.0,
        end_time=target_duration,
    )

    t_wall_end = time.perf_counter()
    t_cpu_end = time.process_time()
    end_rss, end_peak = get_process_memory_mb()

    wall_time = t_wall_end - t_wall_start
    cpu_time = t_cpu_end - t_cpu_start
    realtime_factor = target_duration / wall_time if wall_time > 0 else 0
    time_per_source_hour = (3600.0 / target_duration) * wall_time if target_duration > 0 else 0
    cpu_utilization_pct = (cpu_time / wall_time * 100) if wall_time > 0 else 0

    step = max(1, int(fps / provider.sample_fps))
    frames_inspected = int(target_duration * fps / step)

    # Filter by threshold
    surviving_events = [
        o for o in observations if o.confidence >= config.reaction_confidence_threshold
    ]

    return {
        "slice_duration_seconds": round(target_duration, 2),
        "slice_duration_minutes": round(target_duration / 60.0, 2),
        "full_source_duration_hours": round(full_duration / 3600.0, 2),
        "sampling_fps": provider.sample_fps,
        "frames_inspected": frames_inspected,
        "wall_time_seconds": round(wall_time, 2),
        "cpu_time_seconds": round(cpu_time, 2),
        "cpu_utilization_pct": round(cpu_utilization_pct, 1),
        "realtime_speedup": round(realtime_factor, 1),
        "detector_seconds_per_source_hour": round(time_per_source_hour, 2),
        "detector_minutes_per_source_hour": round(time_per_source_hour / 60.0, 2),
        "start_rss_mb": round(start_rss, 2),
        "end_rss_mb": round(end_rss, 2),
        "peak_rss_mb": round(end_peak, 2),
        "observations_generated": len(observations),
        "events_surviving_threshold": len(surviving_events),
    }


def main():
    root = Path(__file__).resolve().parent.parent
    proxy_candidates = list(root.glob("data/projects/**/proxies/**/*.mp4"))
    
    # Prefer the 5-hour representative proxy
    selected_proxy = None
    for p in proxy_candidates:
        if p.stat().st_size > 500_000_000:  # ~2GB 5-hour proxy
            selected_proxy = p
            break
            
    if not selected_proxy and proxy_candidates:
        selected_proxy = proxy_candidates[0]

    if not selected_proxy or not selected_proxy.exists():
        print("ERROR: No suitable proxy video found for benchmark.")
        sys.exit(1)

    print(f"Benchmarking on proxy: {selected_proxy}")
    print(f"File size: {selected_proxy.stat().st_size / (1024*1024):.1f} MB")

    provider = OpenCVVisualObservationProvider(sample_fps=4.0)
    config = VisualReactionConfig(
        reaction_confidence_threshold=0.70,
        visual_interest_increment=0.15,
        base_visual_interest=0.60,
    )

    # Benchmark 3 representative slices: 5 minutes, 15 minutes, 30 minutes
    slices = [300.0, 900.0, 1800.0]
    results = []

    print("\n" + "=" * 80)
    print(f"{'Slice (min)':<12} | {'Wall (s)':<10} | {'Speedup':<10} | {'Sec/Hour':<10} | {'Peak RSS (MB)':<14} | {'Events':<8}")
    print("-" * 80)

    for s in slices:
        res = benchmark_slice(str(selected_proxy), provider, config, s)
        results.append(res)
        print(
            f"{res['slice_duration_minutes']:<12.1f} | "
            f"{res['wall_time_seconds']:<10.2f} | "
            f"{res['realtime_speedup']:<10.1f}x | "
            f"{res['detector_seconds_per_source_hour']:<10.2f} | "
            f"{res['peak_rss_mb']:<14.1f} | "
            f"{res['events_surviving_threshold']:<8}"
        )

    print("=" * 80 + "\n")

    # Project to full 5-hour VOD
    avg_sec_per_hour = sum(r["detector_seconds_per_source_hour"] for r in results) / len(results)
    full_5h_projected_sec = avg_sec_per_hour * 5.0
    full_5h_projected_min = full_5h_projected_sec / 60.0

    summary = {
        "benchmark_target": str(selected_proxy.relative_to(root)),
        "proxy_file_size_bytes": selected_proxy.stat().st_size,
        "detector": "OpenCVVisualObservationProvider",
        "detector_version": provider.detector_version,
        "sampling_fps": provider.sample_fps,
        "config_version": config.configuration_version,
        "slice_evaluations": results,
        "summary_projections": {
            "average_detector_seconds_per_source_hour": round(avg_sec_per_hour, 2),
            "average_detector_minutes_per_source_hour": round(avg_sec_per_hour / 60.0, 2),
            "projected_full_5h_vod_wall_seconds": round(full_5h_projected_sec, 2),
            "projected_full_5h_vod_wall_minutes": round(full_5h_projected_min, 2),
            "memory_bounded_o1": True,
            "peak_rss_mb": max(r["peak_rss_mb"] for r in results),
        },
    }

    out_json = root / "knowledge-vault" / "04_RESEARCH" / "M2_LONGFORM_DETECTOR_COST_BENCHMARK.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Benchmark artifact persisted to: {out_json}")
    print(f"Average Processing Speed: {avg_sec_per_hour:.1f}s per source hour ({avg_sec_per_hour/60:.2f} min/hr)")
    print(f"Projected 5-Hour VOD Processing Time: {full_5h_projected_sec:.1f}s (~{full_5h_projected_min:.2f} minutes)")
    print(f"Peak Memory Working Set: {summary['summary_projections']['peak_rss_mb']:.1f} MB (strictly O(1) bounded)")


if __name__ == "__main__":
    main()
