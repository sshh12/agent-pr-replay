"""LLM-based analyzer for generating synthesis reports."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from agent_pr_replay.database import Database
from agent_pr_replay.pr_selector import get_claude_path

SYNTHESIS_PROMPT = """Read analysis_data.json which contains analysis of how Claude performed \
on various PR tasks compared to human implementations.

Generate a markdown report with the following structure:

# Coding Agent Repo Report

Start with repo metadata:
- **Repository**: [repo name from data]
- **Sessions Analyzed**: [count]

---

## Synthesized CLAUDE.md / AGENTS.md

This section contains synthesized guidance as a markdown code block.

Create a unified CLAUDE.md / AGENTS.md that combines the best insights from all \
suggested_claude_md entries. Follow these principles:

**Synthesis approach:**
- Deduplicate similar suggestions across sessions
- ONLY include patterns that appear in 2+ sessions (avoid overfitting to single PRs)
- Organize by theme (e.g., "Code Style", "Testing", "Refactoring Decisions")
- Keep only universally applicable guidance (not repo-specific unless clearly marked)
- Merge related bullets into cohesive sections

**Format (for the content inside the code block):**
- Use ## H2 section headers for each theme
- Use concise bullet points (1-2 sentences max per bullet)
- MUST use bullet point format, not prose paragraphs
- NO nested code blocks - use inline `code` for symbols, paths, function names
- Reference EXACT paths, folders, and symbols from the codebase \
(e.g., `torch/_dynamo/trace_rules.py`, `MANUAL_FUNCTIONS`)

**Content principles:**
- Focus on guardrails/corrections, not comprehensive manuals
- When saying "never X", always provide an alternative "prefer Y"
- Prefer pointers to patterns (e.g., "check for X before Y") over verbose explanations
- Include specific file paths and symbol names from the analysis data
- Omit obvious guidance that any competent developer would know

---

## Suggested Skills

Based on the analysis, suggest 1-3 Agent Skills that would help Claude perform better \
on this codebase. Skills are specialized prompt templates that inject domain-specific \
instructions when Claude encounters matching tasks.

ONLY suggest skills based on patterns seen in 2+ sessions. Avoid overfitting to single PRs.

For each suggested skill, provide a complete SKILL.md file in a code block.

**Skill structure:**
Skills have YAML frontmatter (name, description) followed by markdown instructions with \
sections: Overview, Instructions, Patterns to Follow, Anti-patterns to Avoid.

**Frontmatter fields:**
- `name` (required): lowercase letters, numbers, hyphens only (max 64 chars)
- `description` (required): what it does AND when to use it (max 1024 chars). Include \
trigger phrases like "Use when..." to help Claude match user intent.

**Skill content principles:**
- Focus on guardrails/corrections specific to this codebase
- Use imperative language ("Analyze code for...") not second person ("You should...")
- Keep under 500 lines
- NO nested code blocks inside skills - use inline `code` for paths/symbols
- Reference EXACT file paths, function names, and symbols from the codebase
- Use bullet points, not prose paragraphs

---

## Key Insights from Analysis

Add 3-7 bullet points (1-2 sentences each) that cite SPECIFIC sessions by PR title \
to show what informed the CLAUDE.md content and suggested skills above. Format:
- **[Theme]**: [Specific insight]. (From: "[PR Title]")

---

Do NOT include:
- General quality assessments or summaries
- Vague statements without specific session references
- Skills or guidance based on only a single PR (require 2+ occurrences)
- Nested code blocks (code blocks within code blocks)
- "Why this skill helps" explanations for each skill

Write the complete report to report.md"""


def extract_analysis_data(db: Database) -> dict[str, Any]:
    """Extract condensed analysis data from database.

    Returns only the relevant fields needed for synthesis,
    avoiding large raw diffs that would overflow context.
    """
    condensed: dict[str, Any] = {
        "repo": f"{db.repo_owner}/{db.repo_name}",
        "sessions": [],
    }
    for session in db.sessions:
        if session.diff_comparison:
            condensed["sessions"].append(
                {
                    "pr_title": session.pr_title,
                    "human_prompt": session.human_prompt,
                    "analysis": session.diff_comparison.analysis_description,
                    "suggested_claude_md": session.diff_comparison.suggested_claude_md,
                }
            )
    return condensed


def generate_report(db: Database, output_path: Path, model: str = "sonnet") -> Path:
    """Generate an LLM-synthesized report from analysis data.

    Args:
        db: Database containing analysis sessions
        output_path: Where to save the report
        model: Model to use for synthesis

    Returns:
        Path to the generated report
    """
    # Create temp folder
    with tempfile.TemporaryDirectory(prefix="agent-pr-replay-analyze-") as temp_dir:
        temp_path = Path(temp_dir)

        # Extract and write condensed data
        condensed = extract_analysis_data(db)
        data_file = temp_path / "analysis_data.json"
        data_file.write_text(json.dumps(condensed, indent=2))

        # Run Claude
        claude_path = get_claude_path()
        cmd = [
            claude_path,
            "-p",
            "--model",
            model,
            "--allowedTools",
            "Read,Write,Glob",
        ]
        subprocess.run(cmd, cwd=temp_path, input=SYNTHESIS_PROMPT, text=True, check=True)

        # Copy report to output
        report_file = temp_path / "report.md"
        if report_file.exists():
            shutil.copy(report_file, output_path)
            return output_path
        else:
            raise RuntimeError("Claude did not generate report.md")
