import asyncio

from app.review.service import process_pull_request_review
from app.worker import celery_app


@celery_app.task(name="review_pull_request")
def review_pull_request(payload: dict):
    return asyncio.run(process_pull_request_review(payload))
