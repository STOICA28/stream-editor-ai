#!/usr/bin/env python3
"""
Generate synthetic test media files for testing without copyrighted content.

Uses FFmpeg lavfi (virtual input) to produce color bars + sine tone.
These files are committed to tests/fixtures/ so tests can run without
any real media assets.

Usage:
    uv run python scripts/generate_test_media.py
"""
import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"


def ffmpeg_available() -> bool:
    """Check if FFmpeg is available on PATH."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def generate_test_video(
    output: Path,
    duration: int = 30,
    width: int = 1920,
    height: int = 1080,
    color: str = "blue",
) -> None:
    """
    Generate a synthetic test video with color bars and a sine tone.

    Uses only FFmpeg lavfi — no copyrighted content required.
    """
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",  # overwrite without asking
        # Video: solid color
        "-f", "lavfi",
        "-i", f"color=c={color}:size={width}x{height}:rate=30",
        # Audio: 440 Hz sine tone
        "-f", "lavfi",
        "-i", "sine=frequency=440:sample_rate=16000",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "35",
        "-c:a", "aac",
        "-b:a", "64k",
        str(output),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR generating {output}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    size_kb = output.stat().st_size // 1024
    print(f"  Generated: {output.name} ({size_kb} KB)")


def generate_test_audio(output: Path, duration: int = 10) -> None:
    """Generate a synthetic audio-only test file."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=220:sample_rate=16000",
        "-t", str(duration),
        "-c:a", "aac",
        "-b:a", "64k",
        str(output),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR generating {output}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    size_kb = output.stat().st_size // 1024
    print(f"  Generated: {output.name} ({size_kb} KB)")


def main() -> None:
    if not ffmpeg_available():
        print(
            "ERROR: FFmpeg not found on PATH.\n"
            "Install FFmpeg: https://ffmpeg.org/download.html",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Generating synthetic test media in {FIXTURES_DIR} ...")

    # Standard test clips
    generate_test_video(FIXTURES_DIR / "test_30s.mp4", duration=30, color="blue")
    generate_test_video(FIXTURES_DIR / "test_5s.mp4", duration=5, color="red")
    generate_test_video(
        FIXTURES_DIR / "test_proxy_30s.mp4",
        duration=30,
        width=1280,
        height=720,
        color="green",
    )
    generate_test_audio(FIXTURES_DIR / "test_audio_10s.aac", duration=10)

    print("\nTest media generated successfully.")
    print(f"Files are in: {FIXTURES_DIR}")
    print("\nNote: These files are committed to tests/fixtures/ for CI use.")


if __name__ == "__main__":
    main()