---
id: ADV-011
title: Ark Core Unification — Descriptor, Builder, Controller
state: completed
created: 2026-04-15T02:10:00Z
updated: 2026-04-15T06:30:00Z
tasks:
  - ADV011-T001
  - ADV011-T002
  - ADV011-T003
  - ADV011-T004
  - ADV011-T005
  - ADV011-T006
  - ADV011-T007
  - ADV011-T008
  - ADV011-T009
  - ADV011-T010
  - ADV011-T011
  - ADV011-T012
depends_on: [ADV-001, ADV-002, ADV-003, ADV-004, ADV-005, ADV-006, ADV-007, ADV-008]
---

## Concept

Review the concrete results of adventures ADV-001 through ADV-008 (six implemented subsystems plus one research/roadmap adventure and one host-language dogfooding) and plan a set of research tasks that will produce a unified system design for the **core of Ark**. The core of Ark is defined by exactly three roles:

1. **System Descriptor** — the declarative DSL surface (grammar, schemas, AST, parsers) by which a system is specified.
2. **System Builder** — the transformation layer (codegen, verification, analysis, visualization) that turns a descriptor into checked, executable artifacts.
3. **System Controller** — the runtime surface (gateway, scheduler, skill manager, evaluator, self-evolution loop) that executes, observes, and adapts a built system.

### What this adventure is

A **research + design adventure** (like ADV-007 in shape, smaller in scope). It produces documents, schemas, and a target blueprint — not implementation.

### What this adventure delivers

- A **mapping document** that places every concept introduced in ADV-001..008 into exactly one of {descriptor, builder, controller, out-of-scope}.
- A **deduplication matrix** that identifies concepts that are the same thing under different names across the 8 reference adventures (e.g., Z3 ordinals for DAG acyclicity appears in ADV-003 and ADV-006; metrics/telemetry appears in ADV-001/002/005/006 + ADV-010).
- A **pruning catalog** listing everything introduced in ADV-001..008 that is *not* connected to the three core roles, with rationale for removal (e.g., visual surfaces from ADV-006 that are pure UI, Hermes evolution modes that are speculative, research artifacts from ADV-007 that are ecosystem-level).
- A **unified descriptor design** that merges the grammar/schema surface into a single coherent language (one Lark, one Pest, one AST family) instead of eight concept islands with seven grammar extensions.
- A **unified builder design** that describes the single codegen + verify + visualize pipeline and how ADV-001..008's domain-specific verifiers (expression Z3, studio DAG Z3, evolution numeric Z3, visual ordinal Z3, shape grammar termination/determinism) compose as plugins over one shared Z3 harness.
- A **unified controller design** that defines the single runtime surface (gateway, skill-manager, scheduler, evaluator, self-evolution loop, telemetry capture from ADV-010) with its event contracts and state model.
- A **downstream adventure plan** — ordered list of implementation adventures that will realize the unification (expected: 3–6 downstream adventures).

### What this adventure does NOT do

