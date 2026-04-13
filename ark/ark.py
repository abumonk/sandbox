#!/usr/bin/env python3
"""
ark — unified CLI for the ARK system

Usage:
  ark parse     <file.ark>              → JSON AST
  ark verify    <file.ark>              → Z3 invariant checks
  ark impact    <file.ark> <entity>     → dependency impact analysis
  ark codegen   <file.ark> --target X   → generate Rust/C++/Proto/Studio
  ark graph     <file.ark>              → interactive HTML graph
  ark diff      <old.ark> <new.ark>     → structural diff
  ark watch     <file.ark>              → auto re-run pipeline on file changes
  ark dispatch  <backlog.ark>           → plan which Task → which Subagent runs next
  ark pipeline  <file.ark>              → run full pipeline (parse→verify→codegen)
  ark studio    codegen  <file.ark> [--out <dir>]  → generate studio artifacts
  ark studio    verify   <file.ark>                → verify studio hierarchy
  ark studio    orgchart <file.ark> [--out F]      → generate org-chart HTML for roles
  ark codegraph index <path> [--out F]  → index directory to code graph JSON
  ark codegraph stats --file <json>     → show node/edge counts
  ark codegraph query callers <name>    → find callers of a function
  ark codegraph query dead-code         → find dead code
  ark codegraph query complexity [--threshold N]  → find complex functions
  ark codegraph graph <path> [--out F]  → generate interactive HTML visualization
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 stdout/stderr on Windows (cp1252 default chokes on ✓ etc.)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add tools to path
TOOLS = Path(__file__).parent / "tools"
sys.path.insert(0, str(TOOLS / "parser"))
sys.path.insert(0, str(TOOLS / "verify"))
sys.path.insert(0, str(TOOLS / "codegen"))
sys.path.insert(0, str(TOOLS / "visualizer"))
sys.path.insert(0, str(TOOLS / "diff"))
sys.path.insert(0, str(TOOLS / "watch"))
sys.path.insert(0, str(TOOLS / "dispatch"))
sys.path.insert(0, str(TOOLS))  # allows: import codegraph.indexer


def _safe_parse(source, file_path=None):
    """Parse source with ArkParseError → pretty report → exit(2)."""
    from ark_parser import parse, ArkParseError
    try:
        return parse(source, file_path=file_path)
    except ArkParseError as e:
        print(e.format_report(), file=sys.stderr)
        sys.exit(2)


def cmd_parse(args):
    from ark_parser import to_json
    filepath = Path(args[0])
    source = filepath.read_text(encoding="utf-8")
    result = _safe_parse(source, file_path=filepath)
    print(to_json(result))


def cmd_verify(args):
    from ark_verify import verify_file
    from ark_parser import to_json
    import json
    filepath = Path(args[0])
    source = filepath.read_text(encoding="utf-8")
    ark_file = _safe_parse(source, file_path=filepath)
    ast_json = json.loads(to_json(ark_file))
    verify_file(ast_json)


def cmd_impact(args):
    from ark_impact import build_dependency_graph, analyze_impact, print_impact
    from ark_parser import to_json
    import json
    filepath = Path(args[0])
    source = filepath.read_text(encoding="utf-8")
    ark_file = _safe_parse(source, file_path=filepath)
    ast_json = json.loads(to_json(ark_file))
    graph = build_dependency_graph(ast_json)
    impact = analyze_impact(graph, args[1])
    print_impact(impact, args[1])


def cmd_codegen(args):
    from ark_codegen import codegen_file
    from ark_parser import to_json
    import json
    target = "rust"
    out_dir = None
    filepath = args[0]
    for i, a in enumerate(args[1:], 1):
        if a == "--target" and i + 1 < len(args):
            target = args[i + 1]
        if a == "--out" and i + 1 < len(args):
            out_dir = Path(args[i + 1])
    filepath = Path(filepath)
    source = filepath.read_text(encoding="utf-8")
    ark_file = _safe_parse(source, file_path=filepath)

    if target == "studio":
        # studio_codegen needs the parsed ArkFile dataclass, not JSON.
        from studio_codegen import gen_studio
        results = gen_studio(ark_file, out_dir)
        if not out_dir:
            for fname, content in results.items():
                sep = "//" if fname.endswith((".rs", ".h", ".cpp")) else "#"
                print(f"\n{sep} === {fname} ===")
                print(content)
        print(f"\nGenerated {len(results)} studio files")
        return

    ast_json = json.loads(to_json(ark_file))
    results = codegen_file(ast_json, target, out_dir)
    if not out_dir:
        for fname, content in results.items():
            print(f"\n// === {fname} ===")
            print(content)
    print(f"\nGenerated {len(results)} files ({target})")


def cmd_graph(args):
    from ark_visualizer import generate_graph_data, generate_html
    from ark_parser import to_json
    import json
    filepath = Path(args[0])
    source = filepath.read_text(encoding="utf-8")
    ark_file = _safe_parse(source, file_path=filepath)
    ast_json = json.loads(to_json(ark_file))
    graph_data = generate_graph_data(ast_json)
    html = generate_html(graph_data, f"ARK — {filepath.stem}")
    out = filepath.with_suffix(".html")
    for i, a in enumerate(args[1:]):
        if a == "--out":
            out = Path(args[i + 2])
    out.write_text(html, encoding="utf-8")
    print(f"Graph → {out}")


def cmd_diff(args):
    """Structural diff between two .ark files."""
    from ark_diff import diff_ast, render
    from ark_parser import to_json
    import json
    if len(args) < 2:
        print("Usage: ark diff <old.ark> <new.ark> [--json]", file=sys.stderr)
        sys.exit(1)
    old_path = Path(args[0])
    new_path = Path(args[1])
    old_source = old_path.read_text(encoding="utf-8")
    new_source = new_path.read_text(encoding="utf-8")
    old_ast = json.loads(to_json(_safe_parse(old_source, file_path=old_path)))
    new_ast = json.loads(to_json(_safe_parse(new_source, file_path=new_path)))
    changes = diff_ast(old_ast, new_ast)
    if "--json" in args:
        print(json.dumps(changes, indent=2, ensure_ascii=False))
    else:
        print(f"# {old_path.name} → {new_path.name}")
        print(render(changes))
        print(f"\n{len(changes)} change(s)")


def cmd_dispatch(args):
    """Plan which ready Task should run next and by which Subagent."""
    from ark_dispatch import build_plan, render
    from ark_parser import to_json
    import json
    if not args:
        print("Usage: ark dispatch <backlog.ark> [--json]", file=sys.stderr)
        sys.exit(1)
    filepath = Path(args[0])
    source = filepath.read_text(encoding="utf-8")
    ast = json.loads(to_json(_safe_parse(source, file_path=filepath)))
    plan = build_plan(ast)
    if "--json" in args:
        print(json.dumps(plan, indent=2, ensure_ascii=False, default=str))
    else:
        print(render(plan))


def cmd_watch(args):
    """Watch a spec file and re-run the pipeline on every change."""
    from ark_watch import Watcher
    from datetime import datetime
    if not args:
        print("Usage: ark watch <file.ark> [--interval 0.3]", file=sys.stderr)
        sys.exit(1)
    filepath = Path(args[0])
    interval = 0.3
    for i, a in enumerate(args[1:], 1):
        if a == "--interval" and i + 1 < len(args):
            try:
                interval = float(args[i + 1])
            except ValueError:
                pass
    watcher = Watcher(filepath, poll_interval=interval)
    print(f"Watching {filepath} (poll {interval}s, ctrl-c to stop)...")
    # Prime the baseline so the startup event isn't fired.
    watcher.poll_once()
    # Do an initial run so the user sees the current state.
    _watch_run(filepath)

    def on_change():
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{ts}] change detected — re-running pipeline")
        _watch_run(filepath)

    try:
        watcher.watch(on_change)
    except KeyboardInterrupt:
        print("\nstopped.")


def _watch_run(filepath: Path) -> None:
    """Run the full pipeline once, swallowing errors so the watch loop
    stays alive on syntax mistakes mid-edit."""
    try:
        cmd_pipeline([str(filepath)])
    except SystemExit as e:
        # _safe_parse exits with 2 on parse errors; keep watching.
        print(f"  ⚠ pipeline aborted (exit {e.code})")
    except Exception as e:
        print(f"  ⚠ pipeline failed: {e}")


def cmd_pipeline(args):
    """Full pipeline: parse → verify → codegen"""
    from ark_parser import to_json
    from ark_verify import verify_file
    from ark_codegen import codegen_file
    from ark_visualizer import generate_graph_data, generate_html
    import json

    filepath = Path(args[0])
    target = "rust"
    for i, a in enumerate(args[1:], 1):
        if a == "--target" and i + 1 < len(args):
            target = args[i + 1]

    print(f"{'='*60}")
    print(f"  ARK Pipeline: {filepath.name}")
    print(f"{'='*60}")

    # 1. Parse
    print(f"\n[1/4] Parsing...")
    source = filepath.read_text(encoding="utf-8")
    ark_file = _safe_parse(source, file_path=filepath)
    ast_json = json.loads(to_json(ark_file))
    items = ast_json.get("items", [])
    print(f"  ✓ {len(items)} items parsed")

    # 2. Verify
    print(f"\n[2/4] Verifying...")
    if target == "studio":
        try:
            from studio_verify import verify_studio
            verify_result = verify_studio(ast_json)
        except ImportError:
            print("  (studio verify not yet available — skipping)")
            verify_result = {"summary": {"passed": 0, "total": 0, "failed": 0}}
    else:
        verify_result = verify_file(ast_json)
    summary = verify_result.get("summary", {})
    passed = summary.get("passed", 0)
    total = summary.get("total", 0)
    failed = summary.get("failed", 0)

    if failed > 0:
        print(f"\n  ⚠ {failed} verification failures — codegen will proceed with warnings")

    # 3. Codegen
    print(f"\n[3/4] Generating {target} code...")
    out_dir = filepath.parent / "generated" / target
    if target == "studio":
        from studio_codegen import gen_studio
        results = gen_studio(ark_file, out_dir)
    else:
        results = codegen_file(ast_json, target, out_dir)
    print(f"  ✓ {len(results)} files generated → {out_dir}")

    # 4. Graph
    print(f"\n[4/4] Generating visualization...")
    graph_data = generate_graph_data(ast_json)
    html = generate_html(graph_data, f"ARK — {filepath.stem}")
    graph_path = filepath.with_suffix(".html")
    graph_path.write_text(html, encoding="utf-8")
    print(f"  ✓ Graph → {graph_path}")

    print(f"\n{'='*60}")
    print(f"  Done. {len(items)} items, {passed}/{total} checks passed, {len(results)} files generated")
    print(f"{'='*60}")


def cmd_codegraph(args):
    """Code graph subcommands: index, stats, query."""
    import json as _json
    from pathlib import Path as _Path

    CODEGRAPH_USAGE = """\
