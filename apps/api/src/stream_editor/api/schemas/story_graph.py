"""API schemas for Story Graph."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from stream_editor.contracts.editorial import (
    NarrativeThreadContract,
    StoryEdgeContract,
    StoryNodeContract,
)


class StoryGraphGenerationRequest(BaseModel):
    provider: str = "mock"
    candidate_run_id: str


class StoryGraphGenerationResponse(BaseModel):
    message: str
    run_id: str


class StoryGraphRunResponse(BaseModel):
    id: str
    project_id: str
    source_asset_id: str
    candidate_run_id: str
    provider: str
    status: str
    error_message: str | None = None
    node_count: int = 0
    edge_count: int = 0
    thread_count: int = 0
    created_at: str
    completed_at: str | None = None


class StoryGraphDetailResponse(BaseModel):
    run: StoryGraphRunResponse
    nodes: list[StoryNodeContract] = Field(default_factory=list)
    edges: list[StoryEdgeContract] = Field(default_factory=list)
    threads: list[NarrativeThreadContract] = Field(default_factory=list)
