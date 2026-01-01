"""CLI entrypoint for agent-pr-replay."""

import sys
import tempfile
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn
from rich.table import Table

if TYPE_CHECKING:
    from git import Repo

from agent_pr_replay.agent_runner import (
    generate_human_prompt,
    get_session_path,
    run_agent_on_pr,
)
from agent_pr_replay.analyzer import extract_analysis_data, generate_report
from agent_pr_replay.database import AnalysisSession, Database
from agent_pr_replay.diff_comparison import (
    analyze_with_llm,
    capture_worktree_changes,
    compare_diffs,
)
from agent_pr_replay.pr_finder import PR, check_gh_cli, find_merged_prs, get_pr_diff
from agent_pr_replay.pr_selector import check_claude_cli, select_representative_prs
from agent_pr_replay.repo import (
    cleanup_repo,
    cleanup_worktree,
    create_worktree,
    get_github_repo_info,
    get_repo,
    is_url,
)
from agent_pr_replay.session_parser import parse_session
from agent_pr_replay.stats import compute_stats, format_stats_text, print_stats

console = Console()


@click.group()
@click.version_option(package_name="agent-pr-replay")
def main() -> None:
    """Analyze how AI coding agents navigate and understand codebases.

    This tool runs Claude Code against merged PRs from a repository and
    collects data about how the agent explores and modifies the codebase.
    """
    pass