Usage:
  ark codegraph index <path> [--out <file>]       Index directory, print or save JSON
  ark codegraph stats [--file <json>]              Show node/edge counts from last index
  ark codegraph query callers <name>               Find callers of a function
  ark codegraph query dead-code                    Find dead code (uncalled functions)
  ark codegraph query complexity [--threshold N]   Find complex functions
  ark codegraph graph <path> [--out <file>]        Generate interactive HTML visualization
"""

    if not args or args[0] in ("-h", "--help"):
        print(CODEGRAPH_USAGE)
        return

    # Lazy import — tools/ is on sys.path; codegraph is a package under tools/
    from codegraph.indexer import index_directory, index_to_json
    from codegraph.graph_store import GraphStore

    sub = args[0]

    if sub == "index":
        if len(args) < 2:
            print("Usage: ark codegraph index <path> [--out <file>]", file=sys.stderr)
            sys.exit(1)
        target_path = _Path(args[1])
        out_file = None
        for i, a in enumerate(args[2:], 2):
            if a == "--out" and i + 1 < len(args):
                out_file = _Path(args[i + 1])
        print(f"Indexing {target_path}...")
        json_str = index_to_json(target_path)
        if out_file:
            out_file.write_text(json_str, encoding="utf-8")
            data = _json.loads(json_str)
            stats = data.get("stats", {})
            print(f"  Saved to {out_file}")
            print(f"  {stats.get('node_count', 0)} nodes, {stats.get('edge_count', 0)} edges")
        else:
            print(json_str)

    elif sub == "stats":
        # Stats from a saved JSON file or stdin
        json_file = None
        for i, a in enumerate(args[1:], 1):
            if a == "--file" and i + 1 < len(args):
                json_file = _Path(args[i + 1])
        if json_file:
            json_str = json_file.read_text(encoding="utf-8")
        else:
            print("Usage: ark codegraph stats --file <json>", file=sys.stderr)
            sys.exit(1)
        store = GraphStore.from_json(json_str)
        stats = store.stats()
        print(f"Nodes:  {stats['node_count']}")
        print(f"Edges:  {stats['edge_count']}")
        print(f"\nNode types:")
        for t, c in sorted(stats.get("node_types", {}).items()):
            print(f"  {t}: {c}")
        print(f"\nEdge kinds:")
        for k, c in sorted(stats.get("edge_kinds", {}).items()):
            print(f"  {k}: {c}")

    elif sub == "query":
        if len(args) < 2:
            print("Usage: ark codegraph query <callers|dead-code|complexity> [args]", file=sys.stderr)
            sys.exit(1)
        query_kind = args[1]
        # Load store from --file or index on demand
        json_file = None
        for i, a in enumerate(args[2:], 2):
            if a == "--file" and i + 1 < len(args):
                json_file = _Path(args[i + 1])

        if json_file:
            store = GraphStore.from_json(json_file.read_text(encoding="utf-8"))
        else:
            print("  (no --file provided; run 'ark codegraph index <path> --out graph.json' first)", file=sys.stderr)
            sys.exit(1)

        if query_kind == "callers":
            if len(args) < 3:
                print("Usage: ark codegraph query callers <name> --file <json>", file=sys.stderr)
                sys.exit(1)
            name = args[2]
            callers = store.callers(name)
            if callers:
                print(f"Callers of '{name}':")
                for c in sorted(callers):
                    print(f"  {c}")
            else:
                print(f"No callers found for '{name}'")

        elif query_kind == "dead-code":
            dead = store.dead_code()
            if dead:
                print(f"Potentially dead code ({len(dead)} items):")
                for name in sorted(dead):
                    print(f"  {name}")
            else:
                print("No dead code found.")

        elif query_kind == "complexity":
            threshold = 5
            for i, a in enumerate(args[2:], 2):
                if a == "--threshold" and i + 1 < len(args):
                    try:
                        threshold = int(args[i + 1])
                    except ValueError:
                        pass
            complex_nodes = [
                (name, props)
                for name, props in store.nodes.items()
                if props.get("complexity", 0) >= threshold
            ]
            complex_nodes.sort(key=lambda x: x[1].get("complexity", 0), reverse=True)
            if complex_nodes:
                print(f"Functions with complexity >= {threshold}:")
                for name, props in complex_nodes:
                    print(f"  {name}: {props['complexity']}")
            else:
                print(f"No functions with complexity >= {threshold} found.")

        else:
            print(f"Unknown query: {query_kind}", file=sys.stderr)
            print("Available queries: callers, dead-code, complexity", file=sys.stderr)
            sys.exit(1)

    elif sub == "graph":
        if len(args) < 2:
            print("Usage: ark codegraph graph <path> [--out <file>]", file=sys.stderr)
            sys.exit(1)
        target_path = _Path(args[1])
        out_file = _Path("codegraph_viz.html")
        for i, a in enumerate(args[2:], 2):
            if a == "--out" and i + 1 < len(args):
                out_file = _Path(args[i + 1])
        print(f"Indexing {target_path}...")
        json_str = index_to_json(target_path)
        graph_json = _json.loads(json_str)
        # Reshape to nodes/edges format expected by visualizer
        store_nodes = graph_json.get("nodes", {})
        store_edges = graph_json.get("edges", [])
        vis_input = {"nodes": store_nodes, "edges": store_edges}
        from codegraph.visualizer import generate_codegraph_html
        generate_codegraph_html(vis_input, out_file)
        stats = graph_json.get("stats", {})
        print(f"  {stats.get('node_count', len(store_nodes))} nodes, {stats.get('edge_count', len(store_edges))} edges")
        print(f"  Graph → {out_file}")

    else:
        print(f"Unknown codegraph subcommand: {sub}", file=sys.stderr)
        print(CODEGRAPH_USAGE)
        sys.exit(1)


def cmd_studio(args):
    """Studio subcommands: codegen, verify, orgchart."""
    from ark_parser import to_json
    import json as _json

    STUDIO_USAGE = """\
