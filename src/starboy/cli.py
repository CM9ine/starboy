from pathlib import Path

import typer

import starboy
from starboy.issue import read_issue
from starboy.planner import plan_issue

app = typer.Typer()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(starboy.__version__)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True
    ),
) -> None:
    pass


@app.command()
def issue(number: int) -> None:
    """Print a GitHub issue's title and body."""

    fetched_issue = read_issue(number)
    typer.echo(f"{fetched_issue.title}\n\n{fetched_issue.body}")


@app.command()
def plan(number: int) -> None:
    """Write an implementation spec for a GitHub issue."""

    typer.echo(plan_issue(number, Path.cwd()))
