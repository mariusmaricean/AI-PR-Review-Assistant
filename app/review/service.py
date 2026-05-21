import httpx

from app.config import settings
from app.github.client import GitHubClient
from app.review.config_loader import (
    filter_ignored_files,
    load_review_config_from_text,
)
from app.review.line_filter import filter_findings_to_valid_lines
from app.review.orchestrator import run_review


async def process_pull_request_review(payload: dict) -> dict:
    pull_request = payload["pull_request"]
    repository = payload["repository"]

    pr_number = pull_request["number"]
    repo_name = repository["full_name"]
    branch_name = pull_request.get("head", {}).get("ref")

    github_client = GitHubClient(settings.github_token)

    config_text = await github_client.get_file_content(
        repo_full_name=repo_name,
        path=".ai-pr-review.yml",
        ref=branch_name,
    )

    review_config = load_review_config_from_text(config_text)

    files = await github_client.get_pull_request_files(
        repo_full_name=repo_name,
        pr_number=pr_number,
    )

    files = filter_ignored_files(files, review_config)

    review = await run_review(files)

    confidence_filtered_findings = [
        finding
        for finding in review.findings
        if finding.confidence >= review_config.min_confidence
    ]

    filtered_findings = filter_findings_to_valid_lines(
        confidence_filtered_findings,
        files,
    )

    filtered_findings = filtered_findings[: review_config.max_comments]

    inline_comments = [
        {
            "path": finding.file,
            "line": finding.line,
            "body": f"**{finding.title}**\n\n{finding.comment}\n\nSeverity: `{finding.severity}`",
        }
        for finding in filtered_findings
    ]

    review_body = f"""
## AI PR Review Assistant

{review.summary}

Findings: {len(filtered_findings)}
"""

    try:
        if inline_comments:
            await github_client.create_pull_request_review(
                repo_full_name=repo_name,
                pr_number=pr_number,
                body=review_body,
                comments=inline_comments,
            )
            published_as = "inline_review"
        else:
            await github_client.post_pull_request_comment(
                repo_full_name=repo_name,
                pr_number=pr_number,
                body=f"{review_body}\n\nNo high-confidence inline findings.",
            )
            published_as = "summary_comment"

    except httpx.HTTPStatusError:
        await github_client.post_pull_request_comment(
            repo_full_name=repo_name,
            pr_number=pr_number,
            body=f"{review_body}\n\nInline review failed, posted fallback summary.",
        )
        published_as = "fallback_summary_comment"

    return {
        "status": "completed",
        "repository": repo_name,
        "pull_request": pr_number,
        "changed_files": len(files),
        "findings": len(filtered_findings),
        "published_as": published_as,
    }