@main.command()
@click.argument("target")
@click.option(
    "--days",
    default=30,
    help="Number of days to look back for merged PRs.",
    show_default=True,
)
@click.option(
    "--top-k",
    default=5,
    help="Number of representative PRs to analyze.",
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("output.json"),
    help="Output file for the analysis results.",
    show_default=True,
)
@click.option(
    "--instructions",
    help="Custom instructions to guide PR selection (e.g., 'Focus on auth changes').",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without running the agent.",
)
@click.option(
    "--model",
    help="Model name to use for the agent (default: sonnet).",
)
def run(
    target: str,
    days: int,
    top_k: int,
    output: Path,
    instructions: str | None,
    dry_run: bool,
    model: str | None,
) -> None:
    """Run analysis on a repository.

    TARGET can be a GitHub URL (https://github.com/owner/repo) or a local path
    to a git repository.

    Examples:

        agent-pr-replay run https://github.com/django/django --days 30 --top-k 5

        agent-pr-replay run ./my-local-repo --days 7 --top-k 3

        agent-pr-replay run https://github.com/django/django --instructions "Focus on auth"
    """
    console.print(Panel.fit("[bold blue]Agent PR Replay[/bold blue]"))
    console.print()

    # Check prerequisites
    if not check_gh_cli():
        console.print("[red]Error:[/red] GitHub CLI (gh) is not installed or not authenticated.")
        console.print("Please install gh and run 'gh auth login'.")
        sys.exit(1)

    if not dry_run and not check_claude_cli():
        console.print("[red]Error:[/red] Claude CLI is not installed.")
        console.print("Please install claude and authenticate.")
        sys.exit(1)

    # Determine owner/repo from target
    if is_url(target):
        repo_info = get_github_repo_info(target)
        if not repo_info:
            console.print(f"[red]Error:[/red] Could not parse GitHub URL: {target}")
            sys.exit(1)
        owner, repo_name = repo_info
        console.print(f"Repository: [cyan]{owner}/{repo_name}[/cyan]")
    else:
        # For local repos, we need to get the remote URL
        console.print(f"Local repository: [cyan]{target}[/cyan]")
        try:
            repo_obj, repo_path, is_temp = get_repo(target)
            # Try to get the remote URL
            try:
                remote_url = repo_obj.remotes.origin.url
                repo_info = get_github_repo_info(remote_url)
                if repo_info:
                    owner, repo_name = repo_info
                    console.print(f"Remote: [cyan]{owner}/{repo_name}[/cyan]")
                else:
                    console.print(
                        "[red]Error:[/red] Could not determine GitHub repository from remote URL."
                    )
                    sys.exit(1)
            except Exception:
                console.print(
                    "[red]Error:[/red] Could not get remote URL. "
                    "Make sure 'origin' remote points to GitHub."
                )
                sys.exit(1)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    console.print(f"Looking back: [cyan]{days}[/cyan] days")
    console.print(f"Selecting: [cyan]{top_k}[/cyan] PRs")
    if instructions:
        console.print(f"Instructions: [cyan]{instructions}[/cyan]")
    console.print()

    # Find merged PRs
    with console.status("[bold green]Finding merged PRs..."):
        try:
            prs = find_merged_prs(owner, repo_name, days)
        except Exception as e:
            console.print(f"[red]Error finding PRs:[/red] {e}")
            sys.exit(1)

    if not prs:
        console.print("[yellow]No merged PRs found in the specified time range.[/yellow]")
        sys.exit(0)

    console.print(f"Found [green]{len(prs)}[/green] merged PRs")
    console.print()

    # Display PRs in a table
    display_prs(prs)

    if dry_run:
        console.print()
        console.print("[yellow]Dry run mode - stopping here[/yellow]")
        console.print()
        console.print("Next steps would be:")
        console.print(f"  1. Select top {top_k} representative PRs using Claude")
        console.print("  2. For each PR, create a worktree and run agent analysis")
        console.print(f"  3. Save results to {output}")
        return

    # Select representative PRs
    console.print()
    with console.status("[bold green]Selecting representative PRs with Claude..."):
        try:
            selected_prs = select_representative_prs(prs, top_k, instructions)
        except Exception as e:
            console.print(f"[red]Error selecting PRs:[/red] {e}")
            sys.exit(1)

    console.print(f"Selected [green]{len(selected_prs)}[/green] PRs for analysis:")
    for pr in selected_prs:
        console.print(f"  - #{pr.number}: {pr.title}")
    console.print()

    # Initialize database
    db = Database(
        repo_url=target,
        repo_owner=owner,
        repo_name=repo_name,
        days_analyzed=days,
    )

    # Clone repo if needed
    console.print("[bold]Setting up repository...[/bold]")
    try:
        repo_obj, repo_path, is_temp = get_repo(target)
        console.print(f"Repository path: {repo_path}")
    except Exception as e:
        console.print(f"[red]Error setting up repository:[/red] {e}")
        sys.exit(1)

    # Create temp directory for worktrees
    worktree_base = Path(tempfile.mkdtemp(prefix="agent-pr-replay-worktrees-"))

    try:
        # Process each selected PR
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for i, pr in enumerate(selected_prs, 1):
                task = progress.add_task(
                    f"[{i}/{len(selected_prs)}] Processing PR #{pr.number}...",
                    total=None,
                )

                try:
                    session = process_pr(
                        pr=pr,
                        owner=owner,
                        repo_name=repo_name,
                        repo_obj=repo_obj,
                        worktree_base=worktree_base,
                        progress=progress,
                        task_id=task,
                        model=model,
                    )
                    db.add_session(session)

                except Exception as e:
                    console.print(f"[red]Error processing PR #{pr.number}:[/red] {e}")
                    db.add_session(
                        AnalysisSession(
                            pr_number=pr.number,
                            pr_title=pr.title,
                            pr_url=pr.url,
                            human_prompt="",
                            session_id="",
                            success=False,
                            error=str(e),
                        )
                    )

                progress.remove_task(task)

        # Save results
        db.save(output)
        console.print()
        console.print(f"[green]Results saved to:[/green] {output}")

        # Show summary stats
        console.print()
        stats = compute_stats(db)
        print_stats(stats, console)

    finally:
        # Cleanup
        if is_temp:
            cleanup_repo(repo_path, is_temp)
        # Clean up worktrees directory
        import shutil

        if worktree_base.exists():
            shutil.rmtree(worktree_base)


