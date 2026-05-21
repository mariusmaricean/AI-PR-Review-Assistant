import asyncio

from app.ai.client import generate_pr_review
from app.review.chunker import chunk_files
from app.review.context_builder import build_review_context
from app.review.models import ReviewResult


async def review_chunk(chunk: list[dict]):
    context = build_review_context(chunk)

    return await generate_pr_review(context)


async def run_review(files: list[dict]) -> ReviewResult:
    chunks = chunk_files(files)

    results = await asyncio.gather(
        *[review_chunk(chunk) for chunk in chunks]
    )

    summaries = []
    findings = []

    for result in results:
        summaries.append(result.summary)
        findings.extend(result.findings)

    return ReviewResult(
        summary="\n".join(summaries),
        findings=findings,
    )
