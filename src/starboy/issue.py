"""Read GitHub issues through the GitHub CLI."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Issue:
    """The title and body needed from a GitHub issue."""

    title: str
    body: str


def read_issue(number: int) -> Issue:
    """Fetch an issue's title and body using ``gh``."""

    completed = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "title,body"],
        capture_output=True,
        check=True,
        text=True,
    )
    response = json.loads(completed.stdout)
    return Issue(title=response["title"], body=response["body"] or "")
