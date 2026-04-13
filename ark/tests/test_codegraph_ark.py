"""Tests for the Ark parser adapter in tools/codegraph/ark_parser_adapter.py."""
import sys
import tempfile
from pathlib import Path

import pytest

_ARK_ROOT = Path(__file__).resolve().parent.parent
_CODEGRAPH = _ARK_ROOT / "tools" / "codegraph"
_PARSER = _ARK_ROOT / "tools" / "parser"
for _d in (_CODEGRAPH, _PARSER):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from ark_parser_adapter import parse_ark_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_ark(tmp_path: Path, content: str, name: str = "test.ark") -> Path:
    """Write ark source to a temp file and return its path."""
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _nodes_by_type(nodes, node_type):
    return [n for n in nodes if n["type"] == node_type]


def _nodes_by_ark_kind(nodes, ark_kind):
    return [n for n in nodes if n.get("ark_kind") == ark_kind]


def _edges_by_kind(edges, kind):
    return [e for e in edges if e["kind"] == kind]


def _node_names(nodes):
    return {n["name"] for n in nodes}


# ---------------------------------------------------------------------------
# abstraction items → node type "class", ark_kind "abstraction"
# ---------------------------------------------------------------------------

_ABSTRACTION_SRC = """\
abstraction IMovable {
  @in{ throttle: Float }
  @out[]{ position: Float }
  invariant: throttle >= 0
}

abstraction IRenderable {
  @in{ dt: Float }
  @out[]{ frame: Float }
}
"""


def test_abstraction_creates_class_node(tmp_path):
    p = _write_ark(tmp_path, _ABSTRACTION_SRC)
    nodes, _ = parse_ark_file(p)
    abs_nodes = _nodes_by_ark_kind(nodes, "abstraction")
    names = _node_names(abs_nodes)
    assert "IMovable" in names
    assert "IRenderable" in names


def test_abstraction_node_type_is_class(tmp_path):
    p = _write_ark(tmp_path, _ABSTRACTION_SRC)
    nodes, _ = parse_ark_file(p)
    for node in _nodes_by_ark_kind(nodes, "abstraction"):
        assert node["type"] == "class"


def test_abstraction_module_field(tmp_path):
    p = _write_ark(tmp_path, _ABSTRACTION_SRC)
    nodes, _ = parse_ark_file(p)
    for node in _nodes_by_ark_kind(nodes, "abstraction"):
        assert node["module"] == p.name


# ---------------------------------------------------------------------------
# class items → node type "class", ark_kind "class"
# ---------------------------------------------------------------------------

_CLASS_SRC = """\
abstraction IBase {
  @in{ x: Float }
  @out[]{ y: Float }
}

class Vehicle : IBase {
  $data speed: Float = 0.0
  @in{ x: Float }
  @out[]{ y: Float }
}
"""


def test_class_creates_node(tmp_path):
    p = _write_ark(tmp_path, _CLASS_SRC)
    nodes, _ = parse_ark_file(p)
    class_nodes = _nodes_by_ark_kind(nodes, "class")
    assert any(n["name"] == "Vehicle" for n in class_nodes)


def test_class_node_type_is_class(tmp_path):
    p = _write_ark(tmp_path, _CLASS_SRC)
    nodes, _ = parse_ark_file(p)
    vehicle = next(n for n in nodes if n["name"] == "Vehicle")
    assert vehicle["type"] == "class"
    assert vehicle["ark_kind"] == "class"


def test_class_inheritance_produces_inherits_edge(tmp_path):
    p = _write_ark(tmp_path, _CLASS_SRC)
    nodes, edges = parse_ark_file(p)
    inherit_edges = _edges_by_kind(edges, "inherits")
    assert any(e["source"] == "Vehicle" and e["target"] == "IBase"
               for e in inherit_edges)


# ---------------------------------------------------------------------------
# instance items → node type "class", ark_kind "instance"
# ---------------------------------------------------------------------------

_INSTANCE_SRC = """\
class Car {
  $data speed: Float = 0.0
  @in{ throttle: Float }
  @out[]{ speed: Float }
}

instance myCar : Car {}

instance raceCar : Car {}
"""


