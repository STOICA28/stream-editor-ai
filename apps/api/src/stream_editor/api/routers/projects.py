from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from stream_editor.api.database import get_db
from stream_editor.api.models.project import ProcessingJob, Project
from stream_editor.api.schemas.projects import MediaImportRequest, ProjectCreate, ProjectResponse
from stream_editor.worker.tasks.pipeline import ingest_media_task

router = APIRouter()

@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)) -> Any:
    db_project = Project(name=project.name, description=project.description)
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project

@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Project))
    return result.scalars().all()

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)) -> Any:
    # MVP: deletion might just mark as deleted or delete DB rows.
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
    return {"status": "deleted"}

@router.post("/{project_id}/media")
async def register_media(project_id: str, request: MediaImportRequest, db: AsyncSession = Depends(get_db)) -> Any:
    # Trigger ingest pipeline task
    ingest_media_task.delay(project_id, request.source_path)
    return {"status": "registered", "source_path": request.source_path}

@router.get("/{project_id}/jobs")
async def list_jobs(project_id: str, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.project_id == project_id))
    jobs = result.scalars().all()
    # Also fetch steps for these jobs
    # For MVP we can just return basic job info
    return [{"id": j.id, "status": j.status, "current_stage": j.current_stage} for j in jobs]

@router.post("/{project_id}/process")
async def process_project(project_id: str, payload: dict | None = None) -> Any:  # type: ignore[type-arg]
    return {"job_id": "Not implemented", "payload": payload}

