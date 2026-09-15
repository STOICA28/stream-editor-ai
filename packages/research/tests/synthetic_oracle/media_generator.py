import uuid
import cv2
import numpy as np
import json
import os
from typing import Dict, Any, List
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
        
    def _generate_audio_chunk(self, start_sec: float, end_sec: float, speed: float = 1.0) -> np.ndarray:
        duration = end_sec - start_sec
        if speed == 0.0:
            return np.zeros(0)
        t = np.linspace(0, duration / speed, int(self.sample_rate * duration / speed), False)
        freq = 440 + (start_sec * 50)
        audio = np.sin(freq * t * 2 * np.pi)
        return audio

    def generate_source(self) -> str:
        path = os.path.join(self.output_dir, "source.mp4")
        audio_path = os.path.join(self.output_dir, "source.wav")
        transcript_path = os.path.join(self.output_dir, "source.json")
        
        full_audio = self._generate_audio_chunk(0.0, self.source_duration, 1.0)
        wavfile.write(audio_path, self.sample_rate, (full_audio * 32767).astype(np.int16))
        
        s_transcript = []
        for w in range(int(self.source_duration)):
            s_transcript.append({"text": f"word{w}", "start": float(w), "end": w + 0.9})
        with open(transcript_path, "w") as f:
            json.dump(s_transcript, f)
            
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(path, fourcc, self.fps, (self.width, self.height))
        
        for frame_idx in range(int(self.source_duration * self.fps)):
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            time_sec = frame_idx / self.fps
            
            text = f"TIME: {time_sec:.1f}s"
            cv2.putText(frame, text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            x = int(50 + (frame_idx * 5) % (self.width - 100))
            cv2.circle(frame, (x, 200), 20, (0, 0, 255), -1)
            cv2.rectangle(frame, (400, 150), (500, 250), (0, 255, 0), 2)
            cv2.putText(frame, "FACE", (420, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            out.write(frame)
            
        out.release()
        return path

    def generate_edit(self, oracle: Dict[str, Any]) -> str:
        source_path = os.path.join(self.output_dir, "source.mp4")
        path = os.path.join(self.output_dir, "edited.mp4")
        audio_path = os.path.join(self.output_dir, "edited.wav")
        transcript_path = os.path.join(self.output_dir, "edited.json")
        
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
            
            if speed == 0.0:
                chunk = np.zeros(int(self.sample_rate * (block["edit_end"] - block["edit_start"])))
            else:
                chunk = self._generate_audio_chunk(block["source_start"], block["source_end"], speed)
                
            edited_audio_chunks.append(chunk)
            
            for w in range(int(block["source_start"]), int(block["source_end"])):
                s = block["edit_start"] + (w - block["source_start"])/speed if speed > 0 else block["edit_start"]
                e = block["edit_start"] + (w - block["source_start"] + 0.9)/speed if speed > 0 else block["edit_end"]
                e_transcript.append({"text": f"word{w}", "start": s, "end": e})
                
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
                            cx, cy = 450, 200
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
            
        with open(os.path.join(self.output_dir, "ground_truth.json"), "w") as f:
            json.dump(oracle, f, indent=2)
            
        return path

class SmallSyntheticOracle:
    def __init__(self) -> None:
        self.source_duration = 10.0
        self.edit_duration = 0.0
        self.true_blocks: List[Dict[str, Any]] = []
        self.true_effects: List[Dict[str, Any]] = []
        
    def generate_scenario(self) -> Dict[str, Any]:
        self.add_block(0.0, 1.0, 0.0, 1.0, 1.0)
        self.add_block(2.0, 4.0, 1.0, 2.0, 2.0)
        self.add_effect("speed_up", 2.0, 4.0, 1.0, 2.0, "full_frame")
        self.add_block(5.0, 6.0, 2.0, 3.0, 1.0)
        self.add_effect("zoom_face", 5.0, 6.0, 2.0, 3.0, "facecam", scale=1.5)
        self.add_block(6.0, 7.0, 3.0, 4.0, 1.0)
        self.add_effect("grayscale", 6.0, 7.0, 3.0, 4.0, "full_frame")
        self.add_block(7.0, 9.0, 4.0, 6.0, 1.0)
        self.add_effect("crop_focus", 7.0, 8.0, 4.0, 5.0, "screen_region")
        self.add_effect("zoom_face", 8.0, 9.0, 5.0, 6.0, "facecam", scale=1.5)
        self.add_block(9.0, 9.1, 6.0, 7.0, 0.0)
        self.add_effect("freeze_frame", 9.0, 9.1, 6.0, 7.0, "full_frame")
        self.edit_duration = 7.0
        return {
            "blocks": self.true_blocks,
            "effects": self.true_effects,
            "source_duration": self.source_duration,
            "edit_duration": self.edit_duration
        }

    def add_block(self, source_start: float, source_end: float, edit_start: float, edit_end: float, speed: float) -> None:
        self.true_blocks.append({
            "id": str(uuid.uuid4()),
            "run_id": "dummy-run-id",
            "source_start": source_start,
            "source_end": source_end,
            "edit_start": edit_start,
            "edit_end": edit_end,
            "speed_ratio": speed,
            "audio_confidence": 0.99,
            "transcript_confidence": 0.95,
            "visual_confidence": 0.98,
            "combined_confidence": 0.98,
            "method": "combined",
            "is_manual_override": False
        })
        
    def add_effect(self, effect_type: str, source_start: float, source_end: float, edit_start: float, edit_end: float, target: str, **kwargs: Any) -> None:
        self.true_effects.append({
            "id": str(uuid.uuid4()),
            "pair_id": "dummy-pair-id",
            "effect_type": effect_type,
            "target": target,
            "source_start": source_start,
            "source_end": source_end,
            "edit_start": edit_start,
            "edit_end": edit_end,
            "confidence": 0.95,
            "detection_method": "visual",
            "is_manual_override": False,
            "is_false_positive": False,
            **kwargs
        })
