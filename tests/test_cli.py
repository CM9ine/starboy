from importlib import metadata

from typer.testing import CliRunner

import starboy
import starboy.cli
from starboy.cli import app
from starboy.issue import Issue

runner = CliRunner()


def test_import_has_nonempty_version():
    assert isinstance(starboy.__version__, str)
    assert starboy.__version__ != ""


def test_version_matches_package_metadata():
    assert starboy.__version__ == metadata.version("starboy")


def test_cli_version_flag_exits_zero_and_prints_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert starboy.__version__ in result.stdout


def test_issue_command_prints_title_and_body(monkeypatch):
    monkeypatch.setattr(
        starboy.cli,
        "read_issue",
        lambda number: Issue("Fix the button", "It does not submit."),
    )

    result = runner.invoke(app, ["issue", "123"])

    assert result.exit_code == 0
    assert result.stdout == "Fix the button\n\nIt does not submit.\n"
