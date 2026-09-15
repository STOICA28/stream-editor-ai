"""
MockNarrativeProvider — deterministic test provider for Story Graph.

Implements NarrativeAnalysisProvider with hardcoded fixtures covering:
  1. Simple setup/payoff
  2. Callback
  3. Independent clips (no relationship)
  4. False similarity (same word, no relationship)
  5. Unresolved setup (no payoff)

All fixtures are keyed by candidate ID patterns.
"""
from __future__ import annotations

import logging

from stream_editor.contracts.editorial import (
    DependencyStrength,
    EdgeRelationType,
    LocalGraphProposal,
    NarrativeAnalysisProvider,
    ProposedRelationship,
    StoryGraphConfig,
)

logger = logging.getLogger(__name__)

# Fixture: candidate IDs that contain "setup_" → paired with "payoff_" equivalent
_SETUP_MARKER = "setup_"
_PAYOFF_MARKER = "payoff_"
_CALLBACK_SETUP_MARKER = "joke_"
_CALLBACK_REF_MARKER = "callback_"
_FALSE_SIM_MARKER = "false_sim_"
_UNRESOLVED_MARKER = "unresolved_"


class MockNarrativeProvider:
    """
    Deterministic mock narrative provider for tests.

    Relationship rules:
    - If a candidate ID contains 'setup_X' and another contains 'payoff_X',
      propose a setup_for/payoff_of relationship.
    - If a candidate ID contains 'joke_X' and another contains 'callback_X',
      propose a callback_to relationship.
    - If a candidate ID contains 'false_sim_' → NEVER propose a relationship
      even if it's retrieved as a plausible pair.
    - If a candidate ID contains 'unresolved_' → setup but no payoff found.
    - All other candidates: no relationship.
    """

    def build_local_graph(
        self,
        chapter_candidates: list[dict[str, object]],
        chapter_summary: str,
        element_index: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> LocalGraphProposal:
        logger.debug("MockNarrativeProvider.build_local_graph: %d candidates", len(chapter_candidates))
        relationships = self._find_setup_payoff(chapter_candidates)
        relationships += self._find_callbacks(chapter_candidates)
        return LocalGraphProposal(
            relationships=relationships,
            entities_detected=["mock_entity_1"],
            chapter_summary=chapter_summary or "Mock chapter summary.",
            prompt_version=config.prompt_version,
        )

    def link_story_elements(
        self,
        candidate_pairs: list[tuple[dict[str, object], dict[str, object]]],
        element_index: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> LocalGraphProposal:
        logger.debug("MockNarrativeProvider.link_story_elements: %d pairs", len(candidate_pairs))
        relationships: list[ProposedRelationship] = []
        for source, target in candidate_pairs:
            source_id = str(source.get("id", ""))
            target_id = str(target.get("id", ""))
            # False similarity: reject even if retrieved
            if _FALSE_SIM_MARKER in source_id or _FALSE_SIM_MARKER in target_id:
                continue
            # Cross-chapter setup/payoff
            rel = self._match_setup_payoff_pair(source_id, target_id)
            if rel:
                relationships.append(rel)
        return LocalGraphProposal(
            relationships=relationships,
            entities_detected=[],
            chapter_summary="",
            prompt_version=config.prompt_version,
        )

    def review_graph(
        self,
        nodes: list[dict[str, object]],
        edges: list[dict[str, object]],
        threads: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> list[ProposedRelationship]:
        logger.debug("MockNarrativeProvider.review_graph: %d nodes, %d edges", len(nodes), len(edges))
        # Mock critic finds no additional corrections
        return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_setup_payoff(
        self,
        candidates: list[dict[str, object]],
    ) -> list[ProposedRelationship]:
        """Match setup_X → payoff_X pairs within candidates."""
        relationships: list[ProposedRelationship] = []
        setups: dict[str, str] = {}  # suffix -> candidate_id
        payoffs: dict[str, str] = {}

        for c in candidates:
            cid = str(c.get("id", ""))
            if _SETUP_MARKER in cid:
                suffix = cid.split(_SETUP_MARKER, 1)[1].split("_")[0]
                setups[suffix] = cid
            elif _PAYOFF_MARKER in cid:
                suffix = cid.split(_PAYOFF_MARKER, 1)[1].split("_")[0]
                payoffs[suffix] = cid

        for suffix, setup_id in setups.items():
            if suffix in payoffs:
                payoff_id = payoffs[suffix]
                relationships.append(ProposedRelationship(
                    source_candidate=payoff_id,
                    target_candidate=setup_id,
                    relation=EdgeRelationType.payoff_of,
                    confidence=0.95,
                    dependency_strength=DependencyStrength.critical,
                    dependency_strength_score=0.9,
                    evidence_summary=f"Payoff {payoff_id} resolves setup {setup_id}.",
                ))
        return relationships

    def _find_callbacks(
        self,
        candidates: list[dict[str, object]],
    ) -> list[ProposedRelationship]:
        """Match joke_X → callback_X pairs within candidates."""
        relationships: list[ProposedRelationship] = []
        jokes: dict[str, str] = {}
        callbacks: dict[str, str] = {}

        for c in candidates:
            cid = str(c.get("id", ""))
            if _CALLBACK_SETUP_MARKER in cid:
                suffix = cid.split(_CALLBACK_SETUP_MARKER, 1)[1].split("_")[0]
                jokes[suffix] = cid
            elif _CALLBACK_REF_MARKER in cid:
                suffix = cid.split(_CALLBACK_REF_MARKER, 1)[1].split("_")[0]
                callbacks[suffix] = cid

        for suffix, joke_id in jokes.items():
            if suffix in callbacks:
                cb_id = callbacks[suffix]
                relationships.append(ProposedRelationship(
                    source_candidate=cb_id,
                    target_candidate=joke_id,
                    relation=EdgeRelationType.callback_to,
                    confidence=0.88,
                    dependency_strength=DependencyStrength.helpful,
                    dependency_strength_score=0.65,
                    evidence_summary=f"Callback {cb_id} references earlier joke {joke_id}.",
                ))
        return relationships

    def _match_setup_payoff_pair(
        self,
        source_id: str,
        target_id: str,
    ) -> ProposedRelationship | None:
        """For cross-chapter pairs: match payoff (source/later) -> setup (target/earlier)."""
        if _SETUP_MARKER in target_id and _PAYOFF_MARKER in source_id:
            target_suffix = target_id.split(_SETUP_MARKER, 1)[1].split("_")[0]
            source_suffix = source_id.split(_PAYOFF_MARKER, 1)[1].split("_")[0]
            if target_suffix == source_suffix:
                return ProposedRelationship(
                    source_candidate=source_id,
                    target_candidate=target_id,
                    relation=EdgeRelationType.payoff_of,
                    confidence=0.92,
                    dependency_strength=DependencyStrength.critical,
                    dependency_strength_score=0.88,
                    evidence_summary=f"Cross-chapter payoff {source_id} resolves setup {target_id}.",
                )
        return None


# Implement the Protocol formally
NarrativeAnalysisProvider.register(MockNarrativeProvider)  # type: ignore[attr-defined]
