import json
import subprocess
from pathlib import Path

from stream_editor.contracts.media import MediaInfo, ProbeResult

_SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".ts", ".flv"}


def validate_video_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"Path is not a file: {path}")
    if path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {path.suffix}")


def _parse_fps(rate_str: str) -> float:
    """Safely parse a fractional frame rate string like '30000/1001' without eval()."""
    try:
        if "/" in rate_str:
            num, den = rate_str.split("/", 1)
            denominator = int(den)
            if denominator == 0:
                return 0.0
            return int(num) / denominator
        return float(rate_str)
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe_media(path: Path) -> ProbeResult:
    """Run ffprobe and return structured result. Never uses shell=True."""
    validate_video_path(path)
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    video_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"), None
    )
    audio_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None
    )
    format_data = data.get("format", {})

    fps = 0.0
    if video_stream:
        fps = _parse_fps(video_stream.get("r_frame_rate", "0/1"))

    media_info = MediaInfo(
        duration_seconds=float(format_data.get("duration", 0)),
        width=int(video_stream.get("width", 0)) if video_stream else 0,
        height=int(video_stream.get("height", 0)) if video_stream else 0,
        fps=fps,
        video_codec=video_stream.get("codec_name", "") if video_stream else "",
        audio_codec=audio_stream.get("codec_name", "") if audio_stream else "",
        file_size_bytes=int(format_data.get("size", 0)),
        format_name=format_data.get("format_name", ""),
        bit_rate=int(format_data.get("bit_rate", 0)),
    )

    return ProbeResult(path=str(path), media_info=media_info, raw_ffprobe=data)
