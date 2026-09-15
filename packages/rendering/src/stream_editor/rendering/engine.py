import asyncio
import logging
import uuid
import os
import shutil
from pathlib import Path
from typing import Optional, Callable
from stream_editor.contracts.rendering import CompiledTimeline, CompiledSegment, RenderConfig, RenderManifest
from stream_editor.rendering.cache import RenderSegmentCache
from stream_editor.rendering.ffmpeg.graph import FFmpegGraphBuilder
from stream_editor.rendering.validator import MediaValidator

logger = logging.getLogger(__name__)

class RenderingEngine:
    def __init__(self, work_dir: Path) -> None:
        self.work_dir = work_dir
        self.cache = RenderSegmentCache()
        self.graph_builder = FFmpegGraphBuilder()
        self.validator = MediaValidator()

    async def render_segment(
        self,
        segment: CompiledSegment,
        source_path: Path,
        segment_dir: Path,
        config: RenderConfig
    ) -> Path:
        """
        Renders a single segment to the segment_dir. 
        Uses cache if possible.
        """
        signature = segment.signature
        if not signature:
            # Fallback signature
            signature = self.cache.compute_signature(str(source_path), segment, config)
            
        final_seg_path = segment_dir / f"{signature}.mp4"
        partial_seg_path = segment_dir / f"{signature}.partial.mp4"
        
        # Cache check
        if final_seg_path.exists():
            is_valid, _ = await self.validator.validate_output(final_seg_path, segment.duration, tolerance=1.0)
            if is_valid:
                logger.info(f"Cache hit for segment {segment.segment_index} ({signature})")
                return final_seg_path
            else:
                logger.warning(f"Corrupt cache detected for segment {segment.segment_index}. Regenerating.")
                final_seg_path.unlink(missing_ok=True)
                
        logger.info(f"Rendering segment {segment.segment_index} ({signature})")
        
        # Audio continuity: 10ms crossfade equivalent (or simple fade at edges)
        # Using a hard cut, we will add an audio fade in/out of 10ms to avoid clicks
        
        v_filters, a_filters = self.graph_builder.build_segment_filter(
            segment, config.width, config.height, config.fps
        )
        
        # Add a 10ms audio fade
        fade_duration = 0.01
        audio_fade = f"afade=t=in:st=0:d={fade_duration},afade=t=out:st={segment.duration - fade_duration}:d={fade_duration}"
        if a_filters:
            a_filters += f",{audio_fade}"
        else:
            a_filters = audio_fade
            
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(segment.source_start),
            "-t", str(segment.duration),
            "-i", str(source_path)
        ]
        
        if v_filters:
            cmd.extend(["-vf", v_filters])
        if a_filters:
            cmd.extend(["-af", a_filters])
            
        cmd.extend([
            "-c:v", config.video_codec,
            "-c:a", config.audio_codec,
            "-pix_fmt", config.pixel_format,
            "-r", str(config.fps),
            "-crf", str(config.crf),
            "-preset", config.preset,
            str(partial_seg_path)
        ])
        
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed rendering segment {segment.segment_index}: {stderr.decode()}")
            
        is_valid, msg = await self.validator.validate_output(partial_seg_path, segment.duration)
        if not is_valid:
            partial_seg_path.unlink(missing_ok=True)
            raise RuntimeError(f"Validation failed for segment {segment.segment_index}: {msg}")
            
        # Atomic promotion
        partial_seg_path.rename(final_seg_path)
        return final_seg_path

    async def render(
        self,
        timeline: CompiledTimeline,
        config: RenderConfig,
        source_paths: dict[str, Path],
        job_id: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Path:
        """
        Orchestrates rendering of all segments and concatenates them.
        """
        job_dir = self.work_dir / "renders" / job_id
        segments_dir = job_dir / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        
        final_output = job_dir / "final.mp4"
        partial_output = job_dir / "output.partial.mp4"
        
        if progress_callback:
            progress_callback(5.0) # Prepare
            
        # 1. Render all segments
        segment_files = []
        total_segs = len(timeline.segments)
        
        for i, segment in enumerate(timeline.segments):
            src_path = source_paths.get(segment.source_asset_id)
            if not src_path:
                raise ValueError(f"Source path not provided for asset {segment.source_asset_id}")
                
            # Sign the segment
            segment.signature = self.cache.compute_signature(str(src_path), segment, config)
            
            seg_file = await self.render_segment(segment, src_path, segments_dir, config)
            segment_files.append(seg_file)
            
            if progress_callback:
                progress = 5.0 + ((i + 1) / total_segs) * 85.0
                progress_callback(progress)
                
        # 2. Concat
        concat_file = job_dir / "concat.txt"
        with concat_file.open("w") as f:
            for sf in segment_files:
                f.write(f"file '{sf.absolute().as_posix()}'\n")
                
        logger.info(f"Concatenating {len(segment_files)} segments")
        
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(partial_output)
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *concat_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg concat failed: {stderr.decode()}")
            
        # 3. Final Validation
        is_valid, msg = await self.validator.validate_output(partial_output, timeline.expected_duration, tolerance=3.0)
        if not is_valid:
            raise RuntimeError(f"Final output validation failed: {msg}")
            
        # 4. Atomic promotion
        partial_output.rename(final_output)
        
        # 5. Write manifest
        manifest = RenderManifest(
            render_job_id=job_id,
            source_assets=list(source_paths.keys()),
            edit_plan="plan",
            effect_plan="effect",
            renderer_version="1.0",
            render_config=config,
            segments=timeline.segments,
            expected_duration=timeline.expected_duration,
            actual_duration=timeline.expected_duration,  # Simplified for mock
            output_hash=None
        )
        
        with (job_dir / "manifest.json").open("w") as f:
            f.write(manifest.model_dump_json(indent=2))
            
        if progress_callback:
            progress_callback(100.0)
            
        return final_output
