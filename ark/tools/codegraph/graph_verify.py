"""Code graph verification -- structural invariant checks."""
import json
from pathlib import Path


def verify_graph(graph_json: dict) -> list:
    """Run all graph invariant checks. Returns list of result dicts."""
    results = []
    results.append(check_no_dangling_edges(graph_json))
    results.append(check_no_inheritance_cycles(graph_json))
    results.append(check_all_modules_have_names(graph_json))
    return results


def check_no_dangling_edges(graph_json: dict) -> dict:
    """Every edge source and target must exist as a node."""
    nodes = set(graph_json.get("nodes", {}).keys())
    dangling = []
    for edge in graph_json.get("edges", []):
        if edge["source"] not in nodes:
            dangling.append(f"source '{edge['source']}' missing")
        if edge["target"] not in nodes:
            dangling.append(f"target '{edge['target']}' missing")
    return {
        "check": "no_dangling_edges",
        "status": "FAIL" if dangling else "PASS",
        "details": dangling[:10] if dangling else [],
    }


def check_no_inheritance_cycles(graph_json: dict) -> dict:
    """No cycles in inherits edges."""
    # Build adjacency list from inherits edges only
    adj = {}
    for edge in graph_json.get("edges", []):
        if edge["kind"] == "inherits":
            adj.setdefault(edge["source"], []).append(edge["target"])

    # Collect all nodes referenced in inherits edges
    all_nodes = set(adj.keys())
    for targets in adj.values():
        all_nodes.update(targets)

    # DFS cycle detection using three-color marking
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in all_nodes}
    cycle_found = []

    def dfs(node, path):
        color[node] = GRAY
        for neighbor in adj.get(node, []):
            if color[neighbor] == GRAY:
                cycle_found.append(
                    f"cycle: {' -> '.join(path + [node, neighbor])}"
                )
                return
            if color[neighbor] == WHITE:
                dfs(neighbor, path + [node])
        color[node] = BLACK

    for n in list(all_nodes):
        if color[n] == WHITE:
            dfs(n, [])

    return {
        "check": "no_inheritance_cycles",
        "status": "FAIL" if cycle_found else "PASS",
        "details": cycle_found[:5] if cycle_found else [],
    }


def check_all_modules_have_names(graph_json: dict) -> dict:
    """All module nodes must have non-empty names."""
    modules = [
        {"name": k, **v}
        for k, v in graph_json.get("nodes", {}).items()
        if v.get("type") == "module"
    ]
    unnamed = [m["name"] for m in modules if not m["name"].strip()]
    return {
        "check": "all_modules_have_names",
        "status": "FAIL" if unnamed else "PASS",
        "details": unnamed,
    }


def verify_graph_file(path: Path) -> list:
    """Load a graph JSON file and run all invariant checks."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return verify_graph(data)
