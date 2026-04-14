# Shape Grammar Package — Design

## Overview

`shape_grammar/` is a sibling package to `ark/` under `R:/Sandbox/`. It consumes Ark as its host language: shape grammars are written as ordinary `.ark` islands using existing Ark syntax, and `shape_grammar` supplies the semantics — IR extraction, verifier passes, Python reference evaluator, Rust skeleton, OBJ writer, and adapter-based integrations into Ark's visualizer / impact / diff tools.

Driving architectural decision: see `adr-001-shape-grammar-as-external-consumer.md`.

## Target Files

### Package layout (all new, under `R:/Sandbox/shape_grammar/`)

```
shape_grammar/
├── specs/
│   ├── shape_grammar.ark       # Core entities (Shape, Rule, Operation, Scope, SemanticLabel)
│   ├── operations.ark          # Operation primitives (extrude, split, comp, i, t, r, s, scope)
│   └── semantic.ark            # Semantic-label + provenance entities
├── examples/
│   ├── l_system.ark            # Simplest: derivation depth + single rule
│   ├── cga_tower.ark           # Classic CGA-style tower (split / repeat / extrude)
│   ├── semantic_facade.ark     # Facade with semantic labels on windows / load-bearing
│   └── code_graph_viz.ark      # Dogfooded: render an ark code-graph as shapes
├── tools/
│   ├── ir.py                   # Ark AST → shape-grammar IR
│   ├── evaluator.py            # Python reference evaluator
│   ├── ops.py                  # Operation primitives
│   ├── scope.py                # Scope stack + attribute inheritance
│   ├── rng.py                  # Seeded deterministic RNG wrapper
│   ├── obj_writer.py           # OBJ mesh output
│   ├── semantic.py             # Semantic-label propagation + provenance
│   ├── verify/
│   │   ├── termination.py      # Bounded-depth Z3 proof
│   │   ├── determinism.py      # Seed / ordering invariants
│   │   └── scope.py            # Scope + attribute safety
│   ├── integrations/
│   │   ├── visualizer_adapter.py   # reads Ark IR → visualizer annotations
│   │   ├── impact_adapter.py       # reads Ark IR → rule-tree impact edges
│   │   └── diff_adapter.py         # reads Ark IR → rule-tree structural diff
│   └── rust/                   # Rust skeleton (cargo check only)
│       ├── Cargo.toml
│       └── src/
│           ├── lib.rs
│           ├── evaluator.rs
│           ├── ops.rs
│           ├── scope.rs
│           └── semantic.rs
└── tests/
    ├── test_ir.py
    ├── test_verifier.py
    ├── test_evaluator.py
    ├── test_semantic.py
    ├── test_integrations.py
    └── test_examples.py
```

### Files that MUST NOT be touched

Anything under `R:/Sandbox/ark/`. TC-10 proves this with `git diff --stat master -- ark/`.

## Approach

### 1. Spec island in existing Ark syntax

Write shape-grammar entities using Ark's existing `abstraction` / `class` / `island` vocabulary. Every shape-grammar concept becomes:

- **`abstraction Shape`** — contract: inputs (scope state), outputs (derived children or terminal geometry), invariants (max-depth bound, deterministic under seed).
- **`class Rule : Shape`** — concrete rule with a `$data` field `operations: [Operation]` and a `#process` that dispatches on operation kind.
- **`class Operation`** — abstraction with classes per primitive (ExtrudeOp, SplitOp, CompOp, ScopeOp, IOp, TOp, ROp, SOp).
- **`class Scope`** — translation, rotation, scale attributes inherited down a derivation.
- **`class SemanticLabel`** — `{label, tags, provenance}` record propagated to every shape node.
- **`island ShapeGrammar`** — wraps a set of rules with a `max_depth: Int` annotation (checked statically by the termination pass) and `seed: Int` (deterministic evaluation).

Every concept uses existing `@in{}` / `#process[]{}` / `@out[]` / `$data` primitives. No new Ark keywords. `ark verify` must pass on `specs/shape_grammar.ark` under vanilla Ark — this is TC-02.

### 2. IR extraction (`tools/ir.py`)

`ir.py` invokes Ark's parser as a library (`from ark_parser import parse, to_json`) or subprocess (`ark parse spec.ark`), loads the resulting AST, and produces a `ShapeGrammarIR` dataclass:

