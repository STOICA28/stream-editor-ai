
from stream_editor.contracts.analysis import (
    AudioAnalysisProvider,
    AudioEvent,
    AudioEventConfig,
    Scene,
    SceneConfig,
    SceneDetectionProvider,
    TranscriptionConfig,
    TranscriptionProvider,
    TranscriptSegment,
    TranscriptWord,
)


class MockTranscriptionProvider(TranscriptionProvider):
    def transcribe(self, audio_path: str, config: TranscriptionConfig) -> list[TranscriptSegment]:
        return [
            TranscriptSegment(
                text="Hello world, this is a mock transcription.",
                start=0.0,
                end=2.5,
                words=[
                    TranscriptWord(word="Hello", start=0.0, end=0.5, score=0.99),
                    TranscriptWord(word="world,", start=0.5, end=1.0, score=0.98),
                    TranscriptWord(word="this", start=1.0, end=1.3, score=0.99),
                    TranscriptWord(word="is", start=1.3, end=1.5, score=0.99),
                    TranscriptWord(word="a", start=1.5, end=1.6, score=0.99),
                    TranscriptWord(word="mock", start=1.6, end=2.0, score=0.99),
                    TranscriptWord(word="transcription.", start=2.0, end=2.5, score=0.99),
                ],
                speaker="SPEAKER_00"
            ),
            TranscriptSegment(
                text="It is returning synthetic segments deterministically.",
                start=2.5,
                end=5.0,
                words=[
                    TranscriptWord(word="It", start=2.5, end=2.7, score=0.99),
                    TranscriptWord(word="is", start=2.7, end=2.9, score=0.99),
                    TranscriptWord(word="returning", start=2.9, end=3.5, score=0.99),
                    TranscriptWord(word="synthetic", start=3.5, end=4.0, score=0.99),
                    TranscriptWord(word="segments", start=4.0, end=4.5, score=0.99),
                    TranscriptWord(word="deterministically.", start=4.5, end=5.0, score=0.99),
                ],
                speaker="SPEAKER_00"
            )
        ]

class MockSceneDetectionProvider(SceneDetectionProvider):
    def detect_scenes(self, video_path: str, config: SceneConfig) -> list[Scene]:
        return [
            Scene(start_time=0.0, end_time=10.0),
            Scene(start_time=10.0, end_time=25.0)
        ]

class MockAudioAnalysisProvider(AudioAnalysisProvider):
    def analyze_audio(self, audio_path: str, config: AudioEventConfig) -> list[AudioEvent]:
        return [
            AudioEvent(event_type="silence", start_time=0.0, end_time=1.5),
            AudioEvent(event_type="high_energy", start_time=3.0, end_time=5.0)
        ]
