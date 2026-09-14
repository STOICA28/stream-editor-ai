import os
from pathlib import Path
from stream_editor.contracts.media import ProxyConfig, AudioConfig, MediaInfo
from stream_editor.media.probe import probe_media, validate_video_path

def validate_proxy(path: str, source_info: MediaInfo, config: ProxyConfig) -> None:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError("Proxy artifact missing")

    # Temporarily add path to supported extensions if not there for probe
    # probe_media uses validate_video_path which checks extensions.
    
    # We will do a direct probe without validate_video_path if needed, but .mp4 is supported.
    res = probe_media(p)
    info = res.media_info
    
    if info.width == 0 or info.height == 0:
        raise ValueError("Proxy lacks video stream or dimensions")
        
    if info.height > config.max_height:
        raise ValueError(f"Proxy height {info.height} exceeds configured maximum {config.max_height}")
        
    # Duration validation
    if abs(info.duration_seconds - source_info.duration_seconds) > 2.0: # 2 second tolerance
        raise ValueError(f"Proxy duration ({info.duration_seconds}) deviates from source ({source_info.duration_seconds})")
        
def validate_audio(path: str, source_info: MediaInfo, config: AudioConfig) -> None:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError("Audio artifact missing")

    # We need a probe_media variant that accepts audio formats, because probe_media strictly checks video extensions.
    # We'll just run ffprobe directly here.
    import subprocess, json
    
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(p),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not audio_stream:
        raise ValueError("No audio stream found in artifact")
        
    if int(audio_stream.get("sample_rate", 0)) != config.sample_rate:
        raise ValueError("Audio sample rate does not match configuration")
        
    if int(audio_stream.get("channels", 0)) != config.channels:
        raise ValueError("Audio channels do not match configuration")
        
    format_data = data.get("format", {})
    duration = float(format_data.get("duration", 0))
    if abs(duration - source_info.duration_seconds) > 2.0:
        raise ValueError(f"Audio duration ({duration}) deviates from source ({source_info.duration_seconds})")