def process_pr(
    pr: PR,
    owner: str,
    repo_name: str,
    repo_obj: "Repo",
    worktree_base: Path,
    progress: Progress,
    task_id: TaskID,
    model: str | None = None,
) -> AnalysisSession:
    """Process a single PR through the analysis pipeline."""
    # Generate human prompt from PR diff
    progress.update(task_id, description=f"PR #{pr.number}: Generating prompt...")
    human_prompt = generate_human_prompt(owner, repo_name, pr)

    # Create worktree at base commit
    progress.update(task_id, description=f"PR #{pr.number}: Creating worktree...")
    worktree_path = worktree_base / f"pr-{pr.number}"
    create_worktree(repo_obj, pr.base_commit, worktree_path)

    try:
        # Run agent on worktree
        progress.update(task_id, description=f"PR #{pr.number}: Running agent...")
        session_id = str(uuid.uuid4())
        session_id, result = run_agent_on_pr(worktree_path, human_prompt, session_id, model)

        # Capture Claude's diff BEFORE cleanup
        progress.update(task_id, description=f"PR #{pr.number}: Capturing diff...")
        claude_diff_raw = capture_worktree_changes(worktree_path)

        # Parse session data
        progress.update(task_id, description=f"PR #{pr.number}: Parsing session...")
        session_path = get_session_path(worktree_path, session_id)
        session_data = parse_session(session_path)
        session_data.claude_diff_raw = claude_diff_raw

        # Build diff comparison
        progress.update(task_id, description=f"PR #{pr.number}: Comparing diffs...")
        actual_diff_raw = get_pr_diff(owner, repo_name, pr.number)
        diff_comparison = compare_diffs(actual_diff_raw, claude_diff_raw)

        # LLM analysis
        progress.update(task_id, description=f"PR #{pr.number}: Analyzing diff...")
        analysis, suggestions = analyze_with_llm(
            diff_comparison, pr.title, human_prompt, model or "sonnet"
        )
        diff_comparison.analysis_description = analysis
        diff_comparison.suggested_claude_md = suggestions

        return AnalysisSession(
            pr_number=pr.number,
            pr_title=pr.title,
            pr_url=pr.url,
            human_prompt=human_prompt,
            session_id=session_id,
            session_data=session_data,
            diff_comparison=diff_comparison,
            success=True,
        )

    finally:
        # Cleanup worktree
        cleanup_worktree(repo_obj, worktree_path)


def display_prs(prs: list[PR]) -> None:
    """Display PRs in a formatted table."""
    table = Table(title="Merged Pull Requests")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Title", style="white", max_width=50)
    table.add_column("Author", style="green")
    table.add_column("+/-", style="yellow", justify="right")
    table.add_column("Merged", style="dim")

    for pr in prs[:20]:  # Limit to 20 for display
        changes = f"+{pr.additions}/-{pr.deletions}"
        merged_date = pr.merged_at[:10] if pr.merged_at else "?"
        table.add_row(
            str(pr.number),
            pr.title[:50] + ("..." if len(pr.title) > 50 else ""),
            pr.author,
            changes,
            merged_date,
        )

    if len(prs) > 20:
        table.add_row("...", f"({len(prs) - 20} more)", "", "", "")

    console.print(table)


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
def stats(input_file: Path) -> None:
    """Show statistics from a previous analysis run.

    INPUT_FILE is the JSON output from a previous 'agent-pr-replay run' command.
    Output can be piped to a file.

    Example:

        agent-pr-replay stats output.json > stats.txt
    """
    try:
        db = Database.load(input_file)
    except Exception as e:
        print(f"Error loading database: {e}", file=sys.stderr)
        sys.exit(1)

    stats_data = compute_stats(db)
    print(format_stats_text(stats_data))


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output path for the markdown report.",
)
def analyze(input_file: Path, output: Path | None) -> None:
    """Generate an LLM-synthesized report from analysis data.

    Uses Claude to analyze all session data and produce a comprehensive
    CLAUDE.md recommendation with impact assessment.

    Example:

        agent-pr-replay analyze output.json -o report.md
    """
    try:
        db = Database.load(input_file)
    except Exception as e:
        print(f"Error loading database: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing {db.repo_owner}/{db.repo_name}...")

    # Extract data summary
    analysis_data = extract_analysis_data(db)
    print(f"Extracted {len(analysis_data['sessions'])} sessions for analysis")

    # Generate report
    print("Running Claude to synthesize report...")
    output_path = output or Path(str(input_file.with_suffix("")) + "-report.md")

    try:
        generate_report(db, output_path)
        print(f"Report saved to: {output_path}")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
