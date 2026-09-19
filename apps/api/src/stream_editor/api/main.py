from contextlib import asynccontextmanager
from typing import Any
import uuid

from fastapi import FastAPI, Request
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

from .routers import analysis, candidates, health, jobs, planning, projects, story_graph, review, visual, effects, renders, style, benchmark

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    # Setup structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
    yield

app = FastAPI(title='StreamEditor AI', version='0.1.0', lifespan=lifespan)

@app.middleware("http")
async def logging_middleware(request: Request, call_next: Any) -> Any:
    clear_contextvars()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    bind_contextvars(request_id=request_id, path=request.url.path)
    logger.info("request_started", method=request.method)
    
    response = await call_next(request)
    
    logger.info("request_completed", status_code=response.status_code)
    return response

app.include_router(projects.router, prefix="/api/v1/projects")
app.include_router(jobs.router, prefix="/api/v1/jobs")
app.include_router(health.router, prefix="/health")
app.include_router(health.router, prefix="/api/v1/health")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(candidates.router, prefix="/api/v1")
app.include_router(story_graph.router, prefix="/api/v1")
app.include_router(planning.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1")
app.include_router(visual.router, prefix="/api/v1")
app.include_router(visual.run_router, prefix="/api/v1")
app.include_router(effects.router, prefix="/api/v1")
app.include_router(effects.run_router, prefix="/api/v1")
app.include_router(renders.router, prefix="/api/v1")
app.include_router(renders.run_router, prefix="/api/v1")
app.include_router(style.router, prefix="/api/v1")
app.include_router(benchmark.router, prefix="/api/v1")
