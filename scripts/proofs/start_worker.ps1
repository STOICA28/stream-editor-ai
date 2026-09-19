
$env:PYTHONPATH="apps/worker/src;packages/models/src;packages/storage/src;packages/analysis/src;packages/rendering/src;apps/api/src;packages/contracts/src;packages/editorial/src;packages/narrative/src;packages/media/src;packages/research/src"
$env:CELERY_BROKER_URL="sqla+sqlite:///broker.sqlite"
$env:CELERY_RESULT_BACKEND="db+sqlite:///backend.sqlite"
uv run celery -A stream_editor.worker.celery_app worker --loglevel=info -P threads -c 2

