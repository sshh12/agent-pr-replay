# Agent Heatmap

Analyze how AI coding agents (Claude Code) navigate and understand codebases.

This tool runs Claude Code against merged PRs from a repository and collects data about how the agent explores and modifies the codebase, generating insights like:
- Most frequently read files
- Common shell commands used
- Directory access patterns (heatmap)
- Tool usage statistics

## Prerequisites

- Python 3.11+
- [GitHub CLI](https://cli.github.com/) (`gh`) - authenticated with `gh auth login`
- [Claude Code CLI](https://claude.ai/code) (`claude`) - installed and authenticated

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/coding-agent-heatmap.git
cd coding-agent-heatmap

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .

# For development
pip install -e ".[dev]"
pre-commit install
```

## Usage

### Run Analysis

Analyze merged PRs from a GitHub repository:

```bash
# Analyze a GitHub repo (clones to temp directory)
agent-heatmap run https://github.com/pallets/click --days 30 --top-k 5

# Analyze a local repo
agent-heatmap run ./my-local-repo --days 7 --top-k 3

# With custom selection instructions
agent-heatmap run https://github.com/django/django --days 30 --top-k 5 \
  --instructions "Focus on authentication-related changes"

# Dry run to see available PRs without running the agent
agent-heatmap run https://github.com/pallets/click --days 7 --dry-run
```

### View Statistics

View statistics from a previous run:

```bash
agent-heatmap stats output.json
```

### Detailed Analysis

View detailed analysis of each session:

```bash
agent-heatmap analyze output.json
```

## How It Works

1. **Find PRs**: Uses `gh` CLI to find merged PRs in the specified time range
2. **Select PRs**: Uses Claude to select diverse, non-trivial PRs for analysis
3. **Generate Prompts**: For each PR, reverse-engineers a human-like prompt from the diff
4. **Run Agent**: Spawns Claude Code in a worktree at the PR's base commit
5. **Parse Sessions**: Extracts tool calls, file reads, and commands from session history
6. **Generate Stats**: Computes statistics like file heatmaps and command frequency

## Output Format

The output JSON contains:

```json
{
  "repo_url": "https://github.com/owner/repo",
  "repo_owner": "owner",
  "repo_name": "repo",
  "timestamp": "2025-12-31T...",
  "sessions": [
    {
      "pr_number": 123,
      "pr_title": "Fix authentication bug",
      "human_prompt": "Fix the login validation...",
      "session_id": "uuid",
      "session_data": {
        "files_read": ["src/auth.py", ...],
        "files_edited": ["tests/test_auth.py", ...],
        "bash_commands": ["find . -name '*.py'", ...]
      }
    }
  ]
}
```

## CLI Options

### `agent-heatmap run`

| Option | Default | Description |
|--------|---------|-------------|
| `--days` | 30 | Number of days to look back for merged PRs |
| `--top-k` | 5 | Number of representative PRs to analyze |
| `-o, --output` | output.json | Output file for results |
| `--instructions` | - | Custom instructions for PR selection |
| `--dry-run` | - | Show PRs without running analysis |

### `agent-heatmap stats`

Shows statistics including:
- Tool usage breakdown
- Top commands/patterns
- Most read files
- Most edited files
- Directory heatmap

### `agent-heatmap analyze`

Shows detailed analysis of each session including prompts, tool calls, and file operations.

## Development

```bash
# Run type checking
mypy src/agent_heatmap/

# Run linting
ruff check src/agent_heatmap/

# Format code
ruff format src/agent_heatmap/

# Run tests
pytest
```

## License

MIT
