from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PlanningProfile(str, Enum):
    compact = "compact"
    balanced = "balanced"
    comprehensive = "comprehensive"


class EditingGoal(str, Enum):
    SHORT_HIGHLIGHT = "SHORT_HIGHLIGHT"        # 60s - 180s (Shorts/TikTok/Reels)
    LONG_FORM_SUMMARY = "LONG_FORM_SUMMARY"    # 600s - 1200s (10 - 20 min YouTube recap)
    FULL_EDITED_SESSION = "FULL_EDITED_SESSION" # 1800s - 2700s (30 - 45 min full human reference)


class EditPlanConfig(BaseModel):
    target_duration_seconds: float = Field(default=9000.0, description="Target duration in seconds (e.g. 150 min = 9000s)")
    tolerance_seconds: float = Field(default=900.0, description="Acceptable duration variance (e.g. 15 min = 900s)")
    profile: PlanningProfile = Field(default=PlanningProfile.balanced)
    editing_goal: EditingGoal = Field(default=EditingGoal.LONG_FORM_SUMMARY)
    preserve_narrative_anchors: bool = Field(default=True, description="Protect opening greeting and game start from duration pruning")

    @classmethod
    def from_goal(
        cls,
        goal: EditingGoal,
        profile: PlanningProfile = PlanningProfile.balanced,
        preserve_narrative_anchors: bool = True,
    ) -> "EditPlanConfig":
        if goal == EditingGoal.SHORT_HIGHLIGHT:
            return cls(
                target_duration_seconds=120.0,
                tolerance_seconds=30.0,
                profile=profile,
                editing_goal=goal,
                preserve_narrative_anchors=preserve_narrative_anchors,
            )
        elif goal == EditingGoal.FULL_EDITED_SESSION:
            return cls(
                target_duration_seconds=2400.0,
                tolerance_seconds=300.0,
                profile=profile,
                editing_goal=goal,
                preserve_narrative_anchors=preserve_narrative_anchors,
            )
        else:  # LONG_FORM_SUMMARY
            return cls(
                target_duration_seconds=900.0,
                tolerance_seconds=180.0,
                profile=profile,
                editing_goal=goal,
                preserve_narrative_anchors=preserve_narrative_anchors,
            )


class ClipPriority(str, Enum):
    essential = "essential"
    high = "high"
    medium = "medium"
    low = "low"
    context_only = "context_only"


class EditClipContract(BaseModel):
    id: UUID
    plan_id: UUID
    source_start: float
    source_end: float
    core_start: float | None = None
    core_end: float | None = None
    output_start: float
    output_end: float

    candidate_id: str | None = None
    narrative_thread_id: str | None = None
    story_node_id: str | None = None

    selection_reason: str
    priority: ClipPriority
    confidence: float | None = None
    locked: bool = False
    is_narrative_anchor: bool = False
    anchor_type: str | None = None
    
    @property
    def source_duration(self) -> float:
        return self.source_end - self.source_start

    @property
    def output_duration(self) -> float:
        return self.output_end - self.output_start


class EditPlanContract(BaseModel):
    id: UUID
    project_id: str
    run_id: UUID
    version: int
    status: str
    original_duration: float
    selected_duration: float
    compression_ratio: float
    clip_count: int
    locked: bool
    clips: list[EditClipContract] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_plan(self) -> "EditPlanContract":
        if not self.clips:
            return self

        # Ensure output clips do not overlap
        sorted_clips = sorted(self.clips, key=lambda c: c.output_start)
        for i in range(1, len(sorted_clips)):
            prev = sorted_clips[i - 1]
            curr = sorted_clips[i]
            # Floating point tolerance
            if curr.output_start < (prev.output_end - 0.001):
                raise ValueError(
                    f"Clips have overlapping output positions: {prev.id} ends at {prev.output_end}, "
                    f"but {curr.id} starts at {curr.output_start}"
                )

        return self


class PlanCritiqueIssue(BaseModel):
    severity: Literal["critical", "warning", "info"]
    issue_type: str
    description: str
    affected_clip_ids: list[str] = Field(default_factory=list)


class PlanCritique(BaseModel):
    issues: list[PlanCritiqueIssue]
    recommendation: Literal["approve", "revise_minor", "revise_major"]
