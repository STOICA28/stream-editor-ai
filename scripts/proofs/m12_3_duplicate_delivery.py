import uuid
import time
from datetime import datetime, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from stream_editor.api.models.project import Project

from stream_editor.worker.tasks.pipeline import generate_visual_analysis_task
import sys

def log(msg):
    print(msg)
    sys.stdout.flush()

if __name__ == '__main__':
    engine = create_engine('sqlite:///test.db')
    project_id = None
    with Session(engine) as db:
        proj = db.query(Project).filter(Project.id == 'real-5h-65655576').first()
        project_id = proj.id

    from stream_editor.api.models.project import MediaAsset
    with Session(engine) as db:
        asset = db.query(MediaAsset).filter_by(project_id=project_id, media_type='source').first()
        asset_id = str(asset.id)

    log('Dispatching M7 twice...')
    task_id1 = generate_visual_analysis_task.delay(project_id, asset_id, provider_name='antigravity')
    task_id2 = generate_visual_analysis_task.delay(project_id, asset_id, provider_name='antigravity')

    log(f'Deliveries dispatched. task1: {task_id1.id}, task2: {task_id2.id}')
    
    r1 = task_id1.get(timeout=30)
    r2 = task_id2.get(timeout=30)

    log(f'R1: {r1}')
    log(f'R2: {r2}')
