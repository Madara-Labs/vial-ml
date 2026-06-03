import ast
from pathlib import Path


def validate_syntax(code: str) -> tuple[bool, str]:
    """Returns (True, '') if code is valid Python, else (False, error_message)."""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError on line {e.lineno}: {e.msg}\n{e.text or ''}"


def strip_header(content: str, delimiter: str) -> str:
    """Remove the read-only context header block above the delimiter."""
    if delimiter in content:
        _, code = content.split(delimiter, 1)
        return code.strip("\n")
    return content.strip("\n")


def splice_back(
    source_filepath: Path,
    modified_code: str,
    start_line: int,
    end_line: int,
    indent: str = "",
) -> Path:
    """Replace lines [start_line:end_line] in source_filepath with modified_code."""
    original_lines = source_filepath.read_text().splitlines()
    modified_lines = [
        indent + line if line else line
        for line in modified_code.splitlines()
    ]

    new_lines = original_lines[:start_line] + modified_lines + original_lines[end_line:]
    source_filepath.write_text("\n".join(new_lines) + "\n")
    return source_filepath
