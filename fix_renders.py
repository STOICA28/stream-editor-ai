import re

with open("apps/api/src/stream_editor/api/routers/renders.py", "r") as f:
    text = f.read()

text = text.replace("uuid.UUID(c.id)", "uuid.UUID(str(c.id))")
text = text.replace("uuid.UUID(c.plan_id)", "uuid.UUID(str(c.plan_id))")
text = text.replace('def start_render(', 'def start_render(')
text = re.sub(r'async def start_render\((.*?)\):', r'async def start_render(\1) -> dict:', text, flags=re.DOTALL)
text = re.sub(r'async def list_renders\((.*?)\):', r'async def list_renders(\1) -> Any:', text, flags=re.DOTALL)
text = re.sub(r'async def get_render_job\((.*?)\):', r'async def get_render_job(\1) -> Any:', text, flags=re.DOTALL)
text = re.sub(r'async def cancel_render\((.*?)\):', r'async def cancel_render(\1) -> dict:', text, flags=re.DOTALL)
text = text.replace("job.id, project_id", "str(job.id), project_id")

with open("apps/api/src/stream_editor/api/routers/renders.py", "w") as f:
    f.write(text)
