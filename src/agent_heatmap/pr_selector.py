"""Select representative PRs using Claude LLM."""

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from agent_heatmap.pr_finder import PR


def get_claude_path() -> str:
    """Get the path to the claude CLI executable."""
    # Check if claude is in PATH
    try:
        result = subprocess.run(
            ["which", "claude"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return "claude"
    except FileNotFoundError:
        pass

    # Check common installation locations
    common_paths = [
        Path.home() / ".claude" / "local" / "node_modules" / ".bin" / "claude",
        Path("/usr/local/bin/claude"),
        Path("/usr/bin/claude"),
    ]

    for path in common_paths:
        if path.exists():
            return str(path)

    # Check if CLAUDE_PATH env var is set
    if "CLAUDE_PATH" in os.environ:
        return os.environ["CLAUDE_PATH"]

    return "claude"  # Fall back to hoping it's in PATH


def check_claude_cli() -> bool:
    """Check if the claude CLI is installed."""
    claude_path = get_claude_path()
    try:
        result = subprocess.run(
            [claude_path, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def select_representative_prs(
    prs: list[PR],
    k: int,
    instructions: str | None = None,
) -> list[PR]:
    """Select representative PRs using Claude as an LLM.

    Args:
        prs: List of all merged PRs
        k: Number of PRs to select
        instructions: Optional custom instructions for selection

    Returns:
        List of k selected PRs (or fewer if not enough available)
    """
    if not check_claude_cli():
        raise RuntimeError("Claude CLI is not installed. Please install claude and authenticate.")

    if len(prs) <= k:
        return prs

    # Build the prompt for Claude
    pr_summaries = []
    for pr in prs:
        pr_summaries.append(
            {
                "number": pr.number,
                "title": pr.title,
                "author": pr.author,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "files_changed": pr.files_changed,
                "body": (pr.body[:500] + "...") if pr.body and len(pr.body) > 500 else pr.body,
            }
        )

    custom_instructions = ""
    if instructions:
        custom_instructions = f"\n\nAdditional selection criteria: {instructions}"

    prompt = f"""Analyze merged PRs and select the most representative ones for analysis.

Select exactly {k} PRs that are:
1. Diverse - covering different parts of the codebase or types of changes
2. Non-trivial - meaningful changes (not just typo fixes or version bumps)
3. Interesting - good examples of real-world code changes{custom_instructions}

Here are the PRs:

{json.dumps(pr_summaries, indent=2)}

Return your selection as a JSON object with this exact format:
{{
  "selected_prs": [<list of PR numbers as integers>],
  "reasoning": "<brief explanation of why you selected these PRs>"
}}

Return ONLY the JSON object, no other text."""

    # Call Claude CLI
    claude_path = get_claude_path()
    cmd = [
        claude_path,
        "-p",
        "--model",
        "sonnet",
        "--output-format",
        "json",
        prompt,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Parse Claude's response
    response = json.loads(result.stdout)
    result_text = response.get("result", "")

    # Try to extract JSON from the response
    selection = parse_selection_response(result_text)

    # Map selected numbers back to PR objects
    selected_numbers = set(selection.get("selected_prs", []))
    selected_prs = [pr for pr in prs if pr.number in selected_numbers]

    return selected_prs


def parse_selection_response(response_text: str) -> dict[str, Any]:
    """Parse the selection response from Claude.

    Handles cases where Claude might include extra text around the JSON.
    """
    # First try direct JSON parse
    try:
        return dict(json.loads(response_text))
    except json.JSONDecodeError:
        pass

    # Try to find JSON in the response
    import re

    json_match = re.search(r"\{[^{}]*\"selected_prs\"[^{}]*\}", response_text, re.DOTALL)
    if json_match:
        try:
            return dict(json.loads(json_match.group()))
        except json.JSONDecodeError:
            pass

    # Try to find just the array of numbers
    array_match = re.search(r"\[[\d,\s]+\]", response_text)
    if array_match:
        try:
            numbers = json.loads(array_match.group())
            return {"selected_prs": numbers, "reasoning": "Extracted from response"}
        except json.JSONDecodeError:
            pass

    # If all else fails, return empty selection
    return {"selected_prs": [], "reasoning": "Failed to parse response"}
