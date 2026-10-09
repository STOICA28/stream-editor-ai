"""
Temporal windowing: EventClusterer and CandidateWindowBuilder.

Groups TimelineEvents into candidate windows respecting CandidateWindowConfig.
Supports EXP-002 Bounded Relational Clustering.
Does NOT make editorial decisions - it generates infrastructure windows.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from stream_editor.contracts.editorial import (
    CandidateClusteringExperimentConfig,
    CandidateRelationEvidence,
    CandidateRelationType,
    CandidateWindowConfig,
)


@dataclass
class CandidateWindow:
    """Raw candidate window before context expansion."""
    core_start: float
    core_end: float
    source_signals: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    merged_event_ids: list[str] = field(default_factory=list)
    relation_types: list[str] = field(default_factory=list)
    relation_confidence: float = 1.0
    boundary_reason: str = "cluster_core"
    config_version: str = "default"


class CandidateRelationClassifier:
    """
    EXP-002: Evidence-based relation classifier for adjacent TimelineEvents.
    Evaluates causal, reaction, conversational, and scene continuity.
    """

    @staticmethod
    def classify_relation(
        event_a: dict[str, object],
        event_b: dict[str, object],
        clustering_config: CandidateClusteringExperimentConfig,
        scenes: list[dict[str, object]] | None = None,
    ) -> CandidateRelationEvidence:
        start_a = float(str(event_a.get("start_time", 0.0)))
        end_a = float(str(event_a.get("end_time", 0.0)))
        start_b = float(str(event_b.get("start_time", 0.0)))
        end_b = float(str(event_b.get("end_time", 0.0)))
        type_a = str(event_a.get("event_type", "unknown"))
        type_b = str(event_b.get("event_type", "unknown"))
        id_a = str(event_a.get("id", ""))
        id_b = str(event_b.get("id", ""))
        speaker_a = event_a.get("speaker")
        speaker_b = event_b.get("speaker")

        gap = max(0.0, start_b - end_a)

        # 1. Temporal upper bound
        if gap > clustering_config.max_related_event_gap:
            return CandidateRelationEvidence(
                source_event_id=id_a,
                target_event_id=id_b,
                relation_type=CandidateRelationType.UNRELATED,
                confidence=0.0,
                temporal_gap=gap,
                evidence_notes=f"Temporal gap {gap:.2f}s exceeds max_related_event_gap {clustering_config.max_related_event_gap:.2f}s",
            )

        # 2. Visual scene cut hard-stop
        same_scene = True
        if scenes and clustering_config.scene_boundary_hard_stop:
            for sc in scenes:
                sc_start = float(str(sc.get("start_time", 0.0)))
                # If a scene cut occurs strictly between end_a and start_b
                if end_a <= sc_start <= start_b and sc_start > end_a:
                    same_scene = False
                    return CandidateRelationEvidence(
                        source_event_id=id_a,
                        target_event_id=id_b,
                        relation_type=CandidateRelationType.UNRELATED,
                        confidence=0.0,
                        temporal_gap=gap,
                        same_scene=False,
                        evidence_notes=f"Scene cut at {sc_start:.2f}s separates events",
                    )

        # 3. Speaker continuity check
        speaker_cont = (speaker_a is None or speaker_b is None or speaker_a == speaker_b)

        # 4. Reaction following trigger / event
        is_trigger_a = type_a in ("game_event", "gameplay", "gameplay_clutch", "visual_event", "action")
        is_reaction_b = type_b in ("face_reaction", "laughter", "shout", "pause_with_reaction", "reaction")
        if is_trigger_a and is_reaction_b and gap <= clustering_config.reaction_link_window:
            return CandidateRelationEvidence(
                source_event_id=id_a,
                target_event_id=id_b,
                relation_type=CandidateRelationType.EVENT_TO_REACTION,
                confidence=0.95,
                temporal_gap=gap,
                same_scene=same_scene,
                speaker_continuity=speaker_cont,
                evidence_notes="Trigger followed by reaction within link window",
            )

        # Speech setup followed by visual/audio reaction
        if type_a == "speech" and is_reaction_b and gap <= clustering_config.reaction_link_window:
            return CandidateRelationEvidence(
                source_event_id=id_a,
                target_event_id=id_b,
                relation_type=CandidateRelationType.SETUP_TO_PAYOFF,
                confidence=0.92,
                temporal_gap=gap,
                same_scene=same_scene,
                speaker_continuity=speaker_cont,
                evidence_notes="Speech setup followed by reaction within link window",
            )

        # Speech setup followed by game event
        if type_a == "speech" and is_trigger_a and gap <= clustering_config.max_related_event_gap:
            return CandidateRelationEvidence(
                source_event_id=id_a,
                target_event_id=id_b,
                relation_type=CandidateRelationType.SETUP_TO_EVENT,
                confidence=0.88,
                temporal_gap=gap,
                same_scene=same_scene,
                speaker_continuity=speaker_cont,
                evidence_notes="Speech commentary leading into game event",
            )

        # Chat message followed by reaction/speech
        if type_a in ("chat_message", "chat_read") and (type_b == "speech" or is_reaction_b) and gap <= clustering_config.reaction_link_window:
            return CandidateRelationEvidence(
                source_event_id=id_a,
                target_event_id=id_b,
                relation_type=CandidateRelationType.CHAT_TO_REACTION,
                confidence=0.86,
                temporal_gap=gap,
                same_scene=same_scene,
                speaker_continuity=speaker_cont,
                evidence_notes="Chat prompt acknowledged by streamer",
            )

        # Reaction continuation
        if is_reaction_b and type_a in ("face_reaction", "laughter", "shout", "pause_with_reaction", "reaction") and gap <= clustering_config.reaction_link_window:
            return CandidateRelationEvidence(
                source_event_id=id_a,
                target_event_id=id_b,
                relation_type=CandidateRelationType.REACTION_CONTINUATION,
                confidence=0.90,
                temporal_gap=gap,
                same_scene=same_scene,
                speaker_continuity=speaker_cont,
                evidence_notes="Continuation of reaction across short pause",
            )

        # Speech continuity (same beat)
        if type_a == "speech" and type_b == "speech":
            if speaker_cont and gap <= clustering_config.speech_continuity_gap:
                return CandidateRelationEvidence(
                    source_event_id=id_a,
                    target_event_id=id_b,
                    relation_type=CandidateRelationType.SAME_BEAT,
                    confidence=0.82,
                    temporal_gap=gap,
                    same_scene=same_scene,
                    speaker_continuity=speaker_cont,
                    evidence_notes="Conversational continuity within pause threshold",
                )
            else:
                return CandidateRelationEvidence(
                    source_event_id=id_a,
                    target_event_id=id_b,
                    relation_type=CandidateRelationType.UNRELATED,
                    confidence=0.20,
                    temporal_gap=gap,
                    same_scene=same_scene,
                    speaker_continuity=speaker_cont,
                    evidence_notes="Speech gap exceeds continuity threshold without link",
                )

        # Default fallback
        return CandidateRelationEvidence(
            source_event_id=id_a,
            target_event_id=id_b,
            relation_type=CandidateRelationType.UNKNOWN,
            confidence=0.40,
            temporal_gap=gap,
            same_scene=same_scene,
            speaker_continuity=speaker_cont,
            evidence_notes="Unspecified relation",
        )


class EventClusterer:
    """Groups TimelineEvents into temporal clusters by relational evidence or proximity."""

    def cluster(
        self,
        events: list[dict[str, object]],
        merge_gap: float,
        clustering_config: CandidateClusteringExperimentConfig | None = None,
        scenes: list[dict[str, object]] | None = None,
    ) -> list[list[dict[str, object]]]:
        """
        Cluster events respecting CandidateClusteringExperimentConfig if provided,
        or legacy merge_gap if None.

        Args:
            events: List of dicts with 'start_time', 'end_time', 'event_type', 'id'.
            merge_gap: Max gap (seconds) between events to merge into same cluster (legacy).
            clustering_config: EXP-002 bounded relational clustering configuration.
            scenes: Optional list of scenes for boundary detection.

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
            last_event = last_cluster[-1]
            event_start = float(str(event.get("start_time", 0)))

            if clustering_config is not None:
                # EXP-002: Bounded relational clustering
                evidence = CandidateRelationClassifier.classify_relation(
                    last_event, event, clustering_config, scenes=scenes
                )
                should_merge = (
                    evidence.relation_type != CandidateRelationType.UNRELATED
                    and evidence.confidence >= clustering_config.minimum_relation_confidence
                )
                if should_merge:
                    links = event.get("relational_links")
                    if not isinstance(links, list):
                        links = []
                        event["relational_links"] = links
                    links.append(evidence.model_dump())
                    last_cluster.append(event)
                else:
                    clusters.append([event])
            else:
                # Pre-EXP-002: Purely temporal merge_gap clustering
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
            merged_ids = [str(e.get("id", "")) for e in cluster if e.get("id")]

            # Extract relation types from cluster events
            rel_types: list[str] = []
            rel_confs: list[float] = []
            for e in cluster:
                raw_links = e.get("relational_links")
                if isinstance(raw_links, list):
                    for link in raw_links:
                        if isinstance(link, dict) and "relation_type" in link:
                            rel_types.append(str(link["relation_type"]))
                            rel_confs.append(float(link.get("confidence", 1.0)))

            conf_version = config.clustering_config.version if config.clustering_config else "default"
            mean_conf = (sum(rel_confs) / len(rel_confs)) if rel_confs else 1.0

            windows.append(
                CandidateWindow(
                    core_start=core_start,
                    core_end=core_end,
                    source_signals=signals,
                    evidence_ids=evidence_ids,
                    merged_event_ids=merged_ids,
                    relation_types=list(set(rel_types)),
                    relation_confidence=round(mean_conf, 3),
                    boundary_reason="relational_cluster" if rel_types else "cluster_core",
                    config_version=conf_version,
                )
            )

        return windows
