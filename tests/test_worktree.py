import subprocess
from pathlib import Path


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "--initial-branch=main")
    _git(repository, "config", "user.name", "Test User")
    _git(repository, "config", "user.email", "test@example.com")
    (repository / "README.md").write_text("initial\n")
    _git(repository, "add", "README.md")
    _git(repository, "commit", "-m", "Initial commit")
    return repository


def test_scratch_worktree_is_isolated_and_leaves_its_branch(tmp_path: Path) -> None:
    from starboy.worktree import scratch_worktree

    repository = _repository(tmp_path)

    with scratch_worktree(repository, "run-123") as worktree:
        assert worktree != repository
        assert (worktree / "README.md").read_text() == "initial\n"
        assert _git(worktree, "branch", "--show-current").strip() == "starboy/run-123"
        (worktree / "only-in-scratch.txt").write_text("isolated\n")

    assert not worktree.exists()
    assert _git(repository, "branch", "--list", "starboy/run-123").strip() == "starboy/run-123"
    assert not (repository / "only-in-scratch.txt").exists()


def test_concurrent_scratch_worktrees_do_not_collide(tmp_path: Path) -> None:
    from starboy.worktree import scratch_worktree

    repository = _repository(tmp_path)

    with (
        scratch_worktree(repository, "run-one") as first,
        scratch_worktree(repository, "run-two") as second,
    ):
        assert first != second
        (first / "result.txt").write_text("first\n")
        (second / "result.txt").write_text("second\n")
        assert (first / "result.txt").read_text() == "first\n"
        assert (second / "result.txt").read_text() == "second\n"

    assert not first.exists()
    assert not second.exists()
    assert _git(repository, "branch", "--list", "starboy/run-*").split() == [
        "starboy/run-one",
        "starboy/run-two",
    ]
