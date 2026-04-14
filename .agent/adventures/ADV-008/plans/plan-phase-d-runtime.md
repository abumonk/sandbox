# Phase D — Runtime

## Designs Covered
- design-evaluator
- design-shape-grammar-package (runtime section)

## Tasks

### Scope stack + RNG
- **ID**: ADV008-T10
- **Description**: Implement `shape_grammar/tools/scope.py` (Scope, ScopeStack with push/pop/get) and `shape_grammar/tools/rng.py` (SeededRng with deterministic `fork(label)`). Per `design-evaluator.md`. Both modules are pure Python, no external deps beyond stdlib.
- **Files**: `shape_grammar/tools/scope.py`, `shape_grammar/tools/rng.py`
- **Acceptance Criteria**:
  - `Scope.identity()` returns identity transform.
  - `ScopeStack.push(scope).top() == scope`.
  - `SeededRng(42).fork("a")` and `SeededRng(42).fork("a")` produce identical first 100 outputs.
- **Target Conditions**: TC-05, TC-19
- **Depends On**: [ADV008-T07]
- **Evaluation**:
  - Access requirements: Read (designs/), Write (shape_grammar/tools/), Bash (python)
  - Skill set: Python
  - Estimated duration: 20min
  - Estimated tokens: 35000

### Operation primitives
- **ID**: ADV008-T11
- **Description**: Implement `shape_grammar/tools/ops.py` with one class per primitive (ExtrudeOp, SplitOp, CompOp, ScopeOp, IOp, TOp, ROp, SOp). Each implements `apply(scope, rng, label) -> list[(Scope, str, SemanticLabel)]`. Per `design-evaluator.md` op table.
- **Files**: `shape_grammar/tools/ops.py`
- **Acceptance Criteria**:
  - All 8 op classes implemented.
  - Each `apply` is deterministic under fixed seed.
  - Operations registered in a central `OP_REGISTRY` dict for evaluator dispatch.
- **Target Conditions**: TC-05, TC-19
- **Depends On**: [ADV008-T10]
- **Evaluation**:
  - Access requirements: Read (designs/), Write (shape_grammar/tools/), Bash (python)
  - Skill set: Python, computational geometry basics
  - Estimated duration: 30min
  - Estimated tokens: 65000

### Python evaluator core
- **ID**: ADV008-T12
- **Description**: Implement `shape_grammar/tools/evaluator.py` per `design-evaluator.md` § Evaluator loop. Top-level `evaluate(ir, seed) -> list[Terminal]`. CLI: `python -m shape_grammar.tools.evaluator <spec.ark> --seed <int> --out <file.obj>`.
- **Files**: `shape_grammar/tools/evaluator.py`
- **Acceptance Criteria**:
  - CLI runs end-to-end on `examples/cga_tower.ark` (will be added in T15) with `--seed 42 --out /tmp/tower.obj`.
  - For now, runs on `specs/shape_grammar.ark` if it has a minimal axiom; otherwise emits empty terminal list with no crash.
  - `evaluate(ir, 42) == evaluate(ir, 42)` (determinism check).
- **Target Conditions**: TC-05, TC-07
- **Depends On**: [ADV008-T11]
- **Evaluation**:
  - Access requirements: Read (shape_grammar/), Write (shape_grammar/tools/), Bash (python)
  - Skill set: Python, interpreter design
  - Estimated duration: 30min
  - Estimated tokens: 70000

### OBJ writer + semantic propagation
- **ID**: ADV008-T13
- **Description**: Implement `shape_grammar/tools/obj_writer.py` (write OBJ with one group per semantic label) and `shape_grammar/tools/semantic.py` (propagate labels through IR per inheritance rule). Per `design-semantic-rendering.md`.
- **Files**: `shape_grammar/tools/obj_writer.py`, `shape_grammar/tools/semantic.py`
- **Acceptance Criteria**:
  - `write_obj(terminals, '/tmp/x.obj')` produces a non-empty file with `g` directives for each distinct label.
  - `propagate(ir)` returns an IR where every rule has a non-default label (inherited if not declared).
- **Target Conditions**: TC-07, TC-08
- **Depends On**: [ADV008-T12]
- **Evaluation**:
  - Access requirements: Read (shape_grammar/), Write (shape_grammar/tools/), Bash (python)
  - Skill set: Python, OBJ format
  - Estimated duration: 25min
  - Estimated tokens: 45000

### Rust skeleton
- **ID**: ADV008-T14
- **Description**: Create `shape_grammar/tools/rust/` cargo crate with `Cargo.toml`, `src/lib.rs` declaring modules, and `src/{evaluator,ops,scope,semantic}.rs` with trait stubs only. Mirrors Python public API per `design-shape-grammar-package.md` § Rust skeleton. `cargo check` must pass; no functional implementation.
- **Files**: `shape_grammar/tools/rust/Cargo.toml`, `shape_grammar/tools/rust/src/lib.rs`, `shape_grammar/tools/rust/src/evaluator.rs`, `shape_grammar/tools/rust/src/ops.rs`, `shape_grammar/tools/rust/src/scope.rs`, `shape_grammar/tools/rust/src/semantic.rs`
- **Acceptance Criteria**:
  - `cargo check --manifest-path shape_grammar/tools/rust/Cargo.toml` exits 0.
  - At least 4 trait declarations (Evaluator, Op, Scope, Semantic).
  - All trait methods are stubs (`unimplemented!()` or `todo!()` or empty default).
- **Target Conditions**: TC-06
- **Depends On**: [ADV008-T11]
- **Evaluation**:
  - Access requirements: Write (shape_grammar/tools/rust/), Bash (`cargo check`)
  - Skill set: Rust
  - Estimated duration: 20min
  - Estimated tokens: 35000
