import scipy.io.wavfile as wavfile
import numpy as np
from typing import List, Tuple, Dict
from stream_editor.contracts.research import AlignmentBlockContract
import uuid

class AudioAligner:
    """
    Implements real audio cross-correlation to align edited video with source video.
    """
    
    def __init__(self, target_sr: int = 1000):
        self.target_sr = target_sr
        
    def align(self, source_path: str, edited_path: str) -> List[AlignmentBlockContract]:
        # Replace .mp4 with .wav as we generated them alongside
        source_audio = source_path.replace('.mp4', '.wav')
        edited_audio = edited_path.replace('.mp4', '.wav')
        
        s_sr, s_data = wavfile.read(source_audio)
        e_sr, e_data = wavfile.read(edited_audio)
        
        # Convert to float and mono
        if len(s_data.shape) > 1: s_data = s_data.mean(axis=1)
        if len(e_data.shape) > 1: e_data = e_data.mean(axis=1)
        s_data = s_data.astype(float)
        e_data = e_data.astype(float)
        
        # Downsample for speed
        s_step = s_sr // self.target_sr
        e_step = e_sr // self.target_sr
        s_data = s_data[::s_step]
        e_data = e_data[::e_step]
        
        # We process the edited audio in 1-second chunks and find where they match in the source
        blocks = []
        
        chunk_size = self.target_sr
        stride = chunk_size // 2
        
        e_idx = 0
        current_block = None
        
        while e_idx + chunk_size <= len(e_data):
            e_chunk = e_data[e_idx:e_idx+chunk_size]
            
            # Simple cross-correlation
            # In a real app we'd use scipy.signal.correlate with fft=True, or fingerprinting.
            # Here we just use numpy correlate
            # Normalization to get confidence
            e_norm = e_chunk - np.mean(e_chunk)
            if np.std(e_norm) > 0:
                e_norm = e_norm / np.std(e_norm)
            
            # For speed, we just search the entire source (it's 10s)
            best_score = -1
            best_idx = -1
            
            s_norm = s_data - np.mean(s_data)
            if np.std(s_norm) > 0:
                s_norm = s_norm / np.std(s_norm)
                
            correlation = np.correlate(s_norm, e_norm, mode='valid')
            if len(correlation) > 0:
                best_idx = np.argmax(correlation)
                # Pseudo-confidence
                best_score = correlation[best_idx] / len(e_chunk)
                
            e_time = e_idx / self.target_sr
            
            if best_score > 0.5: # Match found
                s_time = best_idx / self.target_sr
                
                if current_block is None:
                    current_block = {
                        "s_start": s_time,
                        "e_start": e_time,
                        "s_end": s_time + 1.0,
                        "e_end": e_time + 1.0,
                        "scores": [best_score]
                    }
                else:
                    # Is it contiguous?
                    expected_s_time = current_block["s_end"] - 1.0 + (e_time - (current_block["e_end"] - 1.0))
                    if abs(s_time - expected_s_time) < 0.2:
                        current_block["s_end"] = s_time + 1.0
                        current_block["e_end"] = e_time + 1.0
                        current_block["scores"].append(best_score)
                    else:
                        # Break block
                        blocks.append(self._finalize_block(current_block))
                        current_block = {
                            "s_start": s_time,
                            "e_start": e_time,
                            "s_end": s_time + 1.0,
                            "e_end": e_time + 1.0,
                            "scores": [best_score]
                        }
            else:
                if current_block is not None:
                    blocks.append(self._finalize_block(current_block))
                    current_block = None
                    
            e_idx += stride
            
        if current_block is not None:
            blocks.append(self._finalize_block(current_block))
            
        return blocks
        
    def _finalize_block(self, b: Dict) -> AlignmentBlockContract:
        s_dur = b["s_end"] - b["s_start"]
        e_dur = b["e_end"] - b["e_start"]
        speed = round(s_dur / e_dur, 1) if e_dur > 0 else 1.0
        conf = float(np.mean(b["scores"]))
        
        return AlignmentBlockContract(
            id=str(uuid.uuid4()),
            run_id="run",
            source_start=b["s_start"],
            source_end=b["s_end"],
            edit_start=b["e_start"],
            edit_end=b["e_end"],
            audio_confidence=conf,
            transcript_confidence=None,
            visual_confidence=None,
            combined_confidence=conf,
            speed_ratio=speed,
            method="audio",
            is_manual_override=False
        )
