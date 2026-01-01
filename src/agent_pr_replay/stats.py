"""Statistics computation and display for agent analysis."""

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent_pr_replay.database import Database


def normalize_path_to_repo_root(path: str) -> str:
    """Normalize a path from worktree to repo-relative path.

    Worktree paths look like:
    /tmp/agent-pr-replay-worktrees-xxx/pr-12345/src/file.py

    This function extracts just the repo-relative part:
    src/file.py
    """
    # Pattern: anything/pr-NNNNN/rest -> rest
    match = re.search(r"/pr-\d+/(.+)$", path)
    if match:
        return match.group(1)

    # If no worktree pattern, return as-is (might already be normalized)
    return path


@dataclass
class Stats:
    """Statistics computed from analysis sessions."""

    repo: str = ""
    total_sessions: int = 0
    successful_sessions: int = 0
    total_tool_calls: int = 0

    # File statistics
    files_read: Counter[str] = field(default_factory=Counter)
    files_edited: Counter[str] = field(default_factory=Counter)

    # Command statistics
    bash_commands: Counter[str] = field(default_factory=Counter)
    tool_usage: Counter[str] = field(default_factory=Counter)

    # Directory heatmap (how often each directory was accessed)
    directory_heatmap: Counter[str] = field(default_factory=Counter)

    # Diff comparison stats
    sessions_with_diff: int = 0
    total_actual_additions: int = 0
    total_actual_deletions: int = 0
    total_claude_additions: int = 0
    total_claude_deletions: int = 0
    files_only_in_actual_count: int = 0
    files_only_in_claude_count: int = 0
    files_in_both_count: int = 0

    # Analysis descriptions (snippets from each session)
    analysis_snippets: list[tuple[str, str]] = field(default_factory=list)  # (pr_title, snippet)


def compute_stats(db: Database) -> Stats:
    """Compute statistics from a database of analysis sessions."""
    stats = Stats(
        repo=f"{db.repo_owner}/{db.repo_name}",
        total_sessions=len(db.sessions),
    )

    for session in db.sessions:
        if session.success:
            stats.successful_sessions += 1

        if session.session_data:
            sd = session.session_data
            stats.total_tool_calls += len(sd.tool_calls)

            # Count file reads (normalized to repo root)
            for file_path in sd.files_read:
                normalized = normalize_path_to_repo_root(file_path)
                stats.files_read[normalized] += 1
                # Also count directory access
                dir_path = str(Path(normalized).parent)
                stats.directory_heatmap[dir_path] += 1

            # Count file edits (normalized to repo root)
            for file_path in sd.files_edited:
                normalized = normalize_path_to_repo_root(file_path)
                stats.files_edited[normalized] += 1
                dir_path = str(Path(normalized).parent)
                stats.directory_heatmap[dir_path] += 1

            # Count bash commands (normalize to get patterns)
            for cmd in sd.bash_commands:
                # Normalize command to just the base command
                normalized = normalize_command(cmd)
                stats.bash_commands[normalized] += 1

            # Count tool usage
            for tc in sd.tool_calls:
                stats.tool_usage[tc.name] += 1

        # Diff comparison stats
        if session.diff_comparison:
            dc = session.diff_comparison
            stats.sessions_with_diff += 1
            stats.total_actual_additions += dc.actual_total_additions
            stats.total_actual_deletions += dc.actual_total_deletions
            stats.total_claude_additions += dc.claude_total_additions
            stats.total_claude_deletions += dc.claude_total_deletions
            stats.files_only_in_actual_count += len(dc.files_only_in_actual)
            stats.files_only_in_claude_count += len(dc.files_only_in_claude)
            stats.files_in_both_count += len(dc.files_in_both)

            # Extract analysis snippet (first ~200 chars)
            if dc.analysis_description:
                snippet = dc.analysis_description[:300]
                if len(dc.analysis_description) > 300:
                    snippet += "..."
                stats.analysis_snippets.append((session.pr_title, snippet))

    return stats


def normalize_command(cmd: str) -> str:
    """Normalize a bash command to extract the pattern."""
    cmd = cmd.strip()

    # Handle glob: and grep: prefixes from session_parser
    if cmd.startswith("glob: "):
        return "glob pattern"
    if cmd.startswith("grep: "):
        return "grep search"

    # Extract base command
    parts = cmd.split()
    if not parts:
        return cmd

    base_cmd = parts[0]

    # For common commands, include first argument type
    if base_cmd in ("find", "ls", "cat", "head", "tail", "tree"):
        return base_cmd
    if base_cmd == "git":
        if len(parts) > 1:
            return f"git {parts[1]}"
        return "git"

    return base_cmd


