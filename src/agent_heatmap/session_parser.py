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
    output: str | None = None
    is_error: bool = False

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
        result: dict[str, Any] = {
            "name": self.name,
            "input": self.input,
            "timestamp": self.timestamp,
            "tool_use_id": self.tool_use_id,
        }
        if self.output is not None:
            result["output"] = self.output
            result["is_error"] = self.is_error
        return result


@dataclass
class BashExecution:
    """Represents a bash command execution with its output."""

    command: str
    output: str
    is_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "command": self.command,
            "output": self.output,
            "is_error": self.is_error,
        }


@dataclass
class SessionData:
    """Parsed data from a Claude session."""

    session_id: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    files_edited: list[str] = field(default_factory=list)
    bash_commands: list[str] = field(default_factory=list)
    bash_outputs: list[BashExecution] = field(default_factory=list)
    total_messages: int = 0
    claude_diff_raw: str | None = None  # Raw diff of changes Claude made

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "files_read": self.files_read,
            "files_edited": self.files_edited,
            "bash_commands": self.bash_commands,
            "bash_outputs": [bo.to_dict() for bo in self.bash_outputs],
            "total_messages": self.total_messages,
            "claude_diff_raw": self.claude_diff_raw,
        }


def _parse_single_session_file(
    session_path: Path,
    files_read_set: set[str],
    files_edited_set: set[str],
    bash_commands_list: list[str],
    bash_outputs_list: list[BashExecution],
    tool_calls: list[ToolCall],
    tool_call_map: dict[str, ToolCall],
) -> int:
    """Parse a single session JSONL file and accumulate results.

    Returns the number of messages parsed.
    """
    message_count = 0

    if not session_path.exists():
        return 0

    with open(session_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            message_count += 1

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
                    tool_calls.append(tool_call)
                    tool_call_map[tool_call.tool_use_id] = tool_call

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

                elif item.get("type") == "tool_result":
                    # Match tool results back to their tool calls
                    tool_use_id = item.get("tool_use_id", "")
                    if tool_use_id and tool_use_id in tool_call_map:
                        tc = tool_call_map[tool_use_id]
                        output_content = item.get("content", "")
                        # Handle content that might be a list of blocks
                        if isinstance(output_content, list):
                            text_parts = []
                            for block in output_content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                                elif isinstance(block, str):
                                    text_parts.append(block)
                            output_content = "\n".join(text_parts)
                        tc.output = output_content
                        tc.is_error = item.get("is_error", False)

                        # If this was a Bash command, add to bash_outputs
                        if tc.name == "Bash":
                            command = tc.input.get("command", "")
                            if command:
                                bash_outputs_list.append(
                                    BashExecution(
                                        command=command,
                                        output=output_content,
                                        is_error=tc.is_error,
                                    )
                                )

    return message_count


def _find_subagent_sessions(session_dir: Path, session_id: str) -> list[Path]:
    """Find all sub-agent session files matching the given session ID.

    Sub-agent files are named agent-*.jsonl and contain a sessionId field
    that matches the parent session.
    """
    subagent_files: list[Path] = []

    for path in session_dir.glob("agent-*.jsonl"):
        # Check if this sub-agent belongs to our session
        try:
            with open(path) as f:
                first_line = f.readline().strip()
                if first_line:
                    entry = json.loads(first_line)
                    if entry.get("sessionId") == session_id:
                        subagent_files.append(path)
        except (json.JSONDecodeError, OSError):
            continue

    return subagent_files


def parse_session(session_path: Path) -> SessionData:
    """Parse a Claude session JSONL file and all related sub-agent sessions.

    Args:
        session_path: Path to the main session JSONL file

    Returns:
        SessionData containing extracted tool calls and file operations
        from both the main session and all sub-agent sessions.
    """
    session_id = session_path.stem
    data = SessionData(session_id=session_id)

    if not session_path.exists():
        return data

    files_read_set: set[str] = set()
    files_edited_set: set[str] = set()
    bash_commands_list: list[str] = []
    bash_outputs_list: list[BashExecution] = []
    tool_calls: list[ToolCall] = []
    tool_call_map: dict[str, ToolCall] = {}

    # Parse main session file
    data.total_messages = _parse_single_session_file(
        session_path,
        files_read_set,
        files_edited_set,
        bash_commands_list,
        bash_outputs_list,
        tool_calls,
        tool_call_map,
    )

    # Find and parse sub-agent sessions
    session_dir = session_path.parent
    subagent_files = _find_subagent_sessions(session_dir, session_id)

    for subagent_path in subagent_files:
        data.total_messages += _parse_single_session_file(
            subagent_path,
            files_read_set,
            files_edited_set,
            bash_commands_list,
            bash_outputs_list,
            tool_calls,
            tool_call_map,
        )

    data.tool_calls = tool_calls
    data.files_read = sorted(files_read_set)
    data.files_edited = sorted(files_edited_set)
    data.bash_commands = bash_commands_list
    data.bash_outputs = bash_outputs_list

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
