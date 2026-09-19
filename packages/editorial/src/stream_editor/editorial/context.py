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

            # EXP-002: Backward setup window expansion
            # If the candidate start truncated the opening of a setup or if an immediate
            # setup lead-in exists within backward_setup_window, extend new_core_start backward.
            setup_window = getattr(config, "backward_setup_window", 0.0)
            if setup_window > 0:
                for seg in segments:
                    # If segment starts slightly before core_start (within setup_window) and ends near or into core
                    if 0.0 <= (window.core_start - seg.start_time) <= setup_window:
                        if seg.start_time < new_core_start:
                            new_core_start = seg.start_time
                            break

            # If a hard scene cut separates setup from core, don't cross it
            if scenes:
                for sc in scenes:
                    if new_core_start < sc.start_time <= window.core_start:
                        new_core_start = sc.start_time
        
        # Ensure it didn't invert
        if new_core_end < new_core_start:
            new_core_end = new_core_start

        # Apply preroll / postroll
        target_start = max(0.0, new_core_start - config.preroll)
        target_end = new_core_end + config.postroll
        
        return ExpandedWindow(
            start_time=target_start,
            end_time=target_end,
            core_start=new_core_start,
            core_end=new_core_end,
            source_signals=list(window.source_signals),
            evidence_ids=list(window.evidence_ids)
        )

