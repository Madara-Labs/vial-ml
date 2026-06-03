from pathlib import Path
import difflib
from vial.workspace import Workspace
from vial.extractor import find_target, extract_class_shape
from vial.context import extract_context
from vial.merger import validate_syntax, strip_header, splice_back, merge_class_shape

HEADER_DELIMITER = "#" + "=" * 40 + " END OF CONTEXT " + "=" * 40


class Vial:
    def __init__(self, workspace_dir: str | Path = ".vial_workspace"):
        self.workspace = Workspace(workspace_dir)

    def extract(self, source_filepath: str | Path, target_name: str, methods: list[str] | None = None) -> str:
        """Extract target_name from source_filepath into an isolated workspace file."""
        source = Path(source_filepath)
        source_code = source.read_text()

        if methods:
            result = extract_class_shape(source_code, target_name, methods)
            extraction_type = "class_shape"
        else:
            result = find_target(source_code, target_name)
            extraction_type = "function"

        context = extract_context(source_code, target_name)

        header = "# Context from original file (read-only — do not modify this block):\n"
        if context:
            header += "\n".join(f"# {line}" for line in context.splitlines()) + "\n"
        header += HEADER_DELIMITER + "\n"

        isolated_path = self.workspace.isolated_path(target_name)
        isolated_path.write_text(header + result.code)

        self.workspace.save_metadata({
            "type": extraction_type,
            "target_methods": methods or [],
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

        source_filepath = Path(meta["source_filepath"])
        original_lines = source_filepath.read_text().splitlines()

        if meta.get("type") == "class_shape":
            new_lines = merge_class_shape(
                original_lines=original_lines,
                modified_code=modified_code,
                target_methods=meta.get("target_methods", []),
                class_start_line=meta["start_line"],
                class_end_line=meta["end_line"],
                indent=meta.get("indent", "")
            )
        else:
            new_lines = splice_back(
                original_lines=original_lines,
                modified_code=modified_code,
                start_line=meta["start_line"],
                end_line=meta["end_line"],
                indent=meta.get("indent", ""),
            )

        source_filepath.write_text("\n".join(new_lines) + "\n")
        self.workspace.cleanup()

    def diff(self) -> str:
        """Return a unified diff between the original source block and the modified isolated code."""
        meta = self.workspace.load_metadata()
        isolated = Path(meta["isolated_filepath"])
        content = isolated.read_text()

        modified_code = strip_header(content, HEADER_DELIMITER)
        
        source_filepath = Path(meta["source_filepath"])
        original_lines = source_filepath.read_text().splitlines()
        
        start_line = meta["start_line"]
        end_line = meta["end_line"]
        indent = meta.get("indent", "")
        
        if meta.get("type") == "class_shape":
            new_lines = merge_class_shape(
                original_lines=original_lines,
                modified_code=modified_code,
                target_methods=meta.get("target_methods", []),
                class_start_line=start_line,
                class_end_line=end_line,
                indent=indent
            )
            # For a complete diff, we diff the entire file
            diff_lines = list(difflib.unified_diff(
                original_lines,
                new_lines,
                fromfile=f"a/{source_filepath.name}",
                tofile=f"b/{source_filepath.name}",
                lineterm=""
            ))
        else:
            original_block = original_lines[start_line:end_line]
            modified_lines = [
                indent + line if line else line
                for line in modified_code.splitlines()
            ]
            diff_lines = list(difflib.unified_diff(
                original_block,
                modified_lines,
                fromfile=f"a/{source_filepath.name}",
                tofile=f"b/{source_filepath.name}",
                lineterm=""
            ))
        
        return "\n".join(diff_lines)
