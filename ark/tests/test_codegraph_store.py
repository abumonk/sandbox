"""Tests for GraphStore in tools/codegraph/graph_store.py."""
import sys
import json
from pathlib import Path

import pytest

# Inject codegraph onto sys.path
_ARK_ROOT = Path(__file__).resolve().parent.parent
_CODEGRAPH = _ARK_ROOT / "tools" / "codegraph"
if str(_CODEGRAPH) not in sys.path:
    sys.path.insert(0, str(_CODEGRAPH))

from graph_store import GraphStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _simple_call_graph() -> GraphStore:
    """Build a small call graph: main → foo → bar, main → baz."""
    g = GraphStore()
    for name, ntype in [("main", "function"), ("foo", "function"),
                        ("bar", "function"), ("baz", "function")]:
        g.add_node(name, ntype)
    g.add_edge("main", "foo", "calls")
    g.add_edge("main", "baz", "calls")
    g.add_edge("foo", "bar", "calls")
    return g


# ---------------------------------------------------------------------------
# add_node / get_node / get_nodes_by_type
# ---------------------------------------------------------------------------

def test_add_and_get_node():
    g = GraphStore()
    g.add_node("Foo", "class", module="mymod")
    node = g.get_node("Foo")
    assert node is not None
    assert node["type"] == "class"
    assert node["module"] == "mymod"


def test_get_node_missing_returns_none():
    g = GraphStore()
    assert g.get_node("nonexistent") is None


def test_add_node_overwrites_existing():
    g = GraphStore()
    g.add_node("X", "function")
    g.add_node("X", "method", module="m2")
    node = g.get_node("X")
    assert node["type"] == "method"
    assert node["module"] == "m2"


def test_get_nodes_by_type():
    g = GraphStore()
    g.add_node("A", "function")
    g.add_node("B", "class")
    g.add_node("C", "function")
    fns = g.get_nodes_by_type("function")
    names = {n["name"] for n in fns}
    assert names == {"A", "C"}
    classes = g.get_nodes_by_type("class")
    assert len(classes) == 1
    assert classes[0]["name"] == "B"


def test_get_nodes_by_type_empty():
    g = GraphStore()
    assert g.get_nodes_by_type("module") == []


# ---------------------------------------------------------------------------
# add_edge / get_edges_from / get_edges_to
# ---------------------------------------------------------------------------

def test_add_and_get_edges_from():
    g = _simple_call_graph()
    edges = g.get_edges_from("main")
    targets = {e["target"] for e in edges}
    assert targets == {"foo", "baz"}


def test_get_edges_from_filtered_by_kind():
    g = GraphStore()
    g.add_node("A", "function")
    g.add_node("B", "function")
    g.add_node("C", "class")
    g.add_edge("A", "B", "calls")
    g.add_edge("A", "C", "inherits")
    call_edges = g.get_edges_from("A", kind="calls")
    assert len(call_edges) == 1
    assert call_edges[0]["target"] == "B"


def test_get_edges_to():
    g = _simple_call_graph()
    edges = g.get_edges_to("foo")
    assert len(edges) == 1
    assert edges[0]["source"] == "main"


def test_get_edges_to_filtered():
    g = GraphStore()
    g.add_node("A", "function")
    g.add_node("B", "class")
    g.add_edge("A", "B", "calls")
    g.add_edge("A", "B", "inherits")
    call_only = g.get_edges_to("B", kind="calls")
    assert len(call_only) == 1


def test_get_edges_from_no_edges():
    g = GraphStore()
    g.add_node("lonely", "function")
    assert g.get_edges_from("lonely") == []


# ---------------------------------------------------------------------------
# callers / callees
# ---------------------------------------------------------------------------

def test_callees():
    g = _simple_call_graph()
    assert set(g.callees("main")) == {"foo", "baz"}
    assert g.callees("bar") == []


def test_callers():
    g = _simple_call_graph()
    assert g.callers("foo") == ["main"]
    assert g.callers("main") == []


