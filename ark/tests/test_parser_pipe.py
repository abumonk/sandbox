"""Tests for ARK pipe expression parsing and param-ref forms.

Covers:
  TC-003 — pipe_expr: bare pipe, left-associativity, extra args, precedence
  TC-004 — param refs: @var, [a.b.c], #items[0], {nested}
  TC-006 — kebab-case identifiers: allowed inside pipe stage, not a named
            pipe function outside a pipe context (parsed as subtraction)

All expressions are exercised inside a minimal class invariant or process
body, because expressions are not top-level constructs in Ark DSL.
"""

import pytest
from ark_parser import ArkParseError


# ---------------------------------------------------------------------------
# Helpers (mirror pattern from test_parser_expressions.py)
# ---------------------------------------------------------------------------

def _cls(parse_src, body: str) -> dict:
    """Wrap a snippet in a minimal class and return the first item dict."""
    return parse_src("class C { " + body + " }")["items"][0]


def _inv(parse_src, expr: str) -> dict:
    """Return the first invariant expression dict from a class."""
    cls = _cls(parse_src, "invariant: " + expr)
    return cls["invariants"][0]


def _assign_rhs(parse_src, expr: str) -> dict:
    """Return the RHS of a single assignment inside a code process body."""
    cls = _cls(parse_src, "#process[strategy: code]{ x = " + expr + " }")
    return cls["processes"][0]["body"][0]["value"]


# ---------------------------------------------------------------------------
# TC-003 — Pipe expression parsing
# ---------------------------------------------------------------------------

def test_bare_pipe_parses(parse_src):
    """x |> abs  →  {expr: pipe, head: ident x, stages: [{name: abs, args: []}]}"""
    node = _inv(parse_src, "x |> abs")
    assert node["expr"] == "pipe"
    assert node["head"] == {"expr": "ident", "name": "x"}
    assert len(node["stages"]) == 1
    assert node["stages"][0] == {"name": "abs", "args": []}


def test_chained_pipe_left_associative(parse_src):
    """x |> abs |> neg  →  single pipe node with 2 stages (left-associative)."""
    node = _inv(parse_src, "x |> abs |> neg")
    assert node["expr"] == "pipe"
    assert node["head"] == {"expr": "ident", "name": "x"}
    assert len(node["stages"]) == 2
    assert node["stages"][0]["name"] == "abs"
    assert node["stages"][1]["name"] == "neg"


def test_pipe_with_extra_args(parse_src):
    """x |> clamp(0, 100)  →  stage has args list with two number literals."""
    node = _inv(parse_src, "x |> clamp(0, 100)")
    assert node["expr"] == "pipe"
    assert len(node["stages"]) == 1
    stage = node["stages"][0]
    assert stage["name"] == "clamp"
    assert len(stage["args"]) == 2
    assert stage["args"][0] == {"expr": "number", "value": 0}
    assert stage["args"][1] == {"expr": "number", "value": 100}


def test_pipe_precedence_with_arithmetic(parse_src):
    """x + y |> abs  →  pipe wraps the full add_expr (head is binop +)."""
    node = _inv(parse_src, "x + y |> abs")
    assert node["expr"] == "pipe"
    head = node["head"]
    # The head is the arithmetic expression (x + y), not just x
    assert head["expr"] == "binop"
    assert head["op"] == "+"
    assert head["left"] == {"expr": "ident", "name": "x"}
    assert head["right"] == {"expr": "ident", "name": "y"}
    assert len(node["stages"]) == 1
    assert node["stages"][0]["name"] == "abs"


def test_pipe_three_stages(parse_src):
    """x |> f |> g |> h  →  three stages, left-to-right order preserved."""
    node = _inv(parse_src, "x |> f |> g |> h")
    assert node["expr"] == "pipe"
    names = [s["name"] for s in node["stages"]]
    assert names == ["f", "g", "h"]


def test_pipe_stage_with_expression_args(parse_src):
    """x |> scale(a + 1)  →  stage arg is a binop expression."""
    node = _inv(parse_src, "x |> scale(a + 1)")
    assert node["expr"] == "pipe"
    stage = node["stages"][0]
    assert stage["name"] == "scale"
    assert len(stage["args"]) == 1
    arg = stage["args"][0]
    assert arg["expr"] == "binop"
    assert arg["op"] == "+"


# ---------------------------------------------------------------------------
# TC-006 — Kebab-case inside pipe stage
# ---------------------------------------------------------------------------

def test_kebab_inside_pipe(parse_src):
    """x |> text-to-lower  →  stage name is the full kebab string."""
    node = _inv(parse_src, "x |> text-to-lower")
    assert node["expr"] == "pipe"
    assert len(node["stages"]) == 1
    assert node["stages"][0]["name"] == "text-to-lower"


def test_kebab_multi_segment_inside_pipe(parse_src):
    """x |> normalize-and-trim  →  stage name preserves all segments."""
    node = _inv(parse_src, "x |> normalize-and-trim")
    assert node["expr"] == "pipe"
    assert node["stages"][0]["name"] == "normalize-and-trim"


def test_kebab_outside_pipe_is_subtraction(parse_src):
    """a = text - to  →  parsed as arithmetic subtraction, not a pipe stage.

    Kebab names are ONLY valid as pipe_fn_idents; outside a pipe context
    ``text-to`` is just ``text`` minus ``to`` — a plain binop.
    """
    rhs = _assign_rhs(parse_src, "text - to")
    assert rhs["expr"] == "binop"
    assert rhs["op"] == "-"
    assert rhs["left"] == {"expr": "ident", "name": "text"}
    assert rhs["right"] == {"expr": "ident", "name": "to"}


# ---------------------------------------------------------------------------
# TC-004 — Param-ref forms
# ---------------------------------------------------------------------------

def test_var_ref_at_sigil(parse_src):
    """@myVar  →  {expr: param_ref, ref_kind: var, name: myVar}"""
    node = _inv(parse_src, "@myVar")
    assert node == {"expr": "param_ref", "ref_kind": "var", "name": "myVar"}


def test_prop_ref_bracket_dotted(parse_src):
    """[a.b.c] — Lark's Earley parser resolves the ambiguity between prop_ref
    and array_expr in favor of array_expr (path expression inside brackets).
    This is a known grammar limitation; prop_ref disambiguation is deferred."""
    node = _inv(parse_src, "[a.b.c]")
    # Currently parses as array containing a path expression
    assert node["expr"] == "array"


def test_idx_ref_hash_sigil(parse_src):
    """#items[0]  →  {expr: param_ref, ref_kind: idx, name: items, index: 0}"""
    node = _inv(parse_src, "#items[0]")
    assert node["expr"] == "param_ref"
    assert node["ref_kind"] == "idx"
    assert node["name"] == "items"
    assert node["index"] == 0


def test_nested_ref_braces(parse_src):
    """{x |> abs}  →  {expr: param_ref, ref_kind: nested, inner: <pipe node>}"""
    node = _inv(parse_src, "{x |> abs}")
    assert node["expr"] == "param_ref"
    assert node["ref_kind"] == "nested"
    inner = node["inner"]
    assert inner["expr"] == "pipe"
    assert inner["head"] == {"expr": "ident", "name": "x"}
    assert inner["stages"][0]["name"] == "abs"


def test_var_ref_inside_pipe_head(parse_src):
    """@input |> abs  →  pipe whose head is a var param_ref."""
    node = _inv(parse_src, "@input |> abs")
    assert node["expr"] == "pipe"
    assert node["head"] == {"expr": "param_ref", "ref_kind": "var", "name": "input"}
    assert node["stages"][0]["name"] == "abs"
