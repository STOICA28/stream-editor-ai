"""
StoryGraphGenerator — orchestrates M4 Story Graph construction.

Pipeline:
  1. Load M3 candidates from DB
  2. Group into chapters (ChapterGrouper)
  3. Per chapter: build local graph (Flash via provider)
  4. Ingest entities into NarrativeElementIndex
  5. Retrieve plausible cross-chapter pairs (TF-IDF retrieval)
  6. Link cross-chapter pairs (Pro via provider)
  7. Validate all proposed edges (GraphValidator)
  8. Persist StoryGraphRun, StoryNodes, StoryEdges to DB
  9. Build NarrativeThreads (ThreadBuilder)
  10. Optional critic pass (Pro via provider)
  11. Update StoryGraphRun metrics and mark complete

Each step is idempotent — if derivation_signature already exists, reuse run.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from stream_editor.contracts.editorial import (
    ContextRequirement,
    DependencyStrength,
    EdgeRelationType,
    LocalGraphProposal,
    NarrativeAnalysisProvider,
    ProposedRelationship,
    StoryGraphConfig,
    StoryNodeType,
)
from stream_editor.narrative.chapters import ChapterGrouper
from stream_editor.narrative.entity_index import NarrativeElementIndex
from stream_editor.narrative.retrieval import CandidatePair, LinkCandidateRetriever
from stream_editor.narrative.thread_builder import NarrativeThreadBuilder
from stream_editor.narrative.validator import GraphValidator

logger = logging.getLogger(__name__)


class StoryGraphGenerator:
    """
    Orchestrates the M4 Story Graph construction pipeline.

    Requires a synchronous SQLAlchemy Session (same pattern as CandidateGenerator).
    """

    def __init__(
        self,
        session: Session,
        provider: NarrativeAnalysisProvider,
        config: StoryGraphConfig | None = None,
    ) -> None:
        self._session = session
        self._provider = provider
        self._config = config or StoryGraphConfig()
        self._grouper = ChapterGrouper(
            chapter_duration_seconds=self._config.chapter_duration_seconds
        )
        self._retriever = LinkCandidateRetriever(
            max_k=self._config.max_retrieval_candidates,
            min_similarity=self._config.min_tfidf_similarity,
        )
        self._validator = GraphValidator()
        self._thread_builder = NarrativeThreadBuilder()
        self._element_index = NarrativeElementIndex()

    def generate(
        self,
        project_id: str,
        source_asset_id: str,
        candidate_run_id: str,
        provider_name: str = "mock",
    ) -> str:
        """
        Run the full Story Graph generation pipeline.

        Returns:
            StoryGraphRun ID.

        Raises:
            RuntimeError if candidate run is not found or not completed.
        """
        from stream_editor.api.models.project import (
            CandidateRun,
            CandidateSegment,
            NarrativeElement,
            NarrativeThread,
            NodeThreadMembership,
            StoryEdge,
            StoryGraphRun,
            StoryNode,
        )

        # --- Validate candidate run ---
        candidate_run = self._session.get(CandidateRun, candidate_run_id)
        if not candidate_run:
            raise RuntimeError(f"CandidateRun {candidate_run_id} not found")

        # --- Idempotency check ---
        run_signature = self._config.get_signature(
            str(candidate_run.derivation_signature) if candidate_run.derivation_signature else candidate_run_id
        )
        existing = (
            self._session.query(StoryGraphRun)
            .filter_by(derivation_signature=run_signature)
            .first()
        )
        if existing and existing.status == "completed":
            logger.info(
                "StoryGraphRun %s already completed (signature match), reusing", existing.id
            )
            return str(existing.id)

        # --- Create StoryGraphRun ---
        run_id = str(uuid.uuid4())
        run = StoryGraphRun(
            id=run_id,
            project_id=project_id,
            source_asset_id=source_asset_id,
            candidate_run_id=candidate_run_id,
            provider=provider_name,
            flash_model=self._config.flash_model,
            pro_model=self._config.pro_model,
            prompt_version=self._config.prompt_version,
            generator_version=self._config.generator_version,
            configuration=self._config.model_dump(),
            derivation_signature=run_signature,
            status="running",
        )
        self._session.add(run)
        self._session.commit()

        try:
            self._run_pipeline(
                run=run,
                project_id=project_id,
                candidate_run_id=candidate_run_id,
                session=self._session,
            )
        except Exception as exc:
            logger.exception("StoryGraphGenerator pipeline error for run %s", run_id)
            run.status = "failed" # type: ignore
            run.error_message = str(exc)[:500] # type: ignore
            self._session.commit()
            raise

        return run_id

    def _run_pipeline(
        self,
        run: Any,
        project_id: str,
        candidate_run_id: str,
        session: Session,
    ) -> None:
        from stream_editor.api.models.project import (
            CandidateSegment,
            NarrativeElement,
            NarrativeThread,
            NodeThreadMembership,
            StoryEdge,
            StoryNode,
        )

        # 1. Load candidates
        candidates_db = (
            session.query(CandidateSegment)
            .filter_by(run_id=candidate_run_id)
            .all()
        )
        if not candidates_db:
            logger.warning("No candidates found for run %s", candidate_run_id)
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            session.commit()
            return

        candidates: list[dict[str, object]] = [
            {
                "id": c.id,
                "start_time": c.start_time,
                "end_time": c.end_time,
                "core_start": c.core_start,
                "core_end": c.core_end,
                "transcript_excerpt": c.transcript_excerpt,
                "summary": c.summary,
                "source_signals": c.source_signals or [],
                "score_humor": c.score_humor,
                "score_importance": c.score_importance,
                "score_story_value": c.score_story_value,
            }
            for c in candidates_db
        ]
        logger.info("Processing %d candidates for StoryGraphRun %s", len(candidates), run.id)

        # 2. Group into chapters
        chapters = self._grouper.group(candidates)
        logger.info("Grouped into %d chapters", len(chapters))

        # 3. Create StoryNodes for each candidate
        node_id_map: dict[str, str] = {}  # candidate_id -> story_node_id
        all_nodes: list[StoryNode] = []

        for chapter in chapters:
            for c in chapter.candidates:
                cid = str(c["id"])
                node_id = str(uuid.uuid4())
                node_id_map[cid] = node_id
                node = StoryNode(
                    id=node_id,
                    story_graph_run_id=run.id,
                    project_id=project_id,
                    node_type=StoryNodeType.candidate.value,
                    start_time=float(str(c.get("start_time", 0))),
                    end_time=float(str(c.get("end_time", 0))),
                    candidate_id=cid,
                    title=str(c.get("summary", "") or "")[:100] or None,
                    summary=str(c.get("transcript_excerpt", "") or "")[:500] or None,
                    confidence=0.9,
                    provider=run.provider,
                    model=run.flash_model,
                    prompt_version=run.prompt_version,
                    chapter_index=chapter.index,
                )
                session.add(node)
                all_nodes.append(node)

        session.flush()  # assign IDs without committing

        # 4. Per-chapter local graph building
        # Rewrite candidate dicts to use node IDs for model interaction
        all_proposals: list[LocalGraphProposal] = []

        for chapter in chapters:
            if not chapter.candidates:
                continue

            # Remap candidate IDs to node IDs for model prompts
            chapter_node_candidates = [
                {**c, "id": node_id_map[str(c["id"])]}
                for c in chapter.candidates
                if str(c["id"]) in node_id_map
            ]

            proposal = self._provider.build_local_graph(
                chapter_candidates=chapter_node_candidates,
                chapter_summary=f"Chapter {chapter.index}, {chapter.start_time:.0f}s–{chapter.end_time:.0f}s",
                element_index=self._element_index.as_list(),
                config=self._config,
            )
            all_proposals.append(proposal)

            # Update entity index
            self._element_index.ingest_from_proposal(
                entity_labels=proposal.entities_detected,
                chapter_start=chapter.start_time,
                chapter_end=chapter.end_time,
                node_ids=[str(c["id"]) for c in chapter_node_candidates],
            )

        # 5. Retrieve cross-chapter plausible pairs (by node ID / content)
        all_node_candidates = [
            {
                "id": node_id_map[str(c["id"])],
                "start_time": c["start_time"],
                "end_time": c["end_time"],
                "transcript_excerpt": c.get("transcript_excerpt", ""),
                "summary": c.get("summary", ""),
            }
            for c in candidates
            if str(c["id"]) in node_id_map
        ]
        retrieval_pairs = self._retriever.retrieve_pairs(all_node_candidates)

        # 6. Cross-chapter linking (Pro model)
        cross_chapter_pairs: list[tuple[dict[str, object], dict[str, object]]] = []
        node_dict_by_id: dict[str, dict[str, object]] = {
            str(n["id"]): n for n in all_node_candidates
        }
        for pair in retrieval_pairs:
            if pair.source_id in node_dict_by_id and pair.target_id in node_dict_by_id:
                cross_chapter_pairs.append((
                    node_dict_by_id[pair.source_id],
                    node_dict_by_id[pair.target_id],
                ))

        cross_proposal: LocalGraphProposal | None = None
        if cross_chapter_pairs:
            cross_proposal = self._provider.link_story_elements(
                candidate_pairs=cross_chapter_pairs[:50],  # cap to avoid huge Pro calls
                element_index=self._element_index.as_list(),
                config=self._config,
            )
            all_proposals.append(cross_proposal)

        # 7. Validate and persist all edges
        # Build node registry for validator
        node_registry: dict[str, dict[str, object]] = {}
        for node in all_nodes:
            node_registry[str(node.id)] = {
                "start_time": float(str(node.start_time)),
                "end_time": float(str(node.end_time)),
                "node_type": str(node.node_type),
            }

        validated_edges: list[StoryEdge] = []
        existing_edge_tuples: list[tuple[str, str, str]] = []

        all_relationships: list[ProposedRelationship] = []
        for proposal in all_proposals:
            all_relationships.extend(proposal.relationships)

        for rel in all_relationships:
            result = self._validator.validate_edge(
                relationship=rel,
                node_registry=node_registry,
                existing_edges=existing_edge_tuples,
            )
            if result.passed:
                edge_id = str(uuid.uuid4())
                edge = StoryEdge(
                    id=edge_id,
                    story_graph_run_id=run.id,
                    source_node_id=rel.source_candidate,
                    target_node_id=rel.target_candidate,
                    relation_type=rel.relation.value,
                    confidence=rel.confidence,
                    dependency_strength=rel.dependency_strength.value,
                    dependency_strength_score=rel.dependency_strength_score,
                    evidence_summary=rel.evidence_summary[:500] if rel.evidence_summary else None,
                    provider=run.provider,
                    model=run.flash_model,
                    prompt_version=run.prompt_version,
                    validated=1,
                )
                session.add(edge)
                validated_edges.append(edge)
                existing_edge_tuples.append((rel.source_candidate, rel.target_candidate, rel.relation.value))
            else:
                logger.debug("Edge rejected: %s", result.errors)

        session.flush()

        # 8. Persist narrative elements
        for entry in self._element_index.as_list():
            el = NarrativeElement(
                id=str(uuid.uuid4()),
                story_graph_run_id=run.id,
                project_id=project_id,
                label=str(entry.get("label", "")),
                element_type=str(entry.get("element_type", "topic")),
                first_seen_time=float(str(entry.get("first_seen_time", 0))),
                last_seen_time=float(str(entry.get("last_seen_time", 0))),
                description=str(entry.get("description", "") or ""),
                node_ids=entry.get("node_ids", []),
                confidence=float(str(entry.get("confidence", 0.8))),
            )
            session.add(el)

        # 9. Build threads
        node_dicts: list[dict[str, object]] = [
            {
                "id": str(n.id),
                "start_time": float(str(n.start_time)),
                "end_time": float(str(n.end_time)),
                "node_type": str(n.node_type),
                "title": str(n.title) if n.title else None,
            }
            for n in all_nodes
        ]
        edge_dicts: list[dict[str, object]] = [
            {
                "source_node_id": str(e.source_node_id),
                "target_node_id": str(e.target_node_id),
                "relation_type": str(e.relation_type),
            }
            for e in validated_edges
        ]
        thread_candidates = self._thread_builder.build_threads(node_dicts, edge_dicts)

        thread_db_list: list[NarrativeThread] = []
        for tc in thread_candidates:
            thread_id = str(uuid.uuid4())
            thread = NarrativeThread(
                id=thread_id,
                story_graph_run_id=run.id,
                project_id=project_id,
                title=tc.title,
                thread_type=tc.thread_type,
                first_occurrence_time=tc.first_occurrence_time,
                last_occurrence_time=tc.last_occurrence_time,
                is_resolved=1 if tc.is_resolved else 0,
                confidence=tc.confidence,
                provider=run.provider,
            )
            session.add(thread)
            thread_db_list.append(thread)
            for nid in tc.node_ids:
                membership = NodeThreadMembership(
                    id=str(uuid.uuid4()),
                    node_id=nid,
                    thread_id=thread_id,
                )
                session.add(membership)

        # 10. Optional critic pass
        if self._config.use_critic and validated_edges:
            critic_proposals = self._provider.review_graph(
                nodes=node_dicts[:50],
                edges=edge_dicts[:100],
                threads=[{"title": t.title, "thread_type": t.thread_type} for t in thread_db_list[:20]],
                config=self._config,
            )
            for rel in critic_proposals:
                result = self._validator.validate_edge(
                    relationship=rel,
                    node_registry=node_registry,
                    existing_edges=existing_edge_tuples,
                )
                if result.passed:
                    edge = StoryEdge(
                        id=str(uuid.uuid4()),
                        story_graph_run_id=run.id,
                        source_node_id=rel.source_candidate,
                        target_node_id=rel.target_candidate,
                        relation_type=rel.relation.value,
                        confidence=rel.confidence,
                        dependency_strength=rel.dependency_strength.value,
                        dependency_strength_score=rel.dependency_strength_score,
                        evidence_summary=rel.evidence_summary[:500] if rel.evidence_summary else None,
                        provider=run.provider,
                        model=run.pro_model,
                        prompt_version=run.prompt_version,
                        validated=1,
                    )
                    session.add(edge)
                    validated_edges.append(edge)
                    existing_edge_tuples.append((rel.source_candidate, rel.target_candidate, rel.relation.value))

        # 11. Update run metrics
        callback_count = sum(
            1 for e in validated_edges
            if e.relation_type == EdgeRelationType.callback_to.value
        )
        setup_payoff_pairs = sum(
            1 for e in validated_edges
            if e.relation_type in {EdgeRelationType.payoff_of.value, EdgeRelationType.setup_for.value}
        )
        # Orphan nodes: nodes with no edges
        nodes_with_edges: set[str] = set()
        for e in validated_edges:
            nodes_with_edges.add(str(e.source_node_id))
            nodes_with_edges.add(str(e.target_node_id))
        orphan_count = sum(1 for n in all_nodes if n.id not in nodes_with_edges)

        run.node_count = len(all_nodes)
        run.edge_count = len(validated_edges)
        run.thread_count = len(thread_db_list)
        run.callback_count = callback_count
        run.setup_payoff_pairs = setup_payoff_pairs
        run.orphan_node_count = orphan_count
        run.status = "completed"
        run.completed_at = datetime.utcnow()

        session.commit()
        logger.info(
            "StoryGraphRun %s complete: %d nodes, %d edges, %d threads, %d callbacks, %d orphans",
            run.id, len(all_nodes), len(validated_edges), len(thread_db_list),
            callback_count, orphan_count,
        )
