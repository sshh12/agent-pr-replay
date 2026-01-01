"""Diff comparison and LLM analysis for agent output vs actual PR."""

import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_heatmap.pr_selector import get_claude_path

logger = logging.getLogger(__name__)


@dataclass
class FileDiffStats:
    """Statistics for a single file's diff."""

    file_path: str
    additions: int
    deletions: int
    status: str  # "added", "modified", "deleted"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "additions": self.additions,
            "deletions": self.deletions,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileDiffStats":
        """Create from dictionary."""
        return cls(
            file_path=data["file_path"],
            additions=data["additions"],
            deletions=data["deletions"],
            status=data["status"],
        )


@dataclass
class DiffComparison:
    """Comparison between actual PR diff and Claude's generated diff."""

    # Actual PR diff data
    actual_diff_raw: str
    actual_files: list[FileDiffStats] = field(default_factory=list)
    actual_total_additions: int = 0
    actual_total_deletions: int = 0

    # Claude's diff data
    claude_diff_raw: str = ""
    claude_files: list[FileDiffStats] = field(default_factory=list)
    claude_total_additions: int = 0
    claude_total_deletions: int = 0

    # LLM analysis (always populated)
    analysis_description: str = ""
    suggested_claude_md: str = ""

    # Derived properties (not stored, computed on demand)
    @property
    def actual_file_paths(self) -> set[str]:
        return {f.file_path for f in self.actual_files}

    @property
    def claude_file_paths(self) -> set[str]:
        return {f.file_path for f in self.claude_files}

    @property
    def files_only_in_actual(self) -> list[str]:
        return sorted(self.actual_file_paths - self.claude_file_paths)

    @property
    def files_only_in_claude(self) -> list[str]:
        return sorted(self.claude_file_paths - self.actual_file_paths)

    @property
    def files_in_both(self) -> list[str]:
        return sorted(self.actual_file_paths & self.claude_file_paths)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "actual_diff_raw": self.actual_diff_raw,
            "actual_files": [f.to_dict() for f in self.actual_files],
            "actual_total_additions": self.actual_total_additions,
            "actual_total_deletions": self.actual_total_deletions,
            "claude_diff_raw": self.claude_diff_raw,
            "claude_files": [f.to_dict() for f in self.claude_files],
            "claude_total_additions": self.claude_total_additions,
            "claude_total_deletions": self.claude_total_deletions,
            "analysis_description": self.analysis_description,
            "suggested_claude_md": self.suggested_claude_md,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiffComparison":
        """Create from dictionary."""
        return cls(
            actual_diff_raw=data.get("actual_diff_raw", ""),
            actual_files=[FileDiffStats.from_dict(f) for f in data.get("actual_files", [])],
            actual_total_additions=data.get("actual_total_additions", 0),
            actual_total_deletions=data.get("actual_total_deletions", 0),
            claude_diff_raw=data.get("claude_diff_raw", ""),
            claude_files=[FileDiffStats.from_dict(f) for f in data.get("claude_files", [])],
            claude_total_additions=data.get("claude_total_additions", 0),
            claude_total_deletions=data.get("claude_total_deletions", 0),
            analysis_description=data.get("analysis_description", ""),
            suggested_claude_md=data.get("suggested_claude_md", ""),
        )


def parse_unified_diff(diff_text: str) -> tuple[list[FileDiffStats], int, int]:
    """Parse a unified diff and extract per-file statistics.

    Args:
        diff_text: Raw unified diff text

    Returns:
        Tuple of (file_stats_list, total_additions, total_deletions)
    """
    if not diff_text.strip():
        return [], 0, 0

    file_stats: list[FileDiffStats] = []
    total_adds = 0
    total_dels = 0

    # Pattern to match diff headers: diff --git a/path b/path
    diff_header_pattern = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)

    # Split by diff headers
    parts = diff_header_pattern.split(diff_text)

    # parts[0] is anything before first diff header (usually empty)
    # Then triplets of (old_path, new_path, content)
    i = 1
    while i + 2 < len(parts):
        old_path = parts[i]
        new_path = parts[i + 1]
        content = parts[i + 2] if i + 2 < len(parts) else ""
        i += 3

        # Count additions and deletions in this file's diff
        adds = 0
        dels = 0
        for line in content.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                adds += 1
            elif line.startswith("-") and not line.startswith("---"):
                dels += 1

        # Determine file status
        if "new file mode" in content:
            status = "added"
            file_path = new_path
        elif "deleted file mode" in content:
            status = "deleted"
            file_path = old_path
        elif old_path != new_path:
            status = "renamed"
            file_path = new_path
        else:
            status = "modified"
            file_path = new_path

        file_stats.append(
            FileDiffStats(
                file_path=file_path,
                additions=adds,
                deletions=dels,
                status=status,
            )
        )
        total_adds += adds
        total_dels += dels

    return file_stats, total_adds, total_dels


