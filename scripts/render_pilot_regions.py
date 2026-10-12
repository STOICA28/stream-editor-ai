"""Render pilot video demonstrations for the 3 diagnostic regions using neutral cuts and validate with MediaValidator."""
import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages" / "rendering" / "src"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "contracts" / "src"))

from stream_editor.rendering.validator import MediaValidator

SOURCE_MP4 = r"C:\Users\adria\Desktop\Descargas\source.mp4"
OUTPUT_DIR = Path("data/work/renders_pilot")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PILOT_SPECS = {
    "region_a_onboarding": {
        "title": "Region A: Session Onboarding & Premise (Admin Fluff Removed)",
        "clips": [
            (0.0, 53.02, "Opening premise & Schedule 1 satire introduction"),
            (188.74, 255.0, "Game campaign start & cartel naming 'Pacofi'"),
            (255.0, 310.0, "3D world spawn and store entrance"),
        ],
    },
    "region_b_transition": {
        "title": "Region B: Debt Payoff to Police Confrontation",
        "clips": [
            (5470.0, 5515.0, "Debt milestone: $280 threshold reached"),
            (5515.0, 5550.0, "Police car arrives & suspicious person check"),
        ],
    },
    "region_c_progression": {
        "title": "Region C: First Client Tutorial & Barber Styling",
        "clips": [
            (945.0, 1015.0, "Chelsea phone contact tutorial & first regular sale"),
            (1820.0, 1851.0, "Character aesthetic setup: 'traficante reventado'"),
            (1889.0, 1930.0, "Barber haircut completion & laughter reaction"),
        ],
    },
}

def render_clip(clip_index: int, start_sec: float, end_sec: float, temp_dir: Path) -> Path:
    dur = round(end_sec - start_sec, 2)
    out_path = temp_dir / f"clip_{clip_index}.mp4"
    print(f"  Rendering clip {clip_index}: {start_sec}s -> {end_sec}s ({dur}s)...")
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-t", str(dur),
        "-i", SOURCE_MP4,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-af", "afade=t=in:ss=0:d=0.01,afade=t=out:st=" + str(max(0, dur - 0.01)) + ":d=0.01",
        str(out_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path

def concat_clips(clip_paths: list[Path], final_path: Path, temp_dir: Path) -> Path:
    concat_list = temp_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for cp in clip_paths:
            f.write(f"file '{cp.resolve().as_posix()}'\n")
            
    print(f"  Concatenating {len(clip_paths)} clips into {final_path.name}...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(final_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return final_path

async def main():
    validator = MediaValidator()
    results = {}
    
    for key, spec in PILOT_SPECS.items():
        print(f"\n=======================================================")
        print(f"Rendering Pilot Demonstration: {spec['title']}")
        print(f"=======================================================")
        temp_dir = OUTPUT_DIR / f"temp_{key}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        clip_paths = []
        expected_dur = 0.0
        for idx, (s_start, s_end, desc) in enumerate(spec["clips"]):
            cp = render_clip(idx + 1, s_start, s_end, temp_dir)
            clip_paths.append(cp)
            expected_dur += (s_end - s_start)
            
        final_mp4 = OUTPUT_DIR / f"{key}_final.mp4"
        concat_clips(clip_paths, final_mp4, temp_dir)
        
        # Validate output with MediaValidator
        is_valid, msg = await validator.validate_output(final_mp4, expected_dur, tolerance=2.0)
        print(f"MediaValidator Result for {final_mp4.name}: {'PASSED' if is_valid else f'FAILED ({msg})'}")
        
        # Probe metadata directly with ffprobe
        p_cmd = ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(final_mp4)]
        p_res = subprocess.run(p_cmd, capture_output=True, check=True)
        meta = json.loads(p_res.stdout)
        act_dur = float(meta.get("format", {}).get("duration", 0.0))
        v_stream = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), {})
        w = v_stream.get("width")
        h = v_stream.get("height")
        codec = v_stream.get("codec_name")
        print(f"  Actual Duration: {act_dur:.2f}s (Expected: {expected_dur:.2f}s)")
        print(f"  Video: {w}x{h}, Codec: {codec}, File Size: {final_mp4.stat().st_size / (1024*1024):.2f} MB")
        
        results[key] = {
            "output_path": str(final_mp4),
            "expected_duration": expected_dur,
            "actual_duration": act_dur,
            "validator_passed": is_valid,
            "clips_count": len(spec["clips"]),
            "file_size_mb": round(final_mp4.stat().st_size / (1024 * 1024), 2),
            "resolution": f"{w}x{h}",
            "codec": codec,
        }

    out_summary = OUTPUT_DIR / "pilot_renders_manifest.json"
    with open(out_summary, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved pilot renders manifest to {out_summary}")

if __name__ == "__main__":
    asyncio.run(main())
