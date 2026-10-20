"""CLI entrypoint stub (FASE 0 scaffold).

Real subcommands (`configure`, `setup-tools`, `scan`, `push`) are built in
FASE 5 per PLAN.md §5.1-5.6. This stub only exists so `vulnflow = "vulnflow.main:app"`
in pyproject.toml resolves and `uv run vulnflow --version` works end-to-end.
"""

import typer

from vulnflow import __version__

app = typer.Typer(
    name="vulnflow",
    help="VulnFlow AI Local CLI Agent — scan ingestion & reporting assistant.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"vulnflow-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Print the installed vulnflow-cli version and exit.",
    ),
) -> None:
    """VulnFlow AI Local CLI Agent.

    Real subcommands (`configure`, `setup-tools`, `scan`, `push`) are added
    in FASE 5 per PLAN.md §5.1-5.6; this callback only exists so
    `uv run vulnflow --version` works end-to-end from FASE 0 onward.
    """


if __name__ == "__main__":
    app()
