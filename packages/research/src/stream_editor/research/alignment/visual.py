import asyncio
import subprocess
import cv2
import numpy as np
from typing import List, Dict
import time
from stream_editor.contracts.research import AlignmentBlockContract
import uuid
import sys

class VisualAligner:
    def __init__(self) -> None:
        pass

    async def _extract_frame(self, path: str, t: float):  # type: ignore[no-untyped-def]
        cmd = [
            "ffmpeg", "-y", "-ss", str(t), "-i", path,
            "-vframes", "1", "-vf", "scale=16:16", "-f", "image2pipe", "-vcodec", "rawvideo", "-pix_fmt", "gray", "-"
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        stdout, _ = await proc.communicate()
        if len(stdout) == 256:
            return t, np.frombuffer(stdout, dtype=np.uint8).astype(int)
        return t, None

    async def _extract_frames_parallel(self, path: str, timestamps: List[float], max_concurrent=20):  # type: ignore[no-untyped-def]
        results = []
        for i in range(0, len(timestamps), max_concurrent):
            batch = timestamps[i:i+max_concurrent]
            tasks = [self._extract_frame(path, t) for t in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend([r for r in batch_results if r[1] is not None])
            print(f"Extracted {len(results)}/{len(timestamps)}", flush=True)
        return results

    def align(self, source_path: str, edited_path: str, unmatched_intervals: List[List[float]] = None) -> List[AlignmentBlockContract]:  # type: ignore[assignment]
        print("VisualAligner: Starting bounded visual search...", flush=True)
        
        # If we don't know what's unmatched, we can't do this efficiently.
        if not unmatched_intervals:
            return []
            
        # 1. Coarse extraction of Source (1 frame every 60s)
        # 5 hours = 18000s -> 300 frames. 
        # This takes ~ 300 / 20 * 4s = 60s
        s_timestamps = list(range(0, 18000, 60))
        print("VisualAligner: Extracting coarse source index...", flush=True)
        s_frames = asyncio.run(self._extract_frames_parallel(source_path, s_timestamps, max_concurrent=20))  # type: ignore[arg-type,arg-type]
        
        blocks = []
        
        # For each unmatched interval > 5s, sample a few frames
        for start, end in unmatched_intervals:
            dur = end - start
            if dur < 5.0:
                continue
                
            print(f"VisualAligner: Searching unmatched interval {start}-{end}", flush=True)
            # Sample frames every 30 seconds
            e_t = list(np.arange(start + 5.0, end, 30.0))
            if not e_t: e_t = [start + dur/2]
            e_frames = asyncio.run(self._extract_frames_parallel(edited_path, e_t, max_concurrent=5))
            
            # Find best match in source
            if not e_frames or not s_frames:
                continue
                
            for et, ef in e_frames:
                best_diff = 999999
                best_st = -1
                for st, sf in s_frames:
                    diff = np.mean(np.abs(sf - ef))
                    if diff < best_diff:
                        best_diff = diff
                        best_st = st
                
                # If coarse match is decent, refine it (extract 1 fps around best_st)
                if best_diff < 40: # 16x16 pixels can differ a bit due to compression/crop
                    print(f"VisualAligner: Coarse match E:{et} -> S:{best_st} (diff {best_diff})", flush=True)
                    # We can create a block!
                    blocks.append(AlignmentBlockContract(
                        id=str(uuid.uuid4()),
                        run_id="run",
                        source_start=round(best_st - 30.0, 2), # Coarse window
                        source_end=round(best_st + 30.0, 2),
                        edit_start=round(et - 2.5, 2),
                        edit_end=round(et + 2.5, 2),
                        audio_confidence=None,
                        transcript_confidence=None,
                        visual_confidence=0.7,
                        combined_confidence=0.7,
                        speed_ratio=1.0,
                        method="visual",
                        is_manual_override=False
                    ))
                    
        return blocks
