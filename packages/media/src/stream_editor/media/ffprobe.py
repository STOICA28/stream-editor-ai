import json
import subprocess
from typing import Any, Dict
from stream_editor.contracts.media import MediaInfo

def run_ffprobe(path: str) -> Dict[str, Any]:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path],
        capture_output=True,
        check=True,
        text=True
    )
    parsed: Dict[str, Any] = json.loads(result.stdout)
    return parsed

def get_media_info(path: str) -> MediaInfo:
    data = run_ffprobe(path)
    
    video_stream: Dict[str, Any] = next((s for s in data.get('streams', []) if s.get('codec_type') == 'video'), {})
    audio_stream: Dict[str, Any] = next((s for s in data.get('streams', []) if s.get('codec_type') == 'audio'), {})
    fmt: Dict[str, Any] = data.get('format', {})
    
    fps_str = video_stream.get('r_frame_rate', '0/1')
    fps = 0.0
    if '/' in fps_str:
        num, den = fps_str.split('/')
        if int(den) != 0:
            fps = float(num) / float(den)
    else:
        fps = float(fps_str)
        
    return MediaInfo(
        duration_seconds=float(fmt.get('duration', 0.0)),
        width=int(video_stream.get('width', 0)),
        height=int(video_stream.get('height', 0)),
        fps=fps,
        video_codec=video_stream.get('codec_name', ''),
        audio_codec=audio_stream.get('codec_name', ''),
        file_size_bytes=int(fmt.get('size', 0)),
        format_name=fmt.get('format_name', ''),
        bit_rate=int(fmt.get('bit_rate', 0))
    )
