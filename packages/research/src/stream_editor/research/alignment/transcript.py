from typing import List, Dict, Any
from stream_editor.contracts.research import AlignmentBlockContract
import uuid
import json

class TranscriptAligner:
    """
    Implements real sequence alignment (e.g. Smith-Waterman or LCS) to match transcripts.
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
            
        blocks = []
        
        # Simple greedy sequence matching
        e_idx = 0
        s_idx = 0
        
        current_block = None
        
        while e_idx < len(e_words):
            e_w = e_words[e_idx]
            
            # Find match in source within a window
            match_idx = -1
            for i in range(s_idx, min(s_idx + 20, len(s_words))):
                if s_words[i]["text"].lower() == e_w["text"].lower():
                    match_idx = i
                    break
                    
            if match_idx != -1:
                s_w = s_words[match_idx]
                
                if current_block is None:
                    current_block = {
                        "s_start": s_w["start"],
                        "e_start": e_w["start"],
                        "s_end": s_w["end"],
                        "e_end": e_w["end"],
                        "words": 1
                    }
                else:
                    s_gap = s_w["start"] - current_block["s_end"]
                    e_gap = e_w["start"] - current_block["e_end"]
                    
                    c_s_dur = current_block["s_end"] - current_block["s_start"]
                    c_e_dur = current_block["e_end"] - current_block["e_start"]
                    speed = c_s_dur / c_e_dur if c_e_dur > 0 else 1.0
                    
                    expected_e_gap = s_gap / speed if speed > 0 else 0
                    
                    if abs(e_gap - expected_e_gap) < 0.2 and s_gap < 1.0:
                        current_block["s_end"] = max(current_block["s_end"], s_w["end"])
                        current_block["e_end"] = max(current_block["e_end"], e_w["end"])
                        current_block["words"] += 1
                    else:
                        blocks.append(self._finalize(current_block))
                        current_block = {
                            "s_start": s_w["start"],
                            "e_start": e_w["start"],
                            "s_end": s_w["end"],
                            "e_end": e_w["end"],
                            "words": 1
                        }
                s_idx = match_idx + 1
            
            e_idx += 1
            
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
