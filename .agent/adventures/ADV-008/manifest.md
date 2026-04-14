---
id: ADV-008
title: ShapeML-style Procedural Shape Grammar in Ark DSL + Semantic Rendering
state: completed
created: 2026-04-14T11:00:00Z
updated: 2026-04-14T15:50:00Z
tasks: [ADV008-T01, ADV008-T02, ADV008-T03, ADV008-T04, ADV008-T05, ADV008-T06, ADV008-T07, ADV008-T08, ADV008-T09, ADV008-T10, ADV008-T11, ADV008-T12, ADV008-T13, ADV008-T14, ADV008-T15, ADV008-T16, ADV008-T17, ADV008-T18, ADV008-T19]
depends_on: []
---

## Concept

Review the ShapeML project — a C++ procedural shape-modeling language for generating 3D geometry via rewriting rules (a modern, compiler-based successor to CGA shape grammars like Esri CityEngine / Pirkka Aho's work). Upstream: `https://github.com/stefalie/shapeml.git`.

**Architecture (settled)**: `shape_grammar/` is a **sibling package in `R:/Sandbox/`** that *consumes* Ark DSL as its host language — it is NOT added to Ark's stdlib. Dependency direction is strict `shape_grammar → ark`; Ark is never modified. Shape grammars are written as ordinary Ark islands using existing Ark syntax (no Lark grammar changes, no new AST nodes in Ark core). The `shape_grammar` package provides the semantics (evaluator, verifier passes, codegen, runtime) that interpret those islands. This serves as the first real dogfooding of Ark-as-host-language.

Model ShapeML's core concepts (shape, rule, module, parameters, terminal vs. non-terminal symbols, geometric operations, attribute inheritance, deterministic evaluation, rewriting engine) as `.ark` island content with Z3-verifiable invariants, codegen paths (Python for the reference interpreter / Rust skeleton for the performant evaluator), and external adapters into the existing Ark toolchain (visualizer, ark-impact, ark-diff).

**Research deliverable**: explore how a procedural shape grammar integrated into Ark can serve *semantic rendering* — i.e. rendering driven by meaning, not just geometry. Candidate directions:
- Shape rules annotated with semantic labels (e.g. "window", "load-bearing", "decorative") that propagate through derivations, letting the renderer select materials/shaders/LOD by semantic class rather than mesh id.
- Shape-grammar output as input to a differentiable or neural renderer, where the rule tree is the scene description (explainable procgen).
- Integration with Ark's `code_graph.ark` island (from ADV-007 T012) so generated shapes have traceability back to the rule that produced them.
- Application to LOD visualization of adventures/workflow graphs themselves (dogfooding — render Ark `.ark` specs as procedural visual forms whose structure reflects the spec's logic).

**Deliverables**:
1. Research: ShapeML architecture, grammar, runtime, compiler pipeline, file format, key abstractions.
2. Design: a `shape_grammar.ark` specification island — entities, rules, operations, evaluation semantics — that mirrors ShapeML's expressive power.
3. Parser: Lark grammar for `.shape` (or inline `.ark` shape-rule) syntax, producing IR compatible with Ark's existing verifier/codegen.
4. Verifier: Z3 invariants — termination (bounded derivation depth), determinism (no order-sensitivity), scope/attribute safety.
5. Codegen: Python interpreter for the reference evaluator; Rust evaluator skeleton for the performant path.
6. Semantic-rendering research document with concrete prototype recipes (at least 2 end-to-end worked examples).
7. Integration with existing Ark tools (visualizer, impact analysis).
8. Automated tests (pytest) covering parser, verifier, evaluator, semantic-rendering scenarios.

## Target Conditions

| ID | Description | Source | Design | Plan | Task(s) | Proof Method | Proof Command | Status |
|----|-------------|--------|--------|------|---------|-------------|---------------|--------|
| TC-01 | `shape_grammar/` package layout exists with specs + tools + tests + examples + rust subtree | design-shape-grammar-package | design-shape-grammar-package | phase-b, phase-d | T04, T05, T06, T07, T10-T15 | poc | `test -d shape_grammar/specs && test -d shape_grammar/tools && test -d shape_grammar/tests && test -d shape_grammar/examples && test -d shape_grammar/tools/rust` | passed |
| TC-02 | `ark verify shape_grammar/specs/shape_grammar.ark` exits 0 under vanilla Ark (proves host-language feasibility) | plan/design-shape-grammar-package | design-shape-grammar-package | phase-b | T04, T05, T06 | poc | `python ark/ark.py verify shape_grammar/specs/shape_grammar.ark` | passed |
| TC-03 | IR extraction returns populated ShapeGrammarIR from every spec island | design-shape-grammar-package §IR | design-shape-grammar-package | phase-c | T07, T09 | autotest | `pytest shape_grammar/tests/test_ir.py -q` | passed |
| TC-04a | Termination verifier pass passes on all 4 examples | design-verifier-passes | design-verifier-passes | phase-c | T08, T09 | autotest | `pytest shape_grammar/tests/test_verifier.py -k termination -q` | passed |
| TC-04b | Determinism verifier pass passes on all 4 examples | design-verifier-passes | design-verifier-passes | phase-c | T08, T09 | autotest | `pytest shape_grammar/tests/test_verifier.py -k determinism -q` | passed |
| TC-04c | Scope-safety verifier pass passes on all 4 examples | design-verifier-passes | design-verifier-passes | phase-c | T08, T09 | autotest | `pytest shape_grammar/tests/test_verifier.py -k scope -q` | passed |
| TC-04d | Termination pass FAILs on the deliberate unbounded-derivation counterexample fixture | design-verifier-passes | design-verifier-passes | phase-c | T08, T09 | autotest | `pytest shape_grammar/tests/test_verifier.py -k unbounded -q` | passed |
| TC-05 | Python evaluator round-trip produces deterministic terminals under fixed seed | design-evaluator | design-evaluator | phase-d, phase-e | T10, T11, T12, T18 | autotest | `pytest shape_grammar/tests/test_evaluator.py -q` | passed |
| TC-06 | Rust skeleton compiles via cargo check | design-shape-grammar-package §Rust | design-shape-grammar-package | phase-d | T14, T19 | poc | `cargo check --manifest-path shape_grammar/tools/rust/Cargo.toml` | passed |
| TC-07 | End-to-end round-trip grammar → evaluator → OBJ produces non-empty file | design-evaluator, design-semantic-rendering | design-evaluator | phase-d, phase-e | T12, T13, T18, T19 | poc | `python -m shape_grammar.tools.evaluator shape_grammar/examples/cga_tower.ark --seed 42 --out /tmp/tower.obj && test -s /tmp/tower.obj` | passed |
| TC-08 | Semantic label propagation: every terminal carries an inherited-or-overridden label | design-semantic-rendering | design-semantic-rendering | phase-d, phase-e | T13, T18 | autotest | `pytest shape_grammar/tests/test_semantic.py -q` | passed |
| TC-09 | Semantic-rendering research document exists with exactly 2 prototypes | design-semantic-rendering | design-semantic-rendering | phase-e | T16 | poc | `test -f .agent/adventures/ADV-008/research/semantic-rendering.md && [ $(grep -c "### Prototype" .agent/adventures/ADV-008/research/semantic-rendering.md) -eq 2 ]` | passed |
| TC-10 | **No Ark modifications by ADV-008** — current `git diff master -- ark/` matches the pre-adventure baseline snapshot captured at T04 start (adjusted for pre-existing drift from prior work) | ADR-001 | adr-001 | phase-e | T19 | poc | `diff <(git diff master -- ark/) .agent/adventures/ADV-008/baseline-ark.diff` | passed |
| TC-11 | Visualizer adapter produces annotated HTML for a shape-grammar island | design-integrations | design-integrations | phase-e | T17, T18 | autotest | `pytest shape_grammar/tests/test_integrations.py -k visualizer -q` | passed |
| TC-12 | Impact adapter returns augmented report with rule-tree edges | design-integrations | design-integrations | phase-e | T17, T18 | autotest | `pytest shape_grammar/tests/test_integrations.py -k impact -q` | passed |
| TC-13 | Diff adapter returns rule-tree structural diff | design-integrations | design-integrations | phase-e | T17, T18 | autotest | `pytest shape_grammar/tests/test_integrations.py -k diff -q` | passed |
| TC-14 | Full integration adapter test suite green | design-integrations | design-integrations | phase-e | T17, T18 | autotest | `pytest shape_grammar/tests/test_integrations.py -q` | passed |
| TC-15 | ShapeML architecture research document exists with ≥6 H2 sections | concept | design-shape-grammar-package | phase-a | T01 | poc | `test -f .agent/adventures/ADV-008/research/shapeml-architecture.md && [ $(grep -c "^## " .agent/adventures/ADV-008/research/shapeml-architecture.md) -ge 6 ]` | passed |
| TC-16 | Test strategy document covers every autotest TC with a named test function | plan/design-shape-grammar-package | design-shape-grammar-package | phase-a | T02 | poc | `test -f .agent/adventures/ADV-008/tests/test-strategy.md && grep -q "TC-03" .agent/adventures/ADV-008/tests/test-strategy.md` | passed |
| TC-17 | Four example grammars exist and parse + verify under vanilla Ark | design-semantic-rendering, design-evaluator | design-shape-grammar-package | phase-e | T15 | poc | `for f in shape_grammar/examples/l_system.ark shape_grammar/examples/cga_tower.ark shape_grammar/examples/semantic_facade.ark shape_grammar/examples/code_graph_viz.ark; do python ark/ark.py verify "$f" || exit 1; done` | passed |
| TC-18 | Ark-as-host feasibility study documents every entity with a feasibility verdict and zero BLOCKED | ADR-001 | design-shape-grammar-package | phase-a | T03 | poc | `test -f .agent/adventures/ADV-008/research/ark-as-host-feasibility.md && ! grep -q "BLOCKED" .agent/adventures/ADV-008/research/ark-as-host-feasibility.md` | passed |
| TC-19 | RNG determinism: `SeededRng(42).fork("a")` reproduces identical sequence across runs | design-evaluator | design-evaluator | phase-d, phase-e | T10, T18 | autotest | `pytest shape_grammar/tests/test_evaluator.py -k rng_determinism -q` | passed |
| TC-20 | Example-driven end-to-end tests: parse + verify + IR + evaluate each of 4 examples | design-shape-grammar-package | design-shape-grammar-package | phase-e | T15, T18 | autotest | `pytest shape_grammar/tests/test_examples.py -q` | passed |
| TC-21 | Full shape_grammar test suite green | plan | design-shape-grammar-package | phase-e | T09, T18, T19 | autotest | `pytest shape_grammar/tests/ -q` | passed |
| TC-22 | Test strategy authored *before* implementation starts (T02 precedes T07+) | knowledge-base pattern "Test strategy before implementation" | design-shape-grammar-package | phase-a | T02 | poc | `test -f .agent/adventures/ADV-008/tests/test-strategy.md` | passed |
| TC-23 | Dependency direction is one-way — `shape_grammar/` is not imported anywhere under `ark/` | ADR-001 | adr-001 | phase-e | T19 | poc | `! grep -r "shape_grammar" ark/ --include="*.py" --include="*.ark" --include="*.rs"` | passed |
| TC-24 | Verifier passes are invokable via CLI: `python -m shape_grammar.tools.verify all <file>` | design-verifier-passes | design-verifier-passes | phase-c | T08 | poc | `python -m shape_grammar.tools.verify all shape_grammar/specs/shape_grammar.ark` | passed |
| TC-25 | `ir.py` is invokable via CLI and emits JSON-shaped IR | design-shape-grammar-package §IR | design-shape-grammar-package | phase-c | T07 | poc | `python -m shape_grammar.tools.ir shape_grammar/specs/shape_grammar.ark` | passed |

## Evaluations
| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |
|------|-------------------|-----------|---------------|-------------|-----------|-----------------|---------------|-------------|----------|
| ADV008-T01 | WebFetch, Write(research/) | research, C++ literacy, technical writing | 25min | 45000 | $0.675 | - | - | - | - |
| ADV008-T02 | Read(designs,schemas), Write(tests/) | pytest, test design | 20min | 30000 | $0.450 | - | - | - | - |
| ADV008-T03 | Read(ark/**), Write(research/) | Ark DSL, Z3, Python parser internals | 30min | 50000 | $0.750 | - | - | - | - |
| ADV008-T04 | Read, Write(shape_grammar/specs/), Bash(ark) | Ark DSL authoring | 25min | 40000 | $0.600 | - | - | - | - |
| ADV008-T05 | Read, Write(shape_grammar/specs/), Bash(ark) | Ark DSL authoring | 20min | 30000 | $0.450 | - | - | - | - |
| ADV008-T06 | Read, Write(shape_grammar/specs/), Bash(ark) | Ark DSL authoring | 15min | 22000 | $0.330 | - | - | - | - |
| ADV008-T07 | Read(ark/parser,shape_grammar/specs), Write(tools/), Bash(python) | Python, Lark AST | 30min | 60000 | $0.900 | - | - | - | - |
| ADV008-T08 | Read(ark/verify,shape_grammar/specs), Write(tools/verify/), Bash(python+z3) | Z3, SMT modeling, Python | 30min | 75000 | $1.125 | - | - | - | - |
| ADV008-T09 | Read(shape_grammar/), Write(tests/ + fixtures/), Bash(pytest) | pytest | 25min | 50000 | $0.750 | - | - | - | - |
| ADV008-T10 | Read(designs), Write(tools/), Bash(python) | Python | 20min | 35000 | $0.525 | - | - | - | - |
| ADV008-T11 | Read(designs), Write(tools/), Bash(python) | Python, geometry basics | 30min | 65000 | $0.975 | - | - | - | - |
| ADV008-T12 | Read(shape_grammar/), Write(tools/), Bash(python) | Python, interpreter design | 30min | 70000 | $1.050 | - | - | - | - |
| ADV008-T13 | Read(shape_grammar/), Write(tools/), Bash(python) | Python, OBJ format | 25min | 45000 | $0.675 | - | - | - | - |
| ADV008-T14 | Write(tools/rust/), Bash(cargo check) | Rust | 20min | 35000 | $0.525 | - | - | - | - |
| ADV008-T15 | Read(shape_grammar/specs,ark/specs/infra/code_graph.ark), Write(examples/), Bash(ark,python) | Ark DSL, shape grammar authoring | 30min | 60000 | $0.900 | - | - | - | - |
| ADV008-T16 | WebSearch, Read(shape_grammar/,designs/), Write(research/) | research, technical writing | 30min | 55000 | $0.825 | - | - | - | - |
| ADV008-T17 | Read(ark/tools/), Write(tools/integrations/), Bash(ark,python) | Python, subprocess wrapping | 30min | 60000 | $0.900 | - | - | - | - |
| ADV008-T18 | Read(shape_grammar/), Write(tests/), Bash(pytest) | pytest | 30min | 70000 | $1.050 | - | - | - | - |
| ADV008-T19 | Read(shape_grammar/,ark/), Write(research/), Bash(git,ark,pytest,cargo,python) | integration testing, validation | 25min | 45000 | $0.675 | - | - | - | - |
| **TOTAL** | - | - | **490min (~8.2h)** | **942000** | **~$14.13** | - | - | - | - |

Notes on evaluations:
- All tasks estimated at opus rates ($0.015/1k tokens). A wave-based runner with sonnet for mechanical tasks (T05, T06, T10, T14) would reduce cost by ~$1.50.
- T08 (verifier passes) is at the `max_task_tokens` threshold (75k vs 100k cap in config). Not split — the three passes share scaffolding and splitting would force duplication.
- T12 (evaluator core) at 70k is within threshold.
- Test tasks (T02 design, T18 implementation) present per mandatory convention.

## Environment
- **Project**: ark (Claudovka ecosystem)
- **Workspace**: R:\Sandbox
- **Repo**: https://github.com/abumonk/sandbox.git
- **Branch**: master
- **PC**: TTT
- **Platform**: Windows 11 Pro 10.0.26200
- **Runtime**: Node v24.12.0, Python 3.12
- **Shell**: bash
