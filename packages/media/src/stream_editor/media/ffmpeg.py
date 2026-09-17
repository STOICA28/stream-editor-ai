import os
import subprocess

from stream_editor.contracts.media import AudioConfig, MediaInfo, ProxyConfig


def generate_proxy(input_path: str, output_path: str, config: ProxyConfig, source_info: MediaInfo) -> None:
    partial_path = output_path + ".partial"
    
    # Pre-generation cleanup
    if os.path.exists(partial_path):
        os.remove(partial_path)
        
    try:
        # Determine scale filter: never upscale, width must be even
        # 'min(720, ih)' means if input height is < 720, it stays input height.
        # scale=-2 ensures width is calculated automatically but kept even.
        scale_filter = f"scale=-2:'min({config.max_height},ih)'"
        
        # Determine FPS strategy
        target_fps = source_info.fps
        if config.fps_mode == "cap" and target_fps > config.fps_max:
            target_fps = config.fps_max
            
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", scale_filter,
            "-r", str(target_fps),
            "-c:v", config.video_codec,
            "-preset", config.preset,
            "-g", str(config.gop_size),
            "-crf", str(config.crf),
            "-c:a", config.audio_codec
        ]
        if config.faststart:
            cmd.extend(["-movflags", "+faststart"])
        cmd.extend(["-f", config.container, partial_path])

        subprocess.run(
            cmd,
            check=True
        )
        os.replace(partial_path, output_path)
    except subprocess.CalledProcessError:
        if os.path.exists(partial_path):
            os.remove(partial_path)
        raise

def extract_audio(input_path: str, output_path: str, config: AudioConfig) -> None:
    partial_path = output_path + ".partial"
    
    # Pre-generation cleanup
    if os.path.exists(partial_path):
        os.remove(partial_path)
        
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-vn",
                "-ac", str(config.channels),
                "-ar", str(config.sample_rate),
                "-c:a", config.codec,
                "-f", config.container,
                partial_path
            ],
            check=True
        )
        os.replace(partial_path, output_path)
    except subprocess.CalledProcessError:
        if os.path.exists(partial_path):
            os.remove(partial_path)
        raise
