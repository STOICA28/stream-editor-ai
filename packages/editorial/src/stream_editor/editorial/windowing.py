"""
Temporal windowing: EventClusterer and CandidateWindowBuilder.

Groups TimelineEvents into candidate windows respecting CandidateWindowConfig.
Does NOT make editorial decisions - it generates infrastructure windows.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from stream_editor.contracts.editorial import CandidateWindowConfig


@dataclass
class CandidateWindow:
    """Raw candidate window before context expansion."""
    core_start: float
    core_end: float
    source_signals: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)


class EventClusterer:
    """Groups TimelineEvents into temporal clusters by proximity."""

    def cluster(
        self,
        events: list[dict[str, object]],
        merge_gap: float,
    ) -> list[list[dict[str, object]]]:
        """
        Cluster events where consecutive events are within merge_gap seconds.

        Args:
            events: List of dicts with 'start_time', 'end_time', 'event_type', 'id'.
            merge_gap: Max gap (seconds) between events to merge into same cluster.

        Returns:
            List of clusters, each cluster is a list of event dicts.
        """
        if not events:
            return []

        sorted_events = sorted(events, key=lambda e: float(str(e.get("start_time", 0))))
        clusters: list[list[dict[str, object]]] = [[sorted_events[0]]]

        for event in sorted_events[1:]:
            last_cluster = clusters[-1]
            last_end = max(float(str(e.get("end_time", 0))) for e in last_cluster)
            event_start = float(str(event.get("start_time", 0)))

            if event_start - last_end <= merge_gap:
                last_cluster.append(event)
            else:
                clusters.append([event])

        return clusters


class CandidateWindowBuilder:
    """Converts event clusters into CandidateWindow objects."""

    def build(
        self,
        clusters: list[list[dict[str, object]]],
        config: CandidateWindowConfig,
    ) -> list[CandidateWindow]:
        """
        Build candidate windows from event clusters.

        - Skips clusters shorter than min_duration.
        - Truncates clusters longer than max_duration to max_duration
          (longer events are truncated from the end, not split).

        Args:
            clusters: Event clusters from EventClusterer.
            config: CandidateWindowConfig controlling durations.

        Returns:
            List of CandidateWindow.
        """
        windows: list[CandidateWindow] = []

        for cluster in clusters:
            if not cluster:
                continue

            core_start = min(float(str(e.get("start_time", 0))) for e in cluster)
            core_end = max(float(str(e.get("end_time", 0))) for e in cluster)
            duration = core_end - core_start

            if duration < config.min_duration:
                # Pad short clusters to min_duration
                pad = (config.min_duration - duration) / 2
                core_start = max(0.0, core_start - pad)
                core_end = core_start + config.min_duration
                duration = config.min_duration

            if duration > config.max_duration:
                # Truncate from end
                core_end = core_start + config.max_duration

            signals = list({str(e.get("event_type", "unknown")) for e in cluster})
            evidence_ids = [str(e.get("id", "")) for e in cluster if e.get("id")]

            windows.append(
                CandidateWindow(
                    core_start=core_start,
                    core_end=core_end,
                    source_signals=signals,
                    evidence_ids=evidence_ids,
                )
            )

        return windows
