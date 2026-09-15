import re

with open('apps/api/src/stream_editor/api/models/project.py', 'r') as f:
    content = f.read()

# Replace the broken FeedbackEvent if it's there
broken_pattern = r'class FeedbackEvent\(Base\):\s*__tablename__ = "feedback_events"\s*id = Column\(String, primary_key=True, default=lambda: str\(uuid\.uuid4\(\)\)\)'

correct_feedback_model = """class FeedbackEvent(Base):
    __tablename__ = "feedback_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    edit_plan_id = Column(String, ForeignKey("edit_plans.id"))
    edit_clip_id = Column(String, ForeignKey("edit_clips.id"), nullable=True)
    
    feedback_type = Column(String)
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    reason_category = Column(String, nullable=True)
    reason_text = Column(String, nullable=True)
    
    candidate_id = Column(String, nullable=True)
    story_node_ids = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
"""

if re.search(broken_pattern, content):
    content = re.sub(broken_pattern, correct_feedback_model, content)
else:
    # If it's already there but full? Or maybe it's completely missing. Let's append if completely missing
    if "project_id = Column(String, ForeignKey(\"projects.id\"))" not in content:
        content += "\n" + correct_feedback_model + "\n"

with open('apps/api/src/stream_editor/api/models/project.py', 'w') as f:
    f.write(content)
