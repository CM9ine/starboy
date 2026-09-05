from importlib import metadata

from typer.testing import CliRunner

import starboy
from starboy.cli import app

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
