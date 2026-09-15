import uuid
import cv2
import numpy as np
import json
import os
import random
from typing import Dict, Any, List, Optional
import scipy.io.wavfile as wavfile

class SyntheticMediaGenerator:
    def __init__(self, output_dir: str = "tests/fixtures"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.fps = 10
        self.width = 640
        self.height = 360
        self.source_duration = 10.0
        self.sample_rate = 44100
        self.words = ["vamos" if i % 3 == 0 else f"word{i}" for i in range(100)] # Repeated words
        
    def _generate_audio_chunk(self, start_sec: float, end_sec: float, speed: float = 1.0, is_silence: bool = False) -> np.ndarray:
        duration = end_sec - start_sec
        if speed == 0.0:
            return np.zeros(0)
        t = np.linspace(0, duration / speed, int(self.sample_rate * duration / speed), False)
        if is_silence:
            # Add some background noise even if "silent"
            audio = np.random.normal(0, 0.01, len(t))
        else:
            freq = 440 + (start_sec * 50)
            audio = np.sin(freq * t * 2 * np.pi) + np.random.normal(0, 0.05, len(t))
        return audio

    def generate_source(self, seed: int = 0) -> str:
        random.seed(seed)
        np.random.seed(seed)
        path = os.path.join(self.output_dir, f"source_{seed}.mp4")
        audio_path = os.path.join(self.output_dir, f"source_{seed}.wav")
        transcript_path = os.path.join(self.output_dir, f"source_{seed}.json")
        
        audio_chunks = []
        s_transcript = []
        
        # Every second has a word, except second 4 which is silent
        for w in range(int(self.source_duration)):
            is_silence = w == 4
            chunk = self._generate_audio_chunk(float(w), float(w+1), 1.0, is_silence)
            audio_chunks.append(chunk)
            
            if not is_silence:
                s_transcript.append({"text": self.words[w], "start": float(w), "end": w + 0.9})
                
        full_audio = np.concatenate(audio_chunks)
        wavfile.write(audio_path, self.sample_rate, (full_audio * 32767).astype(np.int16))
        
        with open(transcript_path, "w") as f:
            json.dump(s_transcript, f)
            
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(path, fourcc, self.fps, (self.width, self.height))
        
        for frame_idx in range(int(self.source_duration * self.fps)):
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            time_sec = frame_idx / self.fps
            
            text = f"TIME: {time_sec:.1f}s"
            cv2.putText(frame, text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Add dynamic movement
            x = int(50 + (frame_idx * 5) % (self.width - 100))
            cv2.circle(frame, (x, 200), 20, (0, 0, 255), -1)
            
            # Face box
            cv2.rectangle(frame, (400, 150), (500, 250), (0, 255, 0), 2)
            cv2.putText(frame, "FACE", (420, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Add some random noise blocks to test perceptual hashing
            if random.random() > 0.9:
                cv2.rectangle(frame, (0, 0), (20, 20), (255, 255, 255), -1)
                
            out.write(frame)
            
        out.release()
        return path

    def generate_edit(self, oracle: Dict[str, Any], seed: int = 0) -> str:
        random.seed(seed)
        np.random.seed(seed)
        source_path = os.path.join(self.output_dir, f"source_{seed}.mp4")
        path = os.path.join(self.output_dir, f"edited_{seed}.mp4")
        audio_path = os.path.join(self.output_dir, f"edited_{seed}.wav")
        transcript_path = os.path.join(self.output_dir, f"edited_{seed}.json")
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(path, fourcc, self.fps, (self.width, self.height))
        
        cap = cv2.VideoCapture(source_path)
        source_frames = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            source_frames.append(frame)
        cap.release()
        
        edited_audio_chunks = []
        e_transcript = []
        
        for block in sorted(oracle["blocks"], key=lambda x: x["edit_start"]):
            start_f = int(block["source_start"] * self.fps)
            end_f = int(block["source_end"] * self.fps)
            speed = block["speed_ratio"]
            
            # Audio
            if speed == 0.0:
                chunk = np.random.normal(0, 0.01, int(self.sample_rate * (block["edit_end"] - block["edit_start"])))
            else:
                block_audio_chunks = []
                for w in range(int(block["source_start"]), int(block["source_end"])):
                    is_silence = w == 4
                    c = self._generate_audio_chunk(float(w), float(w+1), speed, is_silence)
                    block_audio_chunks.append(c)
                if block_audio_chunks:
                    chunk = np.concatenate(block_audio_chunks)
                else:
                    chunk = np.zeros(0)
            edited_audio_chunks.append(chunk)
            
            # Transcript
            for w in range(int(block["source_start"]), int(block["source_end"])):
                if w == 4: continue # silence, no word
                s = block["edit_start"] + (w - block["source_start"])/speed if speed > 0 else block["edit_start"]
                e = block["edit_start"] + (w - block["source_start"] + 0.9)/speed if speed > 0 else block["edit_end"]
                e_transcript.append({"text": self.words[w], "start": s, "end": e})
                
            block_effects = [e for e in oracle["effects"] if e["source_start"] >= block["source_start"] and e["source_end"] <= block["source_end"]]
            frames_to_write = source_frames[start_f:end_f]
            
            if speed == 2.0:
                frames_to_write = frames_to_write[::2]
            elif speed == 0.5:
                frames_to_write = [f for f in frames_to_write for _ in range(2)]
            elif speed == 0.0: 
                if frames_to_write:
                    frames_to_write = [frames_to_write[0]] * int((block["edit_end"] - block["edit_start"]) * self.fps)
            
            final_frames = []
            for i, frame in enumerate(frames_to_write):
                if speed == 1.0:
                    current_src_time = block["source_start"] + (i / self.fps)
                elif speed == 2.0:
                    current_src_time = block["source_start"] + ((i*2) / self.fps)
                elif speed == 0.5:
                    current_src_time = block["source_start"] + ((i/2) / self.fps)
                else:
                    current_src_time = block["source_start"]

                frame_copy = frame.copy()
                
                for eff in block_effects:
                    if eff["source_start"] <= current_src_time < eff["source_end"]:
                        if eff["effect_type"] == "grayscale":
                            frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2GRAY)
                            frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_GRAY2BGR)
                        elif eff["effect_type"] == "zoom_face":
                            scale = eff.get("scale", 1.5)
                            cx, cy = eff.get("cx", 450), eff.get("cy", 200)
                            h, w = self.height, self.width
                            w_new, h_new = int(w / scale), int(h / scale)
                            x1 = max(0, cx - w_new // 2)
                            y1 = max(0, cy - h_new // 2)
                            x2 = min(w, x1 + w_new)
                            y2 = min(h, y1 + h_new)
                            cropped = frame_copy[y1:y2, x1:x2]
                            frame_copy = cv2.resize(cropped, (w, h))
                        elif eff["effect_type"] == "crop_focus" and eff["target"] == "screen_region":
                            cropped = frame_copy[0:300, 0:300]
                            frame_copy = cv2.resize(cropped, (self.width, self.height))

                final_frames.append(frame_copy)
                
            for f in final_frames:
                out.write(f)
                
        out.release()
        
        full_edited_audio = np.concatenate(edited_audio_chunks) if edited_audio_chunks else np.array([])
        wavfile.write(audio_path, self.sample_rate, (full_edited_audio * 32767).astype(np.int16))
        with open(transcript_path, "w") as f:
            json.dump(e_transcript, f)
            
        with open(os.path.join(self.output_dir, f"ground_truth_{seed}.json"), "w") as f:
            json.dump(oracle, f, indent=2)
            
        return path

class SyntheticOracleFactory:
    @staticmethod
    def generate_scenario(seed: int = 0) -> Dict[str, Any]:
        random.seed(seed)
        oracle = {
            "blocks": [],
            "effects": [],
            "source_duration": 10.0,
            "edit_duration": 0.0
        }
        
        edit_cursor = 0.0
        
        def add_block(source_start: float, source_end: float, speed: float):
            nonlocal edit_cursor
            edit_end = edit_cursor + (source_end - source_start) / speed if speed > 0 else edit_cursor + 1.0
            oracle["blocks"].append({
                "id": str(uuid.uuid4()),
                "run_id": f"run-{seed}",
                "source_start": source_start,
                "source_end": source_end,
                "edit_start": edit_cursor,
                "edit_end": edit_end,
                "speed_ratio": speed,
                "is_manual_override": False
            })
            edit_cursor = edit_end
            
        def add_effect(effect_type, s_start, s_end, target, **kwargs):
            # find corresponding edit time
            e_start = None
            e_end = None
            for b in oracle["blocks"]:
                if b["source_start"] <= s_start < b["source_end"]:
                    speed = b["speed_ratio"]
                    e_start = b["edit_start"] + (s_start - b["source_start"])/speed if speed > 0 else b["edit_start"]
                if b["source_start"] < s_end <= b["source_end"]:
                    speed = b["speed_ratio"]
                    e_end = b["edit_start"] + (s_end - b["source_start"])/speed if speed > 0 else b["edit_end"]
            
            if e_start is not None and e_end is not None:
                oracle["effects"].append({
                    "id": str(uuid.uuid4()),
                    "pair_id": f"pair-{seed}",
                    "effect_type": effect_type,
                    "target": target,
                    "source_start": s_start,
                    "source_end": s_end,
                    "edit_start": e_start,
                    "edit_end": e_end,
                    "is_manual_override": False,
                    "is_false_positive": False,
                    **kwargs
                })

        if seed == 0:
            add_block(0.0, 1.0, 1.0) # word0
            add_block(2.0, 4.0, 2.0) # word2, word3 (speed up)
            add_effect("speed_up", 2.0, 4.0, "full_frame")
            add_block(4.0, 6.0, 1.0) # silence (word4), word5
            add_effect("zoom_face", 5.0, 6.0, "facecam", scale=1.5, cx=450, cy=200)
            add_block(6.0, 7.0, 1.0) # word6
            add_effect("grayscale", 6.0, 7.0, "full_frame")
            add_block(7.0, 9.0, 1.0) # word7, word8
            add_effect("crop_focus", 7.0, 8.0, "screen_region")
            add_effect("zoom_face", 8.0, 9.0, "facecam", scale=1.8, cx=450, cy=200)
            add_block(9.0, 9.1, 0.0) # freeze frame
            add_effect("freeze_frame", 9.0, 9.1, "full_frame")
            
        elif seed == 1:
            add_block(1.0, 3.0, 1.0)
            add_block(4.0, 5.0, 1.0) # silence
            add_effect("grayscale", 4.0, 5.0, "full_frame")
            add_block(5.0, 6.0, 0.5) # slowmo
            add_effect("slow_motion", 5.0, 6.0, "full_frame")
            add_block(6.0, 8.0, 1.0)
            add_effect("zoom_face", 6.5, 7.5, "facecam", scale=1.3, cx=450, cy=200)
            
        elif seed == 2:
            # Negative test: natural continuity, no effects
            add_block(0.0, 2.0, 1.0)
            add_block(4.0, 8.0, 1.0)
            
        oracle["edit_duration"] = edit_cursor
        return oracle

