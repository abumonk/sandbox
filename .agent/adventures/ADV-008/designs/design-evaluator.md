# Evaluator — Design

## Overview

The Python evaluator is the correctness reference for shape grammar semantics. It takes a `ShapeGrammarIR`, walks the rule tree, dispatches operations, maintains a scope stack, and emits terminal shapes with semantic labels and provenance. The OBJ writer serializes the terminal set.

Correctness of this module is what `ark verify` + the verifier passes ultimately prove about. The Rust skeleton mirrors the public surface.

## Target Files

- `shape_grammar/tools/evaluator.py` — top-level `evaluate(ir, seed) -> list[Terminal]`.
- `shape_grammar/tools/ops.py` — one class per primitive op (ExtrudeOp, SplitOp, CompOp, ScopeOp, IOp, TOp, ROp, SOp).
- `shape_grammar/tools/scope.py` — `Scope` dataclass + `ScopeStack` (push/pop/read).
- `shape_grammar/tools/rng.py` — `SeededRng` wrapper over `random.Random(seed)` with a `fork(label)` helper for deterministic branching.
- `shape_grammar/tools/obj_writer.py` — `write_obj(terminals, path)` writes vertices/faces/groups (one group per semantic label).

## Approach

### Evaluator loop

```python
def evaluate(ir: ShapeGrammarIR, seed: int) -> list[Terminal]:
    rng = SeededRng(seed)
    stack = ScopeStack()
    stack.push(Scope.identity())
    worklist = [(ir.axiom, stack.top(), SemanticLabel.default(), Provenance.root())]
    terminals = []
    while worklist:
        symbol, scope, label, prov = worklist.pop(0)  # FIFO = deterministic order
        if prov.depth > ir.max_depth:
            raise EvaluationError("max_depth exceeded — should have been caught by termination pass")
        rule = ir.resolve(symbol)
        if rule.is_terminal:
            terminals.append(Terminal(shape=rule.shape, scope=scope, label=label, provenance=prov))
            continue
        for op in rule.operations:
            children = op.apply(scope, rng.fork(op.id), label)
            for child_scope, child_symbol, child_label in children:
                worklist.append((child_symbol, child_scope, child_label, prov.extend(rule.id)))
    return terminals
```

Key properties:
- **Deterministic**: FIFO worklist + RNG forking by op.id → reproducible under same seed.
- **No wall-clock, no env reads** — RNG is the only entropy source; determinism pass verifies this.
- **Bounded**: `max_depth` is statically proved by termination pass; runtime guard catches drift.

### Operation primitives (`ops.py`)

Mirror ShapeML's core set:

| Op | Intent | Effect on scope |
|---|---|---|
| `ExtrudeOp(height)` | extrude 2D profile to 3D | pushes height onto scope.size.z |
| `SplitOp(axis, sizes)` | split scope along axis | produces N child scopes, one per size |
| `CompOp(faces)` | decompose to faces/edges/vertices | emits per-face child scopes |
| `ScopeOp(attrs)` | modify current scope attrs | pushes new scope with overrides |
| `IOp(asset)` | insert terminal asset | emits Terminal directly |
| `TOp(dx, dy, dz)` | translate | adjusts scope.translation |
| `ROp(rx, ry, rz)` | rotate | adjusts scope.rotation |
| `SOp(sx, sy, sz)` | scale | adjusts scope.scale |

Each op's `apply(scope, rng, label)` returns `list[(child_scope, child_symbol, child_label)]`. The scope-safety pass verifies that every `op` only reads attrs that are definitely defined at that point.

### Scope (`scope.py`)

```python
@dataclass
class Scope:
    translation: Vec3
    rotation: Vec3
    scale: Vec3
    size: Vec3
    attrs: dict[str, Any]   # user-defined attrs, inherited by children unless overridden
    @classmethod
    def identity(cls) -> "Scope": ...
    def push(self, override: dict) -> "Scope": ...
    def get(self, name: str) -> Any: ...
```

Inheritance rule: child scope inherits every attr not explicitly overridden. Scope-safety pass confirms every `get(name)` reads an attr definitely present in the dynamic scope chain.

### RNG (`rng.py`)

```python
class SeededRng:
    def __init__(self, seed: int): self._base = seed
    def fork(self, label: str) -> "SeededRng":
        # deterministic subseed from (self._base, label)
        subseed = hash((self._base, label)) & 0xFFFFFFFF
        return SeededRng(subseed)
    def random(self) -> float: ...
    def randint(self, a, b) -> int: ...
```

The `fork(label)` operation makes branches reproducible independent of traversal order.

### OBJ writer (`obj_writer.py`)

Emits one OBJ group per distinct semantic label. Vertices are accumulated with dedup. Faces reference vertex indices. File format is plain OBJ (v/f/g lines). glTF export is a deferred stub that calls the OBJ writer and notes "glTF: TODO" in the header.

## Dependencies

- Depends on `design-shape-grammar-package.md` (IR shape, verifier passes).
- Consumed by `design-semantic-rendering.md` (terminals with labels → renderer-ready).

## Target Conditions Covered

- TC-03 — IR → evaluator round-trip.
- TC-05 — Python evaluator tests pass (`test_evaluator.py`).
- TC-07 — round-trip grammar → evaluator → OBJ produces non-empty file.
- TC-09 — OBJ writer emits a group per semantic label.
