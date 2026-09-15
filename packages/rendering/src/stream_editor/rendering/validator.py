import asyncio
import json
import logging
from typing import Dict, Any, Tuple
from pathlib import Path
import math

logger = logging.getLogger(__name__)

class MediaValidator:
    async def validate_output(self, filepath: Path, expected_duration: float, tolerance: float = 1.0) -> Tuple[bool, str]:
        """
        Validates the output file using ffprobe.
        Checks parsability, presence of streams, and duration.
        """
        if not filepath.exists() or filepath.stat().st_size < 1024:
            return False, "File does not exist or is trivially small"
            
        cmd = [
            "ffprobe", "-v", "error", "-show_format", "-show_streams", 
            "-of", "json", str(filepath)
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return False, f"FFprobe failed to parse file: {stderr.decode()}"
            
        try:
            data = json.loads(stdout.decode())
        except json.JSONDecodeError:
            return False, "Failed to decode FFprobe JSON"
            
        streams = data.get("streams", [])
        if not streams:
            return False, "No streams found"
            
        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        
        if not has_video:
            return False, "No video stream found"
            
        if not has_audio:
            # We assume audio is expected unless explicitly not provided
            logger.warning("No audio stream found in output")
            # Might be okay depending on use case, but standard is we have audio
            
        fmt = data.get("format", {})
        actual_duration = float(fmt.get("duration", 0.0))
        
        if math.isnan(actual_duration):
            return False, "Parsed duration is NaN"
            
        diff = abs(actual_duration - expected_duration)
        if diff > tolerance:
            return False, f"Duration mismatch: expected {expected_duration}, actual {actual_duration} (diff: {diff})"
            
        return True, "Valid"
