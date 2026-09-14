import subprocess
from pathlib import Path


def create_analysis_proxy(source: Path, output: Path, width: int = 1280) -> Path:
    """Create a lower-resolution proxy for analysis. Never uses shell=True."""
    cmd = [
        'ffmpeg', '-i', str(source),
        '-vf', f'scale={width}:-2',
        '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '128k',
        '-y', str(output)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output
