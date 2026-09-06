"""Create isolated Git worktrees for factory runs."""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def scratch_worktree(repository: Path, run_id: str) -> Iterator[Path]:
    """Check out ``main`` on a run-specific branch in a temporary worktree.

    The temporary checkout is removed on exit. Its ``starboy/<run_id>`` branch
    remains available for a later commit and pull request.
    """

    branch = f"starboy/{run_id}"
    with tempfile.TemporaryDirectory(prefix="starboy-worktree-") as directory:
        worktree = Path(directory)
        subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "worktree",
                "add",
                "-b",
                branch,
                str(worktree),
                "main",
            ],
            check=True,
        )
        try:
            yield worktree
        finally:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "worktree",
                    "remove",
                    "--force",
                    str(worktree),
                ],
                check=True,
            )
