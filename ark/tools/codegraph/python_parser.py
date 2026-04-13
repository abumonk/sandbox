"""Python source parser using ast module.

Extracts code graph nodes and edges from Python source files.
Output is compatible with GraphStore from graph_store.py.
"""
import ast
from pathlib import Path
from typing import Optional


def _get_call_name(node: ast.Call) -> Optional[str]:
    """Extract best-effort name from a Call node."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


class _Visitor(ast.NodeVisitor):
    """AST visitor that collects nodes and edges."""

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        # Stack of (qualified_name, kind) — 'class' or 'function'
        self._scope: list[tuple[str, str]] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current_class(self) -> Optional[str]:
        """Return the innermost enclosing class qualified name, or None."""
        for name, kind in reversed(self._scope):
            if kind == "class":
                return name
        return None

    def _current_function(self) -> Optional[str]:
        """Return the innermost enclosing function/method qualified name, or None."""
        for name, kind in reversed(self._scope):
            if kind in ("function", "method"):
                return name
        return None

    def _qualified(self, name: str) -> str:
        """Build a qualified name from current scope + name."""
        if self._scope:
            parent = self._scope[-1][0]
            return f"{parent}.{name}"
        return f"{self.module_name}.{name}"

    def _add_node(self, name: str, node_type: str, line: int, end_line: int):
        self.nodes.append({
            "name": name,
            "type": node_type,
            "module": self.module_name,
            "line": line,
            "end_line": end_line,
        })

    def _add_edge(self, source: str, target: str, kind: str, line: int):
        self.edges.append({
            "source": source,
            "target": target,
            "kind": kind,
            "module": self.module_name,
            "line": line,
        })

    # ------------------------------------------------------------------
    # Visitor methods
    # ------------------------------------------------------------------

    def visit_Import(self, node: ast.Import):
        """ast.Import — add 'imports' edges from the module to each imported name."""
        module_node = self.module_name
        for alias in node.names:
            target = alias.asname if alias.asname else alias.name
            self._add_edge(module_node, target, "imports", node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """ast.ImportFrom — 'from X import Y' → imports edge."""
        module_node = self.module_name
        from_module = node.module or ""
        for alias in node.names:
            if alias.name == "*":
                target = from_module
            else:
                target = f"{from_module}.{alias.name}" if from_module else alias.name
            self._add_edge(module_node, target, "imports", node.lineno)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """ast.ClassDef — emit class node and inheritance edges."""
        qualified = self._qualified(node.name)
        self._add_node(qualified, "class", node.lineno, node.end_lineno or node.lineno)

        # Inheritance edges
        for base in node.bases:
            if isinstance(base, ast.Name):
                self._add_edge(qualified, base.id, "inherits", node.lineno)
            elif isinstance(base, ast.Attribute):
                self._add_edge(qualified, base.attr, "inherits", node.lineno)

        # Visit body with class scope
        self._scope.append((qualified, "class"))
        self.generic_visit(node)
        self._scope.pop()

    def _visit_function(self, node):
        """Shared logic for FunctionDef and AsyncFunctionDef."""
        enclosing_class = self._current_class()
        is_method = enclosing_class is not None

        qualified = self._qualified(node.name)
        node_type = "method" if is_method else "function"
        self._add_node(qualified, node_type, node.lineno, node.end_lineno or node.lineno)

        # Push function scope and visit body for call edges
        self._scope.append((qualified, node_type))
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                callee = _get_call_name(child)
                if callee is not None:
                    self._add_edge(qualified, callee, "calls", child.lineno)
        # Still do generic_visit so nested classes/functions are processed
        self.generic_visit(node)
        self._scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_function(node)


def parse_python_source(source: str, module_name: str) -> tuple[list[dict], list[dict]]:
    """Parse Python source code and extract graph nodes and edges.

    Args:
        source: Python source code as a string.
        module_name: Logical module name (used as prefix for qualified names).

    Returns:
        (nodes, edges) — lists of dicts compatible with GraphStore.
    """
    try:
        tree = ast.parse(source, filename=f"{module_name}.py")
    except SyntaxError as exc:
        # Return a minimal error marker rather than crashing
        return [], []

    # Add the top-level module node
    nodes: list[dict] = [{
        "name": module_name,
        "type": "module",
        "module": module_name,
        "line": 1,
        "end_line": len(source.splitlines()),
    }]
    edges: list[dict] = []

    visitor = _Visitor(module_name)
    visitor.visit(tree)

    nodes.extend(visitor.nodes)
    edges.extend(visitor.edges)

    return nodes, edges


def parse_python_file(path: Path) -> tuple[list[dict], list[dict]]:
    """Parse a Python file and extract graph nodes and edges.

    Args:
        path: Path to the Python file.

    Returns:
        (nodes, edges) — lists of dicts compatible with GraphStore.
    """
    path = Path(path)
    source = path.read_text(encoding="utf-8", errors="replace")

    # Derive module name from file stem (strip .py)
    module_name = path.stem

    return parse_python_source(source, module_name)
