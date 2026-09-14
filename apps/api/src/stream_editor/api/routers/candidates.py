"""
M3 Candidate API endpoints.

All scores are returned as Optional[float]. Never replace null with 0.
debug_label is NOT a final editorial decision.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.project import (
    CandidateRun,
    CandidateSegment,
    MediaAsset,
    Project,
)
from ..schemas.candidates import (
    CandidateRunResponse,
    CandidateSegmentResponse,
    GenerateCandidatesRequest,
    GenerateCandidatesResponse,
)

router = APIRouter(tags=["candidates"])


def _get_project_or_404(project_id: str, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects/{project_id}/candidates/generate", response_model=GenerateCandidatesResponse)
def generate_candidates(
    project_id: str,
    request: GenerateCandidatesRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> GenerateCandidatesResponse:
    """
    Trigger candidate generation for a project.

    Runs asynchronously via Celery (in production) or inline for dev.
    Returns the created CandidateRun ID immediately.
    """
    _get_project_or_404(project_id, db)

    # Find the primary source asset
    asset = (
        db.query(MediaAsset)
        .filter(MediaAsset.project_id == project_id, MediaAsset.media_type == "source")
        .order_by(MediaAsset.created_at.desc())
        .first()
    )
    if not asset:
        raise HTTPException(status_code=422, detail="No source asset found for project")

    # Dispatch Celery task
    from stream_editor.worker.tasks.pipeline import generate_candidates_task
    task = generate_candidates_task.delay(
        project_id=project_id,
        asset_id=str(asset.id),
        provider_name=request.provider or "mock",
        ranking_profile=request.ranking_profile or "balanced",
    )

    return GenerateCandidatesResponse(
        task_id=str(task.id),
        project_id=project_id,
        asset_id=str(asset.id),
        message="Candidate generation started",
    )


@router.get("/projects/{project_id}/candidate-runs", response_model=list[CandidateRunResponse])
def list_candidate_runs(
    project_id: str,
    db: Session = Depends(get_db),
) -> list[CandidateRunResponse]:
    """List all candidate runs for a project, newest first."""
    _get_project_or_404(project_id, db)
    runs = (
        db.query(CandidateRun)
        .filter(CandidateRun.project_id == project_id)
        .order_by(CandidateRun.created_at.desc())
        .all()
    )
    return [CandidateRunResponse.model_validate(r) for r in runs]


@router.get("/candidate-runs/{run_id}", response_model=CandidateRunResponse)
def get_candidate_run(run_id: str, db: Session = Depends(get_db)) -> CandidateRunResponse:
    """Get details of a specific candidate run."""
    run = db.query(CandidateRun).filter(CandidateRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Candidate run not found")
    return CandidateRunResponse.model_validate(run)


@router.get("/candidate-runs/{run_id}/candidates", response_model=list[CandidateSegmentResponse])
def list_candidates(
    run_id: str,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "experimental_rank",
    sort_order: str = "desc",
    min_confidence: float | None = None,
    debug_label: str | None = None,
    db: Session = Depends(get_db),
) -> list[CandidateSegmentResponse]:
    """
    List candidates for a run with pagination and filtering.

    Sort options: experimental_rank, start_time, confidence, score_humor,
                  score_importance, score_story_value
    """
    run = db.query(CandidateRun).filter(CandidateRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Candidate run not found")

    query = db.query(CandidateSegment).filter(CandidateSegment.run_id == run_id)

    if min_confidence is not None:
        query = query.filter(CandidateSegment.confidence >= min_confidence)
    if debug_label is not None:
        query = query.filter(CandidateSegment.debug_label == debug_label)

    sortable_columns = {
        "experimental_rank": CandidateSegment.experimental_rank,
        "start_time": CandidateSegment.start_time,
        "confidence": CandidateSegment.confidence,
        "score_humor": CandidateSegment.score_humor,
        "score_importance": CandidateSegment.score_importance,
        "score_story_value": CandidateSegment.score_story_value,
    }
    col = sortable_columns.get(sort_by, CandidateSegment.experimental_rank)
    if sort_order == "desc":
        query = query.order_by(col.desc())
    else:
        query = query.order_by(col.asc())

    offset = (page - 1) * page_size
    candidates = query.offset(offset).limit(page_size).all()
    return [CandidateSegmentResponse.model_validate(c) for c in candidates]


@router.get("/candidates/{candidate_id}", response_model=CandidateSegmentResponse)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)) -> CandidateSegmentResponse:
    """Get full candidate detail including evidence links."""
    cand = db.query(CandidateSegment).filter(CandidateSegment.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return CandidateSegmentResponse.model_validate(cand)
