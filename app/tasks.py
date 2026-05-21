import asyncio

from app.review.service import process_pull_request_review
from app.worker import celery_app


@celery_app.task(
    name="review_pull_request",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
)
def review_pull_request(self, payload: dict):
    return asyncio.run(process_pull_request_review(payload))
