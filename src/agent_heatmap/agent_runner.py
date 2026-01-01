"""Run Claude agent on worktrees to analyze code changes."""

import json
import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_heatmap.pr_finder import PR, get_pr_diff
from agent_heatmap.pr_selector import get_claude_path


@dataclass
class AgentRun:
    """Result of running the agent on a PR."""

    pr: PR
    session_id: str
    human_prompt: str
    worktree_path: Path
    success: bool
    error: str | None = None
    result: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pr": self.pr.to_dict(),
            "session_id": self.session_id,
            "human_prompt": self.human_prompt,
            "worktree_path": str(self.worktree_path),
            "success": self.success,
            "error": self.error,
            "result": self.result,
        }


def generate_human_prompt(owner: str, repo: str, pr: PR) -> str:
    """Generate a human-like prompt from a PR diff.

    Uses Claude to reverse-engineer what a human might have asked for.
    """
    # Get the PR diff
    try:
        diff = get_pr_diff(owner, repo, pr.number)
    except Exception as e:
        # If we can't get the diff, use just the PR info
        diff = f"(Could not retrieve diff: {e})"

    # Truncate diff if too long
    # ~200k token context window at ~3 chars/token = 600k chars
    max_diff_len = 100000
    if len(diff) > max_diff_len:
        diff = diff[:max_diff_len] + "\n\n... (diff truncated)"

    prompt = f"""You are helping to reverse-engineer what a human might have asked for.

Given this merged PR, write a concise prompt a human might have used to request this change.
The prompt should be:
1. Natural and conversational
2. Focused on the end goal, not implementation details
3. Similar to how a developer would describe the task to a colleague

PR Title: {pr.title}
PR Author: {pr.author}
Files Changed: {pr.files_changed}
Additions: {pr.additions}
Deletions: {pr.deletions}

PR Description:
{pr.body or "(no description)"}

Diff:
{diff}

Return ONLY the human prompt, nothing else. Keep it to 1-3 sentences."""

    claude_path = get_claude_path()
    cmd = [
        claude_path,
        "-p",
        "--model",
        "sonnet",
        prompt,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def run_agent_on_pr(
    worktree_path: Path,
    human_prompt: str,
    session_id: str | None = None,
    model: str | None = None,
) -> tuple[str, str]:
    """Run Claude agent on a worktree with the given prompt.

    Args:
        worktree_path: Path to the worktree
        human_prompt: The prompt to give to Claude
        session_id: Optional session ID (generated if not provided)
        model: Optional model name override (defaults to "sonnet")

    Returns:
        Tuple of (session_id, result_text)
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    # Define allowed tools for the agent
    # Include core tools plus common bash commands the agent might need
    allowed_tools = ",".join(
        [
            # Core file tools
            "Read",
            "Glob",
            "Grep",
            "Edit",
            "Write",
            # Task management
            "TodoWrite",
            "Task",
            # Safe bash commands
            "Bash(find:*)",
            "Bash(ls:*)",
            "Bash(cat:*)",
            "Bash(head:*)",
            "Bash(tail:*)",
            "Bash(wc:*)",
            "Bash(jq:*)",
            "Bash(tree:*)",
            "Bash(grep:*)",
            "Bash(rg:*)",
            # Git commands
            "Bash(git diff:*)",
            "Bash(git log:*)",
            "Bash(git show:*)",
            "Bash(git status:*)",
            "Bash(git branch:*)",
            # Build commands (common in repos)
            "Bash(cargo:*)",
            "Bash(npm:*)",
            "Bash(pip:*)",
            "Bash(make:*)",
            "Bash(python:*)",
            "Bash(pytest:*)",
            "Bash(mkdir:*)",
        ]
    )

    claude_path = get_claude_path()
    cmd = [
        claude_path,
        "-p",
        "--model",
        model or "sonnet",
        "--session-id",
        session_id,
        "--allowedTools",
        allowed_tools,
        "--output-format",
        "json",
        human_prompt,
    ]

    # Run from the worktree directory
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
        cwd=worktree_path,
        env={**os.environ, "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": "1"},
    )

    response = json.loads(result.stdout)
    result_text = response.get("result", "")

    return session_id, result_text


def get_session_path(worktree_path: Path, session_id: str) -> Path:
    """Get the path to a session file in ~/.claude/projects/.

    Args:
        worktree_path: Path to the worktree
        session_id: The session ID

    Returns:
        Path to the session JSONL file
    """
    # Claude encodes paths by replacing / with -
    # The leading slash becomes a leading dash which is preserved
    encoded_path = str(worktree_path.resolve()).replace("/", "-")

    claude_dir = Path.home() / ".claude" / "projects" / encoded_path
    return claude_dir / f"{session_id}.jsonl"
