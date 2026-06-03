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


def extract_class_shape(source_code: str, class_name: str, target_methods: list[str]) -> ExtractionResult:
    """Extract a class, retaining full source for target_methods and stubbing the rest."""
    tree = ast.parse(source_code)
    lines = source_code.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            start = node.lineno - 1
            end = node.end_lineno
            indent = len(lines[start]) - len(lines[start].lstrip())
            indent_str = lines[start][:indent]
            
            methods = []
            for body_node in node.body:
                if isinstance(body_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if body_node.name not in target_methods:
                        methods.append(body_node)
            
            methods.sort(key=lambda n: n.lineno, reverse=True)
            
            class_lines = lines[start:end]
            
            for m in methods:
                m_start = (m.lineno - 1) - start
                m_end = m.end_lineno - start
                
                has_docstring = False
                stub_end = m.lineno
                if hasattr(m, "body") and m.body:
                    first_stmt = m.body[0]
                    if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant) and isinstance(first_stmt.value.value, str):
                        has_docstring = True
                        stub_end = first_stmt.end_lineno
                    else:
                        stub_end = first_stmt.lineno - 1
                
                stub_end_rel = stub_end - start
                stub_lines = class_lines[m_start:stub_end_rel]
                
                if not has_docstring:
                    m_indent = " " * (m.col_offset + 4)
                    stub_lines.append(f"{m_indent}pass  # stub")
                
                class_lines[m_start:m_end] = stub_lines
                
            raw = "\n".join(class_lines)
            return ExtractionResult(
                target_name=class_name,
                start_line=start,
                end_line=end,
                code=textwrap.dedent(raw),
                indent=indent_str,
            )

    raise ValueError(f"Class '{class_name}' not found in source.")
