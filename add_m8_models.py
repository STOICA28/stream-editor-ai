with open('apps/api/src/stream_editor/api/models/project.py', 'a') as f:
    f.write('''
# ---------------------------------------------------------------------------
# M8 - Effect Planning models
# ---------------------------------------------------------------------------

class EffectPlanRun(Base):
    __tablename__ = "effect_plan_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    edit_plan_id = Column(String, ForeignKey("edit_plans.id"))
    visual_analysis_run_id = Column(String, ForeignKey("visual_analysis_runs.id"), nullable=True)
    
    # Provider & Config
    provider = Column(String)  # mock | gemini
    model = Column(String, nullable=True)
    configuration = Column(JSON, nullable=True)
    prompt_version = Column(String, nullable=True)
    editorial_rule_versions = Column(String, nullable=True)
    derivation_signature = Column(String, unique=True)
    
    # Status & Telemetry
    status = Column(String, default="running")  # running | completed | failed | partial
    error_message = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class EffectInstruction(Base):
    __tablename__ = "effect_instructions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    effect_plan_run_id = Column(String, ForeignKey("effect_plan_runs.id"))
    edit_clip_id = Column(String, ForeignKey("edit_clips.id"), nullable=True)
    
    source_start = Column(Float)
    source_end = Column(Float)
    output_start = Column(Float, nullable=True)
    output_end = Column(Float, nullable=True)
    
    effect_type = Column(String)  # none | zoom_region | zoom_face | zoom_chat | crop_focus | grayscale | freeze_frame | slow_motion | speed_up | text_emphasis | highlight_region | audio_duck | audio_gain | fade
    target_type = Column(String)  # full_frame | facecam | chat | screen_region | text_region | content_region | visual_event | unknown
    
    # Bounding Box (normalized 0-1) - Optional
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    
    parameters = Column(JSON, nullable=True)
    
    confidence = Column(Float)
    priority = Column(String)  # critical | high | normal | low
    reason = Column(String, nullable=True)
    evidence_references = Column(JSON, nullable=True)
    
    provider = Column(String)
    review_state = Column(String, default="proposed")  # proposed | accepted | rejected | modified
    
    created_at = Column(DateTime, default=datetime.utcnow)
''')
