"""
GraphValidator — deterministic validation of Story Graph nodes and edges.

All validation runs on application data, BEFORE persisting any edge.
Never trust raw model output without validation.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from stream_editor.contracts.editorial import (
    ACYCLIC_RELATIONS,
    TEMPORALLY_DIRECTED_RELATIONS,
    EdgeRelationType,
    ProposedRelationship,
    StoryNodeType,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class GraphValidator:
    """
    Deterministic validation of Story Graph structure.

    Checks performed:
    - Referenced nodes exist in the run's node set
    - No self-links (source == target)
    - Temporal consistency for directed relations
    - Relation type is a valid EdgeRelationType enum value
    - Confidence is in [0.0, 1.0]
    - dependency_strength_score is in [0.0, 1.0]
    - Duplicate edge detection
    - Cycle detection for acyclic relations
    """

    def validate_edge(
        self,
        relationship: ProposedRelationship,
        node_registry: dict[str, dict[str, object]],
        existing_edges: list[tuple[str, str, str]],  # (source_id, target_id, relation)
    ) -> ValidationResult:
        """
        Validate a single proposed relationship.

        Args:
            relationship: The proposed edge from the model.
            node_registry: Dict of node_id -> node dict with 'start_time', 'end_time'.
            existing_edges: List of already-validated (source_id, target_id, relation_type) tuples.

        Returns:
            ValidationResult with pass/fail and error list.
        """
        errors: list[str] = []
        warnings: list[str] = []

        source_id = relationship.source_candidate
        target_id = relationship.target_candidate

        # 1. No self-links
        if source_id == target_id:
            errors.append(f"Self-link rejected: {source_id}")
            return ValidationResult(passed=False, errors=errors)

        # 2. Referenced nodes must exist
        if source_id not in node_registry:
            errors.append(f"Source node not found in run: {source_id}")
        if target_id not in node_registry:
            errors.append(f"Target node not found in run: {target_id}")
        if errors:
            return ValidationResult(passed=False, errors=errors)

        # 3. Relation type validity
        try:
            relation = EdgeRelationType(relationship.relation)
        except ValueError:
            errors.append(f"Invalid relation type: {relationship.relation}")
            return ValidationResult(passed=False, errors=errors)

        # 4. Confidence range
        if not (0.0 <= relationship.confidence <= 1.0):
            errors.append(f"Confidence out of range: {relationship.confidence}")
        if not (0.0 <= relationship.dependency_strength_score <= 1.0):
            errors.append(f"dependency_strength_score out of range: {relationship.dependency_strength_score}")
        if errors:
            return ValidationResult(passed=False, errors=errors)

        # 5. Temporal direction validation
        if relation in TEMPORALLY_DIRECTED_RELATIONS:
            source_node = node_registry[source_id]
            target_node = node_registry[target_id]
            source_start = float(str(source_node.get("start_time", 0)))
            target_start = float(str(target_node.get("start_time", 0)))
            # For these relations, source must appear AFTER target
            if source_start <= target_start:
                errors.append(
                    f"Temporal violation for {relation.value}: "
                    f"source ({source_id} at {source_start:.1f}s) must appear AFTER "
                    f"target ({target_id} at {target_start:.1f}s)"
                )
            if errors:
                return ValidationResult(passed=False, errors=errors)

        # 6. Duplicate edge detection
        edge_key = (source_id, target_id, relation.value)
        if edge_key in {(s, t, r) for s, t, r in existing_edges}:
            warnings.append(f"Duplicate edge skipped: {source_id} -{relation.value}-> {target_id}")
            return ValidationResult(passed=False, errors=[warnings[0]], warnings=warnings)

        # 7. Cycle detection for acyclic relations
        if relation in ACYCLIC_RELATIONS:
            # Simple cycle check: does target_id ->...-> source_id already exist via this relation?
            if self._would_create_cycle(source_id, target_id, existing_edges, relation):
                warnings.append(
                    f"Cycle detected for acyclic relation {relation.value}: "
                    f"{source_id} -> {target_id}"
                )
                return ValidationResult(passed=False, errors=[warnings[0]], warnings=warnings)

        return ValidationResult(passed=True, warnings=warnings)

    def _would_create_cycle(
        self,
        source_id: str,
        target_id: str,
        existing_edges: list[tuple[str, str, str]],
        relation: EdgeRelationType,
    ) -> bool:
        """
        Check if adding source_id -> target_id for the given relation would create a cycle.
        Uses DFS over the existing edges of the same relation type.
        """
        # Build adjacency list for this relation type
        adjacency: dict[str, list[str]] = {}
        for s, t, r in existing_edges:
            if r == relation.value:
                adjacency.setdefault(s, []).append(t)

        # Can we reach source_id from target_id?
        visited: set[str] = set()
        stack = [target_id]
        while stack:
            node = stack.pop()
            if node == source_id:
                return True
            if node in visited:
                continue
            visited.add(node)
            stack.extend(adjacency.get(node, []))
        return False

    def validate_node_type(self, node_type_value: str) -> ValidationResult:
        """Validate that a node type string is a valid StoryNodeType."""
        try:
            StoryNodeType(node_type_value)
            return ValidationResult(passed=True)
        except ValueError:
            return ValidationResult(
                passed=False,
                errors=[f"Invalid node type: {node_type_value}"],
            )
