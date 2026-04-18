# Unified Descriptor — Design

## Overview

Specifies the unified DSL surface that replaces the current eight concept
islands (`expression.ark`, `predicate.ark`, `code_graph.ark`, `studio.ark`,
`evolution.ark`, `agent.ark`, `visual.ark`, `types.ark`) with a single coherent
language: one Lark grammar, one Pest grammar, one AST family, one stdlib
organisation.

This is a **design document**, not an implementation. It describes the target
shape and the deltas from the current state. The implementation lives in a
downstream adventure (`ADV-Descriptor-Unification` — see the downstream plan).

## Target Files

- `.agent/adventures/ADV-011/designs/design-unified-descriptor.md` (this file)
- `.agent/adventures/ADV-011/research/descriptor-delta.md` — per-file delta
  report: which current stdlib files dissolve, which items stay, which items
  are renamed, which grammar rules consolidate. NEW.

## Approach

### 1. Item kinds — unified inventory

The descriptor layer defines the full vocabulary of item kinds. Drawing from
ADV-001..008, the seed list is:

**Core (kept from ADV-001..006 and 008)**:
- `expression`, `predicate` (ADV-001)
- `struct`, `enum`, `abstraction`, `class`, `island`, `bridge` (pre-existing)
- Code-graph items: `abstraction CodeIndex`, `class GraphStore`, `class Watcher`
  (ADV-002; these are instances of the abstraction/class kinds, not new kinds)
- `role`, `studio`, `workflow_command`, `hook`, `rule`, `template` (ADV-003)
- `evolution_target`, `eval_dataset`, `fitness_function`, `optimizer`,
  `benchmark_gate`, `evolution_run`, `constraint` (ADV-004)
- `agent`, `platform`, `gateway`, `execution_backend`, `skill`,
  `learning_config`, `cron_task`, `model_config` (ADV-005)
- `diagram`, `preview`, `annotation`, `visual_review`, `screenshot`,
  `visual_search`, `render_config`, `feedback` (ADV-006) — **subset kept**;
  UI-only items (`screenshot`, `visual_search`) move out-of-scope per pruning
  catalog.

**Retired / merged**: see `descriptor-delta.md` for per-item verdicts.

### 2. Grammar unification strategy

Current state: every adventure extended both `ark.pest` and `ark_grammar.lark`
in lock-step. The unified grammar design says:

- Single `ark_grammar.lark` file with a fixed section layout (tokens → base
  items → domain items per bucket).
- Single `ark.pest` mirrored by a parity test: the Python and Rust parsers must
  produce byte-identical JSON AST on every stdlib file (already a pattern from
  ADV-001 TC-005).
- New domain additions land as a *single patch on both files* authored from a
  shared design doc — not a per-language task split (current practice: two
  tasks, ADV-003 T003/T004). Enforced by a grammar-parity autotest that
  consumes a matrix of fixture `.ark` files.

### 3. AST family

Single canonical AST family rooted at `Item` (variant enum). Every domain
concept is a variant. The AST lives in one Rust crate (`ark-dsl`) and one
Python module (`ark_parser.Ast`). Dual-input helpers (from ADV-005 pattern
"Dual-input AST helpers") are retained.

### 4. Stdlib organisation

Replace the flat `ark/dsl/stdlib/*.ark` layout with a two-level scheme:

```
ark/dsl/stdlib/
  primitives/         # type-only: types.ark, expression primitives, predicates
  domain/             # one file per domain, each an island
    studio.ark
    evolution.ark
    agent.ark
    visual.ark
    code_graph.ark
```

No content migration in this adventure — only the target layout is specified.

### 5. Import contract

Every `.ark` consumer imports via `stdlib.<primitive-or-domain>.<item>`. The
unification proposal: an auto-prelude of `stdlib.primitives.*` and opt-in
domain imports. Documented here, implemented downstream.

### 6. Host-language contract (from ADV-008)

The descriptor must remain expressive enough that a *sibling package* (e.g.
`shape_grammar/`) can consume the DSL without requiring new item kinds. The
feasibility study in ADV-008 (T03) set this bar: 0 BLOCKED items, ≤2
NEEDS_WORKAROUND. Any future domain addition must re-run that bar.

## Dependencies

- `design-concept-mapping.md` (consumes descriptor-bucket rows)
- `design-deduplication-matrix.md` (consumes dedup rows assigned to descriptor)

## Target Conditions

- This design file references every descriptor-bucket concept from the mapping.
- `descriptor-delta.md` lists every current stdlib file with a verdict:
  `KEEP-AS-IS | KEEP-RENAMED | MERGE-INTO | MOVE-TO-PRIMITIVES | RETIRE`.
- Every dedup row with `assigned_bucket = descriptor` is cited at its
  resolution point in this design.
