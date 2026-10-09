from __future__ import annotations

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
    merged_event_ids: list[str] = field(default_factory=list)
    relation_types: list[str] = field(default_factory=list)
    relation_confidence: float = 1.0
    boundary_reason: str = "merged"
    config_version: str = "default"


class CandidateMerger:
    @staticmethod
    def merge(windows: list[ExpandedWindow], overlap_threshold: float) -> list[MergedWindow]:
        if not windows:
            return []

        sorted_windows = sorted(windows, key=lambda w: w.start_time)
        merged: list[MergedWindow] = []

        w0 = sorted_windows[0]
        current = MergedWindow(
            start_time=w0.start_time,
            end_time=w0.end_time,
            core_start=w0.core_start,
            core_end=w0.core_end,
            source_signals=list(w0.source_signals),
            evidence_ids=list(w0.evidence_ids),
            merged_event_ids=list(getattr(w0, "merged_event_ids", [])),
            relation_types=list(getattr(w0, "relation_types", [])),
            relation_confidence=getattr(w0, "relation_confidence", 1.0),
            boundary_reason=getattr(w0, "boundary_reason", "initial"),
            config_version=getattr(w0, "config_version", "default"),
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
                current.merged_event_ids = list(
                    set(current.merged_event_ids + getattr(nxt, "merged_event_ids", []))
                )
                current.relation_types = list(
                    set(current.relation_types + getattr(nxt, "relation_types", []))
                )
                current.relation_confidence = min(
                    current.relation_confidence, getattr(nxt, "relation_confidence", 1.0)
                )
                current.boundary_reason = f"{current.boundary_reason}+overlap_merge"
            else:
                merged.append(current)
                current = MergedWindow(
                    start_time=nxt.start_time,
                    end_time=nxt.end_time,
                    core_start=nxt.core_start,
                    core_end=nxt.core_end,
                    source_signals=list(nxt.source_signals),
                    evidence_ids=list(nxt.evidence_ids),
                    merged_event_ids=list(getattr(nxt, "merged_event_ids", [])),
                    relation_types=list(getattr(nxt, "relation_types", [])),
                    relation_confidence=getattr(nxt, "relation_confidence", 1.0),
                    boundary_reason=getattr(nxt, "boundary_reason", "initial"),
                    config_version=getattr(nxt, "config_version", "default"),
                )

        merged.append(current)
        return merged