def test_instance_creates_node(tmp_path):
    p = _write_ark(tmp_path, _INSTANCE_SRC)
    nodes, _ = parse_ark_file(p)
    inst_nodes = _nodes_by_ark_kind(nodes, "instance")
    names = _node_names(inst_nodes)
    assert "myCar" in names
    assert "raceCar" in names


def test_instance_node_type_is_class(tmp_path):
    p = _write_ark(tmp_path, _INSTANCE_SRC)
    nodes, _ = parse_ark_file(p)
    for node in _nodes_by_ark_kind(nodes, "instance"):
        assert node["type"] == "class"


# ---------------------------------------------------------------------------
# island items → node type "module", ark_kind "island"
# ---------------------------------------------------------------------------

_ISLAND_SRC = """\
class Worker {
  @in{ task: Float }
  @out[]{ result: Float }
}

island WorkerPool {
  contains: [Worker]
  $data count: Int = 0
  @in{ tick: Float }
  @out[]{ results: Float }
}
"""


def test_island_creates_module_node(tmp_path):
    p = _write_ark(tmp_path, _ISLAND_SRC)
    nodes, _ = parse_ark_file(p)
    island_nodes = _nodes_by_ark_kind(nodes, "island")
    assert any(n["name"] == "WorkerPool" for n in island_nodes)


def test_island_node_type_is_module(tmp_path):
    p = _write_ark(tmp_path, _ISLAND_SRC)
    nodes, _ = parse_ark_file(p)
    island = next(n for n in nodes if n.get("ark_kind") == "island")
    assert island["type"] == "module"


def test_island_contains_edge(tmp_path):
    p = _write_ark(tmp_path, _ISLAND_SRC)
    nodes, edges = parse_ark_file(p)
    contains_edges = _edges_by_kind(edges, "contains")
    assert any(e["source"] == "WorkerPool" and e["target"] == "Worker"
               for e in contains_edges)


# ---------------------------------------------------------------------------
# bridge items → ark_bridge edge (no node emitted)
# ---------------------------------------------------------------------------

_BRIDGE_SRC = """\
island SystemA {
  @out[]{ out_data: Float }
}

island SystemB {
  @in{ in_data: Float }
}

bridge A_to_B {
  from: SystemA.out_data
  to: SystemB.in_data
  contract {
    invariant: out_data > 0
  }
}
"""


def test_bridge_creates_ark_bridge_edge(tmp_path):
    p = _write_ark(tmp_path, _BRIDGE_SRC)
    nodes, edges = parse_ark_file(p)
    bridge_edges = _edges_by_kind(edges, "ark_bridge")
    assert len(bridge_edges) == 1
    e = bridge_edges[0]
    assert e["source"] == "SystemA.out_data"
    assert e["target"] == "SystemB.in_data"


def test_bridge_does_not_create_node(tmp_path):
    p = _write_ark(tmp_path, _BRIDGE_SRC)
    nodes, _ = parse_ark_file(p)
    # No node should have ark_kind "bridge"
    assert not any(n.get("ark_kind") == "bridge" for n in nodes)


# ---------------------------------------------------------------------------
# expression items → node type "function", ark_kind "expression"
# ---------------------------------------------------------------------------

_EXPRESSION_SRC = """\
expression double-value {
  in: x: Float
  out: Float
  chain: x * 2.0
}

expression clamp-value {
  in: x: Float, lo: Float, hi: Float
  out: Float
  chain: x
}
"""


def test_expression_creates_function_node(tmp_path):
    p = _write_ark(tmp_path, _EXPRESSION_SRC)
    nodes, _ = parse_ark_file(p)
    expr_nodes = _nodes_by_ark_kind(nodes, "expression")
    names = _node_names(expr_nodes)
    assert "double-value" in names
    assert "clamp-value" in names


def test_expression_node_type_is_function(tmp_path):
    p = _write_ark(tmp_path, _EXPRESSION_SRC)
    nodes, _ = parse_ark_file(p)
    for node in _nodes_by_ark_kind(nodes, "expression"):
        assert node["type"] == "function"


# ---------------------------------------------------------------------------
# predicate items → node type "function", ark_kind "predicate"
# ---------------------------------------------------------------------------

_PREDICATE_SRC = """\
predicate is-positive {
  in: x: Float
  check: x > 0
}

predicate is-bounded {
  in: x: Float, lo: Float, hi: Float
  check: x >= lo
}
"""


