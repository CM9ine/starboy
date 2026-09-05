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
    cache_write_5m_tokens: int
    cache_write_1h_tokens: int
    output_tokens: int
    reasoning_tokens: int


_ZERO_USAGE = Usage(0, 0, 0, 0, 0, 0)


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
                cache_write_5m_tokens=_cache_creation_tokens(raw_usage, "5m"),
                cache_write_1h_tokens=_cache_creation_tokens(raw_usage, "1h"),
                output_tokens=_int_value(raw_usage, "output_tokens"),
                reasoning_tokens=_thinking_tokens(raw_usage),
            ),
            session_id,
        )

    return _ZERO_USAGE, session_id


def parse_codex_usage(lines: list[str]) -> tuple[Usage, str | None]:
    """Parse Codex's completed-turn usage record and thread identifier."""

    thread_id: str | None = None
    usage = _ZERO_USAGE
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
        # Completed-turn usage is per-turn, not session-cumulative: the clean
        # two-turn fixture reports 6 output tokens for both turns, not 12 on turn two.
        usage = Usage(
            uncached_input_tokens=max(0, total_input - cache_read),
            cache_read_tokens=cache_read,
            # Codex exposes one cache-write count. Its 1.25x input rate is
            # normalised as a 5-minute cache write.
            cache_write_5m_tokens=_int_value(
                raw_usage, "cache_write_input_tokens"
            ),
            cache_write_1h_tokens=0,
            output_tokens=_int_value(raw_usage, "output_tokens"),
            reasoning_tokens=_int_value(raw_usage, "reasoning_output_tokens"),
        )

    return usage, thread_id


def _thinking_tokens(raw_usage: dict[str, Any]) -> int:
    details = raw_usage.get("output_tokens_details")
    if not isinstance(details, dict):
        return 0
    return _int_value(details, "thinking_tokens")


def _cache_creation_tokens(raw_usage: dict[str, Any], duration: str) -> int:
    cache_creation = raw_usage.get("cache_creation")
    if not isinstance(cache_creation, dict):
        return 0
    return _int_value(cache_creation, f"ephemeral_{duration}_input_tokens")
