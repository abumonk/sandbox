"""In-memory graph store for code knowledge graphs."""
import json
from collections import defaultdict
from typing import Optional


class GraphStore:
    """In-memory directed graph with typed nodes and edges."""

    def __init__(self):
        self.nodes = {}          # name -> {type, properties}
        self.edges = []          # list of {source, target, kind, properties}
        self._edges_from = defaultdict(list)  # source -> [edge indices]
        self._edges_to = defaultdict(list)    # target -> [edge indices]

    def add_node(self, name: str, node_type: str, **properties) -> None:
        """Add or update a node."""
        self.nodes[name] = {"type": node_type, **properties}

    def add_edge(self, source: str, target: str, kind: str, **properties) -> None:
        """Add a directed edge."""
        idx = len(self.edges)
        edge = {"source": source, "target": target, "kind": kind, **properties}
        self.edges.append(edge)
        self._edges_from[source].append(idx)
        self._edges_to[target].append(idx)

    def get_node(self, name: str) -> Optional[dict]:
        """Get a node by name, or None."""
        return self.nodes.get(name)

    def get_nodes_by_type(self, node_type: str) -> list:
        """Get all nodes of a given type."""
        return [{"name": k, **v} for k, v in self.nodes.items() if v.get("type") == node_type]

    def get_edges_from(self, source: str, kind: str = None) -> list:
        """Get all edges from a source node, optionally filtered by kind."""
        indices = self._edges_from.get(source, [])
        edges = [self.edges[i] for i in indices]
        if kind:
            edges = [e for e in edges if e["kind"] == kind]
        return edges

    def get_edges_to(self, target: str, kind: str = None) -> list:
        """Get all edges pointing to a target node, optionally filtered by kind."""
        indices = self._edges_to.get(target, [])
        edges = [self.edges[i] for i in indices]
        if kind:
            edges = [e for e in edges if e["kind"] == kind]
        return edges

    def callers(self, name: str) -> list:
        """Get all nodes that call the given function/method."""
        call_edges = self.get_edges_to(name, kind="calls")
        return [e["source"] for e in call_edges]

    def callees(self, name: str) -> list:
        """Get all nodes called by the given function/method."""
        call_edges = self.get_edges_from(name, kind="calls")
        return [e["target"] for e in call_edges]

    def transitive_closure(self, start: str, kind: str = "calls", direction: str = "forward") -> set:
        """BFS reachability from start following edges of given kind."""
        visited = set()
        queue = [start]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            if direction == "forward":
                edges = self.get_edges_from(current, kind=kind)
                queue.extend(e["target"] for e in edges)
            else:
                edges = self.get_edges_to(current, kind=kind)
                queue.extend(e["source"] for e in edges)
        visited.discard(start)
        return visited

    def dead_code(self) -> list:
        """Find nodes with no incoming call edges (potential dead code)."""
        called = {e["target"] for e in self.edges if e["kind"] == "calls"}
        functions = self.get_nodes_by_type("function") + self.get_nodes_by_type("method")
        return [n["name"] for n in functions if n["name"] not in called]

    def has_cycle(self, kind: str = "inherits") -> bool:
        """Check if there's a cycle in edges of the given kind."""
        # Build adjacency list for this edge kind
        adj = defaultdict(list)
        nodes_in_subgraph = set()
        for e in self.edges:
            if e["kind"] == kind:
                adj[e["source"]].append(e["target"])
                nodes_in_subgraph.add(e["source"])
                nodes_in_subgraph.add(e["target"])

        # DFS cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n: WHITE for n in nodes_in_subgraph}

        def dfs(node):
            color[node] = GRAY
            for neighbor in adj.get(node, []):
                if color.get(neighbor) == GRAY:
                    return True
                if color.get(neighbor) == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        return any(dfs(n) for n in nodes_in_subgraph if color[n] == WHITE)

    def dangling_edges(self) -> list:
        """Find edges where source or target doesn't exist as a node."""
        return [e for e in self.edges
                if e["source"] not in self.nodes or e["target"] not in self.nodes]

    def stats(self) -> dict:
        """Return summary statistics."""
        type_counts = defaultdict(int)
        for v in self.nodes.values():
            type_counts[v["type"]] += 1
        edge_kind_counts = defaultdict(int)
        for e in self.edges:
            edge_kind_counts[e["kind"]] += 1
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "node_types": dict(type_counts),
            "edge_kinds": dict(edge_kind_counts),
        }

    def to_json(self) -> str:
        """Serialize the graph to JSON."""
        data = {
            "nodes": {k: v for k, v in self.nodes.items()},
            "edges": self.edges,
            "stats": self.stats(),
        }
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "GraphStore":
        """Deserialize a graph from JSON."""
        data = json.loads(json_str)
        store = cls()
        for name, props in data.get("nodes", {}).items():
            node_type = props.pop("type", "unknown")
            store.add_node(name, node_type, **props)
        for edge in data.get("edges", []):
            source = edge.pop("source")
            target = edge.pop("target")
            kind = edge.pop("kind")
            store.add_edge(source, target, kind, **edge)
        return store
