with open('apps/api/src/stream_editor/api/models/project.py', 'a') as f:
    f.write('''
# ---------------------------------------------------------------------------
# M9 - Rendering Engine models
# ---------------------------------------------------------------------------

class RenderJob(Base):
    __tablename__ = "render_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"), nullable=True)
    edit_plan_id = Column(String, ForeignKey("edit_plans.id"))
    effect_plan_run_id = Column(String, ForeignKey("effect_plan_runs.id"), nullable=True)
    
    render_config = Column(JSON)
    derivation_signature = Column(String, unique=True, nullable=True)
    renderer_version = Column(String, default="1.0")
    
    status = Column(String, default="pending")
    progress = Column(Float, default=0.0)
    output_asset_id = Column(String, ForeignKey("media_assets.id"), nullable=True)
    error_message = Column(String, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
''')