def test_callers_multiple():
    g = GraphStore()
    for n in ("A", "B", "C", "shared"):
        g.add_node(n, "function")
    g.add_edge("A", "shared", "calls")
    g.add_edge("B", "shared", "calls")
    g.add_edge("C", "shared", "calls")
    assert set(g.callers("shared")) == {"A", "B", "C"}


# ---------------------------------------------------------------------------
# transitive_closure
# ---------------------------------------------------------------------------

def test_transitive_closure_forward():
    g = _simple_call_graph()
    # main → foo → bar, main → baz
    reachable = g.transitive_closure("main", kind="calls", direction="forward")
    assert reachable == {"foo", "bar", "baz"}


def test_transitive_closure_backward():
    g = _simple_call_graph()
    # bar is reachable backward from bar: foo, then main
    reachable = g.transitive_closure("bar", kind="calls", direction="backward")
    assert reachable == {"foo", "main"}


def test_transitive_closure_start_not_in_result():
    g = _simple_call_graph()
    reachable = g.transitive_closure("main", kind="calls")
    assert "main" not in reachable


def test_transitive_closure_no_edges():
    g = GraphStore()
    g.add_node("alone", "function")
    assert g.transitive_closure("alone", kind="calls") == set()


def test_transitive_closure_handles_cycles():
    """BFS should not loop forever when cycles exist."""
    g = GraphStore()
    for n in ("A", "B", "C"):
        g.add_node(n, "function")
    g.add_edge("A", "B", "calls")
    g.add_edge("B", "C", "calls")
    g.add_edge("C", "A", "calls")
    reachable = g.transitive_closure("A", kind="calls")
    assert reachable == {"B", "C"}


# ---------------------------------------------------------------------------
# dead_code
# ---------------------------------------------------------------------------

def test_dead_code_detects_uncalled_functions():
    g = _simple_call_graph()
    # main is not called by anyone → dead code
    dead = g.dead_code()
    assert "main" in dead
    # foo, bar, baz are all called
    assert "foo" not in dead
    assert "bar" not in dead
    assert "baz" not in dead


def test_dead_code_includes_methods():
    g = GraphStore()
    g.add_node("MyClass.orphan_method", "method")
    g.add_node("helper", "function")
    g.add_edge("helper", "other_fn", "calls")
    # orphan_method has no incoming call edges
    dead = g.dead_code()
    assert "MyClass.orphan_method" in dead
    assert "helper" in dead  # helper itself is uncalled


def test_dead_code_empty_graph():
    g = GraphStore()
    assert g.dead_code() == []


# ---------------------------------------------------------------------------
# has_cycle
# ---------------------------------------------------------------------------

def test_has_cycle_detects_cycle_in_inherits():
    g = GraphStore()
    for n in ("A", "B", "C"):
        g.add_node(n, "class")
    g.add_edge("A", "B", "inherits")
    g.add_edge("B", "C", "inherits")
    g.add_edge("C", "A", "inherits")  # cycle
    assert g.has_cycle(kind="inherits") is True


def test_has_cycle_no_cycle():
    g = GraphStore()
    for n in ("A", "B", "C"):
        g.add_node(n, "class")
    g.add_edge("A", "B", "inherits")
    g.add_edge("B", "C", "inherits")
    assert g.has_cycle(kind="inherits") is False


def test_has_cycle_empty_graph():
    g = GraphStore()
    assert g.has_cycle() is False


def test_has_cycle_single_node_self_loop():
    g = GraphStore()
    g.add_node("X", "class")
    g.add_edge("X", "X", "inherits")
    assert g.has_cycle(kind="inherits") is True


def test_has_cycle_uses_specified_kind_only():
    g = GraphStore()
    for n in ("A", "B"):
        g.add_node(n, "class")
    g.add_edge("A", "B", "calls")
    g.add_edge("B", "A", "calls")
    # calls cycle should not affect inherits check
    assert g.has_cycle(kind="inherits") is False
    assert g.has_cycle(kind="calls") is True


