import re

with open('apps/api/src/stream_editor/api/models/project.py', 'r') as f:
    content = f.read()

models = '''

# ---------------------------------------------------------------------------
# M7 - Visual Understanding models
# ---------------------------------------------------------------------------

class VisualAnalysisRun(Base):
    __tablename__ = "visual_analysis_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    proxy_asset_id = Column(String, ForeignKey("media_assets.id"), nullable=True)
    
    # Provider & Config
    provider = Column(String)  # mock | gemini
    configuration = Column(JSON)  # sampler settings, thresholds
    derivation_signature = Column(String, unique=True)
    
    # Status & Telemetry
    status = Column(String, default="running")  # running | completed | failed | partial
    error_message = Column(String, nullable=True)
    flash_requests = Column(Integer, default=0)
    pro_requests = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_latency_ms = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class VisualRegion(Base):
    __tablename__ = "visual_regions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_analysis_run_id = Column(String, ForeignKey("visual_analysis_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    
    region_type = Column(String)  # facecam | chat | gameplay | browser | desktop | alert | webcam | subtitle | hud | unknown
    start_time = Column(Float)
    end_time = Column(Float)
    
    # Bounding Box (normalized 0-1)
    x = Column(Float)
    y = Column(Float)
    width = Column(Float)
    height = Column(Float)
    
    confidence = Column(Float)
    detector = Column(String)  # e.g. "mediapipe", "gemini-flash"
    track_id = Column(String, nullable=True)  # stable temporal identifier e.g. FACE_TRACK_01
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class StreamLayout(Base):
    __tablename__ = "stream_layouts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_analysis_run_id = Column(String, ForeignKey("visual_analysis_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    
    start_time = Column(Float)
    end_time = Column(Float)
    
    layout_name = Column(String)  # e.g., "Gameplay + BottomRight Facecam"
    description = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class VisualEvent(Base):
    __tablename__ = "visual_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_analysis_run_id = Column(String, ForeignKey("visual_analysis_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    
    event_type = Column(String)  # layout_change | facecam_appears | facecam_disappears | chat_appears | large_motion | focus_shift | visual_event | strong_face_reaction
    start_time = Column(Float)
    end_time = Column(Float)
    
    confidence = Column(Float)
    description = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class FocusTarget(Base):
    __tablename__ = "focus_targets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_analysis_run_id = Column(String, ForeignKey("visual_analysis_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    
    start_time = Column(Float)
    end_time = Column(Float)
    
    target_type = Column(String)  # facecam | chat | screen_region | text_region | game_region | alert | full_frame | unknown
    
    # Bounding Box (normalized 0-1)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    
    priority = Column(String, nullable=True)
    confidence = Column(Float)
    evidence_summary = Column(String, nullable=True)
    provenance = Column(String)
    
    sequence_id = Column(String, nullable=True)  # Grouping for screen_event -> reaction sequences
    sequence_order = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
'''

if "class VisualAnalysisRun(Base):" not in content:
    content += models

with open('apps/api/src/stream_editor/api/models/project.py', 'w') as f:
    f.write(content)
