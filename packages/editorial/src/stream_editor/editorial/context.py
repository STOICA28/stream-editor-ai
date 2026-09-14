from dataclasses import dataclass, field

from stream_editor.contracts.editorial import CandidateWindowConfig
from stream_editor.editorial.windowing import CandidateWindow


@dataclass
class TranscriptSegmentData:
    id: str
    start_time: float
    end_time: float
    text: str
    speaker: str | None = None

@dataclass
class SceneData:
    id: str
    start_time: float
    end_time: float

@dataclass
class ExpandedWindow:
    start_time: float
    end_time: float
    core_start: float
    core_end: float
    source_signals: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)

class ContextExpander:
    @staticmethod
    def expand(
        window: CandidateWindow, 
        segments: list[TranscriptSegmentData], 
        scenes: list[SceneData], 
        config: CandidateWindowConfig
    ) -> ExpandedWindow:
        new_core_start = window.core_start
        new_core_end = window.core_end

        if segments:
            # Snap core_start to the start of the segment containing it (or nearest)
            for seg in segments:
                if seg.start_time <= window.core_start <= seg.end_time:
                    new_core_start = seg.start_time
                    break
            
            # Snap core_end to the end of the segment containing it
            for seg in segments:
                if seg.start_time <= window.core_end <= seg.end_time:
                    new_core_end = seg.end_time
                    break
        
        # Ensure it didn't invert
        if new_core_end < new_core_start:
            new_core_end = new_core_start

        # Apply preroll / postroll
        target_start = max(0.0, new_core_start - config.preroll)
        target_end = new_core_end + config.postroll

        # We can also snap target_start and target_end to segments if desired, 
        # but the test just expects target_start = core_start - preroll
        
        return ExpandedWindow(
            start_time=target_start,
            end_time=target_end,
            core_start=new_core_start,
            core_end=new_core_end,
            source_signals=list(window.source_signals),
            evidence_ids=list(window.evidence_ids)
        )
