# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Concept

This tool answers the question: *How do AI coding agents "understand" a codebase?*

By replaying real merged PRs against Claude Code, we can observe and measure how the agent navigates unfamiliar code—which files it reads first, what search patterns it uses, how it builds context before making changes. The goal is to generate insights like file access heatmaps, command frequency analysis, and navigation patterns that reveal how agents explore and reason about repositories.

## Build & Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"
pre-commit install

# Type checking
mypy src/agent_pr_replay/

# Linting
ruff check src/agent_pr_replay/

# Format code
ruff format src/agent_pr_replay/
```

## CLI Usage

```bash
# Run analysis on a GitHub repo
agent-pr-replay run https://github.com/owner/repo --days 30 --top-k 5

# Dry run to preview PRs
agent-pr-replay run https://github.com/owner/repo --days 7 --dry-run

# View stats from previous run
agent-pr-replay stats output.json

# Detailed session analysis
agent-pr-replay analyze output.json
```

## Architecture

The tool analyzes how Claude Code explores codebases by running it against real merged PRs:

1. **PR Discovery** (`pr_finder.py`): Uses `gh` CLI to find merged PRs via GitHub search API
2. **PR Selection** (`pr_selector.py`): Uses Claude (via `claude -p`) to pick diverse, non-trivial PRs
3. **Prompt Generation** (`agent_runner.py`): Uses Claude to reverse-engineer human prompts from PR diffs
4. **Agent Execution** (`agent_runner.py`): Runs Claude Code in git worktrees at PR base commits with restricted tool permissions
5. **Session Parsing** (`session_parser.py`): Parses JSONL session files from `~/.claude/projects/` to extract tool calls
6. **Statistics** (`stats.py`): Aggregates file access patterns, tool usage, and directory heatmaps

### Key Data Flow

- `PR` dataclass flows through finder → selector → runner
- `SessionData` captures tool calls, files read/edited, bash commands
- `Database` persists results as JSON with `AnalysisSession` entries
- Session files are stored at `~/.claude/projects/{encoded-path}/{session-id}.jsonl`

### External Dependencies

- **`gh` CLI**: Must be authenticated (`gh auth login`)
- **`claude` CLI**: Used both for PR selection/prompt generation (`-p` flag) and running the actual agent analysis
