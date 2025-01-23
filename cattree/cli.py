from pathlib import Path

import typer

from cattree.cattree import generate_cattree

app = typer.Typer(
    name="cattree",
    help=(
        "Generate a directory tree with regex " "filtering and optional file contents."
    ),
)


@app.command()
def cattree(
    path: Path = typer.Argument(..., help="Path to the root directory."),
    include_pattern: str = typer.Option(
        None,
        "--include-pattern",
        "-i",
        help="Regex pattern to include specific files or directories.",
    ),
    exclude_pattern: str = typer.Option(
        None,
        "--exclude-pattern",
        "-e",
        help="Regex pattern to exclude specific files or directories.",
    ),
    max_lines: int = typer.Option(
        None,
        "--max-lines",
        "-m",
        help="Maximum number of lines to display for each file.",
    ),
    compact_code: bool = typer.Option(
        False,
        "--compact-code",
        "-c",
        help="Remove whitespace from the file content.",
    ),
):
    """
    Generate a directory tree for a given directory path.
    """
    try:
        output = generate_cattree(
            directory=path,
            include_pattern=include_pattern,
            exclude_pattern=exclude_pattern,
            max_lines=max_lines,
            compact_code=compact_code,
        )
        print(output)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
