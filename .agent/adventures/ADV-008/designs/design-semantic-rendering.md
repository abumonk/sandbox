# Semantic Rendering — Design

## Overview

Semantic rendering = rendering driven by *meaning*, not mesh id. The shape grammar's rule tree is annotated with semantic labels (`window`, `load-bearing`, `decorative`, `api-node`, etc.) that propagate through derivations. Renderers select materials, shaders, and LOD by semantic class rather than geometric primitive. The rule tree is the explainable scene description.

This adventure delivers two end-to-end prototypes plus a research document that frames the broader direction (neural / differentiable renderers, Ark spec visualization).

## Target Files

- `shape_grammar/specs/semantic.ark` — `SemanticLabel` + `Provenance` entities as Ark classes.
- `shape_grammar/tools/semantic.py` — label propagation, tag inheritance, provenance chaining.
- `shape_grammar/examples/semantic_facade.ark` — Prototype 1.
- `shape_grammar/examples/code_graph_viz.ark` — Prototype 2.
- `.agent/adventures/ADV-008/research/semantic-rendering.md` — research write-up, 2 worked prototypes with step-by-step recipes.

## Approach

### Semantic entities (specs/semantic.ark)

```ark
class SemanticLabel {
  $data name: String
  $data tags: [String] = []
  $data inherits: Bool = true
  #process[strategy: code]{
    name' = name
  }
}

class Provenance {
  $data rule_chain: [String] = []
  $data depth: Int = 0
  #process[strategy: code]{
    depth' = depth
  }
}
```

Every terminal shape carries one `SemanticLabel` and one `Provenance`. Labels are inherited down the derivation tree unless a rule explicitly overrides (e.g. a `split` rule re-labels the "top" panel as `window` and the rest as `wall`).

### Propagation (tools/semantic.py)

```python
def propagate(ir: ShapeGrammarIR) -> ShapeGrammarIR:
    """Walk rule tree; push labels from parent to child if child doesn't override."""
    ...
def provenance_for(terminal: Terminal) -> list[str]:
    return terminal.provenance.rule_chain
```

### Prototype 1 — Building with Semantic Facade

File: `shape_grammar/examples/semantic_facade.ark`.

Recipe (documented in `research/semantic-rendering.md` as "Prototype 1"):

1. Axiom: `Building` with a scope of 20×30×40.
2. Rule `Building → floors`: split along Z into N floors, each labeled `floor`.
3. Rule `Floor → panels`: split along X into window+wall panels, labeled `window` or `wall`.
4. Rule `Window → frame + glass`: `frame` labeled `frame`, `glass` labeled `glass`.
5. Rule `Wall → extrude`: `wall` labeled `load-bearing` if on ground floor.

Output: OBJ file with 5 distinct semantic groups. Renderer demo: a Python script reads the OBJ's groups and assigns material colors by label (`window` → cyan, `frame` → brown, `wall` → grey, `load-bearing` → dark grey). Proves label-driven material selection end-to-end.

### Prototype 2 — code_graph.ark Visualization

File: `shape_grammar/examples/code_graph_viz.ark`.

Recipe (documented as "Prototype 2"):

1. Take the Ark IR of `ark/specs/infra/code_graph.ark` as input (read via `ark parse`).
2. Every `abstraction` becomes a sphere labeled `abstraction`.
3. Every `class` becomes a cube labeled `class`, sized by its `$data` count.
4. Every `bridge` becomes a cylinder connecting the two class shapes, labeled `bridge`.
5. Layout: a radial plan (abstractions on outer ring, classes inside).

Output: OBJ file visualizing the code_graph.ark island as procedural 3D geometry whose *shape choice* mirrors *semantic kind*. This dogfoods the semantic-rendering claim: Ark specs themselves become procedurally rendered with kind-aware visuals.

### Research document structure

`.agent/adventures/ADV-008/research/semantic-rendering.md` sections:

- `## Thesis` — what semantic rendering means in this package's context.
- `## Why rule trees are a natural semantic source`
- `### Prototype 1 — Building with Semantic Facade` — full recipe + proof command.
- `### Prototype 2 — code_graph.ark Visualization` — full recipe + proof command.
- `## Beyond prototypes — research directions`:
  - Neural / differentiable renderer with rule-tree as scene description.
  - Traceable procgen: every pixel knows which rule produced it.
  - LOD via pruning the rule tree at a semantic level (drop all `decorative`-labeled subtrees).
  - Dogfooding: visualize adventures / workflow graphs as procedural shapes.
- `## Integration points with Ark` — how `ark visualize` + the visualizer adapter consume the labeled OBJ.

TC-09 proof: `grep -c "### Prototype" research/semantic-rendering.md == 2`.

## Dependencies

- `design-shape-grammar-package.md` — IR, evaluator, OBJ writer.
- `design-evaluator.md` — label threading through terminals.

## Target Conditions Covered

- TC-08 — semantic label propagation (`test_semantic.py`).
- TC-09 — semantic-rendering research document with 2 prototypes.
- TC-17 — two example grammars for the prototypes exist and verify.