- No grammar changes. No codegen changes. No runtime changes. No file moves in `ark/` or sibling packages.
- No re-implementation. The outputs are design documents referencing existing ADV-001..008 artifacts.
- No ecosystem planning (that was ADV-007's job). This adventure is strictly about Ark core.

### Method

- Phase 1: **Harvest** — read the 8 adventure manifests + adventure reports + their stdlib/grammar artifacts. Catalog every concept.
- Phase 2: **Classify** — place each concept into descriptor / builder / controller / out-of-scope.
- Phase 3: **Deduplicate** — identify concepts that overlap across adventures; propose a single canonical form for each.
- Phase 4: **Prune** — produce the pruning catalog for non-core material with justification.
- Phase 5: **Design** — produce three unified design documents (descriptor, builder, controller) with explicit references to the source adventure artifacts that each idea came from.
- Phase 6: **Validate** — cross-check the unified design against every target condition from ADV-001..008 to confirm no capability is lost.
- Phase 7: **Downstream plan** — produce the sequence of implementation adventures needed to realize the unified design.

### Autotest proof gate

Every target condition of this adventure has a `proof_method: autotest` where technically feasible. Because this is a research adventure, most proofs will be `test -f` existence checks on deliverables + grep-based content checks for required sections. A small poc subset (e.g., "mapping covers 100% of ADV-001..008 concepts") is acceptable with justification.

### Known constraints

- **No duplication**: if a concept appears in two or more adventures, the unified design must list it once with references to all source adventures, not once per adventure.
- **Ark core only**: UI, ecosystem roadmap, sibling package semantics, evolution research notes, and documentation generators from ADV-001..008 must be explicitly parked out-of-scope with a pointer to a future adventure if warranted.
- **Pattern reuse**: the 15 patterns already captured from ADV-001..008 (wave-spawn closure check, dual Lark+Pest, Z3 ordinals, reflexive dogfooding, etc.) must be reused — the unified design should cite each pattern at the point it applies.

## Target Conditions

| ID | Description | Source | Design | Plan | Task(s) | Proof Method | Proof Command | Status |
|----|-------------|--------|--------|------|---------|-------------|---------------|--------|
| TC-001 | `research/concept-inventory.md` exists and contains at least one row per adventure in ADV-001..008 + ADV-010 | concept/design-concept-mapping | design-concept-mapping | plan-wave-a-harvest | ADV011-T001 | autotest | `test -f .agent/adventures/ADV-011/research/concept-inventory.md && for a in 001 002 003 004 005 006 007 008 010; do grep -q "ADV-$a" .agent/adventures/ADV-011/research/concept-inventory.md \|\| exit 1; done` | pending |
| TC-002 | Concept inventory table has four columns (concept, source_adventure, source_artefact, description) | design-concept-mapping/schemas/entities | design-concept-mapping | plan-wave-a-harvest | ADV011-T001 | autotest | `grep -E "^\| concept \| source_adventure \| source_artefact \| description \|" .agent/adventures/ADV-011/research/concept-inventory.md` | pending |
| TC-TS-1 | `tests/test-strategy.md` exists and maps every TC to a proof command | design-test-strategy | design-test-strategy | plan-wave-a-harvest | ADV011-T002 | autotest | `test -f .agent/adventures/ADV-011/tests/test-strategy.md && [ $(grep -cE "^\| TC-" .agent/adventures/ADV-011/tests/test-strategy.md) -ge 20 ]` | pending |
| TC-003 | `research/concept-mapping.md` exists with master table + per-bucket rationale section | design-concept-mapping | design-concept-mapping | plan-wave-b-classify-deduplicate | ADV011-T003 | autotest | `test -f .agent/adventures/ADV-011/research/concept-mapping.md && grep -q "## Per-Bucket Rationale" .agent/adventures/ADV-011/research/concept-mapping.md` | pending |
| TC-004 | Every mapping row's bucket is one of the four allowed values | design-concept-mapping | design-concept-mapping | plan-wave-b-classify-deduplicate | ADV011-T003 | poc | All non-header rows in the bucket column match `^(descriptor\|builder\|controller\|out-of-scope)$` — proven by `tests/test_mapping_completeness.py::test_buckets_allowlist` | pending |
| TC-005 | `research/deduplication-matrix.md` exists with at least the 6 seed duplication rows | design-deduplication-matrix | design-deduplication-matrix | plan-wave-b-classify-deduplicate | ADV011-T004 | autotest | `test -f .agent/adventures/ADV-011/research/deduplication-matrix.md && for k in "Z3 ordinals" "Lark" "Pest" "telemetry" "PASS_OPAQUE" "dogfood" "Skill"; do grep -qi "$k" .agent/adventures/ADV-011/research/deduplication-matrix.md \|\| exit 1; done` | pending |
| TC-006 | Every dedup matrix row has a non-empty canonical_form column | design-deduplication-matrix | design-deduplication-matrix | plan-wave-b-classify-deduplicate | ADV011-T004 | autotest | `grep -E "^\|.*\|.*\|.*\|.*\|.*\|" .agent/adventures/ADV-011/research/deduplication-matrix.md \| grep -vE "^\| *canonical_form \|" \| grep -vE "^\|-" \| awk -F'\\|' 'NF>=6 && $4 !~ /^ *$/ {c++} END {exit (c>=6)?0:1}'` | pending |
| TC-007 | `research/pruning-catalog.md` exists with ≥ 7 seed rows | design-pruning-catalog | design-pruning-catalog | plan-wave-c-prune | ADV011-T005 | autotest | `test -f .agent/adventures/ADV-011/research/pruning-catalog.md && [ $(grep -cE "^\|.*\|" .agent/adventures/ADV-011/research/pruning-catalog.md) -ge 9 ]` | pending |
| TC-008 | Every pruning disposition matches `OUT-OF-SCOPE → ADV-` or `DROP` | design-pruning-catalog | design-pruning-catalog | plan-wave-c-prune | ADV011-T005 | autotest | `! grep -E "^\|.*\|.*\|.*\|.*\|.*\|" .agent/adventures/ADV-011/research/pruning-catalog.md \| grep -vE "(OUT-OF-SCOPE|DROP\|disposition\|---)"` | pending |
| TC-009 | `research/descriptor-delta.md` exists with a verdict row per stdlib file | design-unified-descriptor | design-unified-descriptor | plan-wave-d-unified-designs | ADV011-T006 | autotest | `test -f .agent/adventures/ADV-011/research/descriptor-delta.md && for f in types expression predicate code_graph code_graph_queries studio evolution agent visual; do grep -q "$f.ark" .agent/adventures/ADV-011/research/descriptor-delta.md \|\| exit 1; done` | pending |
| TC-010 | Descriptor delta cites the host-language contract from ADV-008 | design-unified-descriptor | design-unified-descriptor | plan-wave-d-unified-designs | ADV011-T006 | autotest | `grep -qE "ADV-008\|host-language\|feasibility" .agent/adventures/ADV-011/research/descriptor-delta.md` | pending |
| TC-011 | `research/builder-delta.md` exists and names the four shared verify passes | design-unified-builder | design-unified-builder | plan-wave-d-unified-designs | ADV011-T007 | autotest | `test -f .agent/adventures/ADV-011/research/builder-delta.md && for p in "dag_acyclicity" "opaque_primitive" "numeric_interval" "reference_exists"; do grep -q "$p" .agent/adventures/ADV-011/research/builder-delta.md \|\| exit 1; done` | pending |
| TC-012 | Builder delta classifies every current verify/codegen module | design-unified-builder | design-unified-builder | plan-wave-d-unified-designs | ADV011-T007 | autotest | `for m in ark_verify studio_verify evolution_verify agent_verify visual_verify graph_verify expression_smt ark_codegen studio_codegen evolution_codegen agent_codegen visual_codegen; do grep -q "$m" .agent/adventures/ADV-011/research/builder-delta.md \|\| exit 1; done` | pending |
| TC-013 | `research/controller-delta.md` exists and cites ADV-010 telemetry merge | design-unified-controller | design-unified-controller | plan-wave-d-unified-designs | ADV011-T008 | autotest | `test -f .agent/adventures/ADV-011/research/controller-delta.md && grep -qE "ADV-010\|telemetry" .agent/adventures/ADV-011/research/controller-delta.md` | pending |
| TC-014 | Controller delta names the 7 unified subsystems | design-unified-controller | design-unified-controller | plan-wave-d-unified-designs | ADV011-T008 | autotest | `for s in "gateway" "skill" "scheduler" "evaluator" "evolution" "telemetry" "review"; do grep -qi "$s" .agent/adventures/ADV-011/research/controller-delta.md \|\| exit 1; done` | pending |
| TC-015 | `research/validation-coverage.md` exists; every row has a verdict | design-validation-against-tcs | design-validation-against-tcs | plan-wave-e-validate-and-plan | ADV011-T009 | autotest | `test -f .agent/adventures/ADV-011/research/validation-coverage.md && ! grep -E "^\|.*TC-.*\| *\|" .agent/adventures/ADV-011/research/validation-coverage.md` | pending |
| TC-016 | `covered + retired + deferred = total_source_TCs` arithmetic holds | design-validation-against-tcs | design-validation-against-tcs | plan-wave-e-validate-and-plan | ADV011-T009, ADV011-T011 | autotest | `python -m unittest .agent.adventures.ADV-011.tests.test_coverage_arithmetic` | pending |
| TC-017 | `research/downstream-adventure-plan.md` exists with 3–6 numbered adventures | design-downstream-adventure-plan | design-downstream-adventure-plan | plan-wave-e-validate-and-plan | ADV011-T010 | autotest | `test -f .agent/adventures/ADV-011/research/downstream-adventure-plan.md && c=$(grep -cE "^## ADV-" .agent/adventures/ADV-011/research/downstream-adventure-plan.md); [ "$c" -ge 3 ] && [ "$c" -le 6 ]` | pending |
| TC-018 | Downstream plan states the serial ordering constraint | design-downstream-adventure-plan | design-downstream-adventure-plan | plan-wave-e-validate-and-plan | ADV011-T010 | autotest | `grep -qE "ADV-DU.*ADV-BC.*ADV-CC.*ADV-OP" .agent/adventures/ADV-011/research/downstream-adventure-plan.md` | pending |
| TC-019 | `tests/run-all.sh` exists and exits 0 | design-test-strategy | design-test-strategy | plan-wave-e-validate-and-plan | ADV011-T011 | autotest | `bash .agent/adventures/ADV-011/tests/run-all.sh` | pending |
| TC-020 | `python -m unittest discover` exits 0 | design-test-strategy | design-test-strategy | plan-wave-e-validate-and-plan | ADV011-T011 | autotest | `python -m unittest discover -s .agent/adventures/ADV-011/tests -v` | pending |
| TC-021 | `research/final-validation-report.md` exists citing all artefact counts | design-test-strategy | design-test-strategy | plan-wave-e-validate-and-plan | ADV011-T012 | autotest | `test -f .agent/adventures/ADV-011/research/final-validation-report.md && for k in "inventory" "mapping" "dedup" "pruning" "descriptor" "builder" "controller" "validation" "downstream"; do grep -qi "$k" .agent/adventures/ADV-011/research/final-validation-report.md \|\| exit 1; done` | pending |

## Evaluations

Cost rates (from `.agent/config.md`): opus $0.015/1K, sonnet $0.003/1K, haiku
$0.001/1K. Planner (this spawn) uses opus; every implementation task uses
sonnet.

| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |
|------|-------------------|-----------|---------------|-------------|-----------|-----------------|---------------|-------------|----------|
| ADV011-T001 | Read `.agent/adventures/**`, `ark/dsl/stdlib/**`, Write `research/` | source manifest reading, tabular writing, Ark DSL literacy | 25min | 55000 | $0.165 | — | — | — | — |
| ADV011-T002 | Read `designs/`, `schemas/`, Write `tests/` | test-to-requirement mapping | 15min | 22000 | $0.066 | — | — | — | — |
| ADV011-T003 | Read `research/concept-inventory.md`, Write `research/` | taxonomy design, systems classification | 25min | 55000 | $0.165 | — | — | — | — |
| ADV011-T004 | Read mapping, `.agent/knowledge/**`, Write `research/` | pattern recognition, cross-adventure synthesis | 20min | 40000 | $0.120 | — | — | — | — |
| ADV011-T005 | Read mapping, Write `research/` | prioritisation, architectural judgment | 15min | 30000 | $0.090 | — | — | — | — |
| ADV011-T006 | Read `research/**`, `ark/dsl/stdlib/**`, `ark/dsl/grammar/**`, Write `research/` | DSL architecture, grammar design | 25min | 60000 | $0.180 | — | — | — | — |
| ADV011-T007 | Read `research/**`, `ark/tools/verify/**`, `ark/tools/codegen/**`, Write `research/` | Z3 harness design, codegen pipeline | 25min | 60000 | $0.180 | — | — | — | — |
| ADV011-T008 | Read `research/**`, `ark/tools/agent/**`, `ark/tools/evolution/**`, `.agent/telemetry/**`, Write `research/` | runtime architecture, event systems, telemetry | 25min | 60000 | $0.180 | — | — | — | — |
| ADV011-T009 | Read every ADV-00{1..8,10} manifest, Write `research/` | traceability, cross-document arithmetic | 25min | 75000 | $0.225 | — | — | — | — |
| ADV011-T010 | Read `research/**`, Write `research/` | adventure planning, sequencing | 20min | 40000 | $0.120 | — | — | — | — |
| ADV011-T011 | Read all deliverables, Write `tests/`, Bash (bash, test, grep, python, python -m unittest) | shell, stdlib unittest | 20min | 45000 | $0.135 | — | — | — | — |
| ADV011-T012 | Read `research/**`, `tests/**`, Bash (run-all.sh), Write `research/` | summary writing | 10min | 20000 | $0.060 | — | — | — | — |
| **TOTAL** | | | **4h 10min** | **562000** | **$1.686** | | | | |

**Adventure planner spawn cost** (this run, opus, ~35K in / ~12K out
estimated) ≈ **$0.71** separately.

**Combined estimate**: ~$2.40 total, ~580K tokens. Within the ~$8–12 / 400K–600K
guidance envelope from the adventure brief (at the low end because this is a
read-mostly research adventure with no external web access).

**Threshold check**: `max_task_tokens: 100000`, `max_task_duration: 30min`.
Largest task is T009 at 75K tokens / 25min — well within both thresholds. No
task approaches either limit; no split-on-overrun rules triggered.

## Environment
- **Project**: Sandbox / Claudovka
- **Workspace**: R:\Sandbox
- **Repo**: https://github.com/abumonk/sandbox.git
- **Branch**: master
- **PC**: TTT
- **Platform**: Windows 11 Pro 10.0.26200
- **Runtime**: node v24.12.0
- **Shell**: bash (Git Bash / MSYS2 on Windows)
