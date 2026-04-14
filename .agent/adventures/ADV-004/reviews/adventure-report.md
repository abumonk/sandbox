---
adventure_id: ADV-004
generated_at: 2026-04-13T14:35:00Z
task_count: 19
tc_total: 46
tc_passed: 46
tc_pass_rate: "100%"
total_iterations: 0
knowledge_suggestions_count: 7
---

# Adventure Report: ADV-004

## 1. Executive Summary

| Field | Value |
|-------|-------|
| Adventure | ADV-004 |
| Title | Hermes-style Agent Self-Evolution System in Ark DSL |
| Duration | ~6 hours (2026-04-13 12:30 to ~18:15) |
| Total Tokens | 517,500 in / 91,800 out (~609K total) |
| Estimated Cost | ~$7.50 (est. $6.63 planned) |
| Tasks | 19/19 completed |
| TC Pass Rate | 46/46 (100%) |

ADV-004 implemented a complete agent self-evolution subsystem for the Ark DSL, inspired by the Hermes Agent Self-Evolution project. The adventure delivered: DSL type definitions (14 enums/structs), dual Lark+Pest grammar extensions for 7 new evolution item types, a full Python parser with AST dataclasses, an evaluation framework (dataset builder, fitness scorer, optimizer engine, constraint checker), an evolution runner with CLI integration, codegen and Z3-based verification modules, a visualizer extension, two reflexive .ark specs that use the evolution system to describe its own optimization, and 127 automated tests across 8 test files. All 19 tasks passed review on first submission with zero rework iterations.

## 2. Task Results Summary

| Task ID | Title | Verdict | Key Files |
|---------|-------|---------|-----------|
| ADV004-T001 | Design test strategy | PASSED | test-strategy.md (130 TC refs, 8 test files) |
| ADV004-T002 | Create stdlib/evolution.ark | PASSED | dsl/stdlib/evolution.ark (14 definitions) |
| ADV004-T003 | Extend Lark grammar | PASSED | tools/parser/ark_grammar.lark (7 rules) |
| ADV004-T004 | Extend Pest grammar | PASSED | dsl/grammar/ark.pest (7 rules, mirrors Lark) |
| ADV004-T005 | Parser AST dataclasses | PASSED | tools/parser/ark_parser.py (7 dataclasses) |
| ADV004-T006 | Dataset builder | PASSED | tools/evolution/dataset_builder.py |
| ADV004-T007 | Fitness scoring | PASSED | tools/evolution/fitness.py |
| ADV004-T008 | Optimizer engine | PASSED | tools/evolution/optimizer.py |
| ADV004-T009 | Constraint checker | PASSED | tools/evolution/constraint_checker.py |
| ADV004-T010 | Evolution runner | PASSED | tools/evolution/evolution_runner.py |
| ADV004-T011 | CLI integration | PASSED | ark.py (cmd_evolution) |
| ADV004-T012 | Evolution codegen | PASSED | tools/codegen/evolution_codegen.py |
| ADV004-T013 | Evolution verification | PASSED | tools/verify/evolution_verify.py (Z3) |
| ADV004-T014 | Visualizer extension | PASSED | tools/visualizer/ark_visualizer.py |
| ADV004-T015 | evolution_skills.ark | PASSED | specs/meta/evolution_skills.ark |
| ADV004-T016 | evolution_roles.ark | PASSED | specs/meta/evolution_roles.ark |
| ADV004-T017 | Register in root.ark | PASSED | specs/root.ark |
| ADV004-T018 | Codegen on reflexive specs | PASSED | 8 generated artifacts verified |
| ADV004-T019 | Automated tests (127) | PASSED | 8 test files, 993 total tests green |

## 3. Architecture Analysis

### Layer Structure

The evolution subsystem follows a clean layered architecture:

1. **Schema Layer** (`dsl/stdlib/evolution.ark`) -- 7 enums + 7 structs defining evolution domain types (EvolutionTier, OptimizerEngine, DataSource, FitnessScore, etc.)

2. **Grammar Layer** (`ark_grammar.lark` + `ark.pest`) -- 7 new item rules for declaring evolution targets, datasets, fitness functions, optimizers, benchmark gates, evolution runs, and constraints. Dual Lark/Pest parity maintained.

3. **Parser Layer** (`ark_parser.py`) -- 7 AST dataclasses with transformer methods, ArkFile index integration for cross-referencing.

4. **Evaluation Framework** (`tools/evolution/`) -- 5 modules:
   - `dataset_builder.py` -- synthetic JSONL generation with train/val/test splits
   - `fitness.py` -- LLM-as-judge scoring with configurable rubrics and 3 aggregation methods
   - `optimizer.py` -- GEPA + MIPROv2 engines with Pareto-front selection and convergence detection
   - `constraint_checker.py` -- size, semantic, caching constraints with block/warn enforcement
   - `evolution_runner.py` -- full pipeline orchestration

