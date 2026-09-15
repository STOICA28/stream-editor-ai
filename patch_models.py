import re

with open('apps/api/src/stream_editor/api/models/project.py', 'r') as f:
    content = f.read()

# Add to EditPlan
plan_additions = """
    # M6 Revisions
    parent_plan_id = Column(String, ForeignKey("edit_plans.id"), nullable=True)
    revision_number = Column(Integer, default=1)
    origin = Column(String, default="ai")  # ai | human | hybrid
    revision_reason = Column(String, nullable=True)
"""
content = re.sub(r'(class EditPlan\(Base\):.*?)(?=    created_at = Column)', r'\1' + plan_additions + '\n', content, flags=re.DOTALL)

# Add to EditClip
clip_additions = """
    # M6 Review State
    review_state = Column(String, default="proposed")  # proposed | accepted | rejected | modified
"""
content = re.sub(r'(class EditClip\(Base\):.*?)(?=    # Output timeline boundaries)', r'\1' + clip_additions + '\n', content, flags=re.DOTALL)

# Add FeedbackEvent
feedback_model = """
class FeedbackEvent(Base):
    __tablename__ = "feedback_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    edit_plan_id = Column(String, ForeignKey("edit_plans.id"))
    edit_clip_id = Column(String, ForeignKey("edit_clips.id"), nullable=True)
    
    feedback_type = Column(String) # accept_clip | reject_clip | extend_start | trim_start | extend_end | trim_end | lock_clip | unlock_clip | restore_clip
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    reason_category = Column(String, nullable=True)
    reason_text = Column(String, nullable=True)
    
    candidate_id = Column(String, nullable=True)
    story_node_ids = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
"""
if "class FeedbackEvent" not in content:
    content += "\n" + feedback_model + "\n"

with open('apps/api/src/stream_editor/api/models/project.py', 'w') as f:
    f.write(content)
print("Patched models successfully.")
