# Integration Adapters — Design

## Overview

Adapters wrap Ark's existing tools (`ark graph`, `ark impact`, `ark diff`) and augment their output with shape-grammar semantics. Adapters are one-way consumers: they read Ark's output, never edit Ark source.

If an Ark tool's output surface is insufficient for an adapter, that is logged as a findings item in `research/ark-as-host-feasibility.md` — the adventure does not patch Ark.

## Target Files

- `shape_grammar/tools/integrations/visualizer_adapter.py`
- `shape_grammar/tools/integrations/impact_adapter.py`
- `shape_grammar/tools/integrations/diff_adapter.py`
- `shape_grammar/tests/test_integrations.py`

## Approach

### Visualizer adapter

```python
def augment_graph(ark_file: Path, out_html: Path) -> None:
    """Run `ark graph` then post-process the HTML to add shape-grammar annotations."""
```

Steps:
1. Subprocess `ark graph <file.ark> --out /tmp/base.html`.
2. Load the emitted JSON node/edge data (visualizer embeds a JSON blob in HTML).
3. For every node corresponding to a `Rule` or `Operation` class, inject a CSS class based on its semantic label.
4. Emit augmented HTML to `out_html`.

### Impact adapter

```python
def shape_impact(ark_file: Path, entity_name: str) -> dict:
    """Run `ark impact` then add rule-tree edges."""
```

Steps:
1. Subprocess `ark impact <file.ark> <entity>` → JSON (or text, parsed).
2. Load the shape-grammar IR.
3. For every rule that references `entity_name` (directly or transitively via operations), append a rule-tree impact edge.
4. Return combined impact report.

### Diff adapter

```python
def shape_diff(old_ark: Path, new_ark: Path) -> dict:
    """Run `ark diff` then add rule-tree structural diff."""
```

Steps:
1. Subprocess `ark diff <old> <new>` → JSON.
2. Load both IRs.
3. Compute rule-tree diff (added/removed/modified rules, label changes, operation sequence changes).
4. Merge with Ark's structural diff.

## Dependencies

- `design-shape-grammar-package.md` — IR shape.
- Ark CLI (`ark graph|impact|diff`) as subprocess.

## Target Conditions Covered

- TC-11 — visualizer adapter produces annotated HTML.
- TC-12 — impact adapter produces augmented report.
- TC-13 — diff adapter produces rule-tree diff.
- TC-14 — all integration tests green.
