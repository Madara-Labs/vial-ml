from pathlib import Path
from vial.workspace import Workspace
from vial.extractor import find_target
from vial.context import extract_context
from vial.merger import validate_syntax, strip_header, splice_back

HEADER_DELIMITER = "#" + "=" * 40 + " END OF CONTEXT " + "=" * 40


class Vial:
    def __init__(self, workspace_dir: str | Path = ".vial_workspace"):
        self.workspace = Workspace(workspace_dir)

    def extract(self, source_filepath: str | Path, target_name: str) -> str:
        """Extract target_name from source_filepath into an isolated workspace file."""
        source = Path(source_filepath)
        source_code = source.read_text()

        result = find_target(source_code, target_name)
        context = extract_context(source_code)

        header = "# Context from original file (read-only — do not modify this block):\n"
        if context:
            header += "\n".join(f"# {line}" for line in context.splitlines()) + "\n"
        header += HEADER_DELIMITER + "\n"

        isolated_path = self.workspace.isolated_path(target_name)
        isolated_path.write_text(header + result.code)

        self.workspace.save_metadata({
            "source_filepath": str(source.resolve()),
            "target_name": target_name,
            "start_line": result.start_line,
            "end_line": result.end_line,
            "indent": result.indent,
            "isolated_filepath": str(isolated_path.resolve()),
        })

        return str(isolated_path)

    def merge(self) -> None:
        """Validate and merge the modified isolated file back into the source."""
        meta = self.workspace.load_metadata()
        isolated = Path(meta["isolated_filepath"])
        content = isolated.read_text()

        modified_code = strip_header(content, HEADER_DELIMITER)

        is_valid, error = validate_syntax(modified_code)
        if not is_valid:
            raise ValueError(
                f"Merge aborted — agent produced invalid Python code:\n{error}"
            )

        splice_back(
            source_filepath=Path(meta["source_filepath"]),
            modified_code=modified_code,
            start_line=meta["start_line"],
            end_line=meta["end_line"],
            indent=meta.get("indent", ""),
        )

        self.workspace.cleanup()
