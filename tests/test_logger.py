import json
from decimal import Decimal
from pathlib import Path

from starboy.agent import AgentResult
from starboy.logger import AgentCallContext, log_agent_call, run_agent_logged
from starboy.usage import Usage


def _context(sequence: int = 1, issue: int | None = 42) -> AgentCallContext:
    return AgentCallContext(
        run_id="run-123",
        issue=issue,
        phase="builder",
        sequence=sequence,
        harness="claude",
        model="claude-sonnet-5",
    )


def _result(usage: Usage | None = None) -> AgentResult:
    if usage is None:
        usage = Usage(4, 42_419, 0, 9_249, 119, 0)
    return AgentResult(
        text="greeting.txt was created",
        usage=usage,
        session_id="session-123",
        tool_calls=1,
        seconds=Decimal("2.523"),
        outcome="completed",
        resolved_model="claude-sonnet-5",
    )


def test_log_agent_call_writes_complete_json_line(tmp_path: Path) -> None:
    log_path = tmp_path / "agent-calls.jsonl"

    log_agent_call(log_path, _context(), _result())

    record = json.loads(log_path.read_text())
    assert record == {
        "run_id": "run-123",
        "issue": 42,
        "phase": "builder",
        "sequence": 1,
        "harness": "claude",
        "requested_model": "claude-sonnet-5",
        "resolved_model": "claude-sonnet-5",
        "session_id": "session-123",
        "tool_calls": 1,
        "uncached_input_tokens": 4,
        "cache_read_tokens": 42_419,
        "cache_write_5m_tokens": 0,
        "cache_write_1h_tokens": 9_249,
        "output_tokens": 119,
        "reasoning_tokens": 0,
        "cost_usd": "0.0466778",
        "pricing_version": "2026-09-06",
        "seconds": "2.523",
        "outcome": "completed",
    }


def test_log_agent_call_appends_lines(tmp_path: Path) -> None:
    log_path = tmp_path / "agent-calls.jsonl"

    log_agent_call(log_path, _context(1), _result())
    log_agent_call(log_path, _context(2), _result())

    records = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert [record["sequence"] for record in records] == [1, 2]


def test_log_agent_call_preserves_zero_usage_fields(tmp_path: Path) -> None:
    log_path = tmp_path / "agent-calls.jsonl"

    log_agent_call(log_path, _context(issue=None), _result(Usage(0, 0, 0, 0, 0, 0)))

    record = json.loads(log_path.read_text())
    assert record["issue"] is None
    assert {
        key: record[key]
        for key in (
            "uncached_input_tokens",
            "cache_read_tokens",
            "cache_write_5m_tokens",
            "cache_write_1h_tokens",
            "output_tokens",
            "reasoning_tokens",
        )
    } == {
        "uncached_input_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_5m_tokens": 0,
        "cache_write_1h_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
    }


def test_run_agent_logged_runs_agent_and_writes_result(
    monkeypatch: object, tmp_path: Path
) -> None:
    import starboy.logger

    log_path = tmp_path / "agent-calls.jsonl"
    expected_result = _result()
    monkeypatch.setattr(starboy.logger, "run_agent", lambda *_: expected_result)  # type: ignore[union-attr]

    result = run_agent_logged(_context(), log_path, "say hello", tmp_path)

    assert result == expected_result
    assert json.loads(log_path.read_text())["outcome"] == "completed"
