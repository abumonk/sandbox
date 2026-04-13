"""Self-index Ark's own source tree into a code graph."""
import json
import sys
from pathlib import Path

# Ensure codegraph package is importable
_TOOLS = Path(__file__).resolve().parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from codegraph.indexer import index_directory
from codegraph.graph_store import GraphStore

ARK_ROOT = Path(__file__).resolve().parent.parent.parent

# Directories to index
INDEX_DIRS = [
    ARK_ROOT / "tools",        # Python tools (parser, verify, codegen, etc.)
    ARK_ROOT / "dsl" / "src",  # Rust DSL crate
    ARK_ROOT / "orchestrator" / "src",  # Rust orchestrator
    ARK_ROOT / "specs",        # .ark spec files
    ARK_ROOT / "dsl" / "stdlib",  # .ark stdlib files
]

OUTPUT_PATH = ARK_ROOT / "specs" / "generated" / "code_graph.json"

def self_index() -> GraphStore:
    """Index all Ark source directories into a single GraphStore."""
    combined = GraphStore()

    for dir_path in INDEX_DIRS:
        if not dir_path.exists():
            print(f"  Skipping {dir_path} (not found)")
            continue
        print(f"  Indexing {dir_path}...")
        store = index_directory(dir_path)
        # Merge into combined
        for name, props in store.nodes.items():
            node_type = props.pop("type", "unknown")
            combined.add_node(name, node_type, **props)
        for edge in store.edges:
            e = dict(edge)
            source = e.pop("source")
            target = e.pop("target")
            kind = e.pop("kind")
            combined.add_edge(source, target, kind, **e)

    return combined

def main():
    print("Self-indexing Ark source tree...")
    store = self_index()
    stats = store.stats()

    print(f"\nResults:")
    print(f"  Nodes: {stats['node_count']}")
    print(f"  Edges: {stats['edge_count']}")
    print(f"  Node types: {stats['node_types']}")
    print(f"  Edge kinds: {stats['edge_kinds']}")

    # Check for all three languages
    lang_counts = {"python": 0, "rust": 0, "ark": 0}
    for name, props in store.nodes.items():
        lang = props.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
        elif props.get("ark_kind"):
            lang_counts["ark"] += 1
        else:
            mod = props.get("module", "")
            if mod.endswith(".ark"):
                lang_counts["ark"] += 1
            elif "::" in name or mod.endswith(".rs"):
                lang_counts["rust"] += 1
            else:
                lang_counts["python"] += 1
    languages = {k for k, v in lang_counts.items() if v > 0}
    print(f"  Languages: {languages}")
    print(f"  Language breakdown: {lang_counts}")

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(store.to_json(), encoding="utf-8")
    print(f"\n  Saved to {OUTPUT_PATH}")

    return store

if __name__ == "__main__":
    main()
