import scipy.io.wavfile as wavfile  # type: ignore[import-untyped]
import numpy as np
import scipy.signal  # type: ignore[import-untyped]
from typing import List, Dict
from stream_editor.contracts.research import AlignmentBlockContract
import uuid

class AudioAligner:
    """
    Implements real audio cross-correlation to align edited video with source video.
    Supports speed tolerance and expanded context verification.
    """
    
    def __init__(self, target_sr: int = 10):
        self.target_sr = target_sr
        
    def _resample_envelope(self, env: np.ndarray, speed_ratio: float) -> np.ndarray:
        if speed_ratio == 1.0:
            return env
        target_len = int(len(env) / speed_ratio)
        if target_len <= 0:
            return env
        return np.interp(np.linspace(0, len(env), target_len), np.arange(len(env)), env)  # type: ignore[no-any-return]

    def align(self, source_path: str, edited_path: str) -> List[AlignmentBlockContract]:
        print("AudioAligner: Starting alignment...", flush=True)
        source_audio = source_path.replace(".mp4", ".wav")
        edited_audio = edited_path.replace(".mp4", ".wav")
        
        try:
            s_sr, s_data = wavfile.read(source_audio)
            e_sr, e_data = wavfile.read(edited_audio)
        except Exception as ex:
            print(f"AudioAligner: Exception reading wavs: {ex}", flush=True)
            return []
            
        if len(s_data.shape) > 1: s_data = s_data[:, 0]
        if len(e_data.shape) > 1: e_data = e_data[:, 0]
        
        window = int(s_sr * 0.1)
        s_step = s_sr // self.target_sr
        e_step = e_sr // self.target_sr
        
        chunk_len = s_sr * 60
        s_env = []
        for i in range(0, len(s_data), chunk_len):
            chunk = np.abs(s_data[i:i+chunk_len].astype(np.float32))
            chunk = chunk[::s_step]
            window_small = max(1, window // s_step)
            env_chunk = scipy.signal.fftconvolve(chunk, np.ones(window_small)/window_small, mode='same')
            s_env.append(env_chunk)
        s_env = np.concatenate(s_env)  # type: ignore[assignment]
        
        e_env = []
        for i in range(0, len(e_data), chunk_len):
            chunk = np.abs(e_data[i:i+chunk_len].astype(np.float32))
            chunk = chunk[::e_step]
            window_small = max(1, window // e_step)
            env_chunk = scipy.signal.fftconvolve(chunk, np.ones(window_small)/window_small, mode='same')
            e_env.append(env_chunk)
        e_env = np.concatenate(e_env)  # type: ignore[assignment]
        
        print("AudioAligner: Computed envelopes.", flush=True)
        
        blocks = []  # type: ignore[var-annotated]
        chunk_size = int(self.target_sr * 1.0) # 1s chunk
        stride = int(self.target_sr * 0.5)     # 0.5s stride
        
        # Precompute global source normalization to speed up inner loop
        s_mean = np.mean(s_env)
        s_std = np.std(s_env - s_mean)
        if s_std > 0:
            s_norm_global = (s_env - s_mean) / s_std
        else:
            s_norm_global = s_env - s_mean
            
        e_idx = 0
        matches = []
        
        iteration = 0
        speed_ratios = [0.8, 1.0, 1.25, 1.5]
        
        while e_idx + chunk_size <= len(e_env):
            if iteration % 500 == 0:
                print(f"AudioAligner: Processing chunk {iteration}...", flush=True)
            iteration += 1
            e_chunk = e_env[e_idx:e_idx+chunk_size]
            
            best_overall_score = -1
            best_overall_s_idx = -1
            best_overall_speed = 1.0
            
            e_norm_base = e_chunk - np.mean(e_chunk)
            if np.std(e_norm_base) > 0.1:
                # Test multiple speed ratios
                for speed in speed_ratios:
                    e_chunk_resampled = self._resample_envelope(e_chunk, speed)  # type: ignore[arg-type]
                    e_norm = e_chunk_resampled - np.mean(e_chunk_resampled)
                    std = np.std(e_norm)
                    if std <= 0.1:
                        continue
                    e_norm = e_norm / std
                    
                    correlation = np.correlate(s_norm_global, e_norm, mode='valid')
                    if len(correlation) > 0:
                        best_idx = np.argmax(correlation)
                        best_score = correlation[best_idx] / len(e_norm)
                        
                        if best_score > best_overall_score:
                            best_overall_score = best_score
                            best_overall_s_idx = best_idx  # type: ignore[assignment]
                            best_overall_speed = speed
                            
                # Longer Context Recovery for ambiguous matches
                if 0.25 <= best_overall_score < 0.45:
                    # Expand context to 10 seconds
                    expanded_chunk_size = int(self.target_sr * 10.0)
                    e_expand_start = max(0, e_idx - int(expanded_chunk_size/2))
                    e_expand_end = min(len(e_env), e_expand_start + expanded_chunk_size)
                    e_chunk_expand = e_env[e_expand_start:e_expand_end]
                    
                    if len(e_chunk_expand) > int(self.target_sr * 5.0):
                        e_chunk_expand = self._resample_envelope(e_chunk_expand, best_overall_speed)  # type: ignore[assignment,arg-type]
                        e_norm_ex = e_chunk_expand - np.mean(e_chunk_expand)
                        std_ex = np.std(e_norm_ex)
                        if std_ex > 0.1:
                            e_norm_ex = e_norm_ex / std_ex
                            # Search in a limited neighborhood of the original match
                            s_search_start = max(0, best_overall_s_idx - int(expanded_chunk_size/2) - self.target_sr*5)
                            s_search_end = min(len(s_norm_global), s_search_start + expanded_chunk_size + self.target_sr*10)
                            
                            s_norm_ex = s_norm_global[s_search_start:s_search_end]
                            if len(s_norm_ex) >= len(e_norm_ex):
                                corr_ex = np.correlate(s_norm_ex, e_norm_ex, mode='valid')
                                if len(corr_ex) > 0:
                                    best_ex_idx = np.argmax(corr_ex)
                                    best_ex_score = corr_ex[best_ex_idx] / len(e_norm_ex)
                                    if best_ex_score >= 0.35: # Context confirms it
                                        best_overall_score = best_ex_score
                                        best_overall_s_idx = s_search_start + best_ex_idx + int(expanded_chunk_size/2)  # type: ignore[assignment]
                                    else:
                                        best_overall_score = 0 # Reject  # type: ignore[assignment]  # type: ignore[assignment]
                                        
                if best_overall_score > 0.35:
                    e_time = e_idx / self.target_sr
                    s_time = best_overall_s_idx / self.target_sr
                    matches.append((s_time, e_time, best_overall_speed))
                    
            e_idx += stride
            
        if not matches:
            return blocks
            
        current_block = {
            "s_start": matches[0][0],
            "e_start": matches[0][1],
            "speed": matches[0][2],
            "s_end": matches[0][0] + 0.5,
            "e_end": matches[0][1] + 0.5,
            "matches": [matches[0]]
        }
        
        for k in range(1, len(matches)):
            s_time, e_time, speed = matches[k]
            s_gap = s_time - current_block["s_end"]  # type: ignore
            e_gap = e_time - current_block["e_end"]  # type: ignore
            
            c_s_dur = current_block["s_end"] - current_block["s_start"]  # type: ignore
            c_e_dur = current_block["e_end"] - current_block["e_start"]  # type: ignore
            block_speed = c_s_dur / c_e_dur if c_e_dur > 0 else 1.0
            
            if abs(block_speed - speed) < 0.5 and s_gap < 2.0:
                current_block["s_end"] = max(current_block["s_end"], s_time + 0.5)  # type: ignore
                current_block["e_end"] = max(current_block["e_end"], e_time + 0.5)  # type: ignore
                current_block["matches"].append((s_time, e_time, speed))  # type: ignore
            else:
                blocks.append(self._finalize_block(current_block))
                current_block = {
                    "s_start": s_time,
                    "e_start": e_time,
                    "speed": speed,
                    "s_end": s_time + 0.5,
                    "e_end": e_time + 0.5,
                    "matches": [(s_time, e_time, speed)]
                }
                
        if current_block:
            blocks.append(self._finalize_block(current_block))
            
        return blocks
        
    def _finalize_block(self, b: Dict) -> AlignmentBlockContract:  # type: ignore
        s_dur = b["s_end"] - b["s_start"]
        e_dur = b["e_end"] - b["e_start"]
        speed = round(s_dur / e_dur, 2) if e_dur > 0 else 1.0
        
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
