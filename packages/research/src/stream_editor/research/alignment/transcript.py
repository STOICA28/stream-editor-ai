from typing import List, Dict, Any, Tuple
from stream_editor.contracts.research import AlignmentBlockContract
import uuid
import json
import numpy as np

class TranscriptAligner:
    """
    Implements dynamic programming sequence alignment to match transcripts,
    handling repeated words and gaps.
    """
    
    def align(self, source_path: str, edited_path: str) -> List[AlignmentBlockContract]:
        s_transcript_path = source_path.replace('.mp4', '.json')
        e_transcript_path = edited_path.replace('.mp4', '.json')
        
        try:
            with open(s_transcript_path, 'r') as f:
                s_words = json.load(f)
            with open(e_transcript_path, 'r') as f:
                e_words = json.load(f)
        except FileNotFoundError:
            return []
            
        if not s_words or not e_words:
            return []
            
        N = len(s_words)
        M = len(e_words)
        
        dp = np.zeros((N + 1, M + 1))
        trace = np.zeros((N + 1, M + 1), dtype=int)
        
        MATCH_REWARD = 2
        MISMATCH_PENALTY = -2
        GAP_PENALTY = -1
        
        for i in range(1, N + 1):
            dp[i, 0] = dp[i-1, 0] + GAP_PENALTY
            trace[i, 0] = 1
        for j in range(1, M + 1):
            dp[0, j] = dp[0, j-1] + GAP_PENALTY
            trace[0, j] = 2
            
        for i in range(1, N + 1):
            for j in range(1, M + 1):
                s_w = s_words[i-1]
                e_w = e_words[j-1]
                
                is_match = s_w["text"].lower() == e_w["text"].lower()
                match_score = MATCH_REWARD if is_match else MISMATCH_PENALTY
                
                diag = dp[i-1, j-1] + match_score
                up = dp[i-1, j] + GAP_PENALTY
                left = dp[i, j-1] + GAP_PENALTY
                
                best = max(diag, up, left)
                dp[i, j] = best
                
                if best == diag:
                    trace[i, j] = 0
                elif best == up:
                    trace[i, j] = 1
                else:
                    trace[i, j] = 2
                    
        i, j = N, M
        matches = []
        while i > 0 and j > 0:
            if trace[i, j] == 0:
                s_w = s_words[i-1]
                e_w = e_words[j-1]
                if s_w["text"].lower() == e_w["text"].lower():
                    matches.append((i-1, j-1))
                i -= 1
                j -= 1
            elif trace[i, j] == 1:
                i -= 1
            else:
                j -= 1
                
        matches.reverse()
        
        blocks = []  # type: ignore[var-annotated]
        if not matches:
            return blocks
            
        current_block = {
            "s_start": s_words[matches[0][0]]["start"],
            "s_end": s_words[matches[0][0]]["end"],
            "e_start": e_words[matches[0][1]]["start"],
            "e_end": e_words[matches[0][1]]["end"],
            "words": 1,
            "s_indices": [matches[0][0]],
            "e_indices": [matches[0][1]]
        }
        
        for k in range(1, len(matches)):
            s_idx, e_idx = matches[k]
            s_w = s_words[s_idx]
            e_w = e_words[e_idx]
            
            s_gap = s_w["start"] - current_block["s_end"]
            e_gap = e_w["start"] - current_block["e_end"]
            
            # The speed is calculated based on the *local* step
            local_s_dur = s_w["end"] - s_words[current_block["s_indices"][-1]]["start"]
            local_e_dur = e_w["end"] - e_words[current_block["e_indices"][-1]]["start"]
            
            c_s_dur = current_block["s_end"] - current_block["s_start"]
            c_e_dur = current_block["e_end"] - current_block["e_start"]
            block_speed = c_s_dur / c_e_dur if c_e_dur > 0 else 1.0
            
            local_speed = local_s_dur / local_e_dur if local_e_dur > 0 else 1.0
            
            # Allow slightly loose gap if speeds match roughly
            if abs(block_speed - local_speed) < 0.2 and s_gap < 0.5:
                current_block["s_end"] = max(current_block["s_end"], s_w["end"])
                current_block["e_end"] = max(current_block["e_end"], e_w["end"])
                current_block["words"] += 1
                current_block["s_indices"].append(s_idx)
                current_block["e_indices"].append(e_idx)
            else:
                blocks.append(self._finalize(current_block))
                current_block = {
                    "s_start": s_w["start"],
                    "s_end": s_w["end"],
                    "e_start": e_w["start"],
                    "e_end": e_w["end"],
                    "words": 1,
                    "s_indices": [s_idx],
                    "e_indices": [e_idx]
                }
                
        if current_block:
            blocks.append(self._finalize(current_block))
            
        return blocks
        
    def _finalize(self, b: Dict[str, Any]) -> AlignmentBlockContract:
        s_dur = b["s_end"] - b["s_start"]
        e_dur = b["e_end"] - b["e_start"]
        speed = round(s_dur / e_dur, 1) if e_dur > 0 else 1.0
        
        return AlignmentBlockContract(
            id=str(uuid.uuid4()),
            run_id="run",
            source_start=round(b["s_start"], 2),
            source_end=round(b["s_end"], 2),
            edit_start=round(b["e_start"], 2),
            edit_end=round(b["e_end"], 2),
            audio_confidence=None,
            transcript_confidence=0.9,
            visual_confidence=None,
            combined_confidence=0.9,
            speed_ratio=speed,
            method="transcript",
            is_manual_override=False
        )
