import subprocess
from pathlib import Path

def extract_audio(source: Path, output: Path) -> Path:
    """Extract mono 16kHz WAV for analysis."""
    cmd = [
        'ffmpeg', '-i', str(source),
        '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
        '-y', str(output)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output
