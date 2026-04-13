"""Tests for GraphStore query methods and expression_primitives graph-* entries."""
import sys
from pathlib import Path

import pytest

# Ensure tools/codegraph is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "codegraph"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "codegen"))

from graph_store import GraphStore
from complexity import python_complexity, python_function_complexities
from complexity import rust_complexity, rust_function_complexities


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_call_graph() -> GraphStore:
    """Build a small call graph for query tests.

    Graph:
        main -> foo
        main -> bar
        foo  -> baz
        bar  -> baz
        orphan (no callers, calls nothing — dead code)
    """
    gs = GraphStore()
    for name, ntype in [
        ("main", "function"),
        ("foo", "function"),
        ("bar", "function"),
        ("baz", "function"),
        ("orphan", "function"),
    ]:
        gs.add_node(name, ntype)

    gs.add_edge("main", "foo", "calls")
    gs.add_edge("main", "bar", "calls")
    gs.add_edge("foo", "baz", "calls")
    gs.add_edge("bar", "baz", "calls")
    return gs


# ---------------------------------------------------------------------------
# callers
# ---------------------------------------------------------------------------

class TestCallers:
    def test_callers_multiple(self):
        gs = _make_call_graph()
        result = gs.callers("baz")
        assert sorted(result) == ["bar", "foo"]

    def test_callers_single(self):
        gs = _make_call_graph()
        result = gs.callers("foo")
        assert result == ["main"]

    def test_callers_none(self):
        gs = _make_call_graph()
        # main is never called
        assert gs.callers("main") == []

    def test_callers_nonexistent_node(self):
        gs = _make_call_graph()
        assert gs.callers("does_not_exist") == []


# ---------------------------------------------------------------------------
# callees
# ---------------------------------------------------------------------------

class TestCallees:
    def test_callees_two(self):
        gs = _make_call_graph()
        assert sorted(gs.callees("main")) == ["bar", "foo"]

    def test_callees_leaf(self):
        gs = _make_call_graph()
        assert gs.callees("baz") == []


# ---------------------------------------------------------------------------
# transitive_closure / call_chain
# ---------------------------------------------------------------------------

class TestTransitiveClosure:
    def test_forward_from_main(self):
        gs = _make_call_graph()
        reachable = gs.transitive_closure("main", kind="calls", direction="forward")
        assert reachable == {"foo", "bar", "baz"}

    def test_forward_from_foo(self):
        gs = _make_call_graph()
        reachable = gs.transitive_closure("foo", kind="calls", direction="forward")
        assert reachable == {"baz"}

    def test_forward_leaf_returns_empty(self):
        gs = _make_call_graph()
        reachable = gs.transitive_closure("baz", kind="calls", direction="forward")
        assert reachable == set()

    def test_backward_from_baz(self):
        gs = _make_call_graph()
        ancestors = gs.transitive_closure("baz", kind="calls", direction="backward")
        assert ancestors == {"foo", "bar", "main"}

    def test_start_not_in_result(self):
        """The start node must be excluded from the returned set."""
        gs = _make_call_graph()
        reachable = gs.transitive_closure("main", kind="calls", direction="forward")
        assert "main" not in reachable

    def test_cycle_does_not_hang(self):
        """Cyclic call graphs should terminate, not infinite-loop."""
        gs = GraphStore()
        gs.add_node("a", "function")
        gs.add_node("b", "function")
        gs.add_edge("a", "b", "calls")
        gs.add_edge("b", "a", "calls")
        reachable = gs.transitive_closure("a", kind="calls", direction="forward")
        assert reachable == {"b"}


# ---------------------------------------------------------------------------
# dead_code
# ---------------------------------------------------------------------------

class TestDeadCode:
    def test_orphan_is_dead(self):
        gs = _make_call_graph()
        dead = gs.dead_code()
        # orphan has no callers
        assert "orphan" in dead

    def test_main_is_dead_too(self):
        """main itself has no callers in this tiny graph."""
        gs = _make_call_graph()
        dead = gs.dead_code()
        assert "main" in dead

    def test_called_functions_not_dead(self):
        gs = _make_call_graph()
        dead = gs.dead_code()
        # foo, bar, baz are all called
        for name in ("foo", "bar", "baz"):
            assert name not in dead

    def test_all_called_graph_returns_empty(self):
        gs = GraphStore()
        gs.add_node("a", "function")
        gs.add_node("b", "function")
        gs.add_edge("a", "b", "calls")
        gs.add_edge("b", "a", "calls")
        # both are "called" by each other
        dead = gs.dead_code()
        assert dead == []

    def test_methods_counted_as_dead(self):
        gs = GraphStore()
        gs.add_node("M.method", "method")
        dead = gs.dead_code()
        assert "M.method" in dead


# ---------------------------------------------------------------------------
# complexity threshold queries
# ---------------------------------------------------------------------------

