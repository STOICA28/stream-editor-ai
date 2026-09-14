from typing import Any
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routers import projects, jobs, health

@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    yield

app = FastAPI(title='StreamEditor AI', version='0.1.0', lifespan=lifespan)
app.include_router(projects.router, prefix="/api/v1/projects")
app.include_router(jobs.router, prefix="/api/v1/jobs")
app.include_router(health.router, prefix="/api/v1/health")
