"""Normalise usage records emitted by coding-agent CLI JSONL streams."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Usage:
    """Token usage expressed in billing-relevant categories."""

    uncached_input_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    output_tokens: int
    reasoning_tokens: int


_ZERO_USAGE = Usage(0, 0, 0, 0, 0)


def _records(lines: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in lines:
        try:
            record = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _int_value(record: dict[str, Any], key: str) -> int:
    value = record.get(key, 0)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def parse_claude_code_usage(lines: list[str]) -> tuple[Usage, str | None]:
    """Parse Claude Code's final result usage record and session identifier."""

    session_id: str | None = None
    for record in _records(lines):
        candidate_session_id = record.get("session_id")
        if isinstance(candidate_session_id, str):
            session_id = candidate_session_id

        if record.get("type") != "result":
            continue
        raw_usage = record.get("usage")
        if not isinstance(raw_usage, dict):
            continue

        # Claude's input count excludes its separately reported cache reads.
        # Unknown: this fixture has one captured invocation, so it cannot show
        # whether final-result usage is per-turn or cumulative. A multi-turn
        # capture is required before summing this value across turns.
        return (
            Usage(
                uncached_input_tokens=_int_value(raw_usage, "input_tokens"),
                cache_read_tokens=_int_value(raw_usage, "cache_read_input_tokens"),
                cache_write_tokens=_int_value(
                    raw_usage, "cache_creation_input_tokens"
                ),
                output_tokens=_int_value(raw_usage, "output_tokens"),
                reasoning_tokens=_thinking_tokens(raw_usage),
            ),
            session_id,
        )

    return _ZERO_USAGE, session_id


def parse_codex_usage(lines: list[str]) -> tuple[Usage, str | None]:
    """Parse Codex's completed-turn usage record and thread identifier."""

    thread_id: str | None = None
    for record in _records(lines):
        if record.get("type") == "thread.started":
            candidate_thread_id = record.get("thread_id")
            if isinstance(candidate_thread_id, str):
                thread_id = candidate_thread_id

        if record.get("type") != "turn.completed":
            continue
        raw_usage = record.get("usage")
        if not isinstance(raw_usage, dict):
            continue

        total_input = _int_value(raw_usage, "input_tokens")
        cache_read = _int_value(raw_usage, "cached_input_tokens")
        # Codex's cached input is a subset of input_tokens, so subtract it.
        # Unknown: this fixture has one captured turn, so it cannot show
        # whether completed-turn usage is per-turn or cumulative. A multi-turn
        # capture is required before summing this value across turns.
        return (
            Usage(
                uncached_input_tokens=max(0, total_input - cache_read),
                cache_read_tokens=cache_read,
                cache_write_tokens=_int_value(raw_usage, "cache_write_input_tokens"),
                output_tokens=_int_value(raw_usage, "output_tokens"),
                reasoning_tokens=_int_value(raw_usage, "reasoning_output_tokens"),
            ),
            thread_id,
        )

    return _ZERO_USAGE, thread_id


def _thinking_tokens(raw_usage: dict[str, Any]) -> int:
    details = raw_usage.get("output_tokens_details")
    if not isinstance(details, dict):
        return 0
    return _int_value(details, "thinking_tokens")
