#!/usr/bin/env python3
"""
ark — unified CLI for the ARK system

Usage:
  ark parse    <file.ark>              → JSON AST
  ark verify   <file.ark>              → Z3 invariant checks
  ark impact   <file.ark> <entity>     → dependency impact analysis
  ark codegen  <file.ark> --target X   → generate Rust/C++/Proto
  ark graph    <file.ark>              → interactive HTML graph
  ark diff     <old.ark> <new.ark>     → structural diff
  ark watch    <file.ark>              → auto re-run pipeline on file changes
  ark dispatch <backlog.ark>           → plan which Task → which Subagent runs next
  ark pipeline <file.ark>              → run full pipeline (parse→verify→codegen)
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
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print("Commands:", ", ".join(COMMANDS.keys()))
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
