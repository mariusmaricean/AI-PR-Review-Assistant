from app.ai.client import generate_pr_review
from app.review.chunker import chunk_files
from app.review.context_builder import build_review_context
from app.review.models import ReviewFinding, ReviewResult


async def run_review(files: list[dict]) -> ReviewResult:
    chunks = chunk_files(files)

    all_findings: list[ReviewFinding] = []

    summaries = []

    for chunk in chunks:
        review_context = build_review_context(chunk)

        result = await generate_pr_review(review_context)

        summaries.append(result.summary)

        all_findings.extend(result.findings)

    return ReviewResult(
        summary="\n".join(summaries),
        findings=all_findings,
    )
