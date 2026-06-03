import typer
from pathlib import Path
import tiktoken
from vial import Vial

app = typer.Typer(help="Vial — surgical code isolation for AI agents.")


@app.command()
def extract(
    source: Path = typer.Argument(..., help="Path to the Python source file."),
    target: str = typer.Argument(..., help="Name of the function or class to extract."),
    methods: str = typer.Option(None, help="Comma-separated list of methods to edit within a class"),
    workspace: Path = typer.Option(".vial_workspace", help="Workspace directory."),
):
    """Extract a named function or class into an isolated workspace file."""
    try:
        v = Vial(workspace_dir=workspace)
        methods_list = [m.strip() for m in methods.split(",")] if methods else None
        isolated = v.extract(source, target, methods_list)
        
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            orig_tokens = len(enc.encode(source.read_text()))
            isolated_tokens = len(enc.encode(Path(isolated).read_text()))
            
            typer.echo(f"Isolated '{target}' → {isolated}")
            typer.echo(f"Token count: {isolated_tokens} (down from {orig_tokens} in original file)")
        except Exception:
            typer.echo(f"Isolated '{target}' → {isolated}")
    except (ValueError, FileNotFoundError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def diff(
    workspace: Path = typer.Option(".vial_workspace", help="Workspace directory."),
):
    """Show a unified diff of the modified isolated file against the original source."""
    try:
        v = Vial(workspace_dir=workspace)
        diff_output = v.diff()
        if diff_output:
            typer.echo(diff_output)
        else:
            typer.echo("No changes detected.")
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
