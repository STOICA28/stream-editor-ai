
import torch

from stream_editor.contracts.analysis import (
    TranscriptionConfig,
    TranscriptionProvider,
    TranscriptSegment,
    TranscriptWord,
)


class WhisperXTranscriptionProvider(TranscriptionProvider):
    def transcribe(self, audio_path: str, config: TranscriptionConfig) -> list[TranscriptSegment]:
        import whisperx  # type: ignore[import-not-found]
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = config.compute_type if device == "cuda" else "int8"
        
        model = whisperx.load_model(
            config.model, 
            device, 
            compute_type=compute_type, 
            language=config.language
        )
        
        audio = whisperx.load_audio(audio_path)
        
        result = model.transcribe(audio, batch_size=config.batch_size)
        
        model_a, metadata = whisperx.load_align_model(
            language_code=result["language"], 
            device=device
        )
        
        result = whisperx.align(
            result["segments"], 
            model_a, 
            metadata, 
            audio, 
            device, 
            return_char_alignments=False
        )
        
        # Diarization
        try:
            diarize_model = whisperx.DiarizationPipeline(use_auth_token=True, device=device)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
        except Exception:
            # Diarization can fail if auth token is not set, we can just skip it or log it.
            pass
        
        transcript_segments = []
        for segment in result.get("segments", []):
            words = []
            for word_info in segment.get("words", []):
                words.append(
                    TranscriptWord(
                        word=word_info.get("word", ""),
                        start=word_info.get("start", 0.0),
                        end=word_info.get("end", 0.0),
                        score=word_info.get("score")
                    )
                )
            
            transcript_segments.append(
                TranscriptSegment(
                    text=segment.get("text", "").strip(),
                    start=segment.get("start", 0.0),
                    end=segment.get("end", 0.0),
                    words=words,
                    speaker=segment.get("speaker")
                )
            )
            
        return transcript_segments
