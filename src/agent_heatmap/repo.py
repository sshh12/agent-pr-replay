"""Git repository operations for agent-heatmap."""

import re
import shutil
import tempfile
from pathlib import Path

from git import Repo
from git.exc import GitCommandError


def is_url(target: str) -> bool:
    """Check if target is a URL (GitHub, GitLab, etc.)."""
    url_patterns = [
        r"^https?://",  # HTTP(S) URLs
        r"^git@",  # SSH URLs
        r"^git://",  # Git protocol
    ]
    return any(re.match(pattern, target) for pattern in url_patterns)


def get_github_repo_info(target: str) -> tuple[str, str] | None:
    """Extract owner and repo name from a GitHub URL.

    Returns (owner, repo) tuple or None if not a GitHub URL.
    """
    patterns = [
        r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
        r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, target)
        if match:
            return match.group(1), match.group(2)
    return None


def clone_repo(url: str, dest: Path) -> Repo:
    """Clone a repository from URL to destination.

    Args:
        url: The repository URL to clone
        dest: Destination directory for the clone

    Returns:
        The cloned Repo object
    """
    return Repo.clone_from(url, dest)


def get_repo(target: str, work_dir: Path | None = None) -> tuple[Repo, Path, bool]:
    """Get a repository from a URL or local path.

    Args:
        target: GitHub URL or local path to a git repository
        work_dir: Working directory for cloning (if URL). Uses temp dir if None.

    Returns:
        Tuple of (Repo object, repo path, is_temp) where is_temp indicates
        if the repo was cloned to a temporary directory that should be cleaned up.
    """
    if is_url(target):
        if work_dir is None:
            work_dir = Path(tempfile.mkdtemp(prefix="agent-heatmap-"))
        repo_path = work_dir / "repo"
        repo = clone_repo(target, repo_path)
        return repo, repo_path, True
    else:
        # Local path
        local_path = Path(target).resolve()
        if not local_path.exists():
            raise ValueError(f"Path does not exist: {local_path}")
        if not (local_path / ".git").exists():
            raise ValueError(f"Not a git repository: {local_path}")
        repo = Repo(local_path)
        return repo, local_path, False


def create_worktree(repo: Repo, commit: str, worktree_path: Path) -> Path:
    """Create a git worktree at a specific commit.

    Args:
        repo: The repository to create the worktree from
        commit: The commit hash to checkout
        worktree_path: Path where the worktree should be created

    Returns:
        Path to the created worktree
    """
    # Ensure parent directory exists
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the worktree
    repo.git.worktree("add", str(worktree_path), commit, "--detach")
    return worktree_path


def cleanup_worktree(repo: Repo, worktree_path: Path) -> None:
    """Remove a git worktree.

    Args:
        repo: The main repository
        worktree_path: Path to the worktree to remove
    """
    try:
        repo.git.worktree("remove", str(worktree_path), "--force")
    except GitCommandError:
        # If worktree command fails, try to clean up manually
        if worktree_path.exists():
            shutil.rmtree(worktree_path)


def cleanup_repo(repo_path: Path, is_temp: bool) -> None:
    """Clean up a repository if it's temporary.

    Args:
        repo_path: Path to the repository
        is_temp: Whether the repository is in a temporary location
    """
    if is_temp and repo_path.exists():
        # First try to remove any worktrees
        try:
            repo = Repo(repo_path)
            repo.git.worktree("prune")
        except Exception:
            pass
        # Then remove the directory
        shutil.rmtree(repo_path.parent if repo_path.name == "repo" else repo_path)
