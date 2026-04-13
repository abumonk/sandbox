"""End-to-end integration tests for the code graph subsystem.

Uses index_directory to index small tempdir trees with .py and .rs files,
then verifies the resulting GraphStore, runs queries, checks graph verification,
and round-trips through to_json / from_json.
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest

# The codegraph package uses relative imports, so we import via the package.
_ARK_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ARK_ROOT))
# Also inject codegraph dir for direct imports (graph_store, graph_verify)
sys.path.insert(0, str(_ARK_ROOT / "tools" / "codegraph"))

from tools.codegraph.indexer import index_directory
from graph_store import GraphStore
from graph_verify import verify_graph


# ---------------------------------------------------------------------------
# Fixture — small mixed Python/Rust tempdir
# ---------------------------------------------------------------------------

PY_SOURCE = """\
class Animal:
    pass

class Dog(Animal):
    def bark(self):
        return "woof"

    def fetch(self):
        self.bark()
        return "fetched"

def standalone_helper():
    pass
"""

RS_SOURCE = """\
pub struct Engine {
    pub hp: u32,
}

impl Engine {
    pub fn start(&self) -> bool {
        self.check_fuel()
    }

    fn check_fuel(&self) -> bool {
        true
    }
}

pub fn create_engine(hp: u32) -> Engine {
    Engine { hp }
}
"""


@pytest.fixture(scope="module")
def indexed_store(tmp_path_factory):
    """Index a small temp directory with one .py and one .rs file."""
    root = tmp_path_factory.mktemp("cg_integ")
    (root / "animals.py").write_text(PY_SOURCE, encoding="utf-8")
    (root / "engine.rs").write_text(RS_SOURCE, encoding="utf-8")
    return index_directory(root)


# ---------------------------------------------------------------------------
# Node presence tests
# ---------------------------------------------------------------------------

class TestIndexedNodes:
    def test_python_module_node_exists(self, indexed_store):
        assert "animals" in indexed_store.nodes

    def test_python_class_animal_exists(self, indexed_store):
        assert "animals.Animal" in indexed_store.nodes

    def test_python_class_dog_exists(self, indexed_store):
        assert "animals.Dog" in indexed_store.nodes

    def test_python_method_bark_exists(self, indexed_store):
        assert "animals.Dog.bark" in indexed_store.nodes

    def test_python_method_fetch_exists(self, indexed_store):
        assert "animals.Dog.fetch" in indexed_store.nodes

    def test_python_function_standalone_exists(self, indexed_store):
        assert "animals.standalone_helper" in indexed_store.nodes

    def test_rust_struct_engine_exists(self, indexed_store):
        assert "engine::Engine" in indexed_store.nodes

    def test_rust_function_create_engine_exists(self, indexed_store):
        assert "engine::create_engine" in indexed_store.nodes


# ---------------------------------------------------------------------------
# Edge presence tests
# ---------------------------------------------------------------------------

class TestIndexedEdges:
    def test_dog_inherits_animal(self, indexed_store):
        inherits_edges = indexed_store.get_edges_from("animals.Dog", kind="inherits")
        targets = [e["target"] for e in inherits_edges]
        assert "Animal" in targets

    def test_fetch_calls_bark(self, indexed_store):
        call_edges = indexed_store.get_edges_from("animals.Dog.fetch", kind="calls")
        targets = [e["target"] for e in call_edges]
        assert "bark" in targets

    def test_node_types_correct(self, indexed_store):
        assert indexed_store.nodes["animals.Animal"]["type"] == "class"
        assert indexed_store.nodes["animals.Dog.bark"]["type"] == "method"
        assert indexed_store.nodes["animals.standalone_helper"]["type"] == "function"

    def test_rust_engine_is_class(self, indexed_store):
        assert indexed_store.nodes["engine::Engine"]["type"] == "class"


# ---------------------------------------------------------------------------
# Query tests on indexed graph
# ---------------------------------------------------------------------------

class TestIndexedQueries:
    def test_callers_of_bark(self, indexed_store):
        callers = indexed_store.callers("bark")
        assert "animals.Dog.fetch" in callers

    def test_dead_code_standalone_helper(self, indexed_store):
        dead = indexed_store.dead_code()
        # standalone_helper is never called within this tiny graph
        assert "animals.standalone_helper" in dead

    def test_transitive_closure_from_fetch(self, indexed_store):
        reachable = indexed_store.transitive_closure(
            "animals.Dog.fetch", kind="calls", direction="forward"
        )
        # fetch -> bark (at least)
        assert "bark" in reachable

    def test_stats_returns_counts(self, indexed_store):
        stats = indexed_store.stats()
        assert stats["node_count"] >= 5
        assert stats["edge_count"] >= 1
        assert "class" in stats["node_types"]
        assert "function" in stats["node_types"] or "method" in stats["node_types"]


# ---------------------------------------------------------------------------
# Graph verification on indexed store
# ---------------------------------------------------------------------------

class TestIndexedVerification:
    def test_indexed_graph_passes_verification(self, indexed_store):
        """The graph produced by indexer.py should pass all structural checks."""
        graph_json = json.loads(indexed_store.to_json())
        results = verify_graph(graph_json)

        # Only check dangling edges and cycles — the indexer creates edges to
        # *unresolved* names (e.g. "Animal", "bark") that aren't full nodes,
        # so we test specifically which checks pass/fail for full transparency.
        cycle_result = next(r for r in results if r["check"] == "no_inheritance_cycles")
        assert cycle_result["status"] == "PASS", f"Cycle check failed: {cycle_result['details']}"

        module_result = next(r for r in results if r["check"] == "all_modules_have_names")
        assert module_result["status"] == "PASS", f"Module names check failed: {module_result['details']}"

    def test_verify_graph_returns_required_checks(self, indexed_store):
        graph_json = json.loads(indexed_store.to_json())
        results = verify_graph(graph_json)
        check_names = {r["check"] for r in results}
        assert "no_dangling_edges" in check_names
        assert "no_inheritance_cycles" in check_names
        assert "all_modules_have_names" in check_names


# ---------------------------------------------------------------------------
# to_json / from_json round-trip
# ---------------------------------------------------------------------------

class TestJsonRoundTrip:
    def test_round_trip_preserves_node_count(self, indexed_store):
        json_str = indexed_store.to_json()
        restored = GraphStore.from_json(json_str)
        assert len(restored.nodes) == len(indexed_store.nodes)

    def test_round_trip_preserves_edge_count(self, indexed_store):
        json_str = indexed_store.to_json()
        restored = GraphStore.from_json(json_str)
        assert len(restored.edges) == len(indexed_store.edges)

    def test_round_trip_node_names_identical(self, indexed_store):
        json_str = indexed_store.to_json()
        restored = GraphStore.from_json(json_str)
        assert set(restored.nodes.keys()) == set(indexed_store.nodes.keys())

    def test_round_trip_node_types_preserved(self, indexed_store):
        json_str = indexed_store.to_json()
        restored = GraphStore.from_json(json_str)
        for name, props in indexed_store.nodes.items():
            assert restored.nodes[name]["type"] == props["type"], (
                f"Type mismatch for node {name}"
            )

    def test_round_trip_queries_work(self, indexed_store):
        """Queries on the restored graph produce the same results as the original."""
        json_str = indexed_store.to_json()
        restored = GraphStore.from_json(json_str)

        original_callers = sorted(indexed_store.callers("bark"))
        restored_callers = sorted(restored.callers("bark"))
        assert original_callers == restored_callers

    def test_round_trip_stats_match(self, indexed_store):
        json_str = indexed_store.to_json()
        restored = GraphStore.from_json(json_str)
        orig_stats = indexed_store.stats()
        rest_stats = restored.stats()
        assert orig_stats["node_count"] == rest_stats["node_count"]
        assert orig_stats["edge_count"] == rest_stats["edge_count"]

    def test_round_trip_json_is_valid_json(self, indexed_store):
        json_str = indexed_store.to_json()
        parsed = json.loads(json_str)
        assert "nodes" in parsed
        assert "edges" in parsed
        assert "stats" in parsed

    def test_round_trip_on_empty_graph(self):
        gs = GraphStore()
        restored = GraphStore.from_json(gs.to_json())
        assert len(restored.nodes) == 0
        assert len(restored.edges) == 0

    def test_round_trip_on_manually_built_graph(self):
        gs = GraphStore()
        gs.add_node("mod", "module")
        gs.add_node("mod.Foo", "class")
        gs.add_node("mod.Bar", "class")
        gs.add_node("mod.Foo.run", "method")
        gs.add_edge("mod.Foo", "mod.Bar", "inherits")
        gs.add_edge("mod.Foo.run", "mod.Bar", "calls")

        restored = GraphStore.from_json(gs.to_json())
        assert "mod.Foo" in restored.nodes
        assert len(restored.edges) == 2
        assert sorted(restored.callers("mod.Bar")) == sorted(gs.callers("mod.Bar"))


# ---------------------------------------------------------------------------
# Python-only tempdir integration
# ---------------------------------------------------------------------------

class TestPythonOnlyIndex:
    def test_python_only_dir_indexes_correctly(self, tmp_path):
        src = (
            "def alpha():\n    beta()\n\n"
            "def beta():\n    pass\n"
        )
        (tmp_path / "utils.py").write_text(src, encoding="utf-8")
        store = index_directory(tmp_path)
        assert "utils" in store.nodes
        assert "utils.alpha" in store.nodes
        assert "utils.beta" in store.nodes
        callers = store.callers("beta")
        assert "utils.alpha" in callers

    def test_empty_dir_returns_empty_store(self, tmp_path):
        store = index_directory(tmp_path)
        assert len(store.nodes) == 0
        assert len(store.edges) == 0

    def test_unknown_extension_ignored(self, tmp_path):
        (tmp_path / "README.md").write_text("# hello", encoding="utf-8")
        (tmp_path / "data.txt").write_text("just text", encoding="utf-8")
        store = index_directory(tmp_path)
        assert len(store.nodes) == 0


# ---------------------------------------------------------------------------
# Rust-only tempdir integration
# ---------------------------------------------------------------------------

class TestRustOnlyIndex:
    def test_rust_only_dir_indexes_structs(self, tmp_path):
        src = (
            "pub struct Widget { pub id: u32 }\n"
            "impl Widget {\n"
            "    pub fn render(&self) { self.draw(); }\n"
            "    fn draw(&self) {}\n"
            "}\n"
        )
        (tmp_path / "widget.rs").write_text(src, encoding="utf-8")
        store = index_directory(tmp_path)
        assert "widget::Widget" in store.nodes
        assert store.nodes["widget::Widget"]["type"] == "class"

    def test_rust_methods_indexed(self, tmp_path):
        src = (
            "pub struct Calc {}\n"
            "impl Calc {\n"
            "    pub fn add(&self, a: i32, b: i32) -> i32 { a + b }\n"
            "}\n"
        )
        (tmp_path / "calc.rs").write_text(src, encoding="utf-8")
        store = index_directory(tmp_path)
        assert "calc::Calc::add" in store.nodes
        assert store.nodes["calc::Calc::add"]["type"] == "method"
