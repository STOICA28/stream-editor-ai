from enum import Enum
from uuid import UUID
from typing import List
from pydantic import BaseModel, Field

class CandidateSegmentScores(BaseModel):
    humor: float = Field(ge=0.0, le=1.0)
    importance: float = Field(ge=0.0, le=1.0)
    reaction: float = Field(ge=0.0, le=1.0)
    visual_interest: float = Field(ge=0.0, le=1.0)
    chat_relevance: float = Field(ge=0.0, le=1.0)
    story_value: float = Field(ge=0.0, le=1.0)
    repetition_penalty: float = Field(ge=0.0, le=1.0)

class CandidateSegment(BaseModel):
    id: UUID
    project_id: str
    start_seconds: float
    end_seconds: float
    scores: CandidateSegmentScores
    narrative_context: str
    selected_timeline_events: List[UUID]

class NarrativeNodeType(str, Enum):
    setup = "setup"
    event = "event"
    character_intro = "character_intro"
    joke = "joke"
    callback = "callback"
    payoff = "payoff"
    explanation = "explanation"
    decision = "decision"
    consequence = "consequence"

class NarrativeEdgeType(str, Enum):
    depends_on = "depends_on"
    callback_to = "callback_to"
    explains = "explains"
    caused_by = "caused_by"
    follows = "follows"
    contrasts_with = "contrasts_with"

class NarrativeNode(BaseModel):
    id: UUID
    project_id: str
    node_type: NarrativeNodeType
    candidate_segment_id: UUID
    label: str
    description: str

class NarrativeEdge(BaseModel):
    id: UUID
    from_node_id: UUID
    to_node_id: UUID
    edge_type: NarrativeEdgeType
    strength: float

class StoryGraph(BaseModel):
    project_id: str
    nodes: List[NarrativeNode]
    edges: List[NarrativeEdge]