5. **Integration Layer** -- CLI (`cmd_evolution`), codegen (`evolution_codegen.py`), verification (`evolution_verify.py` with Z3), visualization (evolution node/edge rendering)

6. **Reflexive Layer** (`specs/meta/`) -- The evolution system describes its own optimization targets using its own DSL, demonstrating composability.

### Design Consistency

The architecture follows patterns established in ADV-003 (studio system):
- Separate domain modules for verify and codegen (not extending core files)
- Z3-based verification for numeric constraints (split ratios, weights, tolerances)
- ArkFile index integration for cross-reference resolution
- Dual grammar maintenance with dedicated tasks

### Dependencies

The 8-wave dependency structure was well-designed: foundation (types, grammar, parser) before evaluation framework before runner/CLI before reflexive specs before final test suite. No circular dependencies or unexpected coupling observed.

## 4. Quality Assessment

### Test Coverage

- **127 evolution-specific tests** across 8 test files
- **993 total tests** in the full suite (all green)
- All 46 target conditions verified via automated proof commands
- Test strategy document (T001) mapped all TCs to specific test functions upfront

### Code Quality Observations

- **Consistent patterns**: All modules follow established Ark conventions (result dict format for verify, ArkFile index population, grammar rule naming)
- **Defensive design**: `evolution_codegen.py` handles both ArkFile dataclass and raw JSON dict inputs
- **Error handling**: CLI provides clear messages for missing files, unknown run names
- **Z3 usage**: Appropriate for numeric constraint verification (ratios, weights, tolerances)

### Review Results

- **Zero rework iterations** across all 19 tasks -- every task passed review on first submission
- No issues flagged in any review report
- One minor observation in T012 review: optimizer_ref naming in codegen could be confusing (cosmetic, not correctness)
- One metadata inconsistency noted in T013: task status field said "done" vs "passed"

## 5. Process Analysis

### Execution Timeline

All 19 tasks were implemented in a single session (~6 hours) following the 8-wave dependency order. Parallelism was effectively used within waves (e.g., T001/T002/T003 in Wave 1; T006/T012/T013/T014 in Wave 3).

### Metrics Summary

| Category | Value |
|----------|-------|
| Agent runs | 20 (1 planner + 19 implementers) |
| Planning tokens | 117K (85K in + 32K out) |
| Implementation tokens | ~492K (432.5K in + 59.8K out) |
| Planner model | opus |
| Implementer model | sonnet |
| Total turns | ~253 |

### Estimation Accuracy

Planned cost was $6.63 / 440K tokens. Actual was ~609K tokens (~$7.50 estimated). The 13% overrun is within acceptable bounds, likely driven by the parser task (T005) which used 48K tokens in vs 35K estimated -- the most complex single task requiring 7 dataclasses, transformer methods, and index integration.

### Bottlenecks

- **T005 (Parser AST)** was the critical path bottleneck -- all Wave 3+ tasks depended on it, and it was the highest-token task (53.2K total)
- **T010 (Evolution Runner)** had the longest implementation duration (25 min) as it required reading and integrating all dependent modules

## 6. Issues and Recommendations

### Issues Observed

1. **Metrics completeness**: The metrics.md frontmatter totals are all zeros despite 20 agent runs being recorded. The aggregate fields should be computed from the run table.

2. **Timestamp inconsistencies in adventure.log**: Several log entries have `14:00:00Z` timestamps that appear to be default/placeholder values rather than actual execution times, making precise timeline reconstruction difficult.

3. **Task status inconsistency**: Some tasks recorded `status: done` vs `status: passed` in their frontmatter. The pipeline should standardize on one term.

4. **Darwinian mode stub**: The optimizer's Darwinian (code evolution) mode is a NotImplementedError stub. This is by design (Phase 4 in Hermes roadmap) but should be tracked for future implementation.

### Recommendations

1. **HIGH -- Implement LLM integration for fitness scoring**: The fitness scorer currently uses a callback pattern but needs actual LLM-as-judge integration (API calls) to be functional beyond testing. This is the highest-value next step for making the evolution system operational.

2. **HIGH -- Add end-to-end evolution integration test**: While 127 unit tests exist, an integration test that runs a complete evolution loop (target -> dataset -> optimize -> evaluate -> gate) on a real .ark skill file would validate the full pipeline.

3. **MEDIUM -- Implement Darwinian code evolution**: The optimizer stub for Darwinian mode should be expanded in a future adventure to support code-level evolution with git-based variant management and pytest guardrails.

