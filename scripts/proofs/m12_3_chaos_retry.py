import os
os.environ["CELERY_BROKER_URL"] = "sqla+sqlite:///broker.sqlite"
os.environ["CELERY_RESULT_BACKEND"] = "db+sqlite:///backend.sqlite"
from stream_editor.worker.tasks.chaos import retryable_failing_task
import sys

def log(msg):
    print(msg)
    sys.stdout.flush()

if __name__ == '__main__':
    log('Dispatching retryable task...')
    task = retryable_failing_task.delay()
    result = task.get(timeout=30)
    log(f'Final result: {result}')
