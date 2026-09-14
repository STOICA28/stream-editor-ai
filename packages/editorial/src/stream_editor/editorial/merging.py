from dataclasses import dataclass, field
from stream_editor.editorial.context import ExpandedWindow

@dataclass
class MergedWindow:
    start_time: float
    end_time: float
    core_start: float
    core_end: float
    source_signals: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)

class CandidateMerger:
    @staticmethod
    def merge(windows: list[ExpandedWindow], overlap_threshold: float) -> list[MergedWindow]:
        if not windows:
            return []
            
        sorted_windows = sorted(windows, key=lambda w: w.start_time)
        merged = []
        
        current = MergedWindow(
            start_time=sorted_windows[0].start_time,
            end_time=sorted_windows[0].end_time,
            core_start=sorted_windows[0].core_start,
            core_end=sorted_windows[0].core_end,
            source_signals=list(sorted_windows[0].source_signals),
            evidence_ids=list(sorted_windows[0].evidence_ids)
        )
        
        for nxt in sorted_windows[1:]:
            # Check overlap
            overlap_start = max(current.start_time, nxt.start_time)
            overlap_end = min(current.end_time, nxt.end_time)
            overlap_duration = max(0.0, overlap_end - overlap_start)
            
            dur_current = current.end_time - current.start_time
            dur_nxt = nxt.end_time - nxt.start_time
            min_dur = min(dur_current, dur_nxt)
            
            if min_dur > 0 and (overlap_duration / min_dur) > overlap_threshold:
                # Merge
                current.start_time = min(current.start_time, nxt.start_time)
                current.end_time = max(current.end_time, nxt.end_time)
                current.core_start = min(current.core_start, nxt.core_start)
                current.core_end = max(current.core_end, nxt.core_end)
                current.source_signals = list(set(current.source_signals + nxt.source_signals))
                current.evidence_ids = list(set(current.evidence_ids + nxt.evidence_ids))
            else:
                merged.append(current)
                current = MergedWindow(
                    start_time=nxt.start_time,
                    end_time=nxt.end_time,
                    core_start=nxt.core_start,
                    core_end=nxt.core_end,
                    source_signals=list(nxt.source_signals),
                    evidence_ids=list(nxt.evidence_ids)
                )
                
        merged.append(current)
        return merged
