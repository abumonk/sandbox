---
adventure_id: ADV-008
status: approved
created: 2026-04-14T12:05:00Z
approved: 2026-04-14T12:20:00Z
passes_completed: 4
validation_gaps: 0
---

# Permission Requests — ADV-008: Shape Grammar Sibling Package

## Summary

24 permissions across 19 tasks, 2 custom agents (shape-grammar-researcher, geometry-engineer). All 4 analysis passes complete. 0 validation gaps.

**Critical boundary**: writes to `R:/Sandbox/ark/**` are **explicitly denied** — this preserves TC-10 (`git diff --stat master -- ark/` empty).

## Pass 1 — Codebase Tooling Scan

Discovered:
- Ark CLI: `python ark/ark.py {parse|verify|graph|impact|diff|codegen|pipeline|...}` — entry point.
- Pytest convention: `pytest <path>` from `R:/Sandbox/`. No project-wide `pytest.ini` found; per-package convention.
- Rust: cargo workspace declared at `R:/Sandbox/Cargo.toml`. New crate at `shape_grammar/tools/rust/` will need `cargo check --manifest-path`.
- Python deps: `lark-parser`, `z3-solver` already installed (per `ark/CLAUDE.md`).
- No `Makefile` / `Taskfile` / `justfile` at root.
- Git repo: `master` branch; commit style `conventional`.

## Pass 2 — Plan-Driven Analysis

Per-task trace:
- T01: WebFetch (github.com/stefalie/shapeml), Write research file.
- T02: Read designs/schemas, Write test-strategy.md.
- T03: Read entire `ark/`, Write feasibility doc.
- T04-T06: Read schemas + ark/specs, Write shape_grammar/specs/, Bash `python ark/ark.py {parse,verify}`.
- T07: Read ark parser, Write shape_grammar/tools/, Bash python.
- T08: Read shape_grammar/specs + ark/tools/verify, Write shape_grammar/tools/verify/, Bash python (z3).
- T09: Read shape_grammar/, Write shape_grammar/tests/ + fixtures/, Bash pytest.
- T10-T13: Write shape_grammar/tools/, Bash python.
- T14: Write shape_grammar/tools/rust/, Bash `cargo check`.
- T15: Read shape_grammar/specs + ark/specs/infra/code_graph.ark, Write shape_grammar/examples/, Bash ark verify + python.
- T16: WebSearch (rendering domain), Read shape_grammar/, Write research/.
- T17: Read ark/tools/, Write shape_grammar/tools/integrations/, Bash ark + python.
- T18: Read shape_grammar/, Write shape_grammar/tests/, Bash pytest.
- T19: Read shape_grammar/ + ark/, Write research/, Bash git + ark + pytest + cargo + python.

## Pass 3 — Historical Pattern Match

