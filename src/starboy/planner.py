"""Create a written implementation spec from a GitHub issue."""

from __future__ import annotations

from pathlib import Path

from starboy.agent import run_agent
from starboy.issue import Issue, read_issue

PLANNER_HARNESS = "claude"
PLANNER_MODEL = "claude-sonnet-5"


def build_planner_prompt(number: int, issue: Issue) -> str:
    """Return the bounded prompt used to turn an issue into a spec."""

    return (
        "Write an implementation spec for this GitHub issue. Return only "
        "Markdown with these headings: Problem, Scope, Out of scope, and "
        "Acceptance criteria. Make every acceptance criterion concrete and "
        "testable. Do not write code or wrap the response in a code fence.\n\n"
        f"# Issue {number}: {issue.title}\n\n{issue.body}"
    )


def plan_issue(number: int, cwd: Path) -> Path:
    """Write the planner's Markdown spec for an issue and return its path."""

    issue = read_issue(number)
    result = run_agent(
        PLANNER_HARNESS,
        PLANNER_MODEL,
        build_planner_prompt(number, issue),
        cwd,
    )
    if result.outcome != "completed":
        raise RuntimeError(f"Planner did not complete: {result.outcome}")

    spec_path = cwd / "specs" / f"{number}.md"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(result.text)
    return spec_path