Usage:
  ark studio codegen  <file.ark> [--out <dir>]   Generate studio artifacts
  ark studio verify   <file.ark>                  Verify studio hierarchy
  ark studio orgchart <file.ark> [--out <file>]   Generate org-chart HTML
"""
    if not args or args[0] in ("-h", "--help"):
        print(STUDIO_USAGE)
        return

    sub = args[0]
    rest = args[1:]

    if sub == "codegen":
        if not rest:
            print("Usage: ark studio codegen <file.ark> [--out <dir>]", file=sys.stderr)
            sys.exit(1)
        filepath = Path(rest[0])
        out_dir = None
        for i, a in enumerate(rest[1:], 1):
            if a == "--out" and i + 1 < len(rest):
                out_dir = Path(rest[i + 1])
        source = filepath.read_text(encoding="utf-8")
        ark_file = _safe_parse(source, file_path=filepath)
        from studio_codegen import gen_studio
        results = gen_studio(ark_file, out_dir)
        if not out_dir:
            for fname, content in results.items():
                sep = "//" if fname.endswith((".rs", ".h", ".cpp")) else "#"
                print(f"\n{sep} === {fname} ===")
                print(content)
        print(f"\nGenerated {len(results)} studio files")

    elif sub == "verify":
        if not rest:
            print("Usage: ark studio verify <file.ark>", file=sys.stderr)
            sys.exit(1)
        filepath = Path(rest[0])
        source = filepath.read_text(encoding="utf-8")
        ark_file = _safe_parse(source, file_path=filepath)
        ast_json = _json.loads(to_json(ark_file))
        try:
            from studio_verify import verify_studio
            result = verify_studio(ast_json)
            summary = result.get("summary", {})
            failed = summary.get("failed", 0)
            if failed > 0:
                sys.exit(1)
        except ImportError:
            print("studio verify not yet available (studio_verify module not found)")

    elif sub == "orgchart":
        if not rest:
            print("Usage: ark studio orgchart <file.ark> [--out <file>]", file=sys.stderr)
            sys.exit(1)
        filepath = Path(rest[0])
        out_file = filepath.with_stem(filepath.stem + "_orgchart").with_suffix(".html")
        for i, a in enumerate(rest[1:], 1):
            if a == "--out" and i + 1 < len(rest):
                out_file = Path(rest[i + 1])
        source = filepath.read_text(encoding="utf-8")
        ark_file = _safe_parse(source, file_path=filepath)
        ast_json = _json.loads(to_json(ark_file))
        from ark_visualizer import generate_graph_data, generate_html, extract_orgchart_data
        graph_data = generate_graph_data(ast_json)
        orgchart = graph_data.get("orgchart", {})
        if not orgchart:
            print("No studio/role items found in this .ark file.", file=sys.stderr)
            sys.exit(1)
        html = generate_html(graph_data, f"ARK Org-Chart — {filepath.stem}")
        out_file.write_text(html, encoding="utf-8")
        roles = orgchart.get("roles", [])
        edges = orgchart.get("edges", [])
        studios = orgchart.get("studios", [])
        print(f"Org-chart: {len(studios)} studios, {len(roles)} roles, {len(edges)} escalations")
        print(f"  HTML → {out_file}")

    else:
        print(f"Unknown studio subcommand: {sub}", file=sys.stderr)
        print(STUDIO_USAGE)
        sys.exit(1)


COMMANDS = {
    "parse": cmd_parse,
    "verify": cmd_verify,
    "impact": cmd_impact,
    "codegen": cmd_codegen,
    "graph": cmd_graph,
    "diff": cmd_diff,
    "watch": cmd_watch,
    "dispatch": cmd_dispatch,
    "pipeline": cmd_pipeline,
    "codegraph": cmd_codegraph,
    "studio": cmd_studio,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print("Commands:", ", ".join(COMMANDS.keys()))
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
