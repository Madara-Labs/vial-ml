import ast


def extract_context(source_code: str) -> str:
    """Return import statements and top-level assignments as a single string."""
    if not source_code.strip():
        return ""

    tree = ast.parse(source_code)
    lines = source_code.splitlines()
    collected: list[str] = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)):
            chunk = lines[node.lineno - 1 : node.end_lineno]
            collected.extend(chunk)

    return "\n".join(collected)
