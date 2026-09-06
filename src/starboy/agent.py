"""Run a coding agent and normalise its terminal result."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Literal

from starboy.usage import Usage, parse_claude_code_usage


@dataclass(frozen=True)
class AgentResult:
    """Observed result of one agent invocation."""

    text: str
    usage: Usage
    session_id: str | None
    tool_calls: int
    seconds: Decimal
    outcome: Literal["completed", "error", "timeout"]
    resolved_model: str | None


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


def parse_claude_code_result(lines: list[str]) -> AgentResult:
    """Return Claude Code's terminal text, usage, session, and tool-turn count.

    A tool call is one assistant turn containing one or more ``tool_use`` blocks.
    This deliberately folds the blocks into one unit. The future Codex branch
    will likewise fold the command and file-change events emitted in one agent
    turn, so the count represents tool-using turns rather than stream events.
    """

    usage, session_id = parse_claude_code_usage(lines)
    text = ""
    tool_calls = 0
    duration_ms = 0
    outcome: Literal["completed", "error", "timeout"] = "error"
    resolved_model: str | None = None

    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue

        if record.get("type") == "system" and record.get("subtype") == "init":
            candidate_model = record.get("model")
            if isinstance(candidate_model, str):
                resolved_model = candidate_model

        if record.get("type") == "result":
            result = record.get("result")
            if isinstance(result, str):
                text = result
            candidate_duration_ms = record.get("duration_ms")
            if isinstance(candidate_duration_ms, int) and not isinstance(
                candidate_duration_ms, bool
            ):
                duration_ms = candidate_duration_ms
            if record.get("is_error") is False:
                outcome = "completed"

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

    return AgentResult(
        text=text,
        usage=usage,
        session_id=session_id,
        tool_calls=tool_calls,
        seconds=Decimal(duration_ms) / Decimal(1_000),
        outcome=outcome,
        resolved_model=resolved_model,
    )


def run_agent(
    harness: str, model: str, prompt: str, cwd: Path
) -> AgentResult:
    """Run one supported harness and return its normalised terminal result."""

    if harness != "claude":
        raise ValueError(f"Unsupported harness: {harness}")

    start = time.monotonic()
    try:
        completed = subprocess.run(
            build_claude_command(model, prompt),
            cwd=cwd,
            capture_output=True,
            check=False,
            text=True,
        )
    except subprocess.TimeoutExpired:
        return _failed_result("timeout", start)
    except OSError:
        return _failed_result("error", start)

    result = parse_claude_code_result(completed.stdout.splitlines())
    outcome: Literal["completed", "error", "timeout"] = result.outcome
    if completed.returncode != 0:
        outcome = "error"
    return replace(result, seconds=_elapsed_seconds(start), outcome=outcome)


def _failed_result(
    outcome: Literal["error", "timeout"], start: float
) -> AgentResult:
    return AgentResult(
        text="",
        usage=Usage(0, 0, 0, 0, 0, 0),
        session_id=None,
        tool_calls=0,
        seconds=_elapsed_seconds(start),
        outcome=outcome,
        resolved_model=None,
    )


def _elapsed_seconds(start: float) -> Decimal:
    return Decimal(str(time.monotonic() - start))