def test_predicate_creates_function_node(tmp_path):
    p = _write_ark(tmp_path, _PREDICATE_SRC)
    nodes, _ = parse_ark_file(p)
    pred_nodes = _nodes_by_ark_kind(nodes, "predicate")
    names = _node_names(pred_nodes)
    assert "is-positive" in names
    assert "is-bounded" in names


def test_predicate_node_type_is_function(tmp_path):
    p = _write_ark(tmp_path, _PREDICATE_SRC)
    nodes, _ = parse_ark_file(p)
    for node in _nodes_by_ark_kind(nodes, "predicate"):
        assert node["type"] == "function"


# ---------------------------------------------------------------------------
# struct items → node type "class", ark_kind "struct"
# ---------------------------------------------------------------------------

_STRUCT_SRC = """\
struct Vec3 { x: Float, y: Float, z: Float }

struct BoundingBox { min: Vec3, max: Vec3 }
"""


def test_struct_creates_class_node(tmp_path):
    p = _write_ark(tmp_path, _STRUCT_SRC)
    nodes, _ = parse_ark_file(p)
    struct_nodes = _nodes_by_ark_kind(nodes, "struct")
    names = _node_names(struct_nodes)
    assert "Vec3" in names
    assert "BoundingBox" in names


def test_struct_node_type_is_class(tmp_path):
    p = _write_ark(tmp_path, _STRUCT_SRC)
    nodes, _ = parse_ark_file(p)
    for node in _nodes_by_ark_kind(nodes, "struct"):
        assert node["type"] == "class"


# ---------------------------------------------------------------------------
# enum items → node type "class", ark_kind "enum"
# ---------------------------------------------------------------------------

_ENUM_SRC = """\
enum Strategy { Tensor, Code, Verified }

enum Phase { Init, Running, Done }
"""


def test_enum_creates_class_node(tmp_path):
    p = _write_ark(tmp_path, _ENUM_SRC)
    nodes, _ = parse_ark_file(p)
    enum_nodes = _nodes_by_ark_kind(nodes, "enum")
    names = _node_names(enum_nodes)
    assert "Strategy" in names
    assert "Phase" in names


def test_enum_node_type_is_class(tmp_path):
    p = _write_ark(tmp_path, _ENUM_SRC)
    nodes, _ = parse_ark_file(p)
    for node in _nodes_by_ark_kind(nodes, "enum"):
        assert node["type"] == "class"


# ---------------------------------------------------------------------------
# Ignored kinds: registry, verify — no nodes or edges emitted
# ---------------------------------------------------------------------------

_IGNORED_SRC = """\
class MySystem {
  @in{ x: Float }
  @out[]{ y: Float }
}

island MyIsland {
  contains: [MySystem]
}

registry SystemRegistry {
  register MyIsland { phase: runtime, priority: 10 }
}

verify MySystem {
  check x_positive: x >= 0
}
"""


def test_registry_and_verify_not_emitted_as_nodes(tmp_path):
    p = _write_ark(tmp_path, _IGNORED_SRC)
    nodes, _ = parse_ark_file(p)
    ark_kinds = {n.get("ark_kind") for n in nodes}
    assert "registry" not in ark_kinds
    assert "verify" not in ark_kinds


# ---------------------------------------------------------------------------
# Comprehensive snippet — all mapped kinds together
# ---------------------------------------------------------------------------

_COMPREHENSIVE_SRC = """\
struct Coord { x: Float, y: Float }

enum Direction { North, South, East, West }

abstraction IAgent {
  @in{ cmd: Float }
  @out[]{ pos: Float }
}

class Agent : IAgent {
  $data pos: Float = 0.0
  @in{ cmd: Float }
  @out[]{ pos: Float }
}

instance agent1 : Agent {}

island AgentWorld {
  contains: [Agent]
  @in{ tick: Float }
  @out[]{ states: Float }
}

bridge World_to_Renderer {
  from: AgentWorld.states
  to: Renderer.frames
  contract {
    invariant: states > 0
  }
}

expression scale-value {
  in: v: Float, s: Float
  out: Float
  chain: v * s
}

predicate is-alive {
  in: hp: Float
  check: hp > 0
}
"""


