"""Parse Claude Code session files."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ToolCall:
    """Represents a single tool call from a Claude session."""

    name: str
    input: dict[str, Any]
    timestamp: str
    tool_use_id: str

    @classmethod
    def from_json(cls, data: dict[str, Any], timestamp: str) -> "ToolCall":
        """Create a ToolCall from session JSON data."""
        return cls(
            name=data.get("name", "unknown"),
            input=data.get("input", {}),
            timestamp=timestamp,
            tool_use_id=data.get("id", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "input": self.input,
            "timestamp": self.timestamp,
            "tool_use_id": self.tool_use_id,
        }


@dataclass
class SessionData:
    """Parsed data from a Claude session."""

    session_id: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    files_edited: list[str] = field(default_factory=list)
    bash_commands: list[str] = field(default_factory=list)
    total_messages: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "files_read": self.files_read,
            "files_edited": self.files_edited,
            "bash_commands": self.bash_commands,
            "total_messages": self.total_messages,
        }


def parse_session(session_path: Path) -> SessionData:
    """Parse a Claude session JSONL file.

    Args:
        session_path: Path to the session JSONL file

    Returns:
        SessionData containing extracted tool calls and file operations
    """
    session_id = session_path.stem
    data = SessionData(session_id=session_id)

    if not session_path.exists():
        return data

    files_read_set: set[str] = set()
    files_edited_set: set[str] = set()
    bash_commands_list: list[str] = []

    with open(session_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            data.total_messages += 1

            # Get timestamp
            timestamp = entry.get("timestamp", "")

            # Look for tool_use in assistant messages
            message = entry.get("message", {})
            if not isinstance(message, dict):
                continue

            content = message.get("content", [])
            if not isinstance(content, list):
                continue

            for item in content:
                if not isinstance(item, dict):
                    continue

                if item.get("type") == "tool_use":
                    tool_call = ToolCall.from_json(item, timestamp)
                    data.tool_calls.append(tool_call)

                    # Extract specific information based on tool type
                    tool_name = tool_call.name
                    tool_input = tool_call.input

                    if tool_name == "Read":
                        file_path = tool_input.get("file_path", "")
                        if file_path:
                            files_read_set.add(file_path)

                    elif tool_name in ("Edit", "Write"):
                        file_path = tool_input.get("file_path", "")
                        if file_path:
                            files_edited_set.add(file_path)

                    elif tool_name == "Bash":
                        command = tool_input.get("command", "")
                        if command:
                            bash_commands_list.append(command)

                    elif tool_name == "Glob":
                        # Track glob patterns used
                        pattern = tool_input.get("pattern", "")
                        if pattern:
                            bash_commands_list.append(f"glob: {pattern}")

                    elif tool_name == "Grep":
                        # Track grep patterns used
                        pattern = tool_input.get("pattern", "")
                        path = tool_input.get("path", ".")
                        if pattern:
                            bash_commands_list.append(f"grep: {pattern} in {path}")

    data.files_read = sorted(files_read_set)
    data.files_edited = sorted(files_edited_set)
    data.bash_commands = bash_commands_list

    return data


def extract_file_reads(tool_calls: list[ToolCall]) -> list[str]:
    """Extract file paths from Read tool calls."""
    files: list[str] = []
    for tc in tool_calls:
        if tc.name == "Read":
            file_path = tc.input.get("file_path", "")
            if file_path:
                files.append(file_path)
    return files


def extract_file_edits(tool_calls: list[ToolCall]) -> list[str]:
    """Extract file paths from Edit/Write tool calls."""
    files: list[str] = []
    for tc in tool_calls:
        if tc.name in ("Edit", "Write"):
            file_path = tc.input.get("file_path", "")
            if file_path:
                files.append(file_path)
    return files


def extract_bash_commands(tool_calls: list[ToolCall]) -> list[str]:
    """Extract commands from Bash tool calls."""
    commands: list[str] = []
    for tc in tool_calls:
        if tc.name == "Bash":
            command = tc.input.get("command", "")
            if command:
                commands.append(command)
    return commands
