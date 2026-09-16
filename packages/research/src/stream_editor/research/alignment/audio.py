import scipy.io.wavfile as wavfile
import numpy as np
from typing import List, Dict
from stream_editor.contracts.research import AlignmentBlockContract
import uuid

class AudioAligner:
    """
    Implements real audio cross-correlation to align edited video with source video.
    """
    
    def __init__(self, target_sr: int = 10):
        self.target_sr = target_sr
        
    def align(self, source_path: str, edited_path: str) -> List[AlignmentBlockContract]:
        print("AudioAligner: Starting alignment...", flush=True)
        source_audio = source_path.replace(".mp4", ".wav")
        edited_audio = edited_path.replace(".mp4", ".wav")
        
        try:
            print("AudioAligner: Reading source...", flush=True)
            s_sr, s_data = wavfile.read(source_audio)
            print("AudioAligner: Reading edited...", flush=True)
            e_sr, e_data = wavfile.read(edited_audio)
            print(f"AudioAligner: Read complete. s_len={len(s_data)}, e_len={len(e_data)}", flush=True)
        except Exception as ex:
            print(f"AudioAligner: Exception reading wavs: {ex}", flush=True)
            return []
            
        if len(s_data.shape) > 1: s_data = s_data.mean(axis=1)
        if len(e_data.shape) > 1: e_data = e_data.mean(axis=1)
        
        window = int(s_sr * 0.1)
        s_step = s_sr // self.target_sr
        e_step = e_sr // self.target_sr
        
        import scipy.signal
        s_env = []
        chunk_len = s_sr * 60 # 60 seconds
        for i in range(0, len(s_data), chunk_len):
            chunk = np.abs(s_data[i:i+chunk_len])
            chunk = chunk[::s_step]
            window_small = max(1, window // s_step)
            env_chunk = scipy.signal.fftconvolve(chunk, np.ones(window_small)/window_small, mode='same')
            s_env.append(env_chunk)
        s_env = np.concatenate(s_env)
        
        e_env = []
        for i in range(0, len(e_data), chunk_len):
            chunk = np.abs(e_data[i:i+chunk_len])
            chunk = chunk[::e_step]
            window_small = max(1, window // e_step)
            env_chunk = scipy.signal.fftconvolve(chunk, np.ones(window_small)/window_small, mode='same')
            e_env.append(env_chunk)
        e_env = np.concatenate(e_env)
        
        blocks = []
        chunk_size = int(self.target_sr * 0.5)
        stride = int(self.target_sr * 0.25)
        
        e_idx = 0
        matches = []
        
        while e_idx + chunk_size <= len(e_env):
            e_chunk = e_env[e_idx:e_idx+chunk_size]
            e_norm = e_chunk - np.mean(e_chunk)
            std = np.std(e_norm)
            if std > 0.1: # Skip pure silence matches
                e_norm = e_norm / std
                
                best_score = -1
                best_idx = -1
                
                # Check within bounds
                s_norm = s_env - np.mean(s_env)
                if np.std(s_norm) > 0:
                    s_norm = s_norm / np.std(s_norm)
                    correlation = np.correlate(s_norm, e_norm, mode='valid')
                    if len(correlation) > 0:
                        best_idx = np.argmax(correlation)
                        best_score = correlation[best_idx] / len(e_chunk)
                        
                if best_score > 0.4:
                    e_time = e_idx / self.target_sr
                    s_time = best_idx / self.target_sr
                    matches.append((s_time, e_time))
                    
            e_idx += stride
            
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
                blocks.append(self._finalize_block(current_block))
                current_block = {
                    "s_start": s_time,
                    "e_start": e_time,
                    "s_end": s_time + 0.5,
                    "e_end": e_time + 0.5,
                    "matches": [(s_time, e_time)]
                }
                
        if current_block:
            blocks.append(self._finalize_block(current_block))
            
        return blocks
        
    def _finalize_block(self, b: Dict) -> AlignmentBlockContract:
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
            audio_confidence=0.8,
            transcript_confidence=None,
            visual_confidence=None,
            combined_confidence=0.8,
            speed_ratio=speed,
            method="audio",
            is_manual_override=False
        )
