"""
NarrativeThreadBuilder — groups story nodes into named narrative threads.

A thread is a named narrative arc such as:
  "trying to beat boss X"
  "running joke about blue car"
  "argument with chat about pizza"

Thread identification is done by clustering edge-connected components that share
same_thread, continues, or callback_to/payoff_of relationships.

This is deterministic — no model calls.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from stream_editor.contracts.editorial import EdgeRelationType

logger = logging.getLogger(__name__)

# Relations that indicate same narrative thread
THREAD_RELATIONS: frozenset[EdgeRelationType] = frozenset({
    EdgeRelationType.same_thread,
    EdgeRelationType.continues,
    EdgeRelationType.callback_to,
    EdgeRelationType.payoff_of,
    EdgeRelationType.setup_for,
})


@dataclass
class ThreadCandidate:
    """Intermediate thread before DB persistence."""
    node_ids: list[str]
    relation_types: list[str]   # edge types that connected these nodes
    title: str = ""             # to be filled by model or rule
    thread_type: str = "arc"
    first_occurrence_time: float = 0.0
    last_occurrence_time: float = 0.0
    is_resolved: bool = True
    confidence: float = 0.8


class NarrativeThreadBuilder:
    """
    Builds NarrativeThread candidates by clustering related StoryNodes
    based on their edge relationships.

    Uses Union-Find (disjoint set) to identify connected components
    via thread-forming relations. Each component becomes a thread.
    """

    def build_threads(
        self,
        nodes: list[dict[str, object]],
        edges: list[dict[str, object]],
    ) -> list[ThreadCandidate]:
        """
        Identify narrative threads from nodes and validated edges.

        Args:
            nodes: List of node dicts with 'id', 'start_time', 'end_time', 'node_type', 'title'.
            edges: List of validated edge dicts with 'source_node_id', 'target_node_id', 'relation_type'.

        Returns:
            List of ThreadCandidate objects. Single-node components are omitted
            (threads require at least 2 nodes).
        """
        if not nodes:
            return []

        # Build node registry for fast lookup
        node_map: dict[str, dict[str, object]] = {str(n.get("id", "")): n for n in nodes}
        all_ids = list(node_map.keys())

        # Union-Find
        parent: dict[str, str] = {nid: nid for nid in all_ids}
        rank: dict[str, int] = {nid: 0 for nid in all_ids}
        relation_store: dict[str, list[str]] = {nid: [] for nid in all_ids}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]  # path compression
                x = parent[x]
            return x

        def union(x: str, y: str, relation: str) -> None:
            rx, ry = find(x), find(y)
            if rx == ry:
                return
            if rank[rx] < rank[ry]:
                rx, ry = ry, rx
            parent[ry] = rx
            if rank[rx] == rank[ry]:
                rank[rx] += 1
            relation_store[rx].extend(relation_store[ry])
            relation_store[rx].append(relation)

        # Union nodes connected by thread-forming relations
        for edge in edges:
            rel_str = str(edge.get("relation_type", ""))
            try:
                rel = EdgeRelationType(rel_str)
            except ValueError:
                continue
            if rel not in THREAD_RELATIONS:
                continue
            source_id = str(edge.get("source_node_id", ""))
            target_id = str(edge.get("target_node_id", ""))
            if source_id in node_map and target_id in node_map:
                union(source_id, target_id, rel_str)

        # Collect components
        components: dict[str, list[str]] = {}
        for nid in all_ids:
            root = find(nid)
            components.setdefault(root, []).append(nid)

        # Build ThreadCandidates from multi-node components
        threads: list[ThreadCandidate] = []
        for root, member_ids in components.items():
            if len(member_ids) < 2:
                continue

            member_nodes = [node_map[nid] for nid in member_ids]
            times = [float(str(n.get("start_time", 0))) for n in member_nodes]
            end_times = [float(str(n.get("end_time", 0))) for n in member_nodes]
            first_time = min(times)
            last_time = max(end_times)

            # Determine thread type from relations used
            rels = relation_store.get(root, [])
            thread_type = self._infer_thread_type(rels)

            # Detect unresolved threads (setup without payoff)
            has_setup = any(
                str(n.get("node_type", "")) in {"setup", "question", "unresolved_thread"}
                for n in member_nodes
            )
            has_payoff = any(
                str(n.get("node_type", "")) in {"payoff", "answer"}
                for n in member_nodes
            )
            is_resolved = not has_setup or has_payoff

            # Generate a basic title from node titles
            titles = [str(n.get("title", "")) for n in member_nodes if n.get("title")]
            title = titles[0] if titles else f"Narrative thread ({len(member_ids)} nodes)"

            threads.append(ThreadCandidate(
                node_ids=sorted(member_ids),
                relation_types=sorted(set(rels)),
                title=title,
                thread_type=thread_type,
                first_occurrence_time=first_time,
                last_occurrence_time=last_time,
                is_resolved=is_resolved,
                confidence=0.85,
            ))

        logger.info(
            "ThreadBuilder: %d threads from %d nodes / %d edges",
            len(threads), len(nodes), len(edges),
        )
        return threads

    def _infer_thread_type(self, relation_types: list[str]) -> str:
        rels = set(relation_types)
        if EdgeRelationType.callback_to.value in rels:
            return "callback_chain"
        if EdgeRelationType.payoff_of.value in rels or EdgeRelationType.setup_for.value in rels:
            return "arc"
        if EdgeRelationType.same_thread.value in rels:
            return "running_joke"
        return "arc"
