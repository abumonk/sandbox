---
adventure_id: ADV-001
status: approved
created: 2026-04-11T00:15:00Z
approved: 2026-04-11T00:35:00Z
passes_completed: 4
validation_gaps: 0
---

# Permission Requests — ADV-001: Expressif-style Expression & Predication System in Ark DSL

## Summary

34 permission entries across 32 tasks and 3 agent roles (planner, coder, qa-tester). All
4 analysis passes complete. 0 validation gaps. The Ark project has no git remote, so no
remote git operations are required. Python (`pip install lark-parser z3-solver` already
done per CLAUDE.md) and Rust (cargo workspace at `R:/Sandbox/ark/`) are the runtime
substrates; both are pre-installed.

## Pass 1 — Codebase Tooling Scan

Discovered tooling from the Ark project:

- `R:/Sandbox/ark/ark.py` — unified CLI with subcommands: parse, verify, codegen, impact,
  diff, watch, dispatch, pipeline, graph
- `R:/Sandbox/ark/Cargo.toml` — Rust workspace root; builds via `cargo build -p ark-dsl`,
  tests via `cargo test -p ark-dsl`
- `R:/Sandbox/ark/tests/conftest.py` — pytest fixtures; runs via `pytest R:/Sandbox/ark/tests/ -q`
- Python deps: `lark-parser`, `z3-solver` (pre-installed, used as libraries not CLIs)
- No linter configured (neither `ruff`, `black`, nor `pylint` observed); style follows
  existing code by inspection
- No formatter
- No .env files; no secrets required
- No CI workflow (`.github/workflows/` absent)

## Pass 2 — Plan-Driven Analysis

Per-task execution paths:

- **T001** (planner): Read designs, Write test-strategy.md. No Bash.
- **T002-T004** (coder): Rust grammar/AST edits → `cargo build -p ark-dsl`, `cargo test -p ark-dsl`
- **T005-T006** (coder): Python parser edits → `python ark.py parse ...`, `pytest tests/test_parser_*.py`
- **T007-T011** (coder): Stdlib .ark authoring + Python primitive map → `python ark.py parse`
- **T012-T015** (coder): Z3 translation edits → `pytest tests/test_verify_*.py`
- **T016-T019** (coder): Codegen edits → `python ark.py codegen ...`, optionally
  `rustc --emit=metadata` on generated output
- **T020-T021** (coder): Write .ark specs → `python ark.py parse/verify/codegen/pipeline`
- **T022-T028** (qa-tester): Write test files → `pytest tests/ -q`
- **T029** (qa-tester): Full suite + coverage → `pytest`, `coverage`, `cargo test`
- **T030** (coder): Rust inline tests → `cargo test -p ark-dsl`
- **T031-T032** (coder): Doc edits + backlog → `python ark.py verify specs/meta/backlog.ark`

## Pass 3 — Historical Pattern Match

`.agent/knowledge/patterns.md`, `decisions.md`, `issues.md` are all empty (no prior
adventures). This is the first adventure, so there are no historical gaps to inherit.
Defensive additions based on CLAUDE.md and the test layout:

- `pytest -q` may hit Unicode-encoding issues on Windows; `ark.py` already reconfigures
  stdout/stderr to UTF-8. The test runner inherits this.
- `cargo` invocations must be run from `R:/Sandbox/ark/` (workspace root), not from
  `R:/Sandbox/`.

## Pass 4 — Cross-Validation Matrix

