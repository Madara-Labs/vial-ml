import ast
import textwrap
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    target_name: str
    start_line: int  # 0-indexed, inclusive
    end_line: int    # 0-indexed, exclusive
    code: str
    indent: str      # original leading whitespace of the first line


def find_target(source_code: str, target_name: str) -> ExtractionResult:
    """Locate a named function or class and return its bounds and source."""
    tree = ast.parse(source_code)
    lines = source_code.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == target_name:
                start = node.lineno - 1
                end = node.end_lineno
                raw = "\n".join(lines[start:end])
                indent = len(lines[start]) - len(lines[start].lstrip())
                indent_str = lines[start][:indent]
                return ExtractionResult(
                    target_name=target_name,
                    start_line=start,
                    end_line=end,
                    code=textwrap.dedent(raw),
                    indent=indent_str,
                )

    raise ValueError(
        f"'{target_name}' not found in source. "
        "Check the name and make sure it is a top-level function or class."
    )
