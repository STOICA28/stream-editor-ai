from typing import List, Dict
import cv2
import numpy as np
from stream_editor.contracts.research import AlignmentBlockContract
import uuid

class VisualAligner:
    """
    Implements sliding window visual alignment based on frame difference.
    """
    
    def align(self, source_path: str, edited_path: str) -> List[AlignmentBlockContract]:
        cap_s = cv2.VideoCapture(source_path)
        cap_e = cv2.VideoCapture(edited_path)
        
        s_frames = []
        e_frames = []
        
        fps_s = cap_s.get(cv2.CAP_PROP_FPS)
        fps_e = cap_e.get(cv2.CAP_PROP_FPS)
        
        if fps_s == 0 or fps_e == 0:
            return []
            
        # Extract 2 frames per second for better granularity
        step = int(fps_s / 2) if fps_s >= 2 else 1
        
        idx = 0
        while True:
            cap_s.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap_s.read()
            if not ret: break
            gray = cv2.cvtColor(cv2.resize(frame, (32, 32)), cv2.COLOR_BGR2GRAY)
            s_frames.append((idx / fps_s, gray))
            idx += step
            
        idx = 0
        while True:
            cap_e.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap_e.read()
            if not ret: break
            gray = cv2.cvtColor(cv2.resize(frame, (32, 32)), cv2.COLOR_BGR2GRAY)
            e_frames.append((idx / fps_e, gray))
            idx += step
            
        cap_s.release()
        cap_e.release()
        
        matches = []
        for e_time, e_f in e_frames:
            best_diff = float('inf')
            best_s_time = -1
            
            for s_time, s_f in s_frames:
                diff = np.mean(np.abs(e_f.astype(int) - s_f.astype(int)))
                if diff < best_diff:
                    best_diff = diff
                    best_s_time = s_time
                    
            if best_diff < 30: # threshold
                matches.append((best_s_time, e_time))
                
        blocks = []
        if not matches:
            return blocks
            
        current_block = {
            "s_start": matches[0][0],
            "e_start": matches[0][1],
            "s_end": matches[0][0] + 0.5,
            "e_end": matches[0][1] + 0.5,
            "matches": [matches[0]]
        }
        
        for k in range(1, len(matches)):
            s_time, e_time = matches[k]
            
            s_gap = s_time - current_block["s_end"]
            e_gap = e_time - current_block["e_end"]
            
            c_s_dur = current_block["s_end"] - current_block["s_start"]
            c_e_dur = current_block["e_end"] - current_block["e_start"]
            block_speed = c_s_dur / c_e_dur if c_e_dur > 0 else 1.0
            
            local_speed = (s_time - current_block["matches"][-1][0]) / (e_time - current_block["matches"][-1][1]) if e_time > current_block["matches"][-1][1] else 1.0
            
            if abs(block_speed - local_speed) < 0.5 and s_gap < 1.0:
                current_block["s_end"] = max(current_block["s_end"], s_time + 0.5)
                current_block["e_end"] = max(current_block["e_end"], e_time + 0.5)
                current_block["matches"].append((s_time, e_time))
            else:
                blocks.append(self._finalize(current_block))
                current_block = {
                    "s_start": s_time,
                    "e_start": e_time,
                    "s_end": s_time + 0.5,
                    "e_end": e_time + 0.5,
                    "matches": [(s_time, e_time)]
                }
                
        if current_block:
            blocks.append(self._finalize(current_block))
            
        return blocks

    def _finalize(self, b: Dict) -> AlignmentBlockContract:
        s_dur = b["s_end"] - b["s_start"]
        e_dur = b["e_end"] - b["e_start"]
        speed = round(s_dur / e_dur, 1) if e_dur > 0 else 1.0
        
        return AlignmentBlockContract(
            id=str(uuid.uuid4()),
            run_id="run",
            source_start=round(float(b["s_start"]), 2),
            source_end=round(float(b["s_end"]), 2),
            edit_start=round(float(b["e_start"]), 2),
            edit_end=round(float(b["e_end"]), 2),
            audio_confidence=None,
            transcript_confidence=None,
            visual_confidence=0.8,
            combined_confidence=0.8,
            speed_ratio=speed,
            method="visual",
            is_manual_override=False
        )
