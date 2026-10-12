"""Narrative Dependency Resolver for StreamEditor AI.

Enforces narrative continuity and context dependencies during editorial planning (M4/M5).
Guarantees that action beats, reactions, and payoffs do not appear without prerequisite setup,
and bridges related moments into cohesive narrative episodes.
"""

from __future__ import annotations

import logging
from typing import Sequence
from uuid import UUID, uuid4

from stream_editor.contracts.edit_plan import (
    ClipPriority,
    EditClipContract,
    EditPlanConfig,
)
from stream_editor.contracts.editorial import (
    CandidateSegmentContract,
    DependencyStrength,
    EdgeRelationType,
    EnforcementAction,
    NarrativeDependency,
    StoryGraphContract,
)

logger = logging.getLogger(__name__)


class NarrativeDependencyResolver:
    """
    Enforces causal and narrative dependencies between story beats.
    
    Prevents the common highlight-reel failure mode:
    "Showing an intense payoff or reaction where the viewer is confused because
    the prerequisite explanation, game objective, or setup was cut."
    """

    CRITICAL_DEPENDENCY_TYPES: frozenset[EdgeRelationType] = frozenset({
        EdgeRelationType.depends_on,
        EdgeRelationType.requires_context,
        EdgeRelationType.payoff_of,
        EdgeRelationType.explains_reaction,
        EdgeRelationType.introduces_objective,
    })

    @classmethod
    def resolve_dependencies(
        cls,
        selected_clips: Sequence[EditClipContract],
        all_candidates: Sequence[CandidateSegmentContract],
        story_graph: StoryGraphContract | None = None,
        config: EditPlanConfig | None = None,
    ) -> list[EditClipContract]:
        """
        Takes candidate clip selections and resolves all prerequisite dependencies.
        
        1. Identifies any selected clip that depends on earlier narrative context.
        2. If the prerequisite is missing:
           - Automatically pulls the prerequisite candidate into the edit plan.
           - If the prerequisite cannot be found and dependency is critical,
             drops the dependent clip to protect narrative coherence.
        3. Protects prerequisite clips from premature pruning.
        """
        if not selected_clips:
            return []

        resolved_clips = list(selected_clips)
        cand_by_id: dict[str, CandidateSegmentContract] = {
            str(c.id): c for c in all_candidates
        }
        clip_by_cand_id: dict[str, EditClipContract] = {
            c.candidate_id: c for c in resolved_clips if c.candidate_id
        }

        # Build candidate-to-candidate graph dependency lookup
        # Maps dependent_candidate_id -> list of (prerequisite_candidate_id, relation_type, strength)
        dependencies: dict[str, list[tuple[str, EdgeRelationType, DependencyStrength]]] = {}

        if story_graph and story_graph.edges:
            # Map node_id -> candidate_id
            node_to_cand: dict[str, str] = {
                n.id: n.candidate_id for n in story_graph.nodes if n.candidate_id
            }
            for edge in story_graph.edges:
                src_cand = node_to_cand.get(edge.source_node_id)
                tgt_cand = node_to_cand.get(edge.target_node_id)
                if not src_cand or not tgt_cand or src_cand == tgt_cand:
                    continue

                rel = edge.relation_type
                # For payoff_of, depends_on, requires_context:
                # source_node is the dependent, target_node is the prerequisite setup.
                if rel in cls.CRITICAL_DEPENDENCY_TYPES:
                    dependencies.setdefault(src_cand, []).append(
                        (tgt_cand, rel, edge.dependency_strength)
                    )
                elif rel == EdgeRelationType.setup_for:
                    # setup_for: target is dependent, source is prerequisite
                    dependencies.setdefault(tgt_cand, []).append(
                        (src_cand, EdgeRelationType.requires_context, edge.dependency_strength)
                    )

        # Iterate and resolve
        max_passes = 3
        current_pass = 0
        clips_to_drop: set[str] = set()

        while current_pass < max_passes:
            current_pass += 1
            newly_added_clips: list[EditClipContract] = []

            for clip in resolved_clips:
                cand_id = clip.candidate_id
                if not cand_id or cand_id in clips_to_drop:
                    continue

                clip_deps = dependencies.get(cand_id, [])
                for prereq_cand_id, rel, strength in clip_deps:
                    if prereq_cand_id in clip_by_cand_id:
                        # Prerequisite already present in plan
                        continue

                    # Prerequisite is missing!
                    prereq_cand = cand_by_id.get(prereq_cand_id)
                    if prereq_cand:
                        # Pull prerequisite into plan as context
                        logger.info(
                            f"NarrativeDependency: Pulling prerequisite {prereq_cand_id} "
                            f"for dependent {cand_id} (relation={rel.value}, strength={strength.value})"
                        )
                        new_clip = EditClipContract(
                            id=uuid4(),
                            plan_id=clip.plan_id,
                            source_start=prereq_cand.start_time or 0.0,
                            source_end=prereq_cand.end_time or prereq_cand.duration,
                            output_start=0.0,
                            output_end=prereq_cand.duration,
                            candidate_id=prereq_cand_id,
                            selection_reason=(
                                f"Context requirement: prerequisite {rel.value} "
                                f"for clip {cand_id}"
                            ),
                            priority=(
                                ClipPriority.essential
                                if clip.priority == ClipPriority.essential
                                else ClipPriority.context_only
                            ),
                            confidence=0.85,
                            locked=clip.locked,
                        )
                        newly_added_clips.append(new_clip)
                        clip_by_cand_id[prereq_cand_id] = new_clip
                    else:
                        # Prerequisite missing from candidate catalog
                        if strength == DependencyStrength.critical:
                            logger.warning(
                                f"NarrativeDependency: Critical prerequisite {prereq_cand_id} missing "
                                f"for {cand_id}. Dropping dependent to preserve continuity."
                            )
                            clips_to_drop.add(cand_id)

            if newly_added_clips:
                resolved_clips.extend(newly_added_clips)
            else:
                break

        # Remove any clips marked for dropping
        final_clips = [
            c for c in resolved_clips if (c.candidate_id not in clips_to_drop)
        ]

        # Sort chronologically by source start
        final_clips.sort(key=lambda c: c.source_start)
        return final_clips

    @classmethod
    def link_episode_continuity(
        cls,
        clips: Sequence[EditClipContract],
        max_bridging_gap_seconds: float = 8.0,
    ) -> list[EditClipContract]:
        """
        Identifies tight sub-episode clips separated by tiny gaps (e.g. < 8s)
        and bridges them to eliminate micro-jumpcuts within the same scene.
        """
        if not clips or len(clips) < 2:
            return list(clips)

        sorted_clips = sorted(clips, key=lambda c: c.source_start)
        bridged: list[EditClipContract] = []
        current = sorted_clips[0].model_copy()

        for next_clip in sorted_clips[1:]:
            gap = next_clip.source_start - current.source_end
            if 0.0 <= gap <= max_bridging_gap_seconds:
                # Bridge gap: extend current clip to include the continuous moment
                logger.info(
                    f"EpisodeContinuity: Bridging gap of {gap:.2f}s between "
                    f"[{current.source_start:.1f}, {current.source_end:.1f}] and "
                    f"[{next_clip.source_start:.1f}, {next_clip.source_end:.1f}]"
                )
                current.source_end = next_clip.source_end
                current.output_end = current.output_start + (current.source_end - current.source_start)
                current.selection_reason += f" + bridged with {next_clip.selection_reason}"
                if next_clip.is_narrative_anchor:
                    current.is_narrative_anchor = True
                if next_clip.priority == ClipPriority.essential:
                    current.priority = ClipPriority.essential
            else:
                bridged.append(current)
                current = next_clip.model_copy()

        bridged.append(current)
        return bridged