def test_comprehensive_node_counts(tmp_path):
    p = _write_ark(tmp_path, _COMPREHENSIVE_SRC)
    nodes, edges = parse_ark_file(p)

    ark_kinds = {}
    for n in nodes:
        k = n.get("ark_kind", "?")
        ark_kinds[k] = ark_kinds.get(k, 0) + 1

    assert ark_kinds.get("struct", 0) == 1
    assert ark_kinds.get("enum", 0) == 1
    assert ark_kinds.get("abstraction", 0) == 1
    assert ark_kinds.get("class", 0) == 1
    assert ark_kinds.get("instance", 0) == 1
    assert ark_kinds.get("island", 0) == 1
    assert ark_kinds.get("expression", 0) == 1
    assert ark_kinds.get("predicate", 0) == 1


def test_comprehensive_bridge_edge(tmp_path):
    p = _write_ark(tmp_path, _COMPREHENSIVE_SRC)
    nodes, edges = parse_ark_file(p)
    bridge_edges = _edges_by_kind(edges, "ark_bridge")
    assert len(bridge_edges) == 1
    assert bridge_edges[0]["source"] == "AgentWorld.states"
    assert bridge_edges[0]["target"] == "Renderer.frames"


def test_comprehensive_inherits_edge(tmp_path):
    p = _write_ark(tmp_path, _COMPREHENSIVE_SRC)
    nodes, edges = parse_ark_file(p)
    inherit_edges = _edges_by_kind(edges, "inherits")
    assert any(e["source"] == "Agent" and e["target"] == "IAgent"
               for e in inherit_edges)


def test_comprehensive_contains_edge(tmp_path):
    p = _write_ark(tmp_path, _COMPREHENSIVE_SRC)
    nodes, edges = parse_ark_file(p)
    contains_edges = _edges_by_kind(edges, "contains")
    assert any(e["source"] == "AgentWorld" and e["target"] == "Agent"
               for e in contains_edges)


def test_comprehensive_all_nodes_have_required_fields(tmp_path):
    p = _write_ark(tmp_path, _COMPREHENSIVE_SRC)
    nodes, _ = parse_ark_file(p)
    for node in nodes:
        assert "name" in node
        assert "type" in node
        assert "module" in node
        assert "ark_kind" in node


def test_comprehensive_all_edges_have_required_fields(tmp_path):
    p = _write_ark(tmp_path, _COMPREHENSIVE_SRC)
    _, edges = parse_ark_file(p)
    for edge in edges:
        assert "source" in edge
        assert "target" in edge
        assert "kind" in edge
        assert "module" in edge


# ---------------------------------------------------------------------------
# Module field matches file name
# ---------------------------------------------------------------------------

def test_module_matches_filename(tmp_path):
    p = _write_ark(tmp_path, _CLASS_SRC, name="my_system.ark")
    nodes, edges = parse_ark_file(p)
    for node in nodes:
        assert node["module"] == "my_system.ark"
    for edge in edges:
        assert edge["module"] == "my_system.ark"


# ---------------------------------------------------------------------------
# Empty file — no crashes
# ---------------------------------------------------------------------------

def test_empty_ark_file(tmp_path):
    p = _write_ark(tmp_path, "")
    nodes, edges = parse_ark_file(p)
    assert isinstance(nodes, list)
    assert isinstance(edges, list)


# ---------------------------------------------------------------------------
# Multiple bridges → multiple ark_bridge edges
# ---------------------------------------------------------------------------

def test_multiple_bridges(tmp_path):
    src = """\
island A {
  @out[]{ x: Float }
}

island B {
  @out[]{ y: Float }
}

island C {
  @in{ x: Float }
}

bridge A_to_C {
  from: A.x
  to: C.x
  contract { invariant: x > 0 }
}

bridge B_to_C {
  from: B.y
  to: C.x
  contract { invariant: y > 0 }
}
"""
    p = _write_ark(tmp_path, src)
    nodes, edges = parse_ark_file(p)
    bridge_edges = _edges_by_kind(edges, "ark_bridge")
    assert len(bridge_edges) == 2
    sources = {e["source"] for e in bridge_edges}
    assert "A.x" in sources
    assert "B.y" in sources
