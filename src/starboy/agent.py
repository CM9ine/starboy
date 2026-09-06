"""Run a coding agent and normalise its terminal result."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from starboy.usage import Usage, parse_claude_code_usage


def build_claude_command(model: str, prompt: str) -> list[str]:
    """Build the Claude Code command for a non-interactive JSONL run."""

    return [
        "claude",
        "--print",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "bypassPermissions",
        "--model",
        model,
        prompt,
    ]


def parse_claude_code_result(lines: list[str]) -> tuple[str, Usage, str | None, int]:
    """Return Claude Code's terminal text, usage, session, and tool-turn count.

    A tool call is one assistant turn containing one or more ``tool_use`` blocks.
    This deliberately folds the blocks into one unit. The future Codex branch
    will likewise fold the command and file-change events emitted in one agent
    turn, so the count represents tool-using turns rather than stream events.
    """

    usage, session_id = parse_claude_code_usage(lines)
    text = ""
    tool_calls = 0

    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue

        if record.get("type") == "result":
            result = record.get("result")
            if isinstance(result, str):
                text = result

        message = record.get("message")
        if record.get("type") != "assistant" or not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        if any(
            isinstance(block, dict) and block.get("type") == "tool_use"
            for block in content
        ):
            tool_calls += 1

    return text, usage, session_id, tool_calls


def run_agent(
    harness: str, model: str, prompt: str, cwd: Path
) -> tuple[str, Usage, str | None, int]:
    """Run one supported harness and return its normalised terminal result."""

    if harness != "claude":
        raise ValueError(f"Unsupported harness: {harness}")

    completed = subprocess.run(
        build_claude_command(model, prompt),
        cwd=cwd,
        capture_output=True,
        check=True,
        text=True,
    )
    return parse_claude_code_result(completed.stdout.splitlines())
