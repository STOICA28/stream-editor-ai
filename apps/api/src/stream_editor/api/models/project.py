from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid
from datetime import datetime
from ..database import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    description = Column(String, nullable=True)
    status = Column(String, default="created")
    source_video_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MediaAsset(Base):
    __tablename__ = "media_assets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    name = Column(String)
    path = Column(String)
    media_type = Column(String)
    file_size_bytes = Column(Integer)
    media_info = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    status = Column(String)
    current_stage = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

class JobStep(Base):
    __tablename__ = "job_steps"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("processing_jobs.id"))
    stage = Column(String)
    status = Column(String)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    input_hash = Column(String, nullable=True)
    output_hash = Column(String, nullable=True)
    algorithm_version = Column(String)
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    output_paths = Column(JSON)

# Stubs for others to satisfy Alembic
class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

class Scene(Base):
    __tablename__ = "scenes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

class CandidateSegment(Base):
    __tablename__ = "candidate_segments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scores = Column(JSON)

class EditPlan(Base):
    __tablename__ = "edit_plans"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

class EditPlanVersion(Base):
    __tablename__ = "edit_plan_versions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

class EditClip(Base):
    __tablename__ = "edit_clips"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

class FeedbackEvent(Base):
    __tablename__ = "feedback_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
