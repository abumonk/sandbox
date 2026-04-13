"""
ARK Parser Adapter — wraps ark_parser.py to produce code graph nodes and edges.

Converts .ark file AST items into node/edge dicts compatible with GraphStore format.
"""

import sys
import json
from pathlib import Path

# Ensure tools/parser is on sys.path so we can import ark_parser
_TOOLS_PARSER = Path(__file__).parent.parent / "parser"
if str(_TOOLS_PARSER) not in sys.path:
    sys.path.insert(0, str(_TOOLS_PARSER))

import ark_parser


def parse_ark_file(path: Path) -> tuple:
    """Parse a .ark file and extract graph nodes and edges.

    Args:
        path: Path to the .ark file.

    Returns:
        (nodes, edges) where:
          nodes: list of {"name", "type", "module", "ark_kind", "line"}
          edges: list of {"source", "target", "kind", "module"}
    """
    source = path.read_text(encoding="utf-8")
    ark_file = ark_parser.parse(source, file_path=path)

    module = path.name
    nodes: list = []
    edges: list = []

    # Process import statements → edges of kind "imports"
    for imp in ark_file.imports:
        # imp can be: a list of path parts ["stdlib", "types"],
        # a string "stdlib.types", or a dict with a "module" key
        if isinstance(imp, list):
            target_module = ".".join(str(p) for p in imp)
        elif isinstance(imp, str):
            target_module = imp
        elif isinstance(imp, dict):
            target_module = imp.get("module", str(imp))
        else:
            target_module = str(imp)
        edges.append({
            "source": module,
            "target": target_module,
            "kind": "imports",
            "module": module,
        })

    # Walk top-level items
    for item in ark_file.items:
        _process_item(item, module, nodes, edges)

    return nodes, edges


def _make_node(name: str, node_type: str, module: str, ark_kind: str, line: int = 0) -> dict:
    return {
        "name": name,
        "type": node_type,
        "module": module,
        "ark_kind": ark_kind,
        "line": line,
    }


def _make_edge(source: str, target: str, kind: str, module: str) -> dict:
    return {
        "source": source,
        "target": target,
        "kind": kind,
        "module": module,
    }


def _process_item(item, module: str, nodes: list, edges: list) -> None:
    """Extract nodes and edges from a single AST item (dataclass or dict)."""
    # Support both dataclass instances and plain dicts (from to_json round-trip)
    if hasattr(item, "kind"):
        kind = item.kind
    elif isinstance(item, dict):
        kind = item.get("kind", "")
    else:
        return

    if kind == "abstraction":
        _process_entity(item, "class", "abstraction", module, nodes, edges)
    elif kind == "class":
        _process_entity(item, "class", "class", module, nodes, edges)
    elif kind == "instance":
        _process_instance(item, module, nodes, edges)
    elif kind == "island":
        _process_island(item, module, nodes, edges)
    elif kind == "bridge":
        _process_bridge(item, module, nodes, edges)
    elif kind == "expression":
        _process_named_def(item, "function", "expression", module, nodes, edges)
    elif kind == "predicate":
        _process_named_def(item, "function", "predicate", module, nodes, edges)
    elif kind == "struct":
        _process_named_def(item, "class", "struct", module, nodes, edges)
    elif kind == "enum":
        _process_named_def(item, "class", "enum", module, nodes, edges)
    # Other kinds (registry, verify, primitive) are silently ignored


def _get_attr(item, attr: str, default=None):
    """Retrieve attribute from a dataclass or dict."""
    if isinstance(item, dict):
        return item.get(attr, default)
    return getattr(item, attr, default)


def _process_entity(item, node_type: str, ark_kind: str, module: str,
                    nodes: list, edges: list) -> None:
    """Handle abstraction and class items."""
    name = _get_attr(item, "name", "")
    if not name:
        return
    nodes.append(_make_node(name, node_type, module, ark_kind))

    # inherits edges
    for parent in _get_attr(item, "inherits", []) or []:
        if isinstance(parent, str) and parent:
            edges.append(_make_edge(name, parent, "inherits", module))
        elif isinstance(parent, dict):
            parent_name = parent.get("name", "")
            if parent_name:
                edges.append(_make_edge(name, parent_name, "inherits", module))


def _process_instance(item, module: str, nodes: list, edges: list) -> None:
    """Handle instance items."""
    name = _get_attr(item, "name", "")
    if not name:
        return
    nodes.append(_make_node(name, "class", module, "instance"))


def _process_island(item, module: str, nodes: list, edges: list) -> None:
    """Handle island items — creates module node + contains/nested class edges."""
    name = _get_attr(item, "name", "")
    if not name:
        return
    nodes.append(_make_node(name, "module", module, "island"))

    # contains edges
    for contained in _get_attr(item, "contains", []) or []:
        if isinstance(contained, str) and contained:
            edges.append(_make_edge(name, contained, "contains", module))
        elif isinstance(contained, dict):
            contained_name = contained.get("name", "")
            if contained_name:
                edges.append(_make_edge(name, contained_name, "contains", module))

    # Nested classes inside the island
    for nested_cls in _get_attr(item, "classes", []) or []:
        nested_kind = _get_attr(nested_cls, "kind", "class")
        if nested_kind in ("class", "abstraction"):
            nested_name = _get_attr(nested_cls, "name", "")
            if nested_name:
                nodes.append(_make_node(nested_name, "class", module, nested_kind))
                edges.append(_make_edge(name, nested_name, "contains", module))
                # inherits edges for nested classes
                for parent in _get_attr(nested_cls, "inherits", []) or []:
                    if isinstance(parent, str) and parent:
                        edges.append(_make_edge(nested_name, parent, "inherits", module))
                    elif isinstance(parent, dict):
                        parent_name = parent.get("name", "")
                        if parent_name:
                            edges.append(_make_edge(nested_name, parent_name, "inherits", module))


def _process_bridge(item, module: str, nodes: list, edges: list) -> None:
    """Handle bridge items — creates ark_bridge edges."""
    from_port = _get_attr(item, "from_port", "")
    to_port = _get_attr(item, "to_port", "")
    if from_port and to_port:
        edges.append(_make_edge(from_port, to_port, "ark_bridge", module))


def _process_named_def(item, node_type: str, ark_kind: str, module: str,
                       nodes: list, edges: list) -> None:
    """Handle expression, predicate, struct, and enum items."""
    name = _get_attr(item, "name", "")
    if not name:
        return
    nodes.append(_make_node(name, node_type, module, ark_kind))
