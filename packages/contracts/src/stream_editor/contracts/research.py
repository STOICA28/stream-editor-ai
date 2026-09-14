from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class FindingType(str, Enum):
    observation = "observation"
    inference = "inference"
    hypothesis = "hypothesis"
    approved_rule = "approved_rule"

class ResearchFinding(BaseModel):
    id: UUID
    reference_project_id: UUID
    source_video_id: UUID
    source_range_start: float
    source_range_end: float
    confidence: float
    finding_type: FindingType
    title: str
    description: str
    supporting_evidence: list[dict[str, Any]]
    provenance: dict[str, Any]

class StylePattern(BaseModel):
    id: UUID
    channel_id: str
    name: str
    description: str
    metrics: dict[str, Any]
    evidence_count: int
    confidence: float
    status: str
