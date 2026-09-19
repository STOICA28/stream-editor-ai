import os

from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "sqla+sqlite:///broker.sqlite")
backend_url = os.environ.get("CELERY_RESULT_BACKEND", "db+sqlite:///backend.sqlite")
app = Celery('stream_editor_worker', broker=broker_url, backend=backend_url, include=['stream_editor.worker.tasks.pipeline', 'stream_editor.worker.tasks.chaos'])

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
