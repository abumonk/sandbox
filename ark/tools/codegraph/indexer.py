"""Code graph indexer — walks a directory, dispatches to language parsers, merges into GraphStore."""
import json
from pathlib import Path
from .graph_store import GraphStore
from .python_parser import parse_python_file
from .rust_parser import parse_rust_file
from .ark_parser_adapter import parse_ark_file
from .complexity import python_function_complexities, rust_function_complexities

EXTENSIONS = {
    ".py": "python",
    ".rs": "rust",
    ".ark": "ark",
}


def index_directory(root: Path, extensions: dict = None) -> GraphStore:
    """Walk a directory tree, parse all recognized files, return a populated GraphStore."""
    if extensions is None:
        extensions = EXTENSIONS

    store = GraphStore()
    root = Path(root).resolve()

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        ext = file_path.suffix
        lang = extensions.get(ext)
        if lang is None:
            continue

        try:
            if lang == "python":
                nodes, edges = parse_python_file(file_path)
                # Add complexity
                source = file_path.read_text(encoding="utf-8", errors="replace")
                complexities = python_function_complexities(source)
                # Build nodes first so we can update them with complexity info
                for node in nodes:
                    name = node["name"]
                    node_type = node["type"]
                    props = {k: v for k, v in node.items() if k not in ("name", "type")}
                    store.add_node(name, node_type, **props)

                for c in complexities:
                    # Store complexity as node property update
                    qual_name = f"{file_path.stem}.{c['name']}"
                    if qual_name in store.nodes:
                        store.nodes[qual_name]["complexity"] = c["complexity"]

                for edge in edges:
                    source_name = edge["source"]
                    target = edge["target"]
                    kind = edge["kind"]
                    props = {k: v for k, v in edge.items() if k not in ("source", "target", "kind")}
                    store.add_edge(source_name, target, kind, **props)

            elif lang == "rust":
                nodes, edges = parse_rust_file(file_path)
                source = file_path.read_text(encoding="utf-8", errors="replace")
                complexities = rust_function_complexities(source)

                for node in nodes:
                    name = node["name"]
                    node_type = node["type"]
                    props = {k: v for k, v in node.items() if k not in ("name", "type")}
                    store.add_node(name, node_type, **props)

                for c in complexities:
                    qual_name = f"{file_path.stem}::{c['name']}"
                    if qual_name in store.nodes:
                        store.nodes[qual_name]["complexity"] = c["complexity"]

                for edge in edges:
                    source_name = edge["source"]
                    target = edge["target"]
                    kind = edge["kind"]
                    props = {k: v for k, v in edge.items() if k not in ("source", "target", "kind")}
                    store.add_edge(source_name, target, kind, **props)

            elif lang == "ark":
                nodes, edges = parse_ark_file(file_path)

                for node in nodes:
                    name = node["name"]
                    node_type = node["type"]
                    props = {k: v for k, v in node.items() if k not in ("name", "type")}
                    store.add_node(name, node_type, **props)

                for edge in edges:
                    source_name = edge["source"]
                    target = edge["target"]
                    kind = edge["kind"]
                    props = {k: v for k, v in edge.items() if k not in ("source", "target", "kind")}
                    store.add_edge(source_name, target, kind, **props)

            else:
                continue

        except Exception as e:
            print(f"  Warning: failed to parse {file_path}: {e}")

    return store


def index_to_json(root: Path) -> str:
    """Index a directory and return JSON string."""
    store = index_directory(root)
    return store.to_json()
