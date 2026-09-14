import os
import subprocess

def generate_proxy(input_path: str, output_path: str) -> None:
    partial_path = output_path + ".partial"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", "scale=-2:720",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-f", "mp4",
                partial_path
            ],
            check=True
        )
        os.replace(partial_path, output_path)
    except subprocess.CalledProcessError:
        if os.path.exists(partial_path):
            os.remove(partial_path)
        raise

def extract_audio(input_path: str, output_path: str) -> None:
    partial_path = output_path + ".partial"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-c:a", "pcm_s16le",
                "-f", "wav",
                partial_path
            ],
            check=True
        )
        os.replace(partial_path, output_path)
    except subprocess.CalledProcessError:
        if os.path.exists(partial_path):
            os.remove(partial_path)
        raise
