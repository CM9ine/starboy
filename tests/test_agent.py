from decimal import Decimal
from pathlib import Path

import pytest

from starboy.agent import AgentResult, build_claude_command, parse_claude_code_result
from starboy.usage import Usage

FIXTURES = Path(__file__).parent / "fixtures"


def test_builds_claude_command_for_model_and_prompt() -> None:
    assert build_claude_command("claude-sonnet-5", "say hello") == [
        "claude",
        "--print",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "bypassPermissions",
        "--model",
        "claude-sonnet-5",
        "say hello",
    ]


def test_parses_claude_fixture_into_agent_result() -> None:
    lines = (FIXTURES / "claude_code_stream.jsonl").read_text().splitlines()

    assert parse_claude_code_result(lines) == AgentResult(
        text="greeting.txt was created and contains exactly: `hello`",
        usage=Usage(4, 42419, 0, 9249, 119, 0),
        session_id="2c2c58f3-d008-4b6c-ab0c-7420bce801f9",
        tool_calls=1,
        seconds=Decimal("2.523"),
        outcome="completed",
        resolved_model="claude-sonnet-5",
    )


@pytest.mark.integration
def test_run_agent_makes_a_live_claude_call(tmp_path: Path) -> None:
    from starboy.agent import run_agent

    result = run_agent(
        "claude", "claude-sonnet-5", "Reply with exactly: hello", tmp_path
    )

    assert result.text
    assert result.usage.output_tokens > 0
    assert result.session_id
    assert result.tool_calls >= 0
