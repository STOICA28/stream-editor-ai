import re

with open('apps/api/src/stream_editor/api/models/project.py', 'r') as f:
    content = f.read()

# Add to EditPlan
if "parent_plan_id = Column(" not in content:
    plan_additions = """
    # M6 Revisions
    parent_plan_id = Column(String, ForeignKey("edit_plans.id"), nullable=True)
    revision_number = Column(Integer, default=1)
    origin = Column(String, default="ai")  # ai | human | hybrid
    revision_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)"""
    content = re.sub(r'(class EditPlan\(Base\):.*?)(    created_at = Column\(DateTime, default=datetime\.utcnow\))', r'\1' + plan_additions, content, flags=re.DOTALL)

# Add to EditClip
if "review_state = Column(" not in content:
    clip_additions = """
    # M6 Review State
    review_state = Column(String, default="proposed")  # proposed | accepted | rejected | modified
    
    # Output timeline boundaries"""
    content = re.sub(r'(class EditClip\(Base\):.*?)(    # Output timeline boundaries)', r'\1' + clip_additions, content, flags=re.DOTALL)

with open('apps/api/src/stream_editor/api/models/project.py', 'w') as f:
    f.write(content)
print("Models fully patched.")