def capture_worktree_changes(worktree_path: Path) -> str:
    """Capture all changes in a worktree (staged, unstaged, and untracked).

    Args:
        worktree_path: Path to the git worktree

    Returns:
        Combined diff string of all changes
    """
    try:
        # Get diff of all tracked file changes (staged + unstaged)
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True,
        )
        tracked_diff = result.stdout

        # Get list of untracked files
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True,
        )

        untracked_diff = ""
        for line in result.stdout.strip().split("\n"):
            if line.startswith("??"):
                # Untracked file
                file_path = line[3:].strip()
                full_path = worktree_path / file_path

                if full_path.is_file():
                    try:
                        content = full_path.read_text()
                        # Generate synthetic diff for new file
                        lines = content.split("\n")
                        diff_lines = [f"+{line}" for line in lines]
                        untracked_diff += f"\ndiff --git a/{file_path} b/{file_path}\n"
                        untracked_diff += "new file mode 100644\n"
                        untracked_diff += "--- /dev/null\n"
                        untracked_diff += f"+++ b/{file_path}\n"
                        untracked_diff += f"@@ -0,0 +1,{len(lines)} @@\n"
                        untracked_diff += "\n".join(diff_lines)
                    except Exception as e:
                        logger.warning(f"Could not read untracked file {file_path}: {e}")

        return tracked_diff + untracked_diff

    except subprocess.CalledProcessError as e:
        logger.warning(f"git diff failed: {e}")
        return ""
    except Exception as e:
        logger.error(f"Failed to capture worktree changes: {e}")
        return ""


def compare_diffs(actual_diff_raw: str, claude_diff_raw: str) -> DiffComparison:
    """Build a comparison between actual PR diff and Claude's diff.

    Args:
        actual_diff_raw: The raw diff from the actual merged PR
        claude_diff_raw: The raw diff of changes Claude made

    Returns:
        DiffComparison with parsed stats (LLM fields empty)
    """
    actual_files, actual_adds, actual_dels = parse_unified_diff(actual_diff_raw)
    claude_files, claude_adds, claude_dels = parse_unified_diff(claude_diff_raw)

    return DiffComparison(
        actual_diff_raw=actual_diff_raw,
        actual_files=actual_files,
        actual_total_additions=actual_adds,
        actual_total_deletions=actual_dels,
        claude_diff_raw=claude_diff_raw,
        claude_files=claude_files,
        claude_total_additions=claude_adds,
        claude_total_deletions=claude_dels,
    )


def analyze_with_llm(
    comparison: DiffComparison,
    pr_title: str,
    human_prompt: str,
    model: str = "sonnet",
) -> tuple[str, str]:
    """Use LLM to analyze differences and suggest improvements.

    Args:
        comparison: The diff comparison data
        pr_title: PR title for context
        human_prompt: The prompt given to Claude
        model: Model to use for analysis

    Returns:
        Tuple of (analysis_description, suggested_claude_md)
    """
    # Truncate diffs if too large
    # ~200k token context window at ~3 chars/token = 600k chars
    # Allow 100k per diff (200k total), leaving room for prompt and response
    max_diff_len = 100000
    actual_diff = comparison.actual_diff_raw
    claude_diff = comparison.claude_diff_raw

    if len(actual_diff) > max_diff_len:
        actual_diff = actual_diff[:max_diff_len] + "\n\n... (diff truncated)"
    if len(claude_diff) > max_diff_len:
        claude_diff = claude_diff[:max_diff_len] + "\n\n... (diff truncated)"

    prompt = f"""Analyze the differences between an actual merged PR and what Claude Code \
generated when given the same task.

## Context
PR Title: {pr_title}
Prompt given to Claude: {human_prompt}

## Actual PR Diff (what the human did):
```diff
{actual_diff}
```

## Claude's Diff (what the agent produced):
```diff
{claude_diff}
```

Please provide:
1. A description (2-3 paragraphs) of what was different between the human's changes and \
Claude's changes, and why Claude might have approached it differently
2. Specific suggestions for CLAUDE.md instructions that could help Claude better match \
human patterns in similar tasks

For the CLAUDE.md suggestions, follow these best practices:

**Format:**
- Start with a descriptive ## H2 section header relevant to the pattern observed
- Use concise bullet points (1-2 sentences max)
- Include code patterns or file:line references where relevant

**Content principles:**
- Focus on guardrails/corrections, not comprehensive manuals
- Keep suggestions universally applicable to similar tasks
- When saying "never X", always provide an alternative "prefer Y"
- Use pointers to files (e.g., "see path/to/file:line") not code copies
- Suggest ways to simplify tooling, not just documentation patches

Example format:
```markdown
## [Descriptive Section Name]

- [Pattern]: [Concise guidance on how to apply it]
- Never [anti-pattern]; prefer [better approach]
- [Topic]: [Specific actionable guidance]
- For [complex topic], see `path/to/relevant/file:line`
```

Return JSON:
{{
  "analysis": "Description of differences...",
  "claude_md_suggestions": "## Section Header\\n\\n- Bullet point guidance..."
}}"""

    try:
        claude_path = get_claude_path()
        cmd = [
            claude_path,
            "-p",
            "--model",
            model,
            "--output-format",
            "json",
            prompt,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse the JSON response
        response = json.loads(result.stdout)
        result_text = response.get("result", "")

        # Try to extract JSON from the result
        # The result might be wrapped in markdown code blocks
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if json_match:
            parsed = json.loads(json_match.group())
            analysis = parsed.get("analysis", "Analysis unavailable")
            suggestions = parsed.get("claude_md_suggestions", "")
            return analysis, suggestions

        # If no JSON found, return the raw result as analysis
        return result_text, ""

    except subprocess.CalledProcessError as e:
        logger.warning(f"LLM analysis failed: {e}")
        return "Analysis unavailable - LLM call failed", ""
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM response: {e}")
        return "Analysis unavailable - parse error", ""
    except Exception as e:
        logger.error(f"Unexpected error in LLM analysis: {e}")
        return f"Analysis unavailable - {e}", ""
