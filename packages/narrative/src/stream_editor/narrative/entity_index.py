"""
NarrativeElementIndex — lightweight searchable index of narrative entities/concepts.

Accumulates detected entities across chapters. Later candidates can query:
"Does this reference something previously established?"

Not a full knowledge graph — simple normalized label matching.
No model calls — purely deterministic aggregation.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class NarrativeElementEntry:
    label: str
    element_type: str   # person | place | item | joke | promise | event | topic | phrase
    first_seen_time: float
    last_seen_time: float
    description: str = ""
    node_ids: list[str] = field(default_factory=list)
    confidence: float = 0.8

    def as_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "element_type": self.element_type,
            "first_seen_time": self.first_seen_time,
            "last_seen_time": self.last_seen_time,
            "description": self.description,
            "node_ids": self.node_ids,
            "confidence": self.confidence,
        }


class NarrativeElementIndex:
    """
    Tracks narrative elements (entities/concepts) as they are discovered.

    On each chapter pass, absorbs new entity labels from the model's
    LocalGraphProposal.entities_detected. Deduplicates by normalized label.
    """

    def __init__(self) -> None:
        self._entries: dict[str, NarrativeElementEntry] = {}

    def ingest_from_proposal(
        self,
        entity_labels: list[str],
        chapter_start: float,
        chapter_end: float,
        node_ids: list[str] | None = None,
    ) -> None:
        """
        Add entity labels from a chapter proposal to the index.

        Args:
            entity_labels: Normalized labels returned by the model.
            chapter_start: Chapter start time (seconds).
            chapter_end: Chapter end time (seconds).
            node_ids: Node IDs in this chapter (associated with these entities).
        """
        normalized_node_ids = node_ids or []
        for label in entity_labels:
            key = label.strip().lower()
            if not key:
                continue
            if key in self._entries:
                entry = self._entries[key]
                entry.last_seen_time = max(entry.last_seen_time, chapter_end)
                for nid in normalized_node_ids:
                    if nid not in entry.node_ids:
                        entry.node_ids.append(nid)
            else:
                self._entries[key] = NarrativeElementEntry(
                    label=label.strip(),
                    element_type="topic",   # default; model may refine later
                    first_seen_time=chapter_start,
                    last_seen_time=chapter_end,
                    node_ids=list(normalized_node_ids),
                )
        logger.debug(
            "ElementIndex: ingested %d labels, total %d entries",
            len(entity_labels), len(self._entries),
        )

    def as_list(self) -> list[dict[str, object]]:
        """Return index contents as a list of dicts (for model prompt injection)."""
        return [e.as_dict() for e in self._entries.values()]

    def __len__(self) -> int:
        return len(self._entries)