| Task | Agent | Stage | Read | Write | Shell | MCP | External | Verified |
|------|-------|-------|------|-------|-------|-----|----------|----------|
| T001 | planner | planning | designs/** | adv/tests/test-strategy.md | - | - | - | Y |
| T002 | coder | implementing | ark.pest | ark.pest | cargo build/test | - | - | Y |
| T003 | coder | implementing | lib.rs | lib.rs | cargo build/test | - | - | Y |
| T004 | coder | implementing | parse.rs | parse.rs | cargo test | - | - | Y |
| T005 | coder | implementing | ark_grammar.lark | ark_grammar.lark | python ark.py parse | - | - | Y |
| T006 | coder | implementing | ark_parser.py | ark_parser.py | pytest, ark.py parse | - | - | Y |
| T007 | coder | implementing | stdlib/types.ark | stdlib/expression.ark | ark.py parse | - | - | Y |
| T008 | coder | implementing | stdlib/expression.ark | stdlib/expression.ark | ark.py parse | - | - | Y |
| T009 | coder | implementing | stdlib/expression.ark | stdlib/expression.ark | ark.py parse | - | - | Y |
| T010 | coder | implementing | - | stdlib/predicate.ark | ark.py parse | - | - | Y |
| T011 | coder | implementing | stdlib/*.ark | tools/codegen/expression_primitives.py | python -c | - | - | Y |
| T012 | coder | implementing | ark_verify.py | ark_verify.py | pytest | - | - | Y |
| T013 | coder | implementing | ark_verify.py | ark_verify.py | pytest | - | - | Y |
| T014 | coder | implementing | ark_verify.py | tools/verify/expression_smt.py, ark_verify.py | pytest | - | - | Y |
| T015 | coder | implementing | ark_verify.py | ark_verify.py | pytest | - | - | Y |
| T016 | coder | implementing | ark_codegen.py, expression_primitives.py | ark_codegen.py | ark.py codegen | - | - | Y |
| T017 | coder | implementing | ark_codegen.py | ark_codegen.py | ark.py codegen, rustc | - | - | Y |
| T018 | coder | implementing | ark_codegen.py | ark_codegen.py | ark.py codegen | - | - | Y |
| T019 | coder | implementing | ark_codegen.py | ark_codegen.py | ark.py codegen | - | - | Y |
| T020 | coder | implementing | stdlib/** | specs/test_expression.ark | ark.py pipeline | - | - | Y |
| T021 | coder | implementing | specs/test_expression.ark | specs/examples/expressif_examples.ark | ark.py parse | - | - | Y |
| T022 | qa-tester | reviewing | ark_parser.py | tests/test_parser_pipe.py | pytest | - | - | Y |
| T023 | qa-tester | reviewing | ark_parser.py | tests/test_parser_expression_items.py | pytest | - | - | Y |
| T024 | qa-tester | reviewing | stdlib/**, expression_primitives.py | tests/test_stdlib_expression.py | pytest | - | - | Y |
| T025 | qa-tester | reviewing | ark_verify.py | tests/test_verify_expression.py | pytest | - | - | Y |
| T026 | qa-tester | reviewing | ark_verify.py | tests/test_verify_predicate.py | pytest | - | - | Y |
| T027 | qa-tester | reviewing | ark_codegen.py | tests/test_codegen_expression.py | pytest | - | - | Y |
| T028 | qa-tester | reviewing | specs/test_expression.ark | tests/test_pipeline_expression.py | pytest | - | - | Y |
| T029 | qa-tester | reviewing | all tests | adv/tests/test-results.md | pytest, cargo test, coverage | - | - | Y |
| T030 | coder | implementing | parse.rs | parse.rs | cargo test | - | - | Y |
| T031 | coder | implementing | DSL_SPEC.md | DSL_SPEC.md | - | - | - | Y |
| T032 | coder | implementing | backlog.ark | backlog.ark | ark.py verify | - | - | Y |

Validation checks:
1. Every task has at least one permission entry per assigned agent role → **OK**
2. Every shell command from Pass 1 that relates to a task's files is covered → **OK**
3. Every `proof_command` in target conditions is covered by the shell section → **OK**
4. Every file in a task's `files` field has a corresponding read or write permission → **OK**
5. Task dependencies: dependent task's agent has read access to predecessor's output → **OK**
   (all coder tasks share the same Ark tree read/write scope)
6. Git operations covered if `git.mode` is `branch-per-task` → **N/A** (config is
   `current-branch`, no remote)

## Requests

### Shell Access

| # | Agent | Stage | Command | Reason | Tasks |
|---|-------|-------|---------|--------|-------|
| 1 | coder | implementing | `cd R:/Sandbox/ark && cargo build -p ark-dsl` | Verify Rust grammar + AST changes compile | T002, T003, T004 |
| 2 | coder | implementing | `cd R:/Sandbox/ark && cargo test -p ark-dsl` | Run Rust unit tests after AST/parser changes | T002, T003, T004, T030 |
| 3 | coder | implementing | `cd R:/Sandbox/ark && python ark.py parse <file>` | Smoke-test parser on .ark files | T005, T006, T007, T008, T009, T010, T020, T021 |
| 4 | coder | implementing | `cd R:/Sandbox/ark && python ark.py verify <file>` | Run Z3 verification | T012, T013, T014, T015, T020, T032 |
| 5 | coder | implementing | `cd R:/Sandbox/ark && python ark.py codegen <file> --target rust` | Generate Rust from .ark | T016, T017, T018, T019, T020 |
| 6 | coder | implementing | `cd R:/Sandbox/ark && python ark.py codegen <file> --target cpp` | Trigger C++ stub NotImplementedError | T019 |
| 7 | coder | implementing | `cd R:/Sandbox/ark && python ark.py pipeline <file> --target rust` | Full end-to-end | T020 |
| 8 | coder | implementing | `cd R:/Sandbox/ark && python -c "<snippet>"` | Probe python modules (expression_primitives sanity check) | T011 |
| 9 | coder | implementing | `cd R:/Sandbox/ark && pytest tests/ -q` | Regression guard during implementation | T006, T012-T019 |
| 10 | coder | implementing | `cd R:/Sandbox/ark && rustc --edition 2021 --crate-type=lib --emit=metadata <file>` | Validate generated Rust compiles standalone (optional for T017) | T017 |
| 11 | qa-tester | reviewing | `cd R:/Sandbox/ark && pytest tests/test_parser_*.py -q` | Run parser test subset | T022, T023 |
| 12 | qa-tester | reviewing | `cd R:/Sandbox/ark && pytest tests/test_stdlib_*.py -q` | Run stdlib tests | T024 |
| 13 | qa-tester | reviewing | `cd R:/Sandbox/ark && pytest tests/test_verify_*.py -q` | Run verify tests | T025, T026 |
| 14 | qa-tester | reviewing | `cd R:/Sandbox/ark && pytest tests/test_codegen_*.py -q` | Run codegen tests | T027 |
| 15 | qa-tester | reviewing | `cd R:/Sandbox/ark && pytest tests/test_pipeline_*.py -q` | Run pipeline end-to-end test | T028 |
| 16 | qa-tester | reviewing | `cd R:/Sandbox/ark && pytest tests/ -q` | Full suite regression | T029 |
| 17 | qa-tester | reviewing | `cd R:/Sandbox/ark && cargo test -p ark-dsl` | Final Rust test run | T029 |
| 18 | qa-tester | reviewing | `cd R:/Sandbox/ark && coverage run -m pytest tests/test_*expression*.py tests/test_*predicate*.py && coverage report` | Coverage for TC-028 | T029 |

### File Access

| # | Agent | Stage | Scope | Mode | Reason | Tasks |
|---|-------|-------|-------|------|--------|-------|
| 1 | planner | planning | `R:/Sandbox/.agent/adventures/ADV-001/designs/**` | read | Read designs | T001 |
| 2 | planner | planning | `R:/Sandbox/.agent/adventures/ADV-001/tests/test-strategy.md` | write | Output test strategy | T001 |
| 3 | coder | implementing | `R:/Sandbox/ark/dsl/grammar/ark.pest` | read, write | Edit pest grammar | T002 |
| 4 | coder | implementing | `R:/Sandbox/ark/dsl/src/lib.rs` | read, write | Extend Rust AST | T003 |
| 5 | coder | implementing | `R:/Sandbox/ark/dsl/src/parse.rs` | read, write | Add AST builders + inline tests | T004, T030 |
| 6 | coder | implementing | `R:/Sandbox/ark/tools/parser/ark_grammar.lark` | read, write | Mirror grammar | T005 |
| 7 | coder | implementing | `R:/Sandbox/ark/tools/parser/ark_parser.py` | read, write | Extend transformer + dataclasses | T006 |
| 8 | coder | implementing | `R:/Sandbox/ark/dsl/stdlib/expression.ark` | write | New stdlib file | T007, T008, T009 |
| 9 | coder | implementing | `R:/Sandbox/ark/dsl/stdlib/types.ark` | read | Reference existing types | T007 |
| 10 | coder | implementing | `R:/Sandbox/ark/dsl/stdlib/predicate.ark` | write | New stdlib file | T010 |
| 11 | coder | implementing | `R:/Sandbox/ark/tools/codegen/expression_primitives.py` | write, read | New primitive map | T011, T016 |
| 12 | coder | implementing | `R:/Sandbox/ark/tools/verify/ark_verify.py` | read, write | Extend Z3 translator | T012, T013, T014, T015 |
| 13 | coder | implementing | `R:/Sandbox/ark/tools/verify/expression_smt.py` | write | New opaque primitive module | T014 |
| 14 | coder | implementing | `R:/Sandbox/ark/tools/codegen/ark_codegen.py` | read, write | Extend codegen | T016, T017, T018, T019 |
| 15 | coder | implementing | `R:/Sandbox/ark/specs/test_expression.ark` | write, read | Smoke spec | T020, T021, T028 |
| 16 | coder | implementing | `R:/Sandbox/ark/specs/examples/expressif_examples.ark` | write | Doc example | T021 |
| 17 | coder | implementing | `R:/Sandbox/ark/docs/DSL_SPEC.md` | read, write | Doc section | T031 |
| 18 | coder | implementing | `R:/Sandbox/ark/specs/meta/backlog.ark` | read, write | Backlog entry | T032 |
| 19 | qa-tester | reviewing | `R:/Sandbox/ark/tests/test_parser_pipe.py` | write | New test file | T022 |
| 20 | qa-tester | reviewing | `R:/Sandbox/ark/tests/test_parser_expression_items.py` | write | New test file | T023 |
| 21 | qa-tester | reviewing | `R:/Sandbox/ark/tests/test_stdlib_expression.py` | write | New test file | T024 |
| 22 | qa-tester | reviewing | `R:/Sandbox/ark/tests/test_verify_expression.py` | write | New test file | T025 |
| 23 | qa-tester | reviewing | `R:/Sandbox/ark/tests/test_verify_predicate.py` | write | New test file | T026 |
| 24 | qa-tester | reviewing | `R:/Sandbox/ark/tests/test_codegen_expression.py` | write | New test file | T027 |
| 25 | qa-tester | reviewing | `R:/Sandbox/ark/tests/test_pipeline_expression.py` | write | New test file | T028 |
| 26 | qa-tester | reviewing | `R:/Sandbox/ark/tests/conftest.py` | read | Fixture reference | T022-T028 |
| 27 | qa-tester | reviewing | `R:/Sandbox/.agent/adventures/ADV-001/tests/test-results.md` | write | Results doc | T029 |
| 28 | all | all | `R:/Sandbox/.agent/adventures/ADV-001/**` | read | Read plan / designs / schemas | all |
| 29 | coder | implementing | `R:/Sandbox/ark/tests/**` | read | Reference existing test patterns | T006, T012-T019, T030 |
| 30 | coder | implementing | `R:/Sandbox/ark/ark.py` | read | CLI entry point reference | T006, T016 |

### MCP Tools

None required. The adventure uses only the built-in Claude Code tools (Read, Write, Edit,
Glob, Grep, Bash).

### External Access

None required. This is a pure local code change. The Expressif library reference is
conceptual (already summarized in the manifest concept section); no runtime fetch of
Expressif source is needed — if an implementer wants to cross-check, they may use
WebFetch on the GitHub URL, but it is **optional**.

Optional (not required for task completion):
- `WebFetch https://github.com/Seddryck/Expressif/**` — only for clarification of function
  naming or edge-case behavior; provenance-only, not for copy-paste

## Historical Notes

No prior adventures; `.agent/knowledge/` is empty. This adventure's patterns (grammar
parity between pest and Lark, always run `cargo test -p ark-dsl` after lib.rs edits) should
be recorded in `.agent/knowledge/patterns.md` at close-out.

## Approval

- [ ] Approved by user
- [ ] Approved with modifications: {notes}
- [ ] Denied: {reason}
