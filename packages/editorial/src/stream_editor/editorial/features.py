import math
import re
from collections import Counter
from stream_editor.contracts.editorial import LocalFeatures

class LocalFeatureExtractor:
    @staticmethod
    def extract(segments: list[dict], events: list[dict], scenes: list[dict], start_time: float, end_time: float) -> LocalFeatures:
        duration_seconds = max(end_time - start_time, 0.1)
        
        # Filter items within window
        window_segments = [s for s in segments if s.get('start_time', 0) < end_time and s.get('end_time', 0) > start_time]
        window_events = [e for e in events if e.get('start_time', e.get('timestamp', 0)) >= start_time and e.get('start_time', e.get('timestamp', 0)) <= end_time]
        window_scenes = [s for s in scenes if s.get('start_time', 0) >= start_time and s.get('start_time', 0) <= end_time]

        # transcript text and chars
        text = " ".join(s.get('text', '') for s in window_segments)
        transcript_char_length = len(text)

        # speech density & silence
        speech_time = sum(min(s.get('end_time', 0), end_time) - max(s.get('start_time', 0), start_time) for s in window_segments)
        speech_density = min(1.0, speech_time / duration_seconds) if duration_seconds > 0 else 0.0
        silence_ratio = max(0.0, 1.0 - speech_density)

        # speaker turns
        speaker_changes = 0
        last_speaker = None
        for s in window_segments:
            speaker = s.get('speaker_id', s.get('speaker'))
            if speaker and speaker != last_speaker:
                speaker_changes += 1
                last_speaker = speaker
        speaker_turn_frequency = (speaker_changes / duration_seconds) * 60.0

        # audio peaks
        audio_peaks = sum(1 for e in window_events if e.get('type') == 'high_energy' or e.get('label') == 'high_energy')

        # scene changes
        scene_change_rate = (len(window_scenes) / duration_seconds) * 60.0

        # exclamation density
        sentences = re.split(r'[.!?]+', text)
        sentences_count = len([s for s in sentences if s.strip()])
        exclamation_count = text.count('!')
        exclamation_density = (exclamation_count / sentences_count) if sentences_count > 0 else 0.0

        # Lexical novelty using dummy TF-IDF within segments
        lexical_novelty = 0.5
        if window_segments:
            words = [w.lower() for w in re.findall(r'\w+', text)]
            if words:
                counts = Counter(words)
                # Just a dummy metric based on unique words
                lexical_novelty = len(counts) / len(words)

        return LocalFeatures(
            speech_density=speech_density,
            silence_ratio=silence_ratio,
            speaker_turn_frequency=speaker_turn_frequency,
            audio_peaks=audio_peaks,
            scene_change_rate=scene_change_rate,
            transcript_char_length=transcript_char_length,
            exclamation_density=exclamation_density,
            lexical_novelty=lexical_novelty,
            duration_seconds=duration_seconds,
            audio_rms_estimate=0.5 # placeholder
        )
