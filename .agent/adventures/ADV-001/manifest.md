---
id: ADV-001
title: Expressif-style Expression & Predication System in Ark DSL
state: completed
created: 2026-04-11T00:00:00Z
updated: 2026-04-11T00:35:00Z
approved: 2026-04-11T00:01:00Z
tasks:
  - ADV001-T001
  - ADV001-T002
  - ADV001-T003
  - ADV001-T004
  - ADV001-T005
  - ADV001-T006
  - ADV001-T007
  - ADV001-T008
  - ADV001-T009
  - ADV001-T010
  - ADV001-T011
  - ADV001-T012
  - ADV001-T013
  - ADV001-T014
  - ADV001-T015
  - ADV001-T016
  - ADV001-T017
  - ADV001-T018
  - ADV001-T019
  - ADV001-T020
  - ADV001-T021
  - ADV001-T022
  - ADV001-T023
  - ADV001-T024
  - ADV001-T025
  - ADV001-T026
  - ADV001-T027
  - ADV001-T028
  - ADV001-T029
  - ADV001-T030
  - ADV001-T031
  - ADV001-T032
depends_on: []
---

## Concept

Review the Expressif library (https://github.com/Seddryck/Expressif) — a C# variable-substitution library that provides two core abstractions:

1. **Expression** — left-to-right function chains over a value, using a pipe syntax:
   `"@myVar | text-to-lower | text-to-pad-right(@count, *)"`
   Functions operate on scalars (numeric, text, temporal, file-path) and pass their output to the next function. Parameters can be literals, `@variables`, `[object-properties]`, `#collection-indices`, or nested `{...}` function calls.

2. **Predication** — boolean predicate combinations with short-circuit logical operators (`|AND`, `|OR`, `|XOR`), negation (`!`), and precedence via `{...}` grouping:
   `"starts-with(Nik) |AND ends-with(sla)"`
   Predicate categories include string matching, type checking, numeric intervals (`[0;20[`), temporal pattern matching, and type predicates.

3. **Function / predicate library** across numeric (absolute, add, ceiling, round, power, …), temporal (age, forward/backward, first-of-month, clamp, local-to-utc, …), text (lower, remove-chars, pad-right, …), file I/O (filename, extension, size, creation-datetime, …), and special values (null-to-zero, null-to-value, neutral).

### Goal in Ark

Define and implement this expression/predication system **as a first-class Ark DSL subsystem**, so that `.ark` specs can embed transformations and predicates declaratively, and so that Ark's codegen, verify, and runtime pipelines can target them.

Concretely this means:

- **DSL surface** — design the Ark-native syntax for expression chains and predicate combinations (either as new `expression` / `predicate` top-level items, or embedded inside `#process` bodies). Decide how it coexists with the existing `@in / #process / @out / $data` primitives.
- **Standard library** — port Expressif's function and predicate catalogue into `dsl/stdlib/` as Ark definitions (numeric, text, temporal, file, special). Each stdlib entry declares its input/output types and strategy.
- **Grammar & parser** — extend `dsl/grammar/ark.pest` (Rust) and `tools/parser/ark_grammar.lark` (Python) to parse the pipe/predicate syntax, producing AST nodes for expressions, predicates, and parameter references (literals, `@vars`, `[props]`, `#indices`, `{nested}`).
- **Verification** — add Z3 translation rules so that expression chains and predicate combinations can participate in `verify` blocks (e.g., prove that a chain is type-safe, that a predicate is satisfiable, or that an invariant holds over all inputs).
- **Codegen** — generate Rust (and at least one of C++/Protobuf) code that evaluates the chains at runtime, following Ark's strategy model (tensor / code / script / verified).
- **Test specs** — provide `.ark` examples under `specs/` that exercise both `expression` and `predication` forms, plus unit tests in `tests/` mirroring Expressif's coverage.

### Why this matters

Expressif encodes a mature, field-proven vocabulary for describing "small transformations of values" — exactly the primitive Ark currently lacks. Today Ark can describe entities, ports, processes, and strategies, but the **actual value-level transformations** inside a `#process` are written directly in the target language by codegen. Giving Ark a declarative expression layer closes that gap: designers can express "take `@player.last_seen | age | clamp(0, 30)` is-within `[0;14[`" directly in `.ark`, and the pipeline (parse → verify → codegen) covers it end-to-end.

## Open Design Questions (to resolve at Checkpoint 2)

The planner has deliberately left four trade-off calls to the user. Each is documented
inside the relevant design file with pros/cons. The plan assumes the **default** choice
for each; confirm or override at review time.

| # | Question | Options | Default | Design |
|---|----------|---------|---------|--------|
| 1 | Embedding model for expression/predicate | A top-level only • B inline only • **C both** | C | designs/01_dsl_surface.md |
| 2 | Language targets for v1 | A Rust+C+++Proto • **B Rust-only** | B | designs/05_codegen.md |
| 3 | Stdlib scope for v1 | A full parity • **B core subset (numeric+text+special+predicates)** | B | designs/03_stdlib_catalogue.md |
| 4 | Z3 coverage | A full SMT • **B decidable subset + opaque** | B | designs/04_verification.md |

## Target Conditions

| ID | Description | Source | Design | Plan | Task(s) | Proof Method | Proof Command | Status |
|----|-------------|--------|--------|------|---------|-------------|---------------|--------|
| TC-001 | `.ark` files can declare `expression Name { in, out, chain }` items producing `Item::Expression` | concept/01_dsl_surface | 01_dsl_surface | plan-grammar-ast | ADV001-T003, T004, T006 | autotest | `cd R:/Sandbox/ark && pytest tests/test_parser_expression_items.py -q` | pending |
| TC-002 | `.ark` files can declare `predicate Name { in, check }` items producing `Item::Predicate` | concept/01_dsl_surface | 01_dsl_surface | plan-grammar-ast | ADV001-T003, T004, T006 | autotest | `cd R:/Sandbox/ark && pytest tests/test_parser_expression_items.py -q` | pending |
| TC-003 | `\|>` operator parses left-associative in any expression context | 01_dsl_surface/02_grammar_parser | 02_grammar_parser | plan-grammar-ast | ADV001-T002, T004, T005, T006, T022 | autotest | `cd R:/Sandbox/ark && pytest tests/test_parser_pipe.py -q` | pending |
| TC-004 | Param-ref sigils `@var`, `[a.b]`, `#items[n]`, `{nested}` parse into tagged AST nodes | 01_dsl_surface/02_grammar_parser | 02_grammar_parser | plan-grammar-ast | ADV001-T002, T004, T005, T006, T022 | autotest | `cd R:/Sandbox/ark && pytest tests/test_parser_pipe.py -q` | pending |
| TC-005 | Python and Rust parsers produce equivalent JSON AST for expression forms | 01_dsl_surface | 02_grammar_parser | plan-grammar-ast | ADV001-T003, T004, T006, T030 | autotest | `cd R:/Sandbox/ark && cargo test -p ark-dsl && pytest tests/test_parser_pipe.py -q` | pending |
| TC-006 | Kebab-case function names accepted only inside pipe stages | 02_grammar_parser | 02_grammar_parser | plan-grammar-ast | ADV001-T002, T005, T022 | autotest | `cd R:/Sandbox/ark && pytest tests/test_parser_pipe.py::test_kebab_inside_pipe tests/test_parser_pipe.py::test_kebab_outside_pipe_errors -q` | pending |
| TC-007 | `expression` / `predicate` top-level items reach AST with all fields populated | 01_dsl_surface/02_grammar_parser | 02_grammar_parser | plan-grammar-ast | ADV001-T002, T003, T004, T005, T006, T023 | autotest | `cd R:/Sandbox/ark && pytest tests/test_parser_expression_items.py -q` | pending |
| TC-008 | Malformed expression/predicate items produce `ArkParseError` with file:line:col | 02_grammar_parser | 02_grammar_parser | plan-grammar-ast | ADV001-T006, T023 | autotest | `cd R:/Sandbox/ark && pytest tests/test_parser_expression_items.py::test_missing_chain_clause_errors -q` | pending |
| TC-009 | `import stdlib.expression` and `import stdlib.predicate` resolve and populate the new indices | 03_stdlib_catalogue | 03_stdlib_catalogue | plan-stdlib | ADV001-T006, T007, T008, T009, T010, T024 | autotest | `cd R:/Sandbox/ark && pytest tests/test_stdlib_expression.py -q` | pending |
| TC-010 | Every v1 numeric expression has a valid `EXPR_PRIMITIVES` entry | 03_stdlib_catalogue | 03_stdlib_catalogue | plan-stdlib | ADV001-T007, T011, T024 | autotest | `cd R:/Sandbox/ark && pytest tests/test_stdlib_expression.py::test_numeric_primitives_complete -q` | pending |
| TC-011 | Every v1 text expression has a valid `EXPR_PRIMITIVES` entry | 03_stdlib_catalogue | 03_stdlib_catalogue | plan-stdlib | ADV001-T008, T011, T024 | autotest | `cd R:/Sandbox/ark && pytest tests/test_stdlib_expression.py::test_text_primitives_complete -q` | pending |
| TC-012 | Every v1 predicate parses with Bool-typed `check:` | 03_stdlib_catalogue | 03_stdlib_catalogue | plan-stdlib | ADV001-T010, T024 | autotest | `cd R:/Sandbox/ark && pytest tests/test_stdlib_expression.py::test_predicates_bool -q` | pending |
| TC-013 | `python ark.py verify` translates numeric pipes into Z3 and returns PASS | 04_verification | 04_verification | plan-verify-codegen | ADV001-T012, T025 | autotest | `cd R:/Sandbox/ark && pytest tests/test_verify_expression.py::test_numeric_pipe_verifies -q` | pending |
| TC-014 | Predicate `check:` expressions participate in Z3 verify blocks | 04_verification | 04_verification | plan-verify-codegen | ADV001-T012, T013, T026 | autotest | `cd R:/Sandbox/ark && pytest tests/test_verify_predicate.py -q` | pending |
| TC-015 | Opaque primitives (regex, temporal, file-io) report PASS_OPAQUE not crash | 04_verification | 04_verification | plan-verify-codegen | ADV001-T014, T025 | autotest | `cd R:/Sandbox/ark && pytest tests/test_verify_expression.py::test_opaque_primitive_pass_opaque -q` | pending |
| TC-016 | User-defined expressions inline in verifier when called from process bodies | 04_verification | 04_verification | plan-verify-codegen | ADV001-T013, T025 | autotest | `cd R:/Sandbox/ark && pytest tests/test_verify_expression.py::test_user_expression_inline -q` | pending |
| TC-017 | Unknown pipe stage produces error with fuzzy suggestions | 04_verification | 04_verification | plan-verify-codegen | ADV001-T015, T025 | autotest | `cd R:/Sandbox/ark && pytest tests/test_verify_expression.py::test_unknown_stage_error -q` | pending |
| TC-018 | `ark.py codegen --target rust` emits one `pub fn` per expression item | 05_codegen | 05_codegen | plan-verify-codegen | ADV001-T016, T027 | autotest | `cd R:/Sandbox/ark && pytest tests/test_codegen_expression.py::test_expression_emits_pub_fn -q` | pending |
| TC-019 | Every numeric stdlib expression emits compilable Rust | 05_codegen | 05_codegen | plan-verify-codegen | ADV001-T016, T027 | autotest | `cd R:/Sandbox/ark && pytest tests/test_codegen_expression.py::test_numeric_rust_valid -q` | pending |
| TC-020 | Every text stdlib expression emits compilable Rust | 05_codegen | 05_codegen | plan-verify-codegen | ADV001-T016, T027 | autotest | `cd R:/Sandbox/ark && pytest tests/test_codegen_expression.py::test_text_rust_valid -q` | pending |
| TC-021 | Every predicate emits `pub fn ... -> bool` | 05_codegen | 05_codegen | plan-verify-codegen | ADV001-T017, T027 | autotest | `cd R:/Sandbox/ark && pytest tests/test_codegen_expression.py::test_predicate_emits_bool_fn -q` | pending |
| TC-022 | Inline pipes inside process bodies emit valid Rust | 05_codegen | 05_codegen | plan-verify-codegen | ADV001-T018, T027 | autotest | `cd R:/Sandbox/ark && pytest tests/test_codegen_expression.py::test_inline_pipe_in_process_body -q` | pending |
| TC-023 | C++ / Proto codegen raises `NotImplementedError` with follow-up adventure note | 05_codegen | 05_codegen | plan-verify-codegen | ADV001-T019, T027 | autotest | `cd R:/Sandbox/ark && pytest tests/test_codegen_expression.py::test_cpp_stub_raises -q` | pending |
| TC-024 | `specs/test_expression.ark` parses, verifies, and codegens end-to-end | 06_examples_and_tests | 06_examples_and_tests | plan-examples-and-tests | ADV001-T020, T028 | autotest | `cd R:/Sandbox/ark && pytest tests/test_pipeline_expression.py -q` | pending |
| TC-025 | All new pytest files pass under `pytest tests/ -q` | 06_examples_and_tests | 06_examples_and_tests | plan-examples-and-tests | ADV001-T029 | autotest | `cd R:/Sandbox/ark && pytest tests/ -q` | pending |
| TC-026 | `cargo test -p ark-dsl` passes all new Rust AST tests | 06_examples_and_tests | 06_examples_and_tests | plan-examples-and-tests | ADV001-T030 | autotest | `cd R:/Sandbox/ark && cargo test -p ark-dsl` | pending |
| TC-027 | `specs/examples/expressif_examples.ark` parses cleanly | 06_examples_and_tests | 06_examples_and_tests | plan-examples-and-tests | ADV001-T021 | autotest | `cd R:/Sandbox/ark && python ark.py parse specs/examples/expressif_examples.ark` | pending |
| TC-028 | Line coverage for expression/predicate modules >= 80% | 06_examples_and_tests | 06_examples_and_tests | plan-examples-and-tests | ADV001-T029 | autotest | `cd R:/Sandbox/ark && coverage run -m pytest tests/test_*expression*.py tests/test_*predicate*.py && coverage report --fail-under=80` | pending |
| TC-029 | `docs/DSL_SPEC.md` documents expression/predicate subsystem | 01_dsl_surface | 01_dsl_surface | plan-docs-backlog | ADV001-T031 | manual | read `R:/Sandbox/ark/docs/DSL_SPEC.md`, confirm section exists and cites stdlib files | pending |
| TC-030 | Backlog updated with adventure entry | - | - | plan-docs-backlog | ADV001-T032 | autotest | `cd R:/Sandbox/ark && python ark.py verify specs/meta/backlog.ark` | pending |

## Evaluations

| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |
|------|-------------------|-----------|---------------|-------------|-----------|-----------------|---------------|-------------|----------|
| ADV001-T001 | Read adventure designs, Write | Test planning, pytest, cargo | 15min | 15000 | $0.225 (opus) | - | - | - | - |
| ADV001-T002 | Edit ark.pest, cargo | Rust, pest PEG | 25min | 35000 | $0.105 | - | - | - | - |
| ADV001-T003 | Edit lib.rs, cargo | Rust, serde | 20min | 30000 | $0.090 | - | - | - | - |
| ADV001-T004 | Edit parse.rs, cargo | Rust, pest pairs | 30min | 60000 | $0.180 | - | - | - | - |
| ADV001-T005 | Edit ark_grammar.lark, ark.py | Lark EBNF | 25min | 35000 | $0.105 | - | - | - | - |
| ADV001-T006 | Edit ark_parser.py, pytest | Python, Lark | 30min | 60000 | $0.180 | - | - | - | - |
| ADV001-T007 | Write expression.ark | Ark DSL | 15min | 20000 | $0.060 | - | - | - | - |
| ADV001-T008 | Edit expression.ark | Ark DSL | 10min | 15000 | $0.045 | - | - | - | - |
| ADV001-T009 | Edit expression.ark | Ark DSL | 5min | 8000 | $0.024 | - | - | - | - |
| ADV001-T010 | Write predicate.ark | Ark DSL | 15min | 20000 | $0.060 | - | - | - | - |
| ADV001-T011 | Write expression_primitives.py | Python, Rust map | 20min | 25000 | $0.075 | - | - | - | - |
| ADV001-T012 | Edit ark_verify.py, pytest | Python, Z3 | 25min | 45000 | $0.135 | - | - | - | - |
| ADV001-T013 | Edit ark_verify.py, pytest | Python, cycles | 20min | 35000 | $0.105 | - | - | - | - |
| ADV001-T014 | Write expression_smt.py, pytest | Python, Z3 UF | 20min | 30000 | $0.090 | - | - | - | - |
| ADV001-T015 | Edit ark_verify.py, pytest | Python, difflib | 10min | 15000 | $0.045 | - | - | - | - |
| ADV001-T016 | Edit ark_codegen.py, ark.py | Python, Rust codegen | 30min | 55000 | $0.165 | - | - | - | - |
| ADV001-T017 | Edit ark_codegen.py, rustc | Python, Rust | 15min | 25000 | $0.075 | - | - | - | - |
| ADV001-T018 | Edit ark_codegen.py, ark.py | Python, Rust | 25min | 45000 | $0.135 | - | - | - | - |
| ADV001-T019 | Edit ark_codegen.py | Python | 10min | 12000 | $0.036 | - | - | - | - |
| ADV001-T020 | Write test_expression.ark, ark.py pipeline | Ark DSL | 10min | 15000 | $0.045 | - | - | - | - |
| ADV001-T021 | Write expressif_examples.ark | Ark DSL | 10min | 12000 | $0.036 | - | - | - | - |
| ADV001-T022 | Write test_parser_pipe.py, pytest | pytest | 20min | 30000 | $0.090 | - | - | - | - |
| ADV001-T023 | Write test_parser_expression_items.py | pytest | 15min | 22000 | $0.066 | - | - | - | - |
| ADV001-T024 | Write test_stdlib_expression.py | pytest | 12min | 18000 | $0.054 | - | - | - | - |
| ADV001-T025 | Write test_verify_expression.py | pytest, Z3 | 20min | 30000 | $0.090 | - | - | - | - |
| ADV001-T026 | Write test_verify_predicate.py | pytest, Z3 | 15min | 22000 | $0.066 | - | - | - | - |
| ADV001-T027 | Write test_codegen_expression.py | pytest | 25min | 40000 | $0.120 | - | - | - | - |
| ADV001-T028 | Write test_pipeline_expression.py, subprocess | pytest | 15min | 20000 | $0.060 | - | - | - | - |
| ADV001-T029 | pytest, cargo, coverage, Write | test orchestration | 25min | 40000 | $0.120 | - | - | - | - |
| ADV001-T030 | Edit parse.rs, cargo test | Rust, serde tests | 20min | 30000 | $0.090 | - | - | - | - |
| ADV001-T031 | Edit DSL_SPEC.md | Technical writing | 20min | 25000 | $0.075 | - | - | - | - |
| ADV001-T032 | Edit backlog.ark, ark.py verify | Ark DSL | 10min | 15000 | $0.045 | - | - | - | - |
| **TOTAL** | | | **~9h 20min** | **904000** | **~$2.89** | | | | |

Cost breakdown: T001 opus ($0.225) + 31 sonnet tasks ($2.667) ≈ $2.892. Token totals
assume a single-pass execution; re-runs would scale linearly.

## Environment
- **Project**: ARK (Architecture Kernel) — declarative MMO game-engine DSL
- **Workspace**: R:/Sandbox (Ark tree at R:/Sandbox/ark)
- **Repo**: local (no git remote)
- **Branch**: local (not a git repo)
- **PC**: TTT
- **Platform**: Windows 11 Pro 10.0.26200
- **Runtime**: Node v24.12.0 (project runtime: Python 3 + Rust/Cargo)
- **Shell**: bash