class TestComplexity:
    """Tests for tools/codegraph/complexity.py."""

    # Python complexity -------------------------------------------------------

    def test_simple_function_complexity_1(self):
        src = "def f():\n    return 42\n"
        result = python_complexity(src, func_name="f")
        assert result["complexity"] == 1
        assert result["language"] == "python"
        assert result["name"] == "f"

    def test_function_with_if_complexity_2(self):
        src = "def f(x):\n    if x:\n        return 1\n    return 0\n"
        result = python_complexity(src, func_name="f")
        assert result["complexity"] == 2

    def test_nested_conditions_increase_complexity(self):
        src = (
            "def f(a, b):\n"
            "    if a:\n"
            "        if b:\n"
            "            return 1\n"
            "    return 0\n"
        )
        result = python_complexity(src)
        assert result["complexity"] >= 3

    def test_python_function_complexities_per_function(self):
        src = (
            "def simple():\n    pass\n\n"
            "def branchy(x):\n"
            "    if x > 0:\n"
            "        return 1\n"
            "    elif x < 0:\n"
            "        return -1\n"
            "    return 0\n"
        )
        results = python_function_complexities(src)
        names = {r["name"] for r in results}
        assert "simple" in names
        assert "branchy" in names
        branchy = next(r for r in results if r["name"] == "branchy")
        assert branchy["complexity"] >= 3

    def test_threshold_filter(self):
        src = (
            "def simple():\n    pass\n\n"
            "def complex_fn(x, y):\n"
            "    if x:\n"
            "        if y:\n"
            "            return 1\n"
            "    return 0\n"
        )
        results = python_function_complexities(src)
        high = [r for r in results if r["complexity"] >= 3]
        assert len(high) >= 1
        assert high[0]["name"] == "complex_fn"

    # Rust complexity ---------------------------------------------------------

    def test_rust_simple_fn_complexity_1(self):
        src = "fn hello() {\n    println!(\"hi\");\n}\n"
        result = rust_complexity(src, func_name="hello")
        assert result["complexity"] >= 1
        assert result["language"] == "rust"

    def test_rust_fn_with_if_complexity(self):
        src = "fn check(x: i32) -> bool {\n    if x > 0 {\n        true\n    } else {\n        false\n    }\n}\n"
        result = rust_complexity(src, func_name="check")
        assert result["complexity"] >= 2

    def test_rust_function_complexities(self):
        src = (
            "fn simple() { println!(\"hi\"); }\n"
            "fn branchy(x: i32) -> i32 {\n"
            "    if x > 0 { return 1; }\n"
            "    if x < 0 { return -1; }\n"
            "    0\n"
            "}\n"
        )
        results = rust_function_complexities(src)
        names = {r["name"] for r in results}
        assert "simple" in names
        assert "branchy" in names
        branchy = next(r for r in results if r["name"] == "branchy")
        assert branchy["complexity"] >= 3


# ---------------------------------------------------------------------------
# EXPR_PRIMITIVES graph-* entries
# ---------------------------------------------------------------------------

class TestExprPrimitivesGraphEntries:
    """Verify that expression_primitives.py contains the required graph-* keys."""

    @pytest.fixture(scope="class")
    def primitives(self):
        from expression_primitives import EXPR_PRIMITIVES
        return EXPR_PRIMITIVES

    EXPECTED_GRAPH_KEYS = [
        "graph-callers",
        "graph-call-chain",
        "graph-dead-code",
        "graph-complex",
        "graph-subclasses",
        "graph-importers",
        "graph-module-deps",
        "graph-is-reachable",
        "graph-has-cycles",
        "graph-is-dead",
    ]

    def test_all_graph_keys_present(self, primitives):
        for key in self.EXPECTED_GRAPH_KEYS:
            assert key in primitives, f"Missing key: {key}"

    def test_graph_callers_has_rust_template(self, primitives):
        entry = primitives["graph-callers"]
        assert "rust" in entry
        assert "{0}" in entry["rust"]

    def test_graph_dead_code_is_method(self, primitives):
        entry = primitives["graph-dead-code"]
        assert entry.get("kind") == "method"

    def test_graph_is_reachable_arity_2(self, primitives):
        entry = primitives["graph-is-reachable"]
        assert entry.get("arity") == 2

    def test_graph_has_cycles_is_predicate(self, primitives):
        entry = primitives["graph-has-cycles"]
        assert entry.get("kind") == "predicate"

    def test_graph_entries_have_required_fields(self, primitives):
        for key in self.EXPECTED_GRAPH_KEYS:
            entry = primitives[key]
            assert "rust" in entry, f"{key} missing 'rust' field"
            assert "kind" in entry, f"{key} missing 'kind' field"
            assert "arity" in entry, f"{key} missing 'arity' field"
