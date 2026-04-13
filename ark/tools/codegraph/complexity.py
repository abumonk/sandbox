"""
Cyclomatic complexity calculator for Python and Rust source code.

Cyclomatic complexity = 1 + number of decision points (branches).
Decision points increase the number of linearly independent paths through code.
"""

import ast
import re
from typing import Optional


# ---------------------------------------------------------------------------
# Python complexity
# ---------------------------------------------------------------------------

_PYTHON_DECISION_NODES = (
    ast.If,
    ast.For,
    ast.While,
    ast.ExceptHandler,
    ast.With,
    ast.Assert,
    ast.comprehension,
)


class _ComplexityVisitor(ast.NodeVisitor):
    """AST visitor that counts decision points for cyclomatic complexity."""

    def __init__(self):
        self.complexity = 1  # base complexity

    def visit_If(self, node: ast.If):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert):
        self.complexity += 1
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        # Each `and`/`or` operator adds one branch per additional operand.
        # e.g. `a and b and c` has 2 `and` operators => +2
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


def python_complexity(source: str, func_name: Optional[str] = None) -> dict:
    """Calculate cyclomatic complexity for Python source code.

    Parameters
    ----------
    source:
        Python source code as a string.
    func_name:
        Optional name to attach to the result dict.  When *None* the
        complexity is calculated for the whole module.

    Returns
    -------
    dict with keys ``name``, ``complexity``, ``language``.
    """
    tree = ast.parse(source)
    visitor = _ComplexityVisitor()
    visitor.visit(tree)
    return {
        "name": func_name,
        "complexity": visitor.complexity,
        "language": "python",
    }


def python_function_complexities(source: str) -> list:
    """Calculate cyclomatic complexity per function in a Python source file.

    Parameters
    ----------
    source:
        Python source code as a string.

    Returns
    -------
    List of dicts, each with keys ``name``, ``complexity``, ``language``.
    """
    tree = ast.parse(source)
    results = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Build a minimal module wrapping just this function so the
            # visitor sees the function body as a complete tree.
            func_module = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(func_module)
            visitor = _ComplexityVisitor()
            # Start from complexity 0 so the function itself counts as 1.
            # The visitor starts at 1 (base), which is correct: each
            # function has complexity >= 1.
            visitor.visit(func_module)
            results.append(
                {
                    "name": node.name,
                    "complexity": visitor.complexity,
                    "language": "python",
                }
            )

    return results


# ---------------------------------------------------------------------------
# Rust complexity
# ---------------------------------------------------------------------------

# Patterns that add a branch in Rust code.
_RUST_DECISION_PATTERNS = [
    r"\bif\b",       # if expression
    r"\bmatch\b",    # match expression
    r"\bfor\b",      # for loop
    r"\bwhile\b",    # while loop
    r"\bloop\b",     # infinite loop
    r"&&",           # logical and
    r"\|\|",         # logical or
    r"\?",           # error-propagation operator
]

_RUST_DECISION_RE = re.compile("|".join(_RUST_DECISION_PATTERNS))


def _rust_body_complexity(body: str) -> int:
    """Count decision points in a chunk of Rust source text."""
    return 1 + len(_RUST_DECISION_RE.findall(body))


# Regex to locate Rust function definitions.
# Matches: optional `pub`/`pub(...)`, optional `async`, `fn name`, then
# captures from the opening `{` through a balanced-brace scan done in Python.
_RUST_FN_HEADER_RE = re.compile(
    r"(?:pub(?:\s*\([^)]*\))?\s+)?(?:async\s+)?fn\s+(\w+)\s*[^{]*\{",
    re.MULTILINE,
)


def _extract_rust_functions(source: str) -> list:
    """Return list of (name, body_text) pairs for each Rust function."""
    functions = []
    for m in _RUST_FN_HEADER_RE.finditer(source):
        name = m.group(1)
        # Walk forward from the opening `{` to find the matching `}`.
        start = m.end() - 1  # position of the `{`
        depth = 0
        i = start
        while i < len(source):
            ch = source[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = source[start : i + 1]
        functions.append((name, body))
    return functions


def rust_complexity(source: str, func_name: Optional[str] = None) -> dict:
    """Estimate cyclomatic complexity for Rust source code using regex.

    Parameters
    ----------
    source:
        Rust source code as a string.
    func_name:
        Optional label to include in the returned dict.

    Returns
    -------
    dict with keys ``name``, ``complexity``, ``language``.
    """
    return {
        "name": func_name,
        "complexity": _rust_body_complexity(source),
        "language": "rust",
    }


def rust_function_complexities(source: str) -> list:
    """Calculate cyclomatic complexity per function in a Rust source file.

    Parameters
    ----------
    source:
        Rust source code as a string.

    Returns
    -------
    List of dicts, each with keys ``name``, ``complexity``, ``language``.
    """
    results = []
    for name, body in _extract_rust_functions(source):
        results.append(
            {
                "name": name,
                "complexity": _rust_body_complexity(body),
                "language": "rust",
            }
        )
    return results
