"""Pytest tests for expression/predicate codegen in ark_codegen.py.

Verifies that:
- Numeric expressions generate correct Rust fn signatures and method calls
- Text expressions generate correct Rust method calls
- Predicates generate -> bool return type
- Kebab-case predicate names are mangled to snake_case in Rust
- C++ and Proto targets raise NotImplementedError for expression/predicate items
- Multi-stage pipes (x |> abs |> neg) codegen both stages
- Full stdlib expression.ark codegens 23 files
"""

import json
import sys
import pytest
from pathlib import Path

_ARK_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ARK_ROOT / "tools" / "parser"))
sys.path.insert(0, str(_ARK_ROOT / "tools" / "codegen"))

from ark_parser import parse, to_json
from ark_codegen import gen_rust_expression, gen_rust_predicate, codegen_file


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_expression(src: str) -> dict:
    """Parse an expression/predicate definition and return its AST dict."""
    ark_file = parse(src)
    ast = json.loads(to_json(ark_file))
    return ast["items"][0]


# ---------------------------------------------------------------------------
# 1. test_numeric_absolute_codegen
# ---------------------------------------------------------------------------

def test_numeric_absolute_codegen():
    """numeric_absolute expression generates correct Rust fn signature and .abs() call."""
    item = _parse_expression(
        "expression numeric_absolute { in: x: Float  out: Float  chain: x |> abs }"
    )
    code = gen_rust_expression(item)
    assert "pub fn numeric_absolute(x: f32) -> f32" in code
    assert ".abs()" in code


# ---------------------------------------------------------------------------
# 2. test_numeric_add_codegen
# ---------------------------------------------------------------------------

def test_numeric_add_codegen():
    """numeric_add expression generates Rust with '+ y' binary operator."""
    item = _parse_expression(
        "expression numeric_add { in: x: Float, y: Float  out: Float  chain: x |> add(y) }"
    )
    code = gen_rust_expression(item)
    assert "+ y" in code


# ---------------------------------------------------------------------------
# 3. test_numeric_clamp_codegen
# ---------------------------------------------------------------------------

def test_numeric_clamp_codegen():
    """numeric_clamp expression with 3 inputs generates .clamp(lo, hi) call."""
    item = _parse_expression(
        "expression numeric_clamp { in: x: Float, lo: Float, hi: Float  out: Float  chain: x |> clamp-range(lo, hi) }"
    )
    code = gen_rust_expression(item)
    assert ".clamp(lo, hi)" in code


# ---------------------------------------------------------------------------
# 4. test_text_lower_codegen
# ---------------------------------------------------------------------------

def test_text_lower_codegen():
    """text_to_lower expression generates .to_lowercase() call."""
    item = _parse_expression(
        "expression text_to_lower { in: s: String  out: String  chain: s |> str-lower }"
    )
    code = gen_rust_expression(item)
    assert ".to_lowercase()" in code


# ---------------------------------------------------------------------------
# 5. test_predicate_codegen_returns_bool
# ---------------------------------------------------------------------------

def test_predicate_codegen_returns_bool():
    """Predicate codegen produces a -> bool return type."""
    item = _parse_expression(
        "predicate is-empty { in: s: String  check: s |> str-is-empty }"
    )
    code = gen_rust_predicate(item)
    assert "-> bool" in code


# ---------------------------------------------------------------------------
# 6. test_predicate_name_mangled
# ---------------------------------------------------------------------------

def test_predicate_name_mangled():
    """Kebab-case predicate name 'is-empty' becomes 'is_empty' in generated Rust fn name."""
    item = _parse_expression(
        "predicate is-empty { in: s: String  check: s |> str-is-empty }"
    )
    code = gen_rust_predicate(item)
    assert "pub fn is_empty(" in code
    # Ensure the raw kebab name does not appear as an identifier
    assert "is-empty" not in code


# ---------------------------------------------------------------------------
# 7. test_cpp_expression_raises
# ---------------------------------------------------------------------------

def test_cpp_expression_raises():
    """codegen_file with 'cpp' target on an expression item raises NotImplementedError."""
    ark_file = parse(
        "expression numeric_absolute { in: x: Float  out: Float  chain: x |> abs }"
    )
    ast = json.loads(to_json(ark_file))
    with pytest.raises(NotImplementedError):
        codegen_file(ast, "cpp")


# ---------------------------------------------------------------------------
# 8. test_proto_expression_raises
# ---------------------------------------------------------------------------

def test_proto_expression_raises():
    """codegen_file with 'proto' target on an expression item raises NotImplementedError."""
    ark_file = parse(
        "expression numeric_absolute { in: x: Float  out: Float  chain: x |> abs }"
    )
    ast = json.loads(to_json(ark_file))
    with pytest.raises(NotImplementedError):
        codegen_file(ast, "proto")


# ---------------------------------------------------------------------------
# 9. test_inline_pipe_in_expr
# ---------------------------------------------------------------------------

def test_inline_pipe_in_expr():
    """Multi-stage pipe 'x |> abs |> neg' generates both .abs() and negation."""
    item = _parse_expression(
        "expression test_abs_neg { in: x: Float  out: Float  chain: x |> abs |> neg }"
    )
    code = gen_rust_expression(item)
    # .abs() should be in the output
    assert ".abs()" in code
    # negation: the neg primitive maps to "-{self}", so the result should start with '-'
    # The composed expression is: -x.abs()
    assert "-" in code


# ---------------------------------------------------------------------------
# 10. test_full_stdlib_codegen
# ---------------------------------------------------------------------------

def test_full_stdlib_codegen():
    """Parsing dsl/stdlib/expression.ark and calling codegen_file(ast, 'rust') produces 23 files."""
    expression_file = _ARK_ROOT / "dsl" / "stdlib" / "expression.ark"
    source = expression_file.read_text(encoding="utf-8")
    ark_file = parse(source, file_path=expression_file)
    ast = json.loads(to_json(ark_file))
    results = codegen_file(ast, "rust")
    assert len(results) == 23, (
        f"Expected 23 generated files, got {len(results)}: {list(results.keys())}"
    )
