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
    
    # Provenance
    parent_asset_id = Column(String, ForeignKey("media_assets.id"), nullable=True)
    derivation_signature = Column(String, nullable=True)
    producer = Column(String, nullable=True)
    producer_version = Column(String, nullable=True)
    
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

class TranscriptRun(Base):
    __tablename__ = "transcript_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    provider = Column(String)
    model = Column(String)
    language = Column(String, nullable=True)
    configuration = Column(JSON)
    derivation_signature = Column(String, unique=True)
    status = Column(String, default="running") # running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("transcript_runs.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    status = Column(String, default="pending")
    result_path = Column(String, nullable=True)

class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transcript_run_id = Column(String, ForeignKey("transcript_runs.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    text = Column(String)
    speaker = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    sequence = Column(Integer)

class TranscriptWord(Base):
    __tablename__ = "transcript_words"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    segment_id = Column(String, ForeignKey("transcript_segments.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    text = Column(String)
    confidence = Column(Float, nullable=True)

class Scene(Base):
    __tablename__ = "scenes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    duration = Column(Float)
    detector = Column(String)
    detector_config = Column(JSON)
    confidence = Column(Float, nullable=True)

class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    event_type = Column(String) # speech, scene_change, silence, high_energy
    start_time = Column(Float)
    end_time = Column(Float)
    producer = Column(String)
    producer_version = Column(String)
    confidence = Column(Float, nullable=True)
    data = Column(JSON, nullable=True)

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
