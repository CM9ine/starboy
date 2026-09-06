from decimal import Decimal
from pathlib import Path

from typer.testing import CliRunner

import starboy.cli
from starboy.agent import AgentResult
from starboy.issue import Issue
from starboy.planner import plan_issue
from starboy.usage import Usage

runner = CliRunner()


def _completed_result(text: str) -> AgentResult:
    return AgentResult(
        text=text,
        usage=Usage(0, 0, 0, 0, 0, 0),
        session_id="session-id",
        tool_calls=0,
        seconds=Decimal(0),
        outcome="completed",
        resolved_model="claude-sonnet-5",
    )


def test_plan_issue_writes_agent_spec_for_the_issue(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}
    spec = """# Fix the button\n\n## Acceptance criteria\n\n- The form submits.\n"""

    monkeypatch.setattr(
        "starboy.planner.read_issue",
        lambda number: Issue("Fix the button", "It does not submit."),
    )

    def fake_run_agent(harness: str, model: str, prompt: str, cwd: Path):
        captured.update(
            harness=harness,
            model=model,
            prompt=prompt,
            cwd=cwd,
        )
        return _completed_result(spec)

    monkeypatch.setattr("starboy.planner.run_agent", fake_run_agent)

    assert plan_issue(123, tmp_path) == tmp_path / "specs" / "123.md"
    assert (tmp_path / "specs" / "123.md").read_text() == spec
    assert captured == {
        "harness": "claude",
        "model": "claude-sonnet-5",
        "prompt": (
            "Write an implementation spec for this GitHub issue. Return only "
            "Markdown with these headings: Problem, Scope, Out of scope, and "
            "Acceptance criteria. Make every acceptance criterion concrete and "
            "testable. Do not write code or wrap the response in a code fence.\n\n"
            "# Issue 123: Fix the button\n\nIt does not submit."
        ),
        "cwd": tmp_path,
    }


def test_plan_command_prints_written_spec_path(monkeypatch, tmp_path) -> None:
    spec_path = tmp_path / "specs" / "123.md"
    monkeypatch.setattr(starboy.cli, "plan_issue", lambda number, cwd: spec_path)

    result = runner.invoke(starboy.cli.app, ["plan", "123"])

    assert result.exit_code == 0
    assert result.stdout == f"{spec_path}\n"