From `.agent/knowledge/`:
- ADV-002: indexed Ark codebase from outside via `ark codegraph index`. Pattern reusable here for IR extraction.
- ADV-003: `Separate Domain Modules` — extended to sibling-package level here.
- ADV-006: Optional dependency guard — relevant if OBJ rendering needs Pillow (it doesn't; OBJ is plain text).
- ADV007-T015: Per-role MCP enabling — applied here: shape-grammar-researcher gets WebSearch/WebFetch; geometry-engineer does not.
- No prior adventure has needed write access outside `ark/` and `.agent/`. **New ground**: the explicit `shape_grammar/**` write scope.

## Pass 4 — Cross-Validation Matrix

| Task | Agent | Stage | Read | Write | Shell | MCP | External | Verified |
|------|-------|-------|------|-------|-------|-----|----------|----------|
| T01 | shape-grammar-researcher | research | designs/, schemas/ | research/shapeml-architecture.md | - | - | WebFetch github.com/stefalie/shapeml | yes |
| T02 | geometry-engineer | planning | designs/, schemas/ | tests/test-strategy.md | - | - | - | yes |
| T03 | geometry-engineer | research | ark/** | research/ark-as-host-feasibility.md | - | - | - | yes |
| T04 | geometry-engineer | implementing | ark/specs/, schemas/ | shape_grammar/specs/shape_grammar.ark | python ark/ark.py parse,verify | - | - | yes |
| T05 | geometry-engineer | implementing | schemas/ | shape_grammar/specs/operations.ark | python ark/ark.py verify | - | - | yes |
| T06 | geometry-engineer | implementing | schemas/ | shape_grammar/specs/semantic.ark | python ark/ark.py verify | - | - | yes |
| T07 | geometry-engineer | implementing | ark/tools/parser/, shape_grammar/specs/ | shape_grammar/tools/ir.py, __init__.py | python | - | - | yes |
| T08 | geometry-engineer | implementing | ark/tools/verify/, shape_grammar/specs/ | shape_grammar/tools/verify/** | python | - | - | yes |
| T09 | geometry-engineer | testing | shape_grammar/** | shape_grammar/tests/test_ir.py, test_verifier.py, conftest.py, fixtures/** | pytest | - | - | yes |
| T10 | geometry-engineer | implementing | designs/ | shape_grammar/tools/scope.py, rng.py | python | - | - | yes |
| T11 | geometry-engineer | implementing | designs/ | shape_grammar/tools/ops.py | python | - | - | yes |
| T12 | geometry-engineer | implementing | shape_grammar/** | shape_grammar/tools/evaluator.py | python | - | - | yes |
| T13 | geometry-engineer | implementing | shape_grammar/** | shape_grammar/tools/obj_writer.py, semantic.py | python | - | - | yes |
| T14 | geometry-engineer | implementing | - | shape_grammar/tools/rust/** | cargo check --manifest-path | - | - | yes |
| T15 | geometry-engineer | implementing | shape_grammar/specs/, ark/specs/infra/code_graph.ark | shape_grammar/examples/** | python ark/ark.py verify, python -m shape_grammar.tools.ir | - | - | yes |
| T16 | shape-grammar-researcher | research | shape_grammar/, designs/ | research/semantic-rendering.md | - | - | WebSearch | yes |
| T17 | geometry-engineer | implementing | ark/tools/ | shape_grammar/tools/integrations/** | python ark/ark.py graph,impact,diff; python | - | - | yes |
| T18 | geometry-engineer | testing | shape_grammar/** | shape_grammar/tests/test_evaluator.py, test_semantic.py, test_integrations.py, test_examples.py | pytest | - | - | yes |
| T19 | geometry-engineer | testing | shape_grammar/, ark/ | research/final-validation.md | git diff, ark verify, pytest, cargo check, python | - | - | yes |

Validation checks:
1. Every task has at least one permission entry per assigned agent role: PASS.
2. Every shell command from Pass 1 (ark CLI, pytest, cargo) is covered in at least one task: PASS.
3. Every `proof_command` in target conditions is covered: PASS (cross-checked against TC table in manifest).
4. Every file in a task's `files` field has a corresponding read or write permission: PASS.
5. Task dependencies traced: dependent tasks read predecessor outputs (verified per row).
6. Git operations: `git diff` covered in T19; commit/push handled by pipeline at task close, no per-task git permission needed.

## Requests

### Shell Access

| # | Agent | Stage | Command | Reason | Tasks |
|---|-------|-------|---------|--------|-------|
| 1 | geometry-engineer | implementing/testing | `python ark/ark.py parse <file>` | Verify shape_grammar specs parse under vanilla Ark | T04, T05, T06, T07 |
| 2 | geometry-engineer | implementing/testing | `python ark/ark.py verify <file>` | Verify shape_grammar specs + examples pass Ark Z3 | T04, T05, T06, T15, T19 |
| 3 | geometry-engineer | implementing | `python ark/ark.py graph <file>` | Drive visualizer adapter | T17 |
| 4 | geometry-engineer | implementing | `python ark/ark.py impact <file> <ent>` | Drive impact adapter | T17 |
| 5 | geometry-engineer | implementing | `python ark/ark.py diff <old> <new>` | Drive diff adapter | T17 |
| 6 | geometry-engineer | implementing/testing | `python -m shape_grammar.tools.ir <file>` | IR CLI dump | T07, T15 |
| 7 | geometry-engineer | testing | `python -m shape_grammar.tools.evaluator <file> --seed N --out P` | Round-trip OBJ generation | T12, T19 |
| 8 | geometry-engineer | testing | `python -m shape_grammar.tools.verify {termination,determinism,scope,all} <file>` | Run verifier passes | T08, T19 |
| 9 | geometry-engineer | testing | `pytest shape_grammar/tests/ [path] [-v|-q] [-k expr]` | Run shape-grammar tests | T09, T18, T19 |
| 10 | geometry-engineer | testing | `cargo check --manifest-path shape_grammar/tools/rust/Cargo.toml` | Rust skeleton compiles | T14, T19 |
| 11 | geometry-engineer | testing | `git diff --stat master -- ark/` | Prove TC-10 (no Ark modifications) | T19 |
| 12 | geometry-engineer | implementing | `test -f|-s <path>` and `grep -c <pattern> <file>` | Proof-of-condition shell snippets | T15, T16, T19 |

### File Access

| # | Agent | Stage | Scope | Mode | Reason | Tasks |
|---|-------|-------|-------|------|--------|-------|
| 13 | shape-grammar-researcher | research | `R:/Sandbox/.agent/adventures/ADV-008/research/**` | write | Research output target | T01, T16 |
| 14 | shape-grammar-researcher | research | `R:/Sandbox/shape_grammar/examples/**` | write (read-only after T15) | Research-driven example tweaks | T16 |
| 15 | shape-grammar-researcher | research | `R:/Sandbox/.agent/adventures/ADV-008/**` | read | Read designs, schemas, manifest | T01, T16 |
| 16 | shape-grammar-researcher | research | `R:/Sandbox/shape_grammar/**` | read | Read package state for prototype recipes | T16 |
| 17 | geometry-engineer | implementing/testing | `R:/Sandbox/shape_grammar/**` | write | Primary implementation surface | T04-T15, T17, T18 |
| 18 | geometry-engineer | implementing/testing | `R:/Sandbox/.agent/adventures/ADV-008/**` | write | Research/test/validation docs | T02, T03, T19 |
| 19 | geometry-engineer | implementing | `R:/Sandbox/ark/**` | **read-only** | Reference Ark parser, verifier, specs | T03, T04, T07, T08, T15, T17 |
| 20 | geometry-engineer | DENY | `R:/Sandbox/ark/**` | **WRITE-DENIED** | Preserves TC-10 (no Ark modifications) | all |

### MCP Tools

| # | Agent | Stage | Tool | Reason | Tasks |
|---|-------|-------|------|--------|-------|
| - | - | - | - | None required; this adventure does not use MCP | - |

### External Access

| # | Agent | Stage | Type | Target | Reason | Tasks |
|---|-------|-------|------|--------|--------|-------|
| 21 | shape-grammar-researcher | research | WebFetch | `https://github.com/stefalie/shapeml` and child pages | Read upstream ShapeML source/docs | T01 |
| 22 | shape-grammar-researcher | research | WebFetch | `https://raw.githubusercontent.com/stefalie/shapeml/**` | Fetch raw source files | T01 |
| 23 | shape-grammar-researcher | research | WebSearch | open web | Background on CGA / semantic rendering / differentiable renderers | T01, T16 |
| 24 | geometry-engineer | implementing | none | - | Geometry engineer is offline-only by design | - |

## Validation Matrix

See Pass 4 above. All 6 validation checks PASS. 0 gaps.

## Historical Notes

- ADV-007 established per-role MCP enabling. Applied here: WebSearch/WebFetch are bound to the researcher only.
- ADV-002's reflexive self-indexing pattern motivates Prototype 2 (rendering `code_graph.ark` as procedural shapes).
- Knowledge-base pattern "Tier rather than rank external tools" (ADV007-T015) — not applicable here, no external tool catalog.

## Approval

- [ ] Approved by user
- [ ] Approved with modifications: ___
- [ ] Denied: ___
