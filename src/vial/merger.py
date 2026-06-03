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
    original_lines: list[str],
    modified_code: str,
    start_line: int,
    end_line: int,
    indent: str = "",
) -> list[str]:
    """Replace lines [start_line:end_line] in original_lines with modified_code."""
    modified_lines = [
        indent + line if line else line
        for line in modified_code.splitlines()
    ]

    new_lines = original_lines[:start_line] + modified_lines + original_lines[end_line:]
    return new_lines


def merge_class_shape(
    original_lines: list[str],
    modified_code: str,
    target_methods: list[str],
    class_start_line: int,
    class_end_line: int,
    indent: str = "",
) -> list[str]:
    """Merge back specific target methods and any new methods from an isolated class shape."""
    original_lines = original_lines.copy()
    
    try:
        mod_tree = ast.parse(modified_code)
    except SyntaxError as e:
        raise ValueError(f"SyntaxError in modified code on line {e.lineno}: {e.msg}")
        
    mod_lines = modified_code.splitlines()
    mod_class = None
    for node in mod_tree.body:
        if isinstance(node, ast.ClassDef):
            mod_class = node
            break
            
    if not mod_class:
        raise ValueError("Could not find class definition in modified code.")

    orig_code = "\n".join(original_lines)
    orig_tree = ast.parse(orig_code)
    orig_class = None
    for node in ast.walk(orig_tree):
        if isinstance(node, ast.ClassDef) and node.lineno - 1 == class_start_line:
            orig_class = node
            break

    if not orig_class:
        raise ValueError("Could not find original class definition.")

    orig_methods = {}
    for node in orig_class.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            orig_methods[node.name] = (node.lineno - 1, node.end_lineno)

    replacements = []
    new_methods_to_add = []
    for node in mod_class.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in target_methods or node.name not in orig_methods:
                m_lines = mod_lines[node.lineno - 1 : node.end_lineno]
                indented_m_lines = [indent + line if line else line for line in m_lines]
                
                if node.name in orig_methods:
                    orig_start, orig_end = orig_methods[node.name]
                    replacements.append((orig_start, orig_end, indented_m_lines))
                else:
                    new_methods_to_add.extend(indented_m_lines)
                    
    replacements.sort(key=lambda r: r[0], reverse=True)
    
    if new_methods_to_add:
        if new_methods_to_add[0].strip() != "":
            new_methods_to_add.insert(0, "")
        original_lines[class_end_line:class_end_line] = new_methods_to_add

    for start, end, new_lines in replacements:
        original_lines[start:end] = new_lines
        
    return original_lines
