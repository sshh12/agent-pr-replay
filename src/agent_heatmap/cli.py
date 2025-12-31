"""CLI entrypoint for agent-heatmap."""

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

from agent_heatmap.agent_runner import (
    generate_human_prompt,
    get_session_path,
    run_agent_on_pr,
)
from agent_heatmap.database import AnalysisSession, Database
from agent_heatmap.pr_finder import PR, check_gh_cli, find_merged_prs
from agent_heatmap.pr_selector import check_claude_cli, select_representative_prs
from agent_heatmap.repo import (
    cleanup_repo,
    cleanup_worktree,
    create_worktree,
    get_github_repo_info,
    get_repo,
    is_url,
)
from agent_heatmap.session_parser import parse_session
from agent_heatmap.stats import compute_stats, print_stats, stats_to_dict

console = Console()


@click.group()
@click.version_option(package_name="agent-heatmap")
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
def run(
    target: str,
    days: int,
    top_k: int,
    output: Path,
    instructions: str | None,
    dry_run: bool,
) -> None:
    """Run analysis on a repository.

    TARGET can be a GitHub URL (https://github.com/owner/repo) or a local path
    to a git repository.

    Examples:

        agent-heatmap run https://github.com/django/django --days 30 --top-k 5

        agent-heatmap run ./my-local-repo --days 7 --top-k 3

        agent-heatmap run https://github.com/django/django --instructions "Focus on auth"
    """
    console.print(Panel.fit("[bold blue]Agent Heatmap[/bold blue]"))
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
    worktree_base = Path(tempfile.mkdtemp(prefix="agent-heatmap-worktrees-"))

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
        session_id, result = run_agent_on_pr(worktree_path, human_prompt, session_id)

        # Parse session data
        progress.update(task_id, description=f"PR #{pr.number}: Parsing session...")
        session_path = get_session_path(worktree_path, session_id)
        session_data = parse_session(session_path)

        return AnalysisSession(
            pr_number=pr.number,
            pr_title=pr.title,
            pr_url=pr.url,
            human_prompt=human_prompt,
            session_id=session_id,
            session_data=session_data,
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
@click.option(
    "--json",
    "output_json",
    type=click.Path(path_type=Path),
    help="Export stats to JSON file.",
)
def stats(input_file: Path, output_json: Path | None) -> None:
    """Show statistics from a previous analysis run.

    INPUT_FILE is the JSON output from a previous 'agent-heatmap run' command.

    Example:

        agent-heatmap stats output.json

        agent-heatmap stats output.json --json stats.json
    """
    import json

    try:
        db = Database.load(input_file)
    except Exception as e:
        console.print(f"[red]Error loading database:[/red] {e}")
        sys.exit(1)

    stats_data = compute_stats(db)
    print_stats(stats_data, console)

    if output_json:
        with open(output_json, "w") as f:
            json.dump(stats_to_dict(stats_data), f, indent=2)
        console.print()
        console.print(f"[green]Stats exported to:[/green] {output_json}")


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
def analyze(input_file: Path) -> None:
    """Analyze session data from a previous run.

    INPUT_FILE is the JSON output from a previous 'agent-heatmap run' command.

    Example:

        agent-heatmap analyze output.json
    """
    try:
        db = Database.load(input_file)
    except Exception as e:
        console.print(f"[red]Error loading database:[/red] {e}")
        sys.exit(1)

    console.print(Panel.fit("[bold blue]Agent Heatmap Analysis[/bold blue]"))
    console.print()

    summary = db.summary()
    console.print(f"[bold]Repository:[/bold] {summary['repo']}")
    console.print(f"[bold]Analyzed:[/bold] {summary['timestamp']}")
    console.print()
    console.print(f"Sessions: {summary['successful_sessions']}/{summary['total_sessions']}")
    console.print(f"Total Tool Calls: {summary['total_tool_calls']}")
    console.print(f"Files Read: {summary['total_files_read']}")
    console.print(f"Files Edited: {summary['total_files_edited']}")
    console.print(f"Bash Commands: {summary['total_bash_commands']}")
    console.print()

    # Show details for each session
    for session in db.sessions:
        console.print(f"[bold cyan]PR #{session.pr_number}:[/bold cyan] {session.pr_title}")
        console.print(f"  Prompt: {session.human_prompt[:100]}...")
        if session.session_data:
            sd = session.session_data
            console.print(f"  Tool Calls: {len(sd.tool_calls)}")
            console.print(f"  Files Read: {len(sd.files_read)}")
            console.print(f"  Files Edited: {len(sd.files_edited)}")
        if not session.success:
            console.print(f"  [red]Error: {session.error}[/red]")
        console.print()


if __name__ == "__main__":
    main()
