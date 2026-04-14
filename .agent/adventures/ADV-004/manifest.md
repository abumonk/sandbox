---
id: ADV-004
title: Hermes-style Agent Self-Evolution System in Ark DSL
state: completed
created: 2026-04-13T00:00:00Z
updated: 2026-04-14T00:00:00Z
tasks: [ADV004-T001, ADV004-T002, ADV004-T003, ADV004-T004, ADV004-T005, ADV004-T006, ADV004-T007, ADV004-T008, ADV004-T009, ADV004-T010, ADV004-T011, ADV004-T012, ADV004-T013, ADV004-T014, ADV004-T015, ADV004-T016, ADV004-T017, ADV004-T018, ADV004-T019]
depends_on: [ADV-003]
---

## Concept

Review the Hermes Agent Self-Evolution project (https://github.com/NousResearch/hermes-agent-self-evolution) — a standalone optimization pipeline that improves agent performance through automated evolution loops using DSPy+GEPA, reflective analysis of execution traces, and fitness-gated deployment — and define/implement an Ark-native equivalent.

### What Hermes Self-Evolution does

- **Purpose**: automatically improve agent skills, prompts, tool descriptions, and implementation code through evolutionary optimization loops — all via API calls, no GPU training required.
- **Three optimization engines**:
  1. **DSPy + GEPA** — "genetic-Pareto prompt evolution" for skills, prompts, and instructions. Reads execution traces, proposes targeted mutations informed by failure analysis.
  2. **DSPy MIPROv2** — Bayesian optimization fallback for few-shot examples and instruction text.
  3. **Darwinian Evolver** — Git-based organism model for code-level evolution (Phase 4).
- **Four improvement tiers** (risk-ordered):
  - **Tier 1 — Skill files**: SKILL.md procedural instructions, pure text mutation via GEPA.
  - **Tier 2 — Tool descriptions**: Tool schema description fields, classification optimization.
  - **Tier 3 — System prompt components**: Parameterized prompt sections (persona, policies, formatting).
  - **Tier 4 — Code evolution**: Tool implementation code via Darwinian Evolver + pytest guardrails.
- **Optimization loop**: Select target → Build eval dataset → Wrap as DSPy module → Run optimizer (GEPA/MIPROv2) → Evaluate candidates → Constraint validation (tests, size limits, caching) → Benchmark gate (TBLite/YC-Bench) → Git PR for human review.
- **Evaluation data sources**: Synthetic generation (strong model reads skill → generates test cases), SessionDB mining (real usage, LLM-as-judge scored), hand-curated golden sets, skill-specific auto-evaluation.
- **Fitness scoring**: LLM-as-judge with rubrics (procedure adherence 0-1, output correctness 0-1, conciseness 0-1).
- **Constraints**: Full test suite pass, size limits (+20% max), prompt caching compatibility, semantic preservation, PR-only deployment with human review.
- **Five phases**: Skill evolution → Tool descriptions → System prompt → Code evolution → Continuous loop (~13-17 weeks).

### Goal in Ark

Define and implement an **agent self-evolution subsystem as an Ark island** so that Ark's own agent pipeline (the existing `.agent/` subsystem with roles, skills, and commands) can be systematically optimized through declarative evolution specs — all auditable through the same parse/verify/codegen pipeline.

Concretely:

- **DSL surface** — introduce Ark items to describe:
  - `evolution_target` — a named entity to optimize (skill, prompt, tool description, or code file) with tier, current version, constraints (size limit, semantic preservation).
  - `eval_dataset` — evaluation dataset definition with source (synthetic, session_db, golden, auto_eval), split ratios, scoring rubric.
  - `fitness_function` — scoring specification with rubric dimensions, weights, penalties, and aggregation method.
  - `optimizer` — optimizer configuration: engine (gepa, miprov2, darwinian), iterations, population size, mutation strategy.
  - `benchmark_gate` — validation gate with benchmark name, regression tolerance, pass criteria.
  - `evolution_run` — instance tracking an optimization run: target, optimizer, dataset, results, best variant, status.
  - `constraint` — safety constraint (test_suite, size_limit, caching_compat, semantic_preservation) with enforcement level (block, warn).
- **Schema** — Ark `struct`/`enum` definitions in `dsl/stdlib/evolution.ark` for: EvolutionTier, OptimizerEngine, DataSource, FitnessScore, RunResult, Variant, Constraint, BenchmarkResult.
- **Evaluation framework** — `tools/evolution/` containing:
  - `dataset_builder.py` — generates eval datasets from synthetic sources (reads .ark skills, generates test cases via LLM-as-judge pattern).
  - `fitness.py` — LLM-as-judge scoring with configurable rubrics.
  - `optimizer.py` — GEPA-inspired text mutation engine (simplified: no DSPy dependency, uses pure LLM calls for reflective mutation).
  - `constraint_checker.py` — validates evolved variants against size/semantic/test constraints.
  - `evolution_runner.py` — orchestrates the full loop: target → dataset → optimize → evaluate → gate → output.
- **Reflexive use-case** — run the evolution system on Ark's own skills and roles:
  - Evolve `.agent/roles/` descriptions using the GEPA-style reflective loop.
  - Evolve `.claude/skills/` content to improve task completion quality.
  - Evolve `.ark` spec patterns for better codegen output.
- **Verification** — Z3 checks:
  - Every evolution_target references an existing file/skill.
  - Every eval_dataset has valid split ratios (train+val+test = 1.0).
  - Every fitness_function has weights summing to 1.0.
  - Every benchmark_gate's tolerance is positive and within bounds.
  - Constraint satisfaction: evolved variants must not exceed size limits.
- **Codegen** — generate:
  - Evolution runner CLI commands from `evolution_run` items.
  - Dataset JSONL files from `eval_dataset` specs.
  - Fitness scoring scripts from `fitness_function` specs.
  - Evolution report markdown from run results.
- **Visualization** — extend the visualizer to render the evolution pipeline as a directed graph: target → dataset → optimizer → candidates → gate → output.

### Why this matters

Ark already has an agent pipeline with roles, skills, and commands (formalized in ADV-003's studio hierarchy). What it lacks is a **systematic way to improve those artifacts**. Today, improving a skill or role description requires manual editing and subjective judgment. A self-evolution island gives Ark a declarative, verifiable framework for saying "optimize this skill using these test cases with this fitness function" — and the pipeline handles the rest. The upstream Hermes project provides the pattern (GEPA reflective mutation, LLM-as-judge scoring, constraint gating); Ark provides the declarative substrate to make it auditable, reproducible, and compositional.

## Target Conditions
| ID | Description | Source | Design | Plan | Task(s) | Proof Method | Proof Command | Status |
|----|-------------|--------|--------|------|---------|-------------|---------------|--------|
| TC-001 | evolution.ark parses without errors | design-evolution-schema | design-evolution-schema | plan-foundation | ADV004-T002 | autotest | pytest tests/test_evolution_parser.py::test_stdlib_parse | pending |
| TC-002 | All enums/structs follow existing stdlib patterns | design-evolution-schema | design-evolution-schema | plan-foundation | ADV004-T002 | autotest | pytest tests/test_evolution_parser.py::test_stdlib_syntax | pending |
| TC-003 | Lark grammar parses all 7 evolution items | design-dsl-surface | design-dsl-surface | plan-foundation | ADV004-T003 | autotest | pytest tests/test_evolution_parser.py::test_lark_parse_all_items | pending |
| TC-004 | Pest grammar mirrors Lark for all 7 items | design-dsl-surface | design-dsl-surface | plan-foundation | ADV004-T004 | manual | Inspect pest rules match Lark rules | pending |
| TC-005 | Existing .ark files parse after grammar changes | design-dsl-surface | design-dsl-surface | plan-foundation | ADV004-T003 | autotest | pytest tests/ -k "not evolution" | pending |
| TC-006 | Parser produces correct AST for 7 evolution types | design-dsl-surface | design-dsl-surface | plan-foundation | ADV004-T005 | autotest | pytest tests/test_evolution_parser.py::test_ast_dataclasses | pending |
| TC-007 | ArkFile indices populated for evolution items | design-dsl-surface | design-dsl-surface | plan-foundation | ADV004-T005 | autotest | pytest tests/test_evolution_parser.py::test_arkfile_indices | pending |
| TC-008 | Dataset builder generates valid JSONL from synthetic | design-evaluation-framework | design-evaluation-framework | plan-evaluation-and-optimizer | ADV004-T006 | autotest | pytest tests/test_evolution_fitness.py::test_dataset_synthetic | pending |
| TC-009 | Dataset builder correctly assigns splits | design-evaluation-framework | design-evaluation-framework | plan-evaluation-and-optimizer | ADV004-T006 | autotest | pytest tests/test_evolution_fitness.py::test_dataset_splits | pending |
| TC-010 | Fitness scorer produces 0.0-1.0 scores per dimension | design-evaluation-framework | design-evaluation-framework | plan-evaluation-and-optimizer | ADV004-T007 | autotest | pytest tests/test_evolution_fitness.py::test_score_variant | pending |
| TC-011 | Aggregation methods compute correctly | design-evaluation-framework | design-evaluation-framework | plan-evaluation-and-optimizer | ADV004-T007 | autotest | pytest tests/test_evolution_fitness.py::test_aggregation | pending |
| TC-012 | evaluate_dataset returns mean fitness | design-evaluation-framework | design-evaluation-framework | plan-evaluation-and-optimizer | ADV004-T007 | autotest | pytest tests/test_evolution_fitness.py::test_evaluate_dataset | pending |
| TC-013 | Optimizer runs full loop for 2+ generations | design-optimizer-engine | design-optimizer-engine | plan-evaluation-and-optimizer | ADV004-T008 | autotest | pytest tests/test_evolution_optimizer.py::test_full_loop | pending |
| TC-014 | Pareto-front selection identifies non-dominated variants | design-optimizer-engine | design-optimizer-engine | plan-evaluation-and-optimizer | ADV004-T008 | autotest | pytest tests/test_evolution_optimizer.py::test_pareto | pending |
| TC-015 | Convergence detection stops optimization | design-optimizer-engine | design-optimizer-engine | plan-evaluation-and-optimizer | ADV004-T008 | autotest | pytest tests/test_evolution_optimizer.py::test_convergence | pending |
| TC-016 | MIPROv2 mode uses history-based selection | design-optimizer-engine | design-optimizer-engine | plan-evaluation-and-optimizer | ADV004-T008 | autotest | pytest tests/test_evolution_optimizer.py::test_miprov2 | pending |
| TC-017 | Darwinian mode raises NotImplementedError | design-optimizer-engine | design-optimizer-engine | plan-evaluation-and-optimizer | ADV004-T008 | autotest | pytest tests/test_evolution_optimizer.py::test_darwinian_stub | pending |
| TC-018 | Size limit blocks variants exceeding threshold | design-constraint-system | design-constraint-system | plan-evaluation-and-optimizer | ADV004-T009 | autotest | pytest tests/test_evolution_constraint.py::test_size_block | pending |
| TC-019 | Size limit passes variants within threshold | design-constraint-system | design-constraint-system | plan-evaluation-and-optimizer | ADV004-T009 | autotest | pytest tests/test_evolution_constraint.py::test_size_pass | pending |
| TC-020 | Semantic preservation uses judge callback | design-constraint-system | design-constraint-system | plan-evaluation-and-optimizer | ADV004-T009 | autotest | pytest tests/test_evolution_constraint.py::test_semantic | pending |
| TC-021 | Caching compatibility checks prefix preservation | design-constraint-system | design-constraint-system | plan-evaluation-and-optimizer | ADV004-T009 | autotest | pytest tests/test_evolution_constraint.py::test_caching | pending |
| TC-022 | should_block returns True only for block failures | design-constraint-system | design-constraint-system | plan-evaluation-and-optimizer | ADV004-T009 | autotest | pytest tests/test_evolution_constraint.py::test_should_block | pending |
| TC-023 | Runner executes full pipeline to EvolutionReport | design-evolution-runner | design-evolution-runner | plan-runner-and-cli | ADV004-T010 | autotest | pytest tests/test_evolution_runner.py::test_full_pipeline | pending |
| TC-024 | Runner resolves cross-references correctly | design-evolution-runner | design-evolution-runner | plan-runner-and-cli | ADV004-T010 | autotest | pytest tests/test_evolution_runner.py::test_resolve_refs | pending |
| TC-025 | Runner stops on block constraint violation | design-evolution-runner | design-evolution-runner | plan-runner-and-cli | ADV004-T010 | autotest | pytest tests/test_evolution_runner.py::test_block_constraint | pending |
| TC-026 | CLI `ark evolution run` executes evolution | design-evolution-runner | design-evolution-runner | plan-runner-and-cli | ADV004-T011 | autotest | pytest tests/test_evolution_integration.py::test_cli_run | pending |
| TC-027 | CLI `ark evolution status` displays status | design-evolution-runner | design-evolution-runner | plan-runner-and-cli | ADV004-T011 | autotest | pytest tests/test_evolution_integration.py::test_cli_status | pending |
| TC-028 | Codegen produces valid JSONL templates | design-codegen-reports | design-codegen-reports | plan-codegen-and-verify | ADV004-T012 | autotest | pytest tests/test_evolution_codegen.py::test_dataset_jsonl | pending |
| TC-029 | Codegen produces Python scoring skeletons | design-codegen-reports | design-codegen-reports | plan-codegen-and-verify | ADV004-T012 | autotest | pytest tests/test_evolution_codegen.py::test_scoring_script | pending |
| TC-030 | Codegen produces JSON config files | design-codegen-reports | design-codegen-reports | plan-codegen-and-verify | ADV004-T012 | autotest | pytest tests/test_evolution_codegen.py::test_run_config | pending |
| TC-031 | `ark codegen --target evolution` works e2e | design-codegen-reports | design-codegen-reports | plan-codegen-and-verify | ADV004-T012 | autotest | pytest tests/test_evolution_codegen.py::test_codegen_e2e | pending |
| TC-032 | Split ratio verification catches bad ratios | design-verification | design-verification | plan-codegen-and-verify | ADV004-T013 | autotest | pytest tests/test_evolution_verify.py::test_split_ratio_fail | pending |
| TC-033 | Fitness weight verification catches bad weights | design-verification | design-verification | plan-codegen-and-verify | ADV004-T013 | autotest | pytest tests/test_evolution_verify.py::test_weight_fail | pending |
| TC-034 | Gate tolerance verification catches bad bounds | design-verification | design-verification | plan-codegen-and-verify | ADV004-T013 | autotest | pytest tests/test_evolution_verify.py::test_tolerance_fail | pending |
| TC-035 | Cross-reference verification catches unknowns | design-verification | design-verification | plan-codegen-and-verify | ADV004-T013 | autotest | pytest tests/test_evolution_verify.py::test_xref_fail | pending |
| TC-036 | `ark verify` runs evolution checks when present | design-verification | design-verification | plan-codegen-and-verify | ADV004-T013 | autotest | pytest tests/test_evolution_verify.py::test_verify_integration | pending |
| TC-037 | Visualizer extracts evolution nodes and edges | design-visualization | design-visualization | plan-codegen-and-verify | ADV004-T014 | autotest | pytest tests/test_evolution_integration.py::test_viz_nodes | pending |
| TC-038 | Generated HTML includes evolution color coding | design-visualization | design-visualization | plan-codegen-and-verify | ADV004-T014 | autotest | pytest tests/test_evolution_integration.py::test_viz_colors | pending |
| TC-039 | `ark graph` renders evolution items | design-visualization | design-visualization | plan-codegen-and-verify | ADV004-T014 | poc | python ark.py graph specs/meta/evolution_skills.ark | pending |
| TC-040 | evolution_skills.ark parses without errors | design-reflexive-evolution | design-reflexive-evolution | plan-reflexive-and-tests | ADV004-T015 | autotest | pytest tests/test_evolution_integration.py::test_skills_parse | pending |
| TC-041 | evolution_roles.ark parses without errors | design-reflexive-evolution | design-reflexive-evolution | plan-reflexive-and-tests | ADV004-T016 | autotest | pytest tests/test_evolution_integration.py::test_roles_parse | pending |
| TC-042 | Both reflexive specs pass verify | design-reflexive-evolution | design-reflexive-evolution | plan-reflexive-and-tests | ADV004-T015,ADV004-T016 | autotest | pytest tests/test_evolution_integration.py::test_reflexive_verify | pending |
| TC-043 | Both specs registered in root.ark | design-reflexive-evolution | design-reflexive-evolution | plan-reflexive-and-tests | ADV004-T017 | autotest | pytest tests/test_evolution_integration.py::test_root_registry | pending |
| TC-044 | Codegen generates from reflexive specs | design-reflexive-evolution | design-reflexive-evolution | plan-reflexive-and-tests | ADV004-T018 | autotest | pytest tests/test_evolution_integration.py::test_reflexive_codegen | pending |
| TC-045 | Test strategy document complete | concept | - | plan-foundation | ADV004-T001 | manual | Inspect tests/test-strategy.md exists and covers all TCs | pending |
| TC-046 | All automated tests pass | concept | - | plan-reflexive-and-tests | ADV004-T019 | autotest | pytest tests/test_evolution_*.py | pending |

## Task Dependency Waves

### Wave 1 (parallel, no dependencies)
- ADV004-T001: Design test strategy
- ADV004-T002: Create stdlib/evolution.ark
- ADV004-T003: Extend Lark grammar

### Wave 2 (depends on Wave 1)
- ADV004-T004: Extend pest grammar (depends T003)
- ADV004-T005: Parser AST dataclasses (depends T003)

### Wave 3 (depends on Wave 2)
- ADV004-T006: Dataset builder (depends T005)
- ADV004-T012: Evolution codegen (depends T005)
- ADV004-T013: Evolution verification (depends T005)
- ADV004-T014: Visualizer extension (depends T005)

### Wave 4 (depends on Wave 3)
- ADV004-T007: Fitness scoring (depends T006)
- ADV004-T009: Constraint checker (depends T006)
- ADV004-T015: evolution_skills.ark (depends T005, T013)
- ADV004-T016: evolution_roles.ark (depends T005, T013)

### Wave 5 (depends on Wave 4)
- ADV004-T008: Optimizer engine (depends T007)
- ADV004-T017: Register in root.ark (depends T015, T016)

### Wave 6 (depends on Wave 5)
- ADV004-T010: Evolution runner (depends T008, T009)
- ADV004-T018: Run codegen on reflexive specs (depends T012, T015, T016)

### Wave 7 (depends on Wave 6)
- ADV004-T011: CLI integration (depends T010)

### Wave 8 (final, depends on everything)
- ADV004-T019: Implement all automated tests (depends T001-T018)

## Evaluations
| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |
|------|-------------------|-----------|---------------|-------------|-----------|-----------------|---------------|-------------|----------|
| ADV004-T001 | Read, Write, Glob, Grep | test design, pytest, ark-dsl | 15min | 15000 | $0.23 | | | | |
| ADV004-T002 | Read, Write, Bash | ark-dsl | 15min | 12000 | $0.18 | | | | |
| ADV004-T003 | Read, Write, Bash | lark-grammar, ark-dsl | 25min | 25000 | $0.38 | | | | |
| ADV004-T004 | Read, Write | pest-peg, ark-dsl | 20min | 20000 | $0.30 | | | | |
| ADV004-T005 | Read, Write, Bash | python, lark-transformer | 30min | 35000 | $0.53 | | | | |
| ADV004-T006 | Read, Write, Bash | python | 25min | 25000 | $0.38 | | | | |
| ADV004-T007 | Read, Write, Bash | python | 25min | 25000 | $0.38 | | | | |
| ADV004-T008 | Read, Write, Bash | python, optimization | 30min | 35000 | $0.53 | | | | |
| ADV004-T009 | Read, Write, Bash | python | 20min | 20000 | $0.30 | | | | |
| ADV004-T010 | Read, Write, Bash | python, integration | 30min | 35000 | $0.53 | | | | |
| ADV004-T011 | Read, Write, Bash | python, cli | 20min | 20000 | $0.30 | | | | |
| ADV004-T012 | Read, Write, Bash | python, codegen | 25min | 25000 | $0.38 | | | | |
| ADV004-T013 | Read, Write, Bash | python, z3, smt | 30min | 30000 | $0.45 | | | | |
| ADV004-T014 | Read, Write, Bash | python, d3.js, html | 25min | 25000 | $0.38 | | | | |
| ADV004-T015 | Read, Write, Bash | ark-dsl | 20min | 18000 | $0.27 | | | | |
| ADV004-T016 | Read, Write, Bash | ark-dsl | 15min | 15000 | $0.23 | | | | |
| ADV004-T017 | Read, Write, Bash | ark-dsl | 10min | 8000 | $0.12 | | | | |
| ADV004-T018 | Read, Bash | ark-dsl, codegen | 15min | 12000 | $0.18 | | | | |
| ADV004-T019 | Read, Write, Bash | python, pytest, ark-dsl | 30min | 40000 | $0.60 | | | | |
| **TOTAL** | | | **375min** | **440000** | **$6.63** | | | | |

## Environment
- **Project**: ARK (Architecture Kernel) — declarative MMO game-engine DSL
- **Workspace**: R:/Sandbox (Ark tree at R:/Sandbox/ark)
- **Repo**: local (no git remote)
- **Branch**: local (not a git repo)
- **PC**: TTT
- **Platform**: Windows 11 Pro 10.0.26200
- **Runtime**: Node v24.12.0 (project runtime: Python 3 + Rust/Cargo)
- **Shell**: bash
