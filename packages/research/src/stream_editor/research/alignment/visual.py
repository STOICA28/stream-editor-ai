import cv2
import numpy as np
from typing import List, Tuple, Dict
from stream_editor.contracts.research import AlignmentBlockContract
import uuid

class VisualAligner:
    """
    Implements real frame/perceptual matching to align an edited video with a source video.
    """
    
    def __init__(self, fps_override: int = 2):
        self.fps = fps_override # Downsample for performance

    def align(self, source_path: str, edited_path: str) -> List[AlignmentBlockContract]:
        source_hashes = self._extract_hashes(source_path)
        edited_hashes = self._extract_hashes(edited_path)
        
        # Simple sliding window correlation using MSE of perceptual hashes
        # A more robust approach would use dynamic time warping (DTW) or Smith-Waterman.
        # For M10.1, we implement a robust subsequence match.
        
        blocks = []
        
        # Find matching segments
        e_idx = 0
        while e_idx < len(edited_hashes):
            e_time, e_hash = edited_hashes[e_idx]
            
            best_match_idx = -1
            best_score = float('inf')
            
            for s_idx, (s_time, s_hash) in enumerate(source_hashes):
                score = np.sum(np.abs(e_hash - s_hash))
                if score < best_score:
                    best_score = score
                    best_match_idx = s_idx
                    
            if best_score < 10: # threshold for match
                # found a match! trace it forward
                s_start_time = source_hashes[best_match_idx][0]
                e_start_time = e_time
                
                s_curr = best_match_idx
                e_curr = e_idx
                
                while e_curr < len(edited_hashes) and s_curr < len(source_hashes):
                    score = np.sum(np.abs(edited_hashes[e_curr][1] - source_hashes[s_curr][1]))
                    if score > 15: # Diverged
                        # Check if it's a speedup (2x) by checking s_curr+2 vs e_curr+1
                        if e_curr + 1 < len(edited_hashes) and s_curr + 2 < len(source_hashes):
                            score_2x = np.sum(np.abs(edited_hashes[e_curr+1][1] - source_hashes[s_curr+2][1]))
                            if score_2x < 10:
                                s_curr += 2
                                e_curr += 1
                                continue
                        break
                    s_curr += 1
                    e_curr += 1
                
                s_end_time = source_hashes[s_curr-1][0] if s_curr > 0 else s_start_time
                e_end_time = edited_hashes[e_curr-1][0] if e_curr > 0 else e_start_time
                
                if e_end_time > e_start_time:
                    # Calculate speed
                    s_dur = s_end_time - s_start_time
                    e_dur = e_end_time - e_start_time
                    speed = s_dur / e_dur if e_dur > 0 else 1.0
                    
                    blocks.append(AlignmentBlockContract(
                        id=str(uuid.uuid4()),
                        run_id="run",
                        source_start=s_start_time,
                        source_end=s_end_time,
                        edit_start=e_start_time,
                        edit_end=e_end_time,
                        audio_confidence=None,
                        transcript_confidence=None,
                        visual_confidence=0.9,
                        combined_confidence=0.9,
                        speed_ratio=round(speed, 1),
                        method="visual",
                        is_manual_override=False
                    ))
                e_idx = e_curr
            else:
                e_idx += 1
                
        return blocks
        
    def _extract_hashes(self, path: str) -> List[Tuple[float, np.ndarray]]:
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps / self.fps)
        
        hashes = []
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_idx % frame_interval == 0:
                time_sec = frame_idx / fps
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                resized = cv2.resize(gray, (8, 8))
                mean = np.mean(resized)
                h = (resized > mean).astype(np.uint8)
                hashes.append((time_sec, h))
                
            frame_idx += 1
            
        cap.release()
        return hashes
