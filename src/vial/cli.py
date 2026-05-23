import typer
from pathlib import Path
from vial import Vial

app = typer.Typer(help="Vial — surgical code isolation for AI agents.")


@app.command()
def extract(
    source: Path = typer.Argument(..., help="Path to the Python source file."),
    target: str = typer.Argument(..., help="Name of the function or class to extract."),
    workspace: Path = typer.Option(".vial_workspace", help="Workspace directory."),
):
    """Extract a named function or class into an isolated workspace file."""
    try:
        v = Vial(workspace_dir=workspace)
        isolated = v.extract(source, target)
        typer.echo(f"Isolated '{target}' → {isolated}")
    except (ValueError, FileNotFoundError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def merge(
    workspace: Path = typer.Option(".vial_workspace", help="Workspace directory."),
):
    """Validate and merge the modified isolated file back into the source."""
    try:
        v = Vial(workspace_dir=workspace)
        meta = v.workspace.load_metadata()
        v.merge()
        typer.echo(f"Merged '{meta['target_name']}' back into {meta['source_filepath']}")
    except (ValueError, FileNotFoundError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
