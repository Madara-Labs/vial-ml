import ast
from typing import Set


class DependencyVisitor(ast.NodeVisitor):
    def __init__(self, target_name: str):
        self.target_name = target_name
        self.in_target = False
        self.used_names: Set[str] = set()
        self.used_self_attrs: Set[str] = set()

    def visit_FunctionDef(self, node):
        was_in_target = self.in_target
        if node.name == self.target_name:
            self.in_target = True
        self.generic_visit(node)
        self.in_target = was_in_target

    def visit_AsyncFunctionDef(self, node):
        was_in_target = self.in_target
        if node.name == self.target_name:
            self.in_target = True
        self.generic_visit(node)
        self.in_target = was_in_target

    def visit_ClassDef(self, node):
        was_in_target = self.in_target
        if node.name == self.target_name:
            self.in_target = True
        self.generic_visit(node)
        self.in_target = was_in_target

    def visit_Name(self, node):
        if self.in_target and isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if self.in_target and isinstance(node.value, ast.Name) and node.value.id == "self":
            self.used_self_attrs.add(node.attr)
        self.generic_visit(node)


def _get_stub(node: ast.AST, lines: list[str]) -> list[str]:
    """Return the signature and docstring of a function/class."""
    has_docstring = False
    end_line = node.lineno
    if hasattr(node, "body") and node.body:
        first_stmt = node.body[0]
        if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant) and isinstance(first_stmt.value.value, str):
            has_docstring = True
            end_line = first_stmt.end_lineno
        else:
            end_line = first_stmt.lineno - 1

    stub_lines = lines[node.lineno - 1 : end_line]
    if not has_docstring:
        indent = " " * (node.col_offset + 4)
        stub_lines.append(f"{indent}pass  # stub")
    
    return stub_lines


def extract_context(source_code: str, target_name: str) -> str:
    """Return dependency-aware context block (imports, constants, and stubs)."""
    if not source_code.strip():
        return ""

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return ""

    visitor = DependencyVisitor(target_name)
    visitor.visit(tree)
    used_names = visitor.used_names
    used_self_attrs = visitor.used_self_attrs

    target_class_node = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for body_node in node.body:
                if isinstance(body_node, (ast.FunctionDef, ast.AsyncFunctionDef)) and body_node.name == target_name:
                    target_class_node = node
                    break
            if target_class_node:
                break

    lines = source_code.splitlines()
    collected: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.asname in used_names or alias.name in used_names for alias in node.names):
                collected.extend(lines[node.lineno - 1 : node.end_lineno])
        elif isinstance(node, ast.ImportFrom):
            if any(alias.asname in used_names or alias.name in used_names for alias in node.names):
                collected.extend(lines[node.lineno - 1 : node.end_lineno])
            elif node.module and node.module.split('.')[0] in used_names:
                collected.extend(lines[node.lineno - 1 : node.end_lineno])
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id in used_names:
                    collected.extend(lines[node.lineno - 1 : node.end_lineno])
                    break
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in used_names and node.name != target_name:
                collected.extend(_get_stub(node, lines))
        elif isinstance(node, ast.ClassDef):
            if node.name in used_names and node.name != target_name:
                collected.extend(_get_stub(node, lines))
            elif node == target_class_node:
                collected.extend(_get_stub(node, lines))
                for class_body_node in node.body:
                    if isinstance(class_body_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if class_body_node.name in used_self_attrs and class_body_node.name != target_name:
                            collected.extend(_get_stub(class_body_node, lines))

    return "\n".join(collected)
