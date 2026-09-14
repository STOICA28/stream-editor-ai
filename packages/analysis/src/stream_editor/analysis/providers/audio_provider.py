import subprocess
import re
from typing import List
from stream_editor.contracts.analysis import AudioAnalysisProvider, AudioEventConfig, AudioEvent

class FFmpegAudioAnalysisProvider(AudioAnalysisProvider):
    def analyze_audio(self, audio_path: str, config: AudioEventConfig) -> List[AudioEvent]:
        # Build silencedetect filter
        # e.g., silencedetect=noise=-30dB:d=0.5
        filter_str = f"silencedetect=noise={config.silence_thresh}dB:d={config.silence_duration}"
        
        cmd = [
            "ffmpeg",
            "-i", audio_path,
            "-af", filter_str,
            "-f", "null",
            "-"
        ]
        
        # Run ffmpeg, capture output (it outputs to stderr)
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        
        events = []
        
        # Regex to match silencedetect output
        # [silencedetect @ 0x...] silence_start: 0.5
        # [silencedetect @ 0x...] silence_end: 1.5 | silence_duration: 1.0
        
        start_pattern = re.compile(r"silence_start:\s+([\d\.]+)")
        end_pattern = re.compile(r"silence_end:\s+([\d\.]+)")
        
        current_start = None
        
        for line in result.stderr.splitlines():
            start_match = start_pattern.search(line)
            if start_match:
                current_start = float(start_match.group(1))
                
            end_match = end_pattern.search(line)
            if end_match and current_start is not None:
                end_time = float(end_match.group(1))
                events.append(
                    AudioEvent(
                        event_type="silence",
                        start_time=current_start,
                        end_time=end_time
                    )
                )
                current_start = None
                
        return events
