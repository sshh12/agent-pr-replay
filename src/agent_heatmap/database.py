"""JSON database for storing analysis results."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from agent_heatmap.diff_comparison import DiffComparison
from agent_heatmap.session_parser import BashExecution, SessionData, ToolCall


@dataclass
class AnalysisSession:
    """A single analysis session for one PR."""

    pr_number: int
    pr_title: str
    pr_url: str
    human_prompt: str
    session_id: str
    session_data: SessionData | None = None
    diff_comparison: DiffComparison | None = None
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pr_number": self.pr_number,
            "pr_title": self.pr_title,
            "pr_url": self.pr_url,
            "human_prompt": self.human_prompt,
            "session_id": self.session_id,
            "session_data": self.session_data.to_dict() if self.session_data else None,
            "diff_comparison": self.diff_comparison.to_dict() if self.diff_comparison else None,
            "success": self.success,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisSession":
        """Create from dictionary."""
        session_data = None
        if data.get("session_data"):
            sd = data["session_data"]
            # Reconstruct tool calls from saved data
            tool_calls = []
            for tc_data in sd.get("tool_calls", []):
                tool_calls.append(
                    ToolCall(
                        name=tc_data.get("name", ""),
                        input=tc_data.get("input", {}),
                        timestamp=tc_data.get("timestamp", ""),
                        tool_use_id=tc_data.get("tool_use_id", ""),
                        output=tc_data.get("output"),
                        is_error=tc_data.get("is_error", False),
                    )
                )
            # Reconstruct bash outputs from saved data
            bash_outputs = []
            for bo_data in sd.get("bash_outputs", []):
                bash_outputs.append(
                    BashExecution(
                        command=bo_data.get("command", ""),
                        output=bo_data.get("output", ""),
                        is_error=bo_data.get("is_error", False),
                    )
                )
            session_data = SessionData(
                session_id=sd.get("session_id", ""),
                tool_calls=tool_calls,
                files_read=sd.get("files_read", []),
                files_edited=sd.get("files_edited", []),
                bash_commands=sd.get("bash_commands", []),
                bash_outputs=bash_outputs,
                total_messages=sd.get("total_messages", 0),
                claude_diff_raw=sd.get("claude_diff_raw"),
            )

        # Reconstruct diff comparison if present
        diff_comparison = None
        if data.get("diff_comparison"):
            diff_comparison = DiffComparison.from_dict(data["diff_comparison"])

        return cls(
            pr_number=data["pr_number"],
            pr_title=data["pr_title"],
            pr_url=data.get("pr_url", ""),
            human_prompt=data["human_prompt"],
            session_id=data["session_id"],
            session_data=session_data,
            diff_comparison=diff_comparison,
            success=data.get("success", True),
            error=data.get("error"),
        )


@dataclass
class Database:
    """Database for storing analysis results."""

    repo_url: str = ""
    repo_owner: str = ""
    repo_name: str = ""
    timestamp: str = ""
    days_analyzed: int = 0
    sessions: list[AnalysisSession] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def add_session(self, session: AnalysisSession) -> None:
        """Add an analysis session to the database."""
        self.sessions.append(session)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "repo_url": self.repo_url,
            "repo_owner": self.repo_owner,
            "repo_name": self.repo_name,
            "timestamp": self.timestamp,
            "days_analyzed": self.days_analyzed,
            "sessions": [s.to_dict() for s in self.sessions],
        }

    def save(self, path: Path) -> None:
        """Save database to a JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "Database":
        """Load database from a JSON file."""
        with open(path) as f:
            data = json.load(f)

        db = cls(
            repo_url=data.get("repo_url", ""),
            repo_owner=data.get("repo_owner", ""),
            repo_name=data.get("repo_name", ""),
            timestamp=data.get("timestamp", ""),
            days_analyzed=data.get("days_analyzed", 0),
        )

        for session_data in data.get("sessions", []):
            db.sessions.append(AnalysisSession.from_dict(session_data))

        return db

    def summary(self) -> dict[str, Any]:
        """Get a summary of the database contents."""
        total_tool_calls = 0
        total_files_read = 0
        total_files_edited = 0
        total_bash_commands = 0
        successful = 0

        for session in self.sessions:
            if session.success:
                successful += 1
            if session.session_data:
                total_tool_calls += len(session.session_data.tool_calls)
                total_files_read += len(session.session_data.files_read)
                total_files_edited += len(session.session_data.files_edited)
                total_bash_commands += len(session.session_data.bash_commands)

        return {
            "repo": f"{self.repo_owner}/{self.repo_name}",
            "timestamp": self.timestamp,
            "total_sessions": len(self.sessions),
            "successful_sessions": successful,
            "total_tool_calls": total_tool_calls,
            "total_files_read": total_files_read,
            "total_files_edited": total_files_edited,
            "total_bash_commands": total_bash_commands,
        }
