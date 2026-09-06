from pathlib import Path

import pytest

from starboy.agent import build_claude_command, parse_claude_code_result
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

    text, usage, session_id, tool_calls = parse_claude_code_result(lines)

    assert text == "greeting.txt was created and contains exactly: `hello`"
    assert usage == Usage(4, 42419, 0, 9249, 119, 0)
    assert session_id == "2c2c58f3-d008-4b6c-ab0c-7420bce801f9"
    assert tool_calls == 1


@pytest.mark.integration
def test_run_agent_makes_a_live_claude_call(tmp_path: Path) -> None:
    from starboy.agent import run_agent

    text, usage, session_id, tool_calls = run_agent(
        "claude", "claude-sonnet-5", "Reply with exactly: hello", tmp_path
    )

    assert text
    assert usage.output_tokens > 0
    assert session_id
    assert tool_calls >= 0
