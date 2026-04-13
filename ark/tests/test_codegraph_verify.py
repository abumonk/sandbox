"""Tests for graph_verify.py — structural invariant checks."""
import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "codegraph"))

from graph_verify import (
    verify_graph,
    check_no_dangling_edges,
    check_no_inheritance_cycles,
    check_all_modules_have_names,
    verify_graph_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _well_formed_graph() -> dict:
    """Return a minimal, fully-consistent graph JSON dict."""
    return {
        "nodes": {
            "pkg": {"type": "module"},
            "pkg.Alpha": {"type": "class"},
            "pkg.Beta": {"type": "class"},
            "pkg.Alpha.run": {"type": "method"},
        },
        "edges": [
            {"source": "pkg.Alpha", "target": "pkg.Beta", "kind": "inherits"},
            {"source": "pkg.Alpha.run", "target": "pkg.Alpha", "kind": "calls"},
        ],
    }


# ---------------------------------------------------------------------------
# verify_graph — full suite
# ---------------------------------------------------------------------------

class TestVerifyGraph:
    def test_well_formed_graph_all_pass(self):
        results = verify_graph(_well_formed_graph())
        for r in results:
            assert r["status"] == "PASS", f"Expected PASS for {r['check']}: {r['details']}"

    def test_returns_three_checks(self):
        results = verify_graph(_well_formed_graph())
        checks = {r["check"] for r in results}
        assert checks == {
            "no_dangling_edges",
            "no_inheritance_cycles",
            "all_modules_have_names",
        }

    def test_dangling_edge_causes_fail(self):
        g = _well_formed_graph()
        g["edges"].append({"source": "ghost", "target": "pkg.Alpha", "kind": "calls"})
        results = verify_graph(g)
        failed = [r for r in results if r["status"] == "FAIL"]
        assert any(r["check"] == "no_dangling_edges" for r in failed)

    def test_inheritance_cycle_causes_fail(self):
        g = {
            "nodes": {
                "A": {"type": "class"},
                "B": {"type": "class"},
            },
            "edges": [
                {"source": "A", "target": "B", "kind": "inherits"},
                {"source": "B", "target": "A", "kind": "inherits"},
            ],
        }
        results = verify_graph(g)
        failed = [r for r in results if r["status"] == "FAIL"]
        assert any(r["check"] == "no_inheritance_cycles" for r in failed)

    def test_unnamed_module_causes_fail(self):
        g = {
            "nodes": {
                "": {"type": "module"},     # empty key — unnamed
                "good": {"type": "module"},
            },
            "edges": [],
        }
        results = verify_graph(g)
        failed = [r for r in results if r["status"] == "FAIL"]
        assert any(r["check"] == "all_modules_have_names" for r in failed)

    def test_empty_graph_all_pass(self):
        results = verify_graph({"nodes": {}, "edges": []})
        for r in results:
            assert r["status"] == "PASS"


# ---------------------------------------------------------------------------
# check_no_dangling_edges
# ---------------------------------------------------------------------------

class TestCheckNoDanglingEdges:
    def test_all_nodes_present_passes(self):
        g = _well_formed_graph()
        result = check_no_dangling_edges(g)
        assert result["status"] == "PASS"
        assert result["details"] == []

    def test_missing_source_detected(self):
        g = _well_formed_graph()
        g["edges"].append({"source": "missing_src", "target": "pkg.Alpha", "kind": "calls"})
        result = check_no_dangling_edges(g)
        assert result["status"] == "FAIL"
        assert any("missing_src" in d for d in result["details"])

    def test_missing_target_detected(self):
        g = _well_formed_graph()
        g["edges"].append({"source": "pkg.Alpha", "target": "missing_tgt", "kind": "calls"})
        result = check_no_dangling_edges(g)
        assert result["status"] == "FAIL"
        assert any("missing_tgt" in d for d in result["details"])

    def test_details_capped_at_10(self):
        """details list must not exceed 10 entries."""
        nodes = {"n0": {"type": "class"}}
        edges = [{"source": f"x{i}", "target": "n0", "kind": "calls"} for i in range(20)]
        result = check_no_dangling_edges({"nodes": nodes, "edges": edges})
        assert result["status"] == "FAIL"
        assert len(result["details"]) <= 10

    def test_no_edges_passes(self):
        result = check_no_dangling_edges({"nodes": {"A": {"type": "class"}}, "edges": []})
        assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# check_no_inheritance_cycles
# ---------------------------------------------------------------------------

class TestCheckNoInheritanceCycles:
    def test_linear_hierarchy_passes(self):
        g = {
            "nodes": {"A": {"type": "class"}, "B": {"type": "class"}, "C": {"type": "class"}},
            "edges": [
                {"source": "B", "target": "A", "kind": "inherits"},
                {"source": "C", "target": "B", "kind": "inherits"},
            ],
        }
        result = check_no_inheritance_cycles(g)
        assert result["status"] == "PASS"

    def test_direct_cycle_detected(self):
        g = {
            "nodes": {"A": {"type": "class"}, "B": {"type": "class"}},
            "edges": [
                {"source": "A", "target": "B", "kind": "inherits"},
                {"source": "B", "target": "A", "kind": "inherits"},
            ],
        }
        result = check_no_inheritance_cycles(g)
        assert result["status"] == "FAIL"
        assert len(result["details"]) >= 1

    def test_three_node_cycle_detected(self):
        g = {
            "nodes": {"A": {}, "B": {}, "C": {}},
            "edges": [
                {"source": "A", "target": "B", "kind": "inherits"},
                {"source": "B", "target": "C", "kind": "inherits"},
                {"source": "C", "target": "A", "kind": "inherits"},
            ],
        }
        result = check_no_inheritance_cycles(g)
        assert result["status"] == "FAIL"

    def test_non_inherits_edges_ignored(self):
        """Cycles in 'calls' edges do not trigger the inherits check."""
        g = {
            "nodes": {"A": {"type": "function"}, "B": {"type": "function"}},
            "edges": [
                {"source": "A", "target": "B", "kind": "calls"},
                {"source": "B", "target": "A", "kind": "calls"},
            ],
        }
        result = check_no_inheritance_cycles(g)
        assert result["status"] == "PASS"

    def test_no_edges_passes(self):
        result = check_no_inheritance_cycles({"nodes": {}, "edges": []})
        assert result["status"] == "PASS"

    def test_details_capped_at_5(self):
        """details list must not exceed 5 entries."""
        # Build a graph with many short cycles
        nodes = {chr(65 + i): {"type": "class"} for i in range(10)}
        edges = []
        for i in range(10):
            a = chr(65 + i)
            b = chr(65 + (i + 1) % 10)
            edges.append({"source": a, "target": b, "kind": "inherits"})
        result = check_no_inheritance_cycles({"nodes": nodes, "edges": edges})
        assert len(result["details"]) <= 5


# ---------------------------------------------------------------------------
# check_all_modules_have_names
# ---------------------------------------------------------------------------

class TestCheckAllModulesHaveNames:
    def test_all_named_passes(self):
        g = {
            "nodes": {
                "mymod": {"type": "module"},
                "othermod": {"type": "module"},
            },
            "edges": [],
        }
        result = check_all_modules_have_names(g)
        assert result["status"] == "PASS"
        assert result["details"] == []

    def test_empty_key_caught(self):
        g = {
            "nodes": {
                "": {"type": "module"},
            },
            "edges": [],
        }
        result = check_all_modules_have_names(g)
        assert result["status"] == "FAIL"
        assert "" in result["details"]

    def test_whitespace_only_key_caught(self):
        g = {
            "nodes": {
                "   ": {"type": "module"},
            },
            "edges": [],
        }
        result = check_all_modules_have_names(g)
        assert result["status"] == "FAIL"

    def test_non_module_nodes_ignored(self):
        """classes/functions with empty names don't fail this check."""
        g = {
            "nodes": {
                "": {"type": "class"},   # not a module — ignored
                "mod": {"type": "module"},
            },
            "edges": [],
        }
        result = check_all_modules_have_names(g)
        assert result["status"] == "PASS"

    def test_no_modules_passes(self):
        g = {
            "nodes": {
                "fn_a": {"type": "function"},
            },
            "edges": [],
        }
        result = check_all_modules_have_names(g)
        assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# verify_graph_file
# ---------------------------------------------------------------------------

class TestVerifyGraphFile:
    def test_well_formed_file_all_pass(self):
        data = _well_formed_graph()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp = Path(f.name)
        try:
            results = verify_graph_file(tmp)
            for r in results:
                assert r["status"] == "PASS", f"{r['check']}: {r['details']}"
        finally:
            tmp.unlink()

    def test_file_with_cycle_fails(self):
        data = {
            "nodes": {"X": {"type": "class"}, "Y": {"type": "class"}},
            "edges": [
                {"source": "X", "target": "Y", "kind": "inherits"},
                {"source": "Y", "target": "X", "kind": "inherits"},
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp = Path(f.name)
        try:
            results = verify_graph_file(tmp)
            assert any(r["status"] == "FAIL" for r in results)
        finally:
            tmp.unlink()

    def test_returns_list_of_check_dicts(self):
        data = {"nodes": {}, "edges": []}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp = Path(f.name)
        try:
            results = verify_graph_file(tmp)
            assert isinstance(results, list)
            for r in results:
                assert "check" in r
                assert "status" in r
        finally:
            tmp.unlink()
