"""Extract and transcribe authentic audio for the 3 diagnostic pilot regions."""
import os
import json
import time
import subprocess
import numpy as np
from pathlib import Path
from faster_whisper import WhisperModel

CACHE_DIR = Path("cache/pilot_transcripts")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_WAV = r"C:\Users\adria\Desktop\Descargas\source.wav"

REGIONS = {
    "region_a_intro": (0.0, 360.0),            # 0 to 6 mins: Greeting, audio/YouTube checks, premise, launch
    "region_b_police": (5440.0, 5550.0),        # Police inspection payoff
    "region_b_store_jump": (11800.0, 11920.0),  # Massive jump location: 104 mins later
    "region_c_customer_loop": (920.0, 1050.0),  # First customer & grinding loop
    "region_c_cultivation": (1820.0, 1930.0),   # Basement grow setup
}

def transcribe_slice(model: WhisperModel, start_sec: float, duration_sec: float):
    print(f"Extracting audio slice: {start_sec}s -> {start_sec + duration_sec}s...")
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-t", str(duration_sec),
        "-i", SOURCE_WAV,
        "-f", "f32le", "-ac", "1", "-ar", "16000", "-"
    ]
    p = subprocess.run(cmd, capture_output=True, check=True)
    audio_data = np.frombuffer(p.stdout, dtype=np.float32)

    print(f"Transcribing {duration_sec}s of audio...")
    segments, info = model.transcribe(audio_data, language="es", beam_size=5)
    
    results = []
    for s in segments:
        abs_start = round(start_sec + s.start, 2)
        abs_end = round(start_sec + s.end, 2)
        results.append({
            "source_start": abs_start,
            "source_end": abs_end,
            "duration": round(abs_end - abs_start, 2),
            "text": s.text.strip(),
            "avg_logprob": s.avg_logprob,
            "no_speech_prob": s.no_speech_prob,
        })
    return results

def main():
    print("Loading faster-whisper base model...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    
    all_data = {}
    for name, (start_sec, end_sec) in REGIONS.items():
        dur = end_sec - start_sec
        out_file = CACHE_DIR / f"{name}.json"
        if out_file.exists():
            print(f"Loading cached {name} from {out_file}")
            with open(out_file, "r", encoding="utf-8") as f:
                all_data[name] = json.load(f)
            continue
            
        print(f"\n--- Transcribing {name} ({start_sec}s - {end_sec}s) ---")
        t0 = time.time()
        segs = transcribe_slice(model, start_sec, dur)
        print(f"Transcribed {len(segs)} segments in {time.time() - t0:.2f}s")
        
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(segs, f, indent=2, ensure_ascii=False)
        all_data[name] = segs

    print("\nTranscription extraction complete!")

if __name__ == "__main__":
    main()
