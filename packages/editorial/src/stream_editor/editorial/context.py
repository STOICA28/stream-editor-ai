from dataclasses import dataclass, field
from stream_editor.contracts.editorial import CandidateWindowConfig
from stream_editor.editorial.windowing import CandidateWindow

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
    def expand(window: CandidateWindow, segments: list[dict], scenes: list[dict], config: CandidateWindowConfig) -> ExpandedWindow:
        target_start = max(0.0, window.core_start - config.preroll)
        target_end = window.core_end + config.postroll

        actual_start = target_start
        actual_end = target_end

        if segments:
            best_start = target_start
            min_diff_start = float('inf')
            for seg in segments:
                start_t = seg.get('start_time', 0.0)
                diff = abs(start_t - target_start)
                if diff < min_diff_start:
                    min_diff_start = diff
                    best_start = start_t
            
            best_end = target_end
            min_diff_end = float('inf')
            for seg in segments:
                end_t = seg.get('end_time', 0.0)
                diff = abs(end_t - target_end)
                if diff < min_diff_end:
                    min_diff_end = diff
                    best_end = end_t
            
            actual_start = best_start
            actual_end = best_end

        actual_start = min(actual_start, window.core_start)
        actual_end = max(actual_end, window.core_end)

        return ExpandedWindow(
            start_time=actual_start,
            end_time=actual_end,
            core_start=window.core_start,
            core_end=window.core_end,
            source_signals=list(window.source_signals),
            evidence_ids=list(window.evidence_ids)
        )
