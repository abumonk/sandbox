"""Unit tests for the four ARK primitives (@in, @out, #process, $data)
plus invariant/temporal statements.

Each test wraps the primitive in a minimal enclosing class and asserts on
the resulting class AST.
"""

import pytest


def _cls(parse_src, body: str) -> dict:
    return parse_src("class C { " + body + " }")["items"][0]


# ---------------------------------------------------------------
# @in port
# ---------------------------------------------------------------

def test_in_port_with_fields(parse_src):
    cls = _cls(parse_src, "@in{ throttle: Float, dt: Float }")
    assert len(cls["in_ports"]) == 1
    ip = cls["in_ports"][0]
    assert ip["kind"] == "in_port"
    names = [f["name"] for f in ip["fields"]]
    assert names == ["throttle", "dt"]
    assert ip["fields"][0]["type"]["name"] == "Float"


# ---------------------------------------------------------------
# @out port
# ---------------------------------------------------------------

def test_out_port_with_meta(parse_src):
    cls = _cls(parse_src, "@out[guaranteed: true]{ speed: Float }")
    assert len(cls["out_ports"]) == 1
    op = cls["out_ports"][0]
    assert op["kind"] == "out_port"
    assert len(op["fields"]) == 1
    assert op["fields"][0]["name"] == "speed"
    # meta carries guaranteed: true
    assert any(
        m["key"] == "guaranteed"
        and m["value"] == {"expr": "bool", "value": True}
        for m in op["meta"]
    )


# ---------------------------------------------------------------
# #process rule (with pre / post)
# ---------------------------------------------------------------

def test_process_rule_with_pre_post(parse_src):
    body = """
    #process[strategy: tensor, priority: 10]{
      pre: x > 0
      y = x + 1
      post: y > x
    }
    """
    cls = _cls(parse_src, body)
    assert len(cls["processes"]) == 1
    p = cls["processes"][0]
    assert p["kind"] == "process"
    assert len(p["pre"]) == 1
    assert len(p["post"]) == 1
    assert len(p["body"]) == 1  # one assignment
    assert p["pre"][0]["op"] == ">"
    assert p["post"][0]["op"] == ">"
    # meta carries strategy + priority
    keys = {m["key"] for m in p["meta"]}
    assert keys == {"strategy", "priority"}


def test_process_rule_with_empty_meta(parse_src):
    """Regression: #process[]{} must parse — empty meta brackets are allowed.

    Previously the grammar required at least one meta_pair, so vehicle_physics.ark
    failed with "unexpected character ']'". Fixed by making meta_pair_list optional
    inside meta_brackets (EmptyProcessMetaTask).
    """
    cls = _cls(parse_src, "#process[]{ pre: x > 0 }")
    assert len(cls["processes"]) == 1
    p = cls["processes"][0]
    assert p["kind"] == "process"
    assert p["meta"] == []
    assert len(p["pre"]) == 1


def test_process_rule_with_no_meta_brackets(parse_src):
    """The meta brackets themselves are optional — #process{} must still parse."""
    cls = _cls(parse_src, "#process{ pre: x > 0 }")
    p = cls["processes"][0]
    assert p["meta"] == []


def test_process_rule_requires_is_alias_for_pre(parse_src):
    """`requires:` is accepted as a synonym for `pre:` and lands in the same
    list. Introduced by RequiresStmtTask to unblock vehicle_physics.ark.
    """
    cls = _cls(parse_src, "#process[]{ requires: x > 0 }")
    p = cls["processes"][0]
    assert len(p["pre"]) == 1
    assert p["pre"][0]["op"] == ">"
    # body stays empty — requires does NOT fall into the body bucket
    assert p["body"] == []


def test_data_prefix_in_expression_is_alias_for_ident(parse_src):
    """`$data IDENT` inside an expression is an explicit marker for a data
    field reference and lowers to the same ident-expr as bare IDENT.
    Introduced by DataPrefixExprTask.
    """
    cls = _cls(parse_src, "#process[]{ requires: $data fuel > 0 }")
    p = cls["processes"][0]
    assert len(p["pre"]) == 1
    e = p["pre"][0]
    assert e["op"] == ">"
    assert e["left"] == {"expr": "ident", "name": "fuel"}
    assert e["right"] == {"expr": "number", "value": 0}


def test_data_prefix_equivalent_to_bare_ident(parse_src):
    """`$data x` and bare `x` produce identical AST nodes."""
    cls_prefixed = _cls(parse_src, "#process[]{ pre: $data x > 0 }")
    cls_bare = _cls(parse_src, "#process[]{ pre: x > 0 }")
    assert cls_prefixed["processes"][0]["pre"][0] == cls_bare["processes"][0]["pre"][0]


# ---------------------------------------------------------------
# $data field — range constraint
# ---------------------------------------------------------------

def test_data_field_with_range_constraint(parse_src):
    cls = _cls(parse_src, "$data fuel: Float [0..100] = 50")
    assert len(cls["data_fields"]) == 1
    f = cls["data_fields"][0]
    assert f["name"] == "fuel"
    assert f["type"]["name"] == "Float"
    c = f["constraint"]
    assert c is not None
    assert c["constraint"] == "range"
    # range bounds are expr nodes
    assert c["min"] == {"expr": "number", "value": 0}
    assert c["max"] == {"expr": "number", "value": 100}
    assert f["default"] == {"expr": "number", "value": 50}


# ---------------------------------------------------------------
# $data field — enum constraint
# ---------------------------------------------------------------

def test_data_field_with_enum_constraint(parse_src):
    # Grammar: constraint = "{" expr_list "}" — string literals are exprs,
    # so {"todo", "done"} should parse as an enum_constraint of two strings.
    cls = _cls(parse_src, '$data status: String {"todo", "done"}')
    f = cls["data_fields"][0]
    assert f["name"] == "status"
    c = f["constraint"]
    assert c is not None
    assert c["constraint"] == "enum"
    assert len(c["values"]) == 2
    # The STRING terminal returns the literal including quotes
    assert all(v["expr"] == "string" for v in c["values"])


# ---------------------------------------------------------------
# invariant / temporal
# ---------------------------------------------------------------

def test_invariant_statement(parse_src):
    cls = _cls(parse_src, "invariant: fuel >= 0")
    assert len(cls["invariants"]) == 1
    inv = cls["invariants"][0]
    assert inv["expr"] == "binop"
    assert inv["op"] == ">="


def test_temporal_statement(parse_src):
    # Grammar: TEMPORAL_OP includes "□" → unary temporal expression
    cls = _cls(parse_src, "temporal: □(fuel >= 0)")
    assert len(cls["temporals"]) == 1
    t = cls["temporals"][0]
    assert t["expr"] == "temporal"
    assert t["op"] == "□"
    # operand is the parenthesised comparison
    assert t["operand"]["expr"] == "binop"
    assert t["operand"]["op"] == ">="