def print_stats(stats: Stats, console: Console | None = None) -> None:
    """Print statistics in a formatted way."""
    if console is None:
        console = Console()

    # Header
    console.print()
    console.print(Panel.fit(f"[bold blue]Agent PR Replay Stats[/bold blue]\n{stats.repo}"))
    console.print()

    # Summary
    console.print(f"[bold]Sessions:[/bold] {stats.successful_sessions}/{stats.total_sessions}")
    console.print(f"[bold]Total Tool Calls:[/bold] {stats.total_tool_calls}")
    console.print()

    # Tool usage table
    if stats.tool_usage:
        table = Table(title="Tool Usage")
        table.add_column("Tool", style="cyan")
        table.add_column("Count", justify="right", style="green")

        for tool, count in stats.tool_usage.most_common(10):
            table.add_row(tool, str(count))

        console.print(table)
        console.print()

    # Top bash commands
    if stats.bash_commands:
        table = Table(title="Top Commands/Patterns")
        table.add_column("Command", style="cyan")
        table.add_column("Count", justify="right", style="green")

        for cmd, count in stats.bash_commands.most_common(15):
            table.add_row(cmd, str(count))

        console.print(table)
        console.print()

    # Most read files
    if stats.files_read:
        table = Table(title="Most Read Files")
        table.add_column("File", style="cyan", max_width=60)
        table.add_column("Reads", justify="right", style="green")

        for file_path, count in stats.files_read.most_common(15):
            # Shorten path for display
            display_path = file_path
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            table.add_row(display_path, str(count))

        console.print(table)
        console.print()

    # Most edited files
    if stats.files_edited:
        table = Table(title="Most Edited Files")
        table.add_column("File", style="cyan", max_width=60)
        table.add_column("Edits", justify="right", style="yellow")

        for file_path, count in stats.files_edited.most_common(10):
            display_path = file_path
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            table.add_row(display_path, str(count))

        console.print(table)
        console.print()

    # Directory heatmap
    if stats.directory_heatmap:
        table = Table(title="Directory Heatmap (Most Accessed)")
        table.add_column("Directory", style="cyan", max_width=60)
        table.add_column("Access Count", justify="right", style="magenta")

        for dir_path, count in stats.directory_heatmap.most_common(15):
            display_path = dir_path
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            table.add_row(display_path, str(count))

        console.print(table)
        console.print()


def stats_to_dict(stats: Stats) -> dict[str, Any]:
    """Convert stats to a dictionary for JSON export."""
    return {
        "repo": stats.repo,
        "total_sessions": stats.total_sessions,
        "successful_sessions": stats.successful_sessions,
        "total_tool_calls": stats.total_tool_calls,
        "tool_usage": dict(stats.tool_usage.most_common()),
        "top_commands": dict(stats.bash_commands.most_common(20)),
        "top_files_read": dict(stats.files_read.most_common(20)),
        "top_files_edited": dict(stats.files_edited.most_common(20)),
        "directory_heatmap": dict(stats.directory_heatmap.most_common(20)),
    }


def format_stats_text(stats: Stats) -> str:
    """Format stats as plain text for piping."""
    lines = []

    # Header
    lines.append(f"Agent PR Replay Stats: {stats.repo}")
    lines.append("=" * 50)
    lines.append("")

    # Summary
    lines.append(f"Sessions: {stats.successful_sessions}/{stats.total_sessions}")
    lines.append(f"Total Tool Calls: {stats.total_tool_calls}")
    lines.append("")

    # Diff Comparison Summary
    if stats.sessions_with_diff > 0:
        lines.append("Diff Comparison (Actual PR vs Claude):")
        lines.append(f"  Sessions with diff data: {stats.sessions_with_diff}")
        lines.append(
            f"  Actual PR total: +{stats.total_actual_additions}/-{stats.total_actual_deletions}"
        )
        lines.append(
            f"  Claude total:    +{stats.total_claude_additions}/-{stats.total_claude_deletions}"
        )
        lines.append(f"  Files only in actual PRs: {stats.files_only_in_actual_count}")
        lines.append(f"  Files only in Claude: {stats.files_only_in_claude_count}")
        lines.append(f"  Files in both: {stats.files_in_both_count}")
        lines.append("")

    # Tool usage
    if stats.tool_usage:
        lines.append("Tool Usage:")
        for tool, count in stats.tool_usage.most_common(10):
            lines.append(f"  {tool}: {count}")
        lines.append("")

    # Top commands
    if stats.bash_commands:
        lines.append("Top Commands/Patterns:")
        for cmd, count in stats.bash_commands.most_common(15):
            lines.append(f"  {cmd}: {count}")
        lines.append("")

    # Most read files
    if stats.files_read:
        lines.append("Most Read Files:")
        for path, count in stats.files_read.most_common(15):
            lines.append(f"  {path}: {count}")
        lines.append("")

    # Most edited files
    if stats.files_edited:
        lines.append("Most Edited Files:")
        for path, count in stats.files_edited.most_common(10):
            lines.append(f"  {path}: {count}")
        lines.append("")

    # Directory heatmap
    if stats.directory_heatmap:
        lines.append("Directory Heatmap:")
        for path, count in stats.directory_heatmap.most_common(15):
            lines.append(f"  {path}: {count}")
        lines.append("")

    # Analysis snippets
    if stats.analysis_snippets:
        lines.append("Analysis Snippets:")
        lines.append("-" * 50)
        for pr_title, snippet in stats.analysis_snippets:
            lines.append(f"PR: {pr_title}")
            # Indent the snippet
            for line in snippet.split("\n"):
                lines.append(f"  {line}")
            lines.append("")

    return "\n".join(lines)