```python
@dataclass
class ShapeGrammarIR:
    max_depth: int
    seed: int
    rules: list[Rule]
    axiom: str              # starting non-terminal
    semantic_labels: list[SemanticLabel]
    provenance: dict[str, str]   # rule-id → source location
```

Consumers (evaluator, verifier passes, adapters) depend only on the IR, never on Ark's AST shape directly. This isolates shape-grammar semantics from future Ark AST changes.

### 3. Verifier passes (post-Ark-verify)

Each pass is a Python module that:
1. Loads the IR (via `ir.py`).
2. Builds Z3 obligations using `z3-solver` (same library Ark uses).
3. Emits `PASS`, `FAIL` (with counter-example), or `PASS_OPAQUE` (for constructs that require opaque primitives — see ADV-002's `PASS_OPAQUE` pattern).

Passes:
- **`termination.py`** — asserts `max_depth` is statically bounded and every rule expansion consumes at least 1 depth unit. Z3 witness: a derivation tree of depth `max_depth + 1` is unsatisfiable.
- **`determinism.py`** — asserts every rule RHS is ordered (no set-valued operations), and every stochastic operation reads from the explicit RNG seed stream. No wall-clock, no environment reads. Z3 witness: two evaluations with the same seed produce identical IR outputs (symbolically).
- **`scope.py`** — asserts every operation referencing a scope attribute reads only attributes that are in scope at that point in the derivation. Z3 witness: an operation reading an undefined attribute is unsatisfiable.

Entry point: `python -m shape_grammar.tools.verify termination|determinism|scope <spec.ark>`. These passes are invoked *after* `ark verify` passes — they layer on top, never replace.

### 4. Python evaluator (`tools/evaluator.py`)

Reference interpreter. Walks the IR, dispatches operations through `ops.py`, maintains a scope stack in `scope.py`, uses seeded RNG from `rng.py`. Emits a list of terminal shapes, each with its semantic label + provenance chain. `obj_writer.py` serializes the terminal set to OBJ.

CLI: `python -m shape_grammar.tools.evaluator <spec.ark> --seed <int> --out <file.obj>`.

### 5. Rust skeleton (`tools/rust/`)

Cargo crate with module declarations and trait stubs. Every trait signature mirrors the Python evaluator's public API. `cargo check` must pass — this is TC-06. No `cargo test` obligation; no functional Rust yet.

```rust
pub trait Evaluator {
    fn evaluate(&self, ir: &ShapeGrammarIR, seed: u64) -> Vec<Terminal>;
}
pub trait Op {
    fn apply(&self, scope: &Scope, rng: &mut Rng) -> Vec<ScopedShape>;
}
```

### 6. Semantic labels + provenance

`tools/semantic.py` walks the IR and annotates every node with `{label, tags, provenance}`. Labels propagate down the derivation by inheritance (child inherits parent's label unless overridden). Provenance is a chain of rule IDs back to the axiom. The evaluator threads these through to terminals.

### 7. Integration adapters

Each adapter is a Python module that:
- Invokes Ark's tool (`ark graph`, `ark impact`, `ark diff`) on a shape-grammar `.ark` file.
- Loads the tool's output (JSON / HTML / diff report).
- Augments it with shape-grammar semantics (rule-tree edges, semantic labels, derivation provenance).
- Writes an annotated view to `shape_grammar/out/` or stdout.

No adapter edits Ark tool source. If an Ark tool cannot be wrapped from outside, log to `research/ark-as-host-feasibility.md`.

## Dependencies

- `ADR-001` — settled architectural decision.
- `design-semantic-rendering.md` — defines `SemanticLabel` shape and prototype scenarios.
- `design-evaluator.md` — Python evaluator internals + op primitives + scope semantics.
- External: Ark's parser library (`ark_parser.py`), Ark's CLI (`ark verify|parse|graph|impact|diff`), `z3-solver`, `lark` (indirectly via Ark).

## Target Conditions Covered

- TC-01 — package layout exists (`shape_grammar/` tree + empty-but-present files).
- TC-02 — `ark verify shape_grammar/specs/shape_grammar.ark` exits 0.
- TC-03 — IR extraction returns populated `ShapeGrammarIR`.
- TC-06 — Rust skeleton compiles.
- TC-10 — `git diff --stat master -- ark/` empty.
- Indirectly supports TC-04, TC-05, TC-07, TC-08, TC-09 via supporting designs.