# ---------------------------------------------------------------------------
# dangling_edges
# ---------------------------------------------------------------------------

def test_dangling_edges_detects_missing_nodes():
    g = GraphStore()
    g.add_node("A", "function")
    g.add_edge("A", "ghost", "calls")    # ghost doesn't exist
    dangling = g.dangling_edges()
    assert len(dangling) == 1
    assert dangling[0]["target"] == "ghost"


def test_dangling_edges_source_missing():
    g = GraphStore()
    g.add_node("B", "function")
    g.add_edge("phantom", "B", "calls")
    dangling = g.dangling_edges()
    assert len(dangling) == 1
    assert dangling[0]["source"] == "phantom"


def test_dangling_edges_none_when_all_present():
    g = _simple_call_graph()
    assert g.dangling_edges() == []


def test_dangling_edges_empty_graph():
    g = GraphStore()
    assert g.dangling_edges() == []


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

def test_stats_basic():
    g = _simple_call_graph()
    s = g.stats()
    assert s["node_count"] == 4
    assert s["edge_count"] == 3
    assert s["node_types"] == {"function": 4}
    assert s["edge_kinds"] == {"calls": 3}


def test_stats_mixed_types():
    g = GraphStore()
    g.add_node("MyClass", "class")
    g.add_node("my_fn", "function")
    g.add_node("my_method", "method")
    g.add_edge("MyClass", "my_fn", "calls")
    g.add_edge("MyClass", "other", "inherits")
    s = g.stats()
    assert s["node_count"] == 3
    assert s["edge_count"] == 2
    assert s["node_types"]["class"] == 1
    assert s["node_types"]["function"] == 1
    assert s["node_types"]["method"] == 1
    assert s["edge_kinds"]["calls"] == 1
    assert s["edge_kinds"]["inherits"] == 1


def test_stats_empty():
    g = GraphStore()
    s = g.stats()
    assert s["node_count"] == 0
    assert s["edge_count"] == 0
    assert s["node_types"] == {}
    assert s["edge_kinds"] == {}


# ---------------------------------------------------------------------------
# to_json / from_json round-trip
# ---------------------------------------------------------------------------

def test_to_json_is_valid_json():
    g = _simple_call_graph()
    j = g.to_json()
    parsed = json.loads(j)
    assert "nodes" in parsed
    assert "edges" in parsed
    assert "stats" in parsed


def test_from_json_round_trip():
    g = _simple_call_graph()
    g.add_node("MyClass", "class", module="mymod")
    g.add_edge("main", "MyClass", "instantiates")

    j = g.to_json()
    g2 = GraphStore.from_json(j)

    # Nodes preserved
    assert set(g2.nodes.keys()) == set(g.nodes.keys())
    assert g2.get_node("MyClass")["type"] == "class"
    assert g2.get_node("MyClass")["module"] == "mymod"

    # Edges preserved
    assert len(g2.edges) == len(g.edges)

    # Edge index rebuilt correctly
    edges_from_main = g2.get_edges_from("main")
    targets = {e["target"] for e in edges_from_main}
    assert "foo" in targets
    assert "MyClass" in targets


def test_from_json_callers_callees_work_after_roundtrip():
    g = _simple_call_graph()
    j = g.to_json()
    g2 = GraphStore.from_json(j)
    assert set(g2.callees("main")) == {"foo", "baz"}
    assert g2.callers("bar") == ["foo"]


def test_to_json_preserves_extra_properties():
    g = GraphStore()
    g.add_node("fn_a", "function", module="mod1", line=10)
    g.add_edge("fn_a", "fn_b", "calls", module="mod1", line=12)
    j = g.to_json()
    g2 = GraphStore.from_json(j)
    node = g2.get_node("fn_a")
    assert node["module"] == "mod1"
    assert node["line"] == 10
    edges = g2.get_edges_from("fn_a")
    assert edges[0]["line"] == 12
