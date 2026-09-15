"""Story Graph API routes."""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from stream_editor.api.database import get_db
from stream_editor.api.models.project import (
    MediaAsset,
    NodeThreadMembership,
    Project,
    StoryEdge,
    StoryGraphRun,
    StoryNode,
    NarrativeThread,
)
from stream_editor.api.schemas.story_graph import (
    StoryGraphDetailResponse,
    StoryGraphGenerationRequest,
    StoryGraphGenerationResponse,
    StoryGraphRunResponse,
)
from stream_editor.contracts.editorial import (
    ContextRequirement,
    DependencyStrength,
    EdgeRelationType,
    NarrativeThreadContract,
    StoryEdgeContract,
    StoryNodeContract,
    StoryNodeType,
)
from stream_editor.worker.tasks.pipeline import generate_story_graph_task

router = APIRouter(prefix="/projects/{project_id}/story-graph", tags=["Story Graph"])

@router.post("", response_model=StoryGraphGenerationResponse)
async def generate_story_graph(
    project_id: UUID,
    request: StoryGraphGenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> StoryGraphGenerationResponse:
    project = await db.get(Project, str(project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # MVP: get first asset
    asset_res = await db.execute(select(MediaAsset).where(MediaAsset.project_id == str(project_id)).limit(1))
    asset = asset_res.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail="Project has no assets")

    # The actual task executes synchronously via Celery in the background.
    # For MVP without Celery worker running, we'll enqueue it via background_tasks
    background_tasks.add_task(
        generate_story_graph_task.delay,
        str(project_id),
        asset.id,
        request.candidate_run_id,
        request.provider,
    )

    return StoryGraphGenerationResponse(
        message="Story Graph generation task queued.",
        run_id="pending",
    )


@router.get("/runs", response_model=list[StoryGraphRunResponse])
async def list_story_graph_runs(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[StoryGraphRunResponse]:
    result = await db.execute(
        select(StoryGraphRun)
        .where(
            StoryGraphRun.project_id == str(project_id)
        )
        .order_by(StoryGraphRun.created_at.desc())
    )
    runs = result.scalars().all()
    return [
        StoryGraphRunResponse(
            id=r.id,
            project_id=r.project_id,
            source_asset_id=r.source_asset_id,
            candidate_run_id=r.candidate_run_id,
            provider=r.provider,
            status=r.status,
            error_message=r.error_message,
            node_count=r.node_count or 0,
            edge_count=r.edge_count or 0,
            thread_count=r.thread_count or 0,
            created_at=r.created_at.isoformat(),
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
        )
        for r in runs
    ]


@router.get("/runs/{run_id}", response_model=StoryGraphDetailResponse)
async def get_story_graph(
    project_id: UUID,
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> StoryGraphDetailResponse:
    run = await db.get(StoryGraphRun, str(run_id))
    if not run or run.project_id != str(project_id):
        raise HTTPException(status_code=404, detail="StoryGraphRun not found")

    # Fetch nodes
    nodes_res = await db.execute(
        select(StoryNode).where(StoryNode.story_graph_run_id == str(run_id))
    )
    nodes_db = nodes_res.scalars().all()

    # Fetch threads and memberships
    threads_res = await db.execute(
        select(NarrativeThread).where(NarrativeThread.story_graph_run_id == str(run_id))
    )
    threads_db = threads_res.scalars().all()

    memberships_res = await db.execute(
        select(NodeThreadMembership).join(NarrativeThread).where(NarrativeThread.story_graph_run_id == str(run_id))
    )
    memberships_db = memberships_res.scalars().all()

    node_threads: dict[str, list[str]] = {}
    for m in memberships_db:
        node_threads.setdefault(str(m.node_id), []).append(str(m.thread_id))

    # Fetch edges
    edges_res = await db.execute(
        select(StoryEdge).where(StoryEdge.story_graph_run_id == str(run_id))
    )
    edges_db = edges_res.scalars().all()

    # Map to contracts
    node_contracts = [
        StoryNodeContract(
            id=str(n.id),
            story_graph_run_id=str(n.story_graph_run_id),
            node_type=StoryNodeType(str(n.node_type)),
            start_time=float(str(n.start_time)),
            end_time=float(str(n.end_time)),
            candidate_id=str(n.candidate_id) if n.candidate_id else None,
            title=str(n.title) if n.title else None,
            summary=str(n.summary) if n.summary else None,
            confidence=float(str(n.confidence)),
            context_requirement=ContextRequirement.model_validate(n.context_requirement) if n.context_requirement else None,
            graph_narrative_value=float(str(n.graph_narrative_value)) if n.graph_narrative_value else None,
            chapter_index=int(str(n.chapter_index)) if n.chapter_index else None,
            provider=str(n.provider),
            model=str(n.model) if n.model else None,
            thread_ids=node_threads.get(str(n.id), []),
        )
        for n in nodes_db
    ]

    edge_contracts = [
        StoryEdgeContract(
            id=e.id,
            story_graph_run_id=e.story_graph_run_id,
            source_node_id=e.source_node_id,
            target_node_id=e.target_node_id,
            relation_type=EdgeRelationType(e.relation_type),
            confidence=e.confidence,
            dependency_strength=DependencyStrength(e.dependency_strength),
            dependency_strength_score=e.dependency_strength_score,
            evidence_summary=e.evidence_summary,
            provider=e.provider,
            model=e.model,
            validated=e.validated,
        )
        for e in edges_db
    ]

    thread_contracts = [
        NarrativeThreadContract(
            id=t.id,
            story_graph_run_id=t.story_graph_run_id,
            title=t.title,
            summary=t.summary,
            thread_type=t.thread_type,
            first_occurrence_time=t.first_occurrence_time,
            last_occurrence_time=t.last_occurrence_time,
            is_resolved=bool(t.is_resolved),
            importance=t.importance,
            confidence=t.confidence,
            node_ids=[m.node_id for m in memberships_db if m.thread_id == t.id],
        )
        for t in threads_db
    ]

    run_response = StoryGraphRunResponse(
        id=run.id,
        project_id=run.project_id,
        source_asset_id=run.source_asset_id,
        candidate_run_id=run.candidate_run_id,
        provider=run.provider,
        status=run.status,
        error_message=run.error_message,
        node_count=run.node_count or 0,
        edge_count=run.edge_count or 0,
        thread_count=run.thread_count or 0,
        created_at=run.created_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )

    return StoryGraphDetailResponse(
        run=run_response,
        nodes=node_contracts,
        edges=edge_contracts,
        threads=thread_contracts,
    )
