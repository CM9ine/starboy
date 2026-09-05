import typer

import starboy

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
