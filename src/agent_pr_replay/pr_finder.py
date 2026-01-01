"""Find merged PRs from GitHub repositories using gh CLI."""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class PR:
    """Represents a merged pull request."""

    number: int
    title: str
    url: str
    merge_commit: str
    base_commit: str
    merged_at: str
    author: str
    files_changed: int
    additions: int
    deletions: int
    body: str | None = None

    @classmethod
    def from_gh_json(cls, data: dict[str, Any]) -> "PR":
        """Create a PR from GitHub API JSON response."""
        return cls(
            number=data["number"],
            title=data["title"],
            url=data["url"],
            merge_commit=data.get("mergeCommit", {}).get("oid", ""),
            base_commit=data.get("baseRefOid", ""),
            merged_at=data.get("mergedAt", ""),
            author=data.get("author", {}).get("login", "unknown"),
            files_changed=data.get("changedFiles", 0),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            body=data.get("body"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "number": self.number,
            "title": self.title,
            "url": self.url,
            "merge_commit": self.merge_commit,
            "base_commit": self.base_commit,
            "merged_at": self.merged_at,
            "author": self.author,
            "files_changed": self.files_changed,
            "additions": self.additions,
            "deletions": self.deletions,
            "body": self.body,
        }

    def summary(self) -> str:
        """Return a one-line summary of the PR."""
        return f"#{self.number}: {self.title} (+{self.additions}/-{self.deletions})"


def check_gh_cli() -> bool:
    """Check if the gh CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def find_merged_prs(owner: str, repo: str, days: int, limit: int = 100) -> list[PR]:
    """Find merged PRs in a GitHub repository.

    Args:
        owner: Repository owner (e.g., "django")
        repo: Repository name (e.g., "django")
        days: Number of days to look back
        limit: Maximum number of PRs to return

    Returns:
        List of PR objects for merged PRs in the time range
    """
    if not check_gh_cli():
        raise RuntimeError(
            "GitHub CLI (gh) is not installed or not authenticated. "
            "Please install gh and run 'gh auth login'."
        )

    # Calculate the date threshold
    since_date = datetime.now() - timedelta(days=days)
    since_str = since_date.strftime("%Y-%m-%d")

    # Use gh CLI to query merged PRs
    # We use the search API which allows filtering by merged date
    query = f"repo:{owner}/{repo} is:pr is:merged merged:>={since_str}"

    cmd = [
        "gh",
        "api",
        "-X",
        "GET",
        "/search/issues",
        "-f",
        f"q={query}",
        "-f",
        "sort=updated",
        "-f",
        "order=desc",
        "-f",
        f"per_page={min(limit, 100)}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    search_data = json.loads(result.stdout)

    prs: list[PR] = []
    for item in search_data.get("items", []):
        # Get detailed PR info including merge commit
        pr_number = item["number"]
        pr_cmd = [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--repo",
            f"{owner}/{repo}",
            "--json",
            "number,title,url,mergeCommit,baseRefOid,mergedAt,author,"
            "changedFiles,additions,deletions,body",
        ]
        pr_result = subprocess.run(pr_cmd, capture_output=True, text=True, check=True)
        pr_data = json.loads(pr_result.stdout)
        prs.append(PR.from_gh_json(pr_data))

    return prs


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Get the diff for a specific PR.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: PR number

    Returns:
        The PR diff as a string
    """
    cmd = [
        "gh",
        "pr",
        "diff",
        str(pr_number),
        "--repo",
        f"{owner}/{repo}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout
