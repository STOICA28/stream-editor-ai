from celery import shared_task

@shared_task(bind=True, max_retries=3)
def retryable_failing_task(self):
    print(f"Attempt {self.request.retries + 1}")
    if self.request.retries < 2:
        raise self.retry(exc=Exception("Simulated failure"), countdown=1)
    return 'Success after 3 attempts'