4. **MEDIUM -- Compute metrics aggregates**: The metrics.md frontmatter should be populated with actual totals from the agent run table.

5. **LOW -- Standardize task status vocabulary**: Choose either "done" or "passed" and enforce it across the pipeline. Recommend "passed" for tasks that pass review, "done" for tasks that complete but haven't been reviewed.

## 7. Knowledge Extraction Suggestions

| # | Type | Target File | Title |
|---|------|-------------|-------|
| 1 | pattern | .agent/knowledge/patterns.md | Evolution Module Architecture |
| 2 | pattern | .agent/knowledge/patterns.md | Reflexive Dogfooding Pattern |
| 3 | pattern | .agent/knowledge/patterns.md | Zero-Rework Through Design-First (Reinforced) |
| 4 | issue | .agent/knowledge/issues.md | Metrics Frontmatter Aggregation Gap |
| 5 | issue | .agent/knowledge/issues.md | Log Timestamp Placeholders |
| 6 | decision | .agent/knowledge/decisions.md | LLM-as-Judge Callback Pattern |
| 7 | decision | .agent/knowledge/decisions.md | Phased Optimizer Engine |

### Suggestion 1: Evolution Module Architecture
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Evolution Module Architecture**: Large subsystem features (7+ item types) benefit from a dedicated `tools/{domain}/` package with separate modules for each concern (dataset_builder, fitness, optimizer, constraint_checker, runner) plus dedicated verify, codegen, and visualizer extensions. This keeps the package self-contained while integrating cleanly with the existing pipeline. ADV-004 delivered 5 evaluation modules + 3 integration modules with zero coupling issues. (from ADV-004)
  ```

### Suggestion 2: Reflexive Dogfooding Pattern
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Reflexive Dogfooding**: When building a DSL subsystem, create specs that use the subsystem to describe itself (e.g., evolution_skills.ark uses evolution items to define how to optimize Ark skills). This validates end-to-end composability and serves as living documentation. ADV-004's reflexive specs caught 2 bugs in evolution_verify.py during T016 implementation. (from ADV-004)
  ```

### Suggestion 3: Zero-Rework Through Design-First (Reinforced)
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Design-First Zero-Rework (Reinforced)**: ADV-004 (19 tasks, 10 designs, 5 plans) achieved 0 rework iterations across all tasks, reinforcing the ADV-003 finding. The 10 design documents with explicit acceptance criteria and 46 target conditions with proof commands eliminated ambiguity. This pattern has now been validated across 2 adventures (33 total tasks, 0 rework). (from ADV-004)
  ```

### Suggestion 4: Metrics Frontmatter Aggregation Gap
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **Metrics Frontmatter Aggregation Gap**: In ADV-004, the metrics.md frontmatter fields (total_tokens_in, total_tokens_out, total_duration, total_cost) remained at zero despite 20 agent runs being recorded in the table. Solution: the last agent to write to metrics.md (or the adventure-reviewer) should compute and update aggregate totals from the run table. (from ADV-004)
  ```

### Suggestion 5: Log Timestamp Placeholders
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **Log Timestamp Placeholders**: In ADV-004, multiple adventure.log entries used identical placeholder timestamps (e.g., 14:00:00Z repeated across different tasks), making timeline reconstruction unreliable. Solution: implementer agents should use actual wall-clock timestamps, not round numbers. If precise timestamps aren't available, use sequential offsets from the spawn timestamp. (from ADV-004)
  ```

### Suggestion 6: LLM-as-Judge Callback Pattern
- **Type**: decision
- **Target File**: `.agent/knowledge/decisions.md`
- **Content**:
  ```
  ## LLM-as-Judge Callback Pattern for Evolution Fitness
  - **Context**: The evolution fitness scorer needs LLM evaluation but the implementation should not hardcode a specific LLM API.
  - **Decision**: Fitness scoring uses a callback/dependency-injection pattern where the LLM judge function is passed as a parameter. This allows unit testing with mock scorers while supporting any LLM backend in production. The same pattern is used for semantic preservation checks in constraint_checker.py.
  - **From**: ADV-004
  ```

### Suggestion 7: Phased Optimizer Engine
- **Type**: decision
- **Target File**: `.agent/knowledge/decisions.md`
- **Content**:
  ```
  ## Phased Optimizer Engine Implementation
  - **Context**: The Hermes project defines three optimizer engines (GEPA, MIPROv2, Darwinian) with different maturity levels.
  - **Decision**: Implement GEPA and MIPROv2 as functional engines in the initial adventure; Darwinian (code evolution) as a NotImplementedError stub. This delivers immediate value for text-based evolution (skills, prompts, roles) while deferring the more complex code evolution to a future adventure with proper git integration and pytest guardrails.
  - **From**: ADV-004
  ```
