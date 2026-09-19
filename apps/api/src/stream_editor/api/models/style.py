import uuid
from datetime import datetime

from stream_editor.api.models.mixins import JobLeaseMixin
from stream_editor.api.models.states import JobState
from sqlalchemy import UniqueConstraint, JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base

class EditorialStylePolicy(Base):
    __tablename__ = "editorial_style_policies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    description = Column(String, nullable=True)
    status = Column(String, default="draft")
    source_reference_project_id = Column(String, ForeignKey("reference_projects.id"), nullable=True)
    source_style_profile_id = Column(String, ForeignKey("style_profiles.id"), nullable=True)
    source_style_profile_version = Column(Integer, nullable=True)
    policy_version = Column(Integer, default=1)
    experimental = Column(Boolean, default=False)
    
    # Store the configured StyleSignals as JSON
    signals = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="system")

class StylePolicyVersion(Base):
    __tablename__ = "style_policy_versions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = Column(String, ForeignKey("editorial_style_policies.id"))
    version = Column(Integer)
    
    # Immutable snapshot of signals
    signals = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    
class StyleApplicationRun(JobLeaseMixin, Base):
    __tablename__ = "style_application_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    style_policy_id = Column(String, ForeignKey("editorial_style_policies.id"), nullable=True)
    style_policy_version_id = Column(String, ForeignKey("style_policy_versions.id"))
    
    style_application_config = Column(JSON, default=dict)
    experimental = Column(Boolean, default=False)
    dry_run = Column(Boolean, default=False)

    input_candidate_run_id = Column(String, nullable=True)
    input_story_graph_run_id = Column(String, nullable=True)
    input_visual_analysis_run_id = Column(String, nullable=True)
    
    output_edit_plan_run_id = Column(String, nullable=True)
    output_effect_plan_run_id = Column(String, nullable=True)
    
    status = Column(String, default=JobState.PENDING.value)
    signature = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

