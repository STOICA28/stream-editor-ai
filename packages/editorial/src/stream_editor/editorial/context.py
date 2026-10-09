from __future__ import annotations

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
    merged_event_ids: list[str] = field(default_factory=list)
    relation_types: list[str] = field(default_factory=list)
    relation_confidence: float = 1.0
    boundary_reason: str = "expanded"
    config_version: str = "default"


class ContextExpander:
    @staticmethod
    def expand(
        window: CandidateWindow,
        segments: list[TranscriptSegmentData],
        scenes: list[SceneData],
        config: CandidateWindowConfig,
    ) -> ExpandedWindow:
        new_core_start = window.core_start
        new_core_end = window.core_end
        boundary_reasons: list[str] = []

        clustering_cfg = getattr(config, "clustering_config", None)

        if segments:
            # Snap core_start to the start of the segment containing it (or nearest)
            for seg in segments:
                if seg.start_time <= window.core_start <= seg.end_time:
                    new_core_start = seg.start_time
                    boundary_reasons.append("snapped_to_utterance_start")
                    break

            # Snap core_end to the end of the segment containing it
            for seg in segments:
                if seg.start_time <= window.core_end <= seg.end_time:
                    new_core_end = seg.end_time
                    boundary_reasons.append("snapped_to_utterance_end")
                    break

            if clustering_cfg is not None:
                # EXP-002: Bounded relational context expansion
                max_backward = clustering_cfg.max_backward_context
                max_forward = clustering_cfg.max_forward_context

                # 1. Backward setup expansion bounded by max_backward_context
                for seg in segments:
                    diff = window.core_start - seg.start_time
                    if 0.0 <= diff <= max_backward:
                        if seg.start_time < new_core_start:
                            new_core_start = seg.start_time
                            boundary_reasons.append("expanded_backward_setup")
                            break

                # Hard clamp to max_backward_context
                min_allowed_start = max(0.0, window.core_start - max_backward)
                if new_core_start < min_allowed_start:
                    new_core_start = min_allowed_start
                    boundary_reasons.append("clamped_by_max_backward")

                # 2. Forward payoff expansion bounded by max_forward_context
                for seg in segments:
                    diff = seg.end_time - window.core_end
                    if 0.0 <= diff <= max_forward:
                        if seg.end_time > new_core_end:
                            new_core_end = seg.end_time
                            boundary_reasons.append("expanded_forward_payoff")
                            break

                # Hard clamp to max_forward_context
                max_allowed_end = window.core_end + max_forward
                if new_core_end > max_allowed_end:
                    new_core_end = max_allowed_end
                    boundary_reasons.append("clamped_by_max_forward")

                # 3. Scene boundary hard stop (Section 14 & 15)
                if scenes and clustering_cfg.scene_boundary_hard_stop:
                    for sc in scenes:
                        # Backward: scene cut cannot be crossed by setup expansion
                        if new_core_start < sc.start_time <= window.core_start:
                            new_core_start = sc.start_time
                            boundary_reasons.append("scene_boundary_hard_stop_backward")
                        # Forward: scene cut cannot be crossed by payoff expansion
                        if window.core_end <= sc.start_time < new_core_end:
                            new_core_end = sc.start_time
                            boundary_reasons.append("scene_boundary_hard_stop_forward")

            else:
                # Legacy EXP-002 baseline: backward_setup_window
                setup_window = getattr(config, "backward_setup_window", 0.0)
                if setup_window > 0:
                    for seg in segments:
                        if 0.0 <= (window.core_start - seg.start_time) <= setup_window:
                            if seg.start_time < new_core_start:
                                new_core_start = seg.start_time
                                boundary_reasons.append("legacy_backward_setup")
                                break

                # Scene cut guard
                if scenes:
                    for sc in scenes:
                        if new_core_start < sc.start_time <= window.core_start:
                            new_core_start = sc.start_time
                            boundary_reasons.append("legacy_scene_guard")

        # Ensure it didn't invert
        if new_core_end < new_core_start:
            new_core_end = new_core_start

        # Apply preroll / postroll
        target_start = max(0.0, new_core_start - config.preroll)
        target_end = new_core_end + config.postroll

        conf_version = (
            clustering_cfg.version if clustering_cfg else getattr(window, "config_version", "default")
        )
        reason_str = ";".join(boundary_reasons) if boundary_reasons else getattr(window, "boundary_reason", "expanded")

        return ExpandedWindow(
            start_time=target_start,
            end_time=target_end,
            core_start=new_core_start,
            core_end=new_core_end,
            source_signals=list(window.source_signals),
            evidence_ids=list(window.evidence_ids),
            merged_event_ids=list(getattr(window, "merged_event_ids", [])),
            relation_types=list(getattr(window, "relation_types", [])),
            relation_confidence=getattr(window, "relation_confidence", 1.0),
            boundary_reason=reason_str,
            config_version=conf_version,
        )
