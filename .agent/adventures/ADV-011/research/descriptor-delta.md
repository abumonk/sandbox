# Descriptor Delta Report — ADV-011

**Purpose.** Per-file disposition of every `ark/dsl/stdlib/*.ark` file against
the target two-level layout specified in `designs/design-unified-descriptor.md`
§4. This document is a planning artefact — it decides what the downstream
`ADV-Descriptor-Unification` adventure must do, without moving any code.

**Inputs.** Nine files returned by `ls ark/dsl/stdlib/*.ark` (confirmed at
write time): `types.ark`, `predicate.ark`, `expression.ark`, `code_graph.ark`,
`code_graph_queries.ark`, `studio.ark`, `evolution.ark`, `agent.ark`,
`visual.ark`. Concept references drawn from `research/concept-mapping.md`;
dedup references from `research/deduplication-matrix.md`; DROP checks from
`research/pruning-catalog.md` (no stdlib file carries a DROP verdict there).

---

## Verdict Table

Decision tree applied in order (first match wins):
1. **MOVE-TO-PRIMITIVES** — file contains only `primitive`/`struct`/`enum` items
   OR items (`predicate`/`expression`) that are type-level building blocks with
   no domain-specific item kinds, AND are consumed by ≥ 2 other stdlib files or
   by the core grammar.
2. **RETIRE** — file listed as DROP in `research/pruning-catalog.md` OR
   strictly superseded by canonical form in a dedup-matrix row.
3. **MERGE-INTO** — file's entire item list is a proper subset of a larger
   domain's natural scope AND a dedup row names it as the absorbed form.
4. **KEEP-RENAMED** — file survives as a domain island but requires path
   promotion from flat `stdlib/` into `stdlib/domain/`.
5. **KEEP-AS-IS** — file survives at its current path unchanged (reserved;
   applies to zero files in the current flat layout since every file needs
   promotion to the two-level layout).

| file | verdict | target | rationale | concept_refs | dedup_refs |
|------|---------|--------|-----------|--------------|------------|
| types.ark | MOVE-TO-PRIMITIVES | primitives/types.ark | Contains exclusively `primitive`, `struct`, and `enum` items (7 primitives, 10 math/time/networking structs, 6 enums for orchestration and memory strategy) with no domain-specific item kinds; these types are consumed by every other stdlib file, satisfying the ≥2 consumer rule. | struct_Module (cross-file schema base), struct_ArkEntity, enum_EdgeKind, numeric_expression_stdlib (imports types), string_predicate_stdlib (imports types), sibling_package_dsl_consumer | — |
| predicate.ark | MOVE-TO-PRIMITIVES | primitives/predicate.ark | Contains only `predicate` items (5 string predicates, 4 numeric comparison predicates, 1 null predicate) which are type-level boolean primitives reused across every domain's `check:` clauses; no domain-specific item kinds present. | Item::Predicate, predicate_combinator, param_ref, string_predicate_stdlib, numeric_predicate_stdlib, is_null_predicate | — |
| expression.ark | MOVE-TO-PRIMITIVES | primitives/expression.ark | Contains only `expression` items (numeric, text, and null-handling stdlib declarations) which are type-level pipe-stage primitives; the `pipe_chain` grammar rule and `param_ref` sigils are consumed by every domain's processing clauses, satisfying the cross-domain reuse criterion. | Item::Expression, pipe_chain, param_ref, numeric_expression_stdlib, text_expression_stdlib, null_handling_expression_stdlib | — |
| code_graph.ark | KEEP-RENAMED | domain/code_graph.ark | File is a single-domain island defining the CodeGraph schema (structs for Module, Function, Class, Method, Parameter, Variable, Edge, Complexity, ArkEntity, GraphMetadata, CodeGraph, and the EdgeKind enum); it must be promoted from the flat stdlib root into the `domain/` subdirectory per the two-level layout. | struct_Module, struct_Function, struct_Class, struct_Method, struct_Parameter, struct_Variable, enum_EdgeKind, struct_Edge, struct_Complexity, struct_ArkEntity, struct_GraphMetadata, struct_CodeGraph | — |
| code_graph_queries.ark | MERGE-INTO | domain/code_graph.ark#queries | File contains exclusively expression and predicate declarations scoped to the CodeGraph domain (7 expressions: callers, call-chain, dead-code, complex-functions, subclasses, importers, module-deps; 3 predicates: is-reachable, has-cycles, is-dead); the dedup matrix row "Dual Lark+Pest grammar parity" covers its grammar extension, and its content is a proper subset of code_graph.ark's natural scope, warranting absorption under the `#queries` section. | expression_callers, expression_call_chain, expression_dead_code, expression_complex_functions, expression_subclasses, expression_importers, expression_module_deps, predicate_is_reachable, predicate_has_cycles, predicate_is_dead | dual_grammar_parity |
| studio.ark | KEEP-RENAMED | domain/studio.ark | File is a single-domain island containing all studio item kinds (`role`, `studio`, `workflow_command`, `hook`, `rule`, `template`) plus supporting enums and structs; no content changes are required, only path promotion from flat root to `domain/` subdirectory. | Item_StudioJob_role, Item_StudioJob_studio, Item::WorkflowCommand, Item::Hook, Item::Rule, Item::Template, enum_Tier, enum_AgentTool, enum_HookEvent, enum_Severity, enum_WorkflowPhase, struct_Skill, struct_EscalationPath, struct_CommandOutput | skill_definitions |
| evolution.ark | KEEP-RENAMED | domain/evolution.ark | File is a single-domain island containing all evolution item kinds (`evolution_target`, `eval_dataset`, `fitness_function`, `optimizer`, `benchmark_gate`, `evolution_run`, `constraint`) plus supporting enums and structs; path promotion to `domain/` is the only required change. | Item::EvolutionTarget, Item::EvalDataset, Item::FitnessFunction, Item::Optimizer, Item::BenchmarkGate, Item::EvolutionRun, Item::Constraint, enum_EvolutionTier, enum_OptimizerEngine, enum_DataSource, enum_EnforcementLevel, enum_RunStatus, enum_MutationStrategy, enum_AggregationMethod, struct_FitnessScore, struct_Variant, struct_ConstraintDef, struct_BenchmarkResult, struct_RunResult, struct_SplitRatio, struct_RubricDimension | — |
| agent.ark | KEEP-RENAMED | domain/agent.ark | File is a single-domain island containing all hermes agent item kinds (`agent`, `platform`, `gateway`, `execution_backend`, `skill`, `learning_config`, `cron_task`, `model_config`) plus supporting enums and structs; path promotion to `domain/` is the only required change. | Item::Agent, Item::Platform, Item::Gateway, Item::ExecutionBackend, Item_Skill, Item::LearningConfig, Item::CronTask, Item::ModelConfig, enum_Platform, enum_BackendType, enum_ModelProvider, enum_SkillStatus, enum_MessageFormat, enum_LearningMode, struct_GatewayRoute, struct_ModelParams, struct_ResourceLimits, struct_SkillTrigger, struct_ImprovementEntry, struct_CronSchedule | skill_definitions |
| visual.ark | KEEP-RENAMED | domain/visual.ark | File is a single-domain island containing visual item kinds; `Item::Screenshot` and `Item::VisualSearch` are retired per `research/pruning-catalog.md` (row: `screenshot_manager, visual_search, html_previewer` → OUT-OF-SCOPE → ADV-UI) and `struct_ScreenshotMeta` and `struct_SearchQuery`/`struct_SearchResult` are correspondingly dropped; remaining items (`diagram`, `preview`, `annotation`, `visual_review`, `render_config`, plus `Item::Feedback`) survive with path promotion to `domain/`. | Item::Diagram, Item::Preview, Item::Annotation, Item::VisualReview, Item::Screenshot, Item::VisualSearch, Item::RenderConfig, enum_DiagramType, enum_PreviewMode, enum_AnnotationType, enum_FeedbackStatus, enum_RenderFormat, enum_ViewportSize, enum_SearchMode, enum_VisualTag, struct_RenderConfig, struct_Position, struct_ArrowEndpoints, struct_AnnotationElement, struct_ReviewFeedback, struct_ScreenshotMeta, struct_SearchQuery, struct_SearchResult | — |

**Verdict summary.** MOVE-TO-PRIMITIVES: 3 (`types`, `predicate`, `expression`).
MERGE-INTO: 1 (`code_graph_queries`). KEEP-RENAMED: 5 (`code_graph`, `studio`,
`evolution`, `agent`, `visual`). RETIRE: 0. KEEP-AS-IS: 0. Total: 9 rows. ✓

---

## Target Two-Level Stdlib Layout

Reproduced from `designs/design-unified-descriptor.md` §4, annotated with
verdict-table row numbers (rows counted from the first data row above).

```
ark/dsl/stdlib/
  primitives/              # type-only — auto-preluded into every consumer
    types.ark              ← row 1 (MOVE-TO-PRIMITIVES)
    predicate.ark          ← row 2 (MOVE-TO-PRIMITIVES)
    expression.ark         ← row 3 (MOVE-TO-PRIMITIVES)
  domain/                  # one file per domain island, opt-in import
    code_graph.ark         ← row 4 (KEEP-RENAMED) + row 5 absorbed under #queries
    studio.ark             ← row 6 (KEEP-RENAMED)
    evolution.ark          ← row 7 (KEEP-RENAMED)
    agent.ark              ← row 8 (KEEP-RENAMED)
    visual.ark             ← row 9 (KEEP-RENAMED; Screenshot/VisualSearch items dropped)
```

**`primitives/` invariant.** Every file under `primitives/` contains only
`primitive`, `struct`, `enum`, `predicate`, and `expression` items — no domain
item kinds (`studio`, `role`, `agent`, `evolution_target`, `diagram`, etc.),
and no imports of `domain/*`. Enforced by a lint pass in the downstream
`ADV-Descriptor-Unification` adventure. The three files promoted here satisfy
this invariant in their current form; no content rewrite is required, only
path rename.

**`domain/` invariant.** Every file is a single-domain island. A domain file
may import `stdlib.primitives.*` (available via auto-prelude without explicit
import) and may import other `stdlib.domain.*` siblings only via an explicit
`import` statement. No circular domain-to-domain imports are allowed.

**Import path rewrite.** Every current consumer that writes
`import stdlib.types` must be updated to `import stdlib.primitives.types`.
The auto-prelude will make the explicit form optional for primitives, but
existing explicit imports must still resolve. This rewrite is a mechanical
find-and-replace in the downstream adventure.

**Merged items.** Row 5 (`code_graph_queries.ark`) dissolves entirely: its 7
expression decls and 3 predicate decls are absorbed into
`domain/code_graph.ark` under a delimited `# queries` section. The file
`code_graph_queries.ark` is deleted from disk in the downstream adventure.

**Visual pruning.** Row 9 (`visual.ark`) undergoes item-level pruning in
addition to path promotion: `Item::Screenshot`, `Item::VisualSearch`,
`struct_ScreenshotMeta`, `struct_SearchQuery`, and `struct_SearchResult` are
removed per the pruning catalog (OUT-OF-SCOPE → ADV-UI). The surviving items
retain their current field schemas.

---

## Grammar Authoring Contract

This section pins the Lark-primary / Pest-secondary workflow that the downstream
`ADV-Descriptor-Unification` adventure will enforce across all grammar changes.
The rules below supersede the ad-hoc practice visible across ADV-001..006,
where each adventure introduced its own grammar-extension approach (ADV-003
split the work across two tasks T003/T004; ADV-005 added agent rules in a
separate session; ADV-006 added visual rules in yet another). The unified
contract makes the procedure mandatory and machine-verifiable.

### Rule 1 — Primacy

`ark/tools/parser/ark_grammar.lark` is the **authoring grammar** — the file a
developer edits when adding or modifying a language construct. `ark/dsl/grammar/ark.pest`
is a **mirror** — it must produce byte-identical JSON AST on every shared
fixture. The Lark grammar is primary because the Python parser (`ark_parser.py`)
is the reference implementation (see `ark.py parse`); ADV-001 TC-005 already
established Lark↔Pest byte-identity as a hard contract. The dedup-matrix row
"Dual Lark+Pest grammar parity" (canonical: `single grammar authoring contract`)
is resolved here: one source-of-truth edit flow, one parity test to enforce it.

### Rule 2 — Fixed Six-Section Layout

Every grammar file (`ark_grammar.lark` and `ark.pest`) must maintain this
section ordering, delimited by comment banners:

```
(a) Whitespace and comments         — WHITESPACE, COMMENT, inline_comment
(b) Top-level file structure        — file, import_stmt, item
(c) Four primitives                 — @in, #process, @out, $data rules
(d) Base items (alphabetical)       — abstraction, bridge, class, enum,
                                      instance, island, primitive,
                                      registry, struct, verify
(e) Domain items (alphabetical)     — agent_def, annotation_def,
                                      benchmark_gate_def, cron_task_def,
                                      diagram_def, eval_dataset_def,
                                      evolution_run_def, evolution_target_def,
                                      execution_backend_def, expression_def,
                                      fitness_function_def, gateway_def,
                                      hook_def, learning_config_def,
                                      model_config_def, optimizer_def,
                                      platform_def, predicate_def,
                                      preview_def, render_config_def,
                                      role_def, rule_def, skill_def,
                                      studio_def, template_def,
                                      visual_review_def, workflow_command_def
(f) Shared terminals                — IDENT, STRING, NUMBER,
                                      PIPE_FN_IDENT, dotted_path,
                                      typed_field_list, pipe_expr
```

The current `ark.pest` top-level (lines 17–59) already approximates this shape
— the contract formalises and mandates it. Domain item rules in section (e) are
in strict alphabetical order by rule name in both files so that diffs remain
reviewable and the two files stay visually aligned.

### Rule 3 — One-Patch Rule

Any domain addition or rename lands as a **single atomic commit** that patches
both grammar files simultaneously, accompanied by one new fixture under
`ark/dsl/stdlib/fixtures/` (or equivalent) that exercises the new rule in both
parsers. This commit may not be split across tasks or adventures. This rule
replaces the ADV-003 practice of separating Lark and Pest work into distinct
tasks. The downstream `ADV-Descriptor-Unification` adventure enforces this rule
in its task acceptance criteria.

### Rule 4 — Grammar-Parity Autotest

`tests/test_grammar_parity.py` is a new test module (created in the downstream
adventure) that:

1. Enumerates every `.ark` file under `ark/dsl/stdlib/` and `specs/`.
2. Parses each file with both `ark_parser.py` (Lark) and the Rust `dsl` crate
   (Pest) via `ark-dsl`'s public API.
3. Asserts that the JSON AST produced by both parsers is byte-identical (same
   key order, same field values, no floating-point divergence in numeric
   literals).
4. Runs as part of CI (`cargo test` + `pytest`). Any grammar drift — where one
   file is patched without the other — fails the build immediately.

The test is the machine-verifiable enforcement of Rule 1. Its existence makes
the one-patch rule (Rule 3) structurally necessary: if a developer patches only
one grammar, the parity test fails.

### Rule 5 — Domain Ordering

Domain item rules in section (e) of both grammars MUST appear in alphabetical
order by rule name keyword (e.g. `agent_def` before `annotation_def` before
`benchmark_gate_def`). This ordering must be preserved on every patch. Reviewers
must reject PRs that insert a domain rule out of alphabetical order. The ordering
makes the two files visually aligned, making cross-file diffs trivially
reviewable.

### Rule 6 — Cross-Cutting Terminals

Shared syntactic elements — `pipe_expr`, `typed_field_list`, `dotted_path`,
numeric literal syntax, `PIPE_FN_IDENT` — MUST live in section (f) (Shared
terminals). Domain additions MUST NOT redefine or shadow these terminals in
section (e). Any domain rule that needs a new shared terminal must first add it
to section (f) in both files (in the same atomic commit), then reference it
from section (e). This prevents silent grammar divergence via redefined
terminals.

---

## AST Family Spec

### Single Root

`Item` is a variant enum that is the root of the unified AST. Every top-level
declaration in a parsed `.ark` file produces exactly one `Item` variant. The
enum lives in two places:

- **Rust**: `ark-dsl` crate, single `ast.rs` module, `pub enum Item { ... }`.
  No per-domain crate split. Cross-references the `PestParseRsTask` pattern
  from ADV-005's dual-parser work as the canonical structure.
- **Python**: `ark_parser.Ast.Item` — a tagged union using Python dataclasses
  with a `kind` discriminant field. The existing `ark_parser.py` already emits
  a `type`-keyed JSON structure that maps to this.

No per-domain `Item` sub-enum is introduced. All ~40 variants live in a single
flat enum with a domain-grouping comment header in the source.

### Variant Seed List

The following table lists all seed variants, grouped by domain. Variants marked
`(DROPPED)` are retired per `research/pruning-catalog.md` and do not appear in
the final enum.

**Base group (10 variants)**
These variants correspond to the pre-existing ark item kinds present in
`ark_grammar.lark` before ADV-001:

| Variant | Grammar keyword | Source file |
|---------|----------------|-------------|
| `Abstraction` | `abstraction` | core grammar |
| `Class` | `class` | core grammar |
| `Instance` | `instance` | core grammar |
| `Island` | `island` | core grammar |
| `Bridge` | `bridge` | core grammar |
| `Registry` | `registry` | core grammar |
| `Verify` | `verify` | core grammar |
| `Primitive` | `primitive` | stdlib keywords (StdlibKeywordsTask) |
| `Struct` | `struct` | stdlib keywords (StdlibKeywordsTask) |
| `Enum` | `enum` | stdlib keywords (StdlibKeywordsTask) |

**Primitives group (2 variants)**
These variants are type-level building blocks promoted to `primitives/`:

| Variant | Grammar keyword | Target file |
|---------|----------------|------------|
| `Expression` | `expression` | primitives/expression.ark |
| `Predicate` | `predicate` | primitives/predicate.ark |

**Studio domain group (6 variants)**

| Variant | Grammar keyword | Source file |
|---------|----------------|-------------|
| `Role` | `role` | domain/studio.ark |
| `Studio` | `studio` | domain/studio.ark |
| `Command` | `workflow_command` | domain/studio.ark |
| `Hook` | `hook` | domain/studio.ark |
| `Rule` | `rule` | domain/studio.ark |
| `Template` | `template` | domain/studio.ark |

**Evolution domain group (7 variants)**

| Variant | Grammar keyword | Source file |
|---------|----------------|-------------|
| `EvolutionTarget` | `evolution_target` | domain/evolution.ark |
| `EvalDataset` | `eval_dataset` | domain/evolution.ark |
| `FitnessFunction` | `fitness_function` | domain/evolution.ark |
| `Optimizer` | `optimizer` | domain/evolution.ark |
| `BenchmarkGate` | `benchmark_gate` | domain/evolution.ark |
| `EvolutionRun` | `evolution_run` | domain/evolution.ark |
| `Constraint` | `constraint` | domain/evolution.ark |

**Agent domain group (8 variants)**

| Variant | Grammar keyword | Source file |
|---------|----------------|-------------|
| `Agent` | `agent` | domain/agent.ark |
| `Platform` | `platform` | domain/agent.ark |
| `Gateway` | `gateway` | domain/agent.ark |
| `ExecutionBackend` | `execution_backend` | domain/agent.ark |
| `Skill` | `skill` | domain/agent.ark |
| `LearningConfig` | `learning_config` | domain/agent.ark |
| `CronTask` | `cron_task` | domain/agent.ark |
| `ModelConfig` | `model_config` | domain/agent.ark |

**Visual domain group (6 variants)**
`Screenshot` and `VisualSearch` are dropped per pruning-catalog row
`screenshot_manager, visual_search, html_previewer` (OUT-OF-SCOPE → ADV-UI).

| Variant | Grammar keyword | Source file |
|---------|----------------|-------------|
| `Diagram` | `diagram` | domain/visual.ark |
| `Preview` | `preview` | domain/visual.ark |
| `Annotation` | `annotation` | domain/visual.ark |
| `VisualReview` | `visual_review` | domain/visual.ark |
| `RenderConfig` | `render_config` | domain/visual.ark |
| `Feedback` | `feedback` | domain/visual.ark |
| `Screenshot` | `screenshot` | (DROPPED — pruning-catalog: OUT-OF-SCOPE → ADV-UI) |
| `VisualSearch` | `visual_search` | (DROPPED — pruning-catalog: OUT-OF-SCOPE → ADV-UI) |

**Code-graph domain group (note — no new variants)**
The CodeGraph schema is expressed entirely via `Struct` and `Enum` base
variants with a domain annotation field (`domain: "code_graph"`). The 7
expression and 3 predicate query decls from `code_graph_queries.ark` are
absorbed as `Expression` and `Predicate` variant instances under the
`code_graph.ark#queries` section. No new `CodeGraphNode` or `CodeGraphEdge`
variant is introduced; the base `Struct` variant carries a `domain` attribute
that the codegen and verify layers use to route to domain-specific handlers.

**Total variant count.** Base (10) + Primitives (2) + Studio (6) + Evolution
(7) + Agent (8) + Visual (6, after dropping 2) = **39 active variants**.
This is down from 43 item kinds currently declared across the two grammar files,
reduced by retiring `Screenshot` and `VisualSearch` and by folding the code-graph
query items under the `Expression`/`Predicate` base variants rather than
introducing new kinds. The count falls within the design's "~40 variants" target.

### Dual-Input Helper Contract

Every `Item` variant exposes two construction helpers:

- `from_lark(tree: lark.Tree) -> Item` (Python, in `ark_parser.py`) — converts
  the Lark parse tree node for this item kind into the corresponding `Item`
  variant dataclass.
- `from_pest(pair: pest::iterators::Pair) -> Item` (Rust, in `ark-dsl/ast.rs`)
  — converts the Pest `Pair` for this rule into the corresponding `Item` enum
  variant.

Both helpers are exercised by the grammar-parity autotest (`Rule 4` of the
Grammar Authoring Contract) via a shared fixture matrix: each `.ark` fixture is
parsed by both helpers and the resulting JSON is compared byte-for-byte. This
preserves the "Dual-input AST helpers" pattern established in ADV-005 and makes
the parity autotest trivially implementable.

### Extensibility Rule

Adding a new domain variant requires all five of the following in one atomic
patch (enforced by the one-patch rule, Grammar Authoring Contract Rule 3):

1. A new rule in `ark_grammar.lark` (section e, alphabetical position).
2. A mirrored rule in `ark.pest` (section e, same alphabetical position).
3. A new variant in `pub enum Item` (`ast.rs`) and the Python dataclass.
4. A `from_lark` and `from_pest` helper for the new variant.
5. A fixture `.ark` file under `ark/dsl/stdlib/fixtures/` exercising the new
   rule, verifiable by the grammar-parity autotest.

---

## Citations

### 5a. Descriptor-Bucket Concepts from concept-mapping.md

Every row in `research/concept-mapping.md` with `bucket = descriptor` is cited
below. The `resolved_in` column identifies which section of this document or
`design-unified-descriptor.md` addresses the concept.

| concept_row_id (canonical_name) | concept_name | resolved_in |
|---------------------------------|--------------|-------------|
| Item::Expression | Item::Expression | §AST Family Spec — Primitives group variant `Expression`; §Verdict Table row 3 (expression.ark MOVE-TO-PRIMITIVES) |
| Item::Predicate | Item::Predicate | §AST Family Spec — Primitives group variant `Predicate`; §Verdict Table row 2 (predicate.ark MOVE-TO-PRIMITIVES) |
| pipe_chain | pipe_chain | §Grammar Authoring Contract Rule 6 — cross-cutting terminal in shared terminals section (f) |
| predicate_combinator | predicate_combinator | §Grammar Authoring Contract Rule 6 — cross-cutting terminal; §Verdict Table row 2 |
| param_ref | param_ref | §Grammar Authoring Contract Rule 6 — cross-cutting terminal `PIPE_FN_IDENT` family; §Verdict Table rows 2, 3 |
| dual_grammar_parity | Dual-grammar parity | §Grammar Authoring Contract — entire section; dedup row "Dual Lark+Pest grammar parity" resolved in Rule 1 |
| numeric_expression_stdlib | numeric expression stdlib | §Verdict Table row 3 (expression.ark MOVE-TO-PRIMITIVES); §Target Two-Level Stdlib Layout `primitives/expression.ark` |
| text_expression_stdlib | text expression stdlib | §Verdict Table row 3; §Target Two-Level Stdlib Layout `primitives/expression.ark` |
| null_handling_expression_stdlib | null-handling expression stdlib | §Verdict Table row 3; §Target Two-Level Stdlib Layout `primitives/expression.ark` |
| string_predicate_stdlib | string predicate stdlib | §Verdict Table row 2 (predicate.ark MOVE-TO-PRIMITIVES); §Target Two-Level Stdlib Layout `primitives/predicate.ark` |
| numeric_predicate_stdlib | numeric predicate stdlib | §Verdict Table row 2; §Target Two-Level Stdlib Layout `primitives/predicate.ark` |
| is_null_predicate | is-null predicate | §Verdict Table row 2; §Target Two-Level Stdlib Layout `primitives/predicate.ark` |
| struct_Module | struct Module | §Verdict Table row 4 (code_graph.ark KEEP-RENAMED); §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| struct_Function | struct Function | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| struct_Class | struct Class | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| struct_Method | struct Method | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| struct_Parameter | struct Parameter | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| struct_Variable | struct Variable | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| enum_EdgeKind | enum EdgeKind | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| struct_Edge | struct Edge | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| struct_Complexity | struct Complexity | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| struct_ArkEntity | struct ArkEntity | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| struct_GraphMetadata | struct GraphMetadata | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| struct_CodeGraph | struct CodeGraph | §Verdict Table row 4; §Target Two-Level Stdlib Layout `domain/code_graph.ark` |
| expression_callers | expression callers | §Verdict Table row 5 (code_graph_queries.ark MERGE-INTO `domain/code_graph.ark#queries`) |
| expression_call_chain | expression call-chain | §Verdict Table row 5; §Target Two-Level Stdlib Layout row 5 annotation |
| expression_dead_code | expression dead-code | §Verdict Table row 5; §Target Two-Level Stdlib Layout row 5 annotation |
| expression_complex_functions | expression complex-functions | §Verdict Table row 5; §Target Two-Level Stdlib Layout row 5 annotation |
| expression_subclasses | expression subclasses | §Verdict Table row 5; §Target Two-Level Stdlib Layout row 5 annotation |
| expression_importers | expression importers | §Verdict Table row 5; §Target Two-Level Stdlib Layout row 5 annotation |
| expression_module_deps | expression module-deps | §Verdict Table row 5; §Target Two-Level Stdlib Layout row 5 annotation |
| predicate_is_reachable | predicate is-reachable | §Verdict Table row 5; §Target Two-Level Stdlib Layout row 5 annotation |
| predicate_has_cycles | predicate has-cycles | §Verdict Table row 5; §Target Two-Level Stdlib Layout row 5 annotation |
| predicate_is_dead | predicate is-dead | §Verdict Table row 5; §Target Two-Level Stdlib Layout row 5 annotation |
| Item_StudioJob_role | Item::StudioJob (role) | §AST Family Spec — Studio domain group variant `Role`; §Verdict Table row 6 |
| Item_StudioJob_studio | Item::StudioJob (studio) | §AST Family Spec — Studio domain group variant `Studio`; §Verdict Table row 6 |
| Item::WorkflowCommand | Item::WorkflowCommand | §AST Family Spec — Studio domain group variant `Command`; §Verdict Table row 6 |
| Item::Hook | Item::Hook | §AST Family Spec — Studio domain group variant `Hook`; §Verdict Table row 6 |
| Item::Rule | Item::Rule | §AST Family Spec — Studio domain group variant `Rule`; §Verdict Table row 6 |
| Item::Template | Item::Template | §AST Family Spec — Studio domain group variant `Template`; §Verdict Table row 6 |
| enum_Tier | enum Tier | §Verdict Table row 6 (studio.ark KEEP-RENAMED); §Target Two-Level Stdlib Layout `domain/studio.ark` |
| enum_AgentTool | enum AgentTool | §Verdict Table row 6; §Target Two-Level Stdlib Layout `domain/studio.ark` |
| enum_HookEvent | enum HookEvent | §Verdict Table row 6; §Target Two-Level Stdlib Layout `domain/studio.ark` |
| enum_Severity | enum Severity | §Verdict Table row 6; §Target Two-Level Stdlib Layout `domain/studio.ark` |
| enum_WorkflowPhase | enum WorkflowPhase | §Verdict Table row 6; §Target Two-Level Stdlib Layout `domain/studio.ark` |
| struct_Skill | struct Skill | §Verdict Table row 6; dedup row "Skill definitions" resolved in §5b |
| struct_EscalationPath | struct EscalationPath | §Verdict Table row 6; §Target Two-Level Stdlib Layout `domain/studio.ark` |
| struct_CommandOutput | struct CommandOutput | §Verdict Table row 6; §Target Two-Level Stdlib Layout `domain/studio.ark` |
| Item::EvolutionTarget | Item::EvolutionTarget | §AST Family Spec — Evolution domain group; §Verdict Table row 7 |
| Item::EvalDataset | Item::EvalDataset | §AST Family Spec — Evolution domain group; §Verdict Table row 7 |
| Item::FitnessFunction | Item::FitnessFunction | §AST Family Spec — Evolution domain group; §Verdict Table row 7 |
| Item::Optimizer | Item::Optimizer | §AST Family Spec — Evolution domain group; §Verdict Table row 7 |
| Item::BenchmarkGate | Item::BenchmarkGate | §AST Family Spec — Evolution domain group; §Verdict Table row 7 |
| Item::EvolutionRun | Item::EvolutionRun | §AST Family Spec — Evolution domain group; §Verdict Table row 7 |
| Item::Constraint | Item::Constraint | §AST Family Spec — Evolution domain group; §Verdict Table row 7 |
| enum_EvolutionTier | enum EvolutionTier | §Verdict Table row 7 (evolution.ark KEEP-RENAMED); §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| enum_OptimizerEngine | enum OptimizerEngine | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| enum_DataSource | enum DataSource | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| enum_EnforcementLevel | enum EnforcementLevel | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| enum_RunStatus | enum RunStatus | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| enum_MutationStrategy | enum MutationStrategy | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| enum_AggregationMethod | enum AggregationMethod | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| struct_FitnessScore | struct FitnessScore | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| struct_Variant | struct Variant | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| struct_ConstraintDef | struct ConstraintDef | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| struct_BenchmarkResult | struct BenchmarkResult | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| struct_RunResult | struct RunResult | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| struct_SplitRatio | struct SplitRatio | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| struct_RubricDimension | struct RubricDimension | §Verdict Table row 7; §Target Two-Level Stdlib Layout `domain/evolution.ark` |
| Item::Agent | Item::Agent | §AST Family Spec — Agent domain group; §Verdict Table row 8 |
| Item::Platform | Item::Platform | §AST Family Spec — Agent domain group; §Verdict Table row 8 |
| Item::Gateway | Item::Gateway | §AST Family Spec — Agent domain group; §Verdict Table row 8 |
| Item::ExecutionBackend | Item::ExecutionBackend | §AST Family Spec — Agent domain group; §Verdict Table row 8 |
| Item_Skill | Item::Skill | §AST Family Spec — Agent domain group variant `Skill`; dedup row "Skill definitions" resolved in §5b; §Verdict Table row 8 |
| Item::LearningConfig | Item::LearningConfig | §AST Family Spec — Agent domain group; §Verdict Table row 8 |
| Item::CronTask | Item::CronTask | §AST Family Spec — Agent domain group; §Verdict Table row 8 |
| Item::ModelConfig | Item::ModelConfig | §AST Family Spec — Agent domain group; §Verdict Table row 8 |
| enum_Platform | enum Platform | §Verdict Table row 8 (agent.ark KEEP-RENAMED); §Target Two-Level Stdlib Layout `domain/agent.ark` |
| enum_BackendType | enum BackendType | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| enum_ModelProvider | enum ModelProvider | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| enum_SkillStatus | enum SkillStatus | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| enum_MessageFormat | enum MessageFormat | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| enum_LearningMode | enum LearningMode | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| struct_GatewayRoute | struct GatewayRoute | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| struct_ModelParams | struct ModelParams | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| struct_ResourceLimits | struct ResourceLimits | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| struct_SkillTrigger | struct SkillTrigger | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| struct_ImprovementEntry | struct ImprovementEntry | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| struct_CronSchedule | struct CronSchedule | §Verdict Table row 8; §Target Two-Level Stdlib Layout `domain/agent.ark` |
| Item::Diagram | Item::Diagram | §AST Family Spec — Visual domain group; §Verdict Table row 9 |
| Item::Preview | Item::Preview | §AST Family Spec — Visual domain group; §Verdict Table row 9 |
| Item::Annotation | Item::Annotation | §AST Family Spec — Visual domain group; §Verdict Table row 9 |
| Item::VisualReview | Item::VisualReview | §AST Family Spec — Visual domain group; §Verdict Table row 9 |
| Item::Screenshot | Item::Screenshot | §AST Family Spec — Visual domain group (DROPPED); pruning-catalog `screenshot_manager, visual_search, html_previewer` → OUT-OF-SCOPE → ADV-UI |
| Item::VisualSearch | Item::VisualSearch | §AST Family Spec — Visual domain group (DROPPED); pruning-catalog → OUT-OF-SCOPE → ADV-UI |
| Item::RenderConfig | Item::RenderConfig | §AST Family Spec — Visual domain group variant `RenderConfig`; §Verdict Table row 9 |
| enum_DiagramType | enum DiagramType | §Verdict Table row 9 (visual.ark KEEP-RENAMED); §Target Two-Level Stdlib Layout `domain/visual.ark` |
| enum_PreviewMode | enum PreviewMode | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| enum_AnnotationType | enum AnnotationType | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| enum_FeedbackStatus | enum FeedbackStatus | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| enum_RenderFormat | enum RenderFormat | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| enum_ViewportSize | enum ViewportSize | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| enum_SearchMode | enum SearchMode | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` (struct_SearchQuery dropped — no surviving item; enum retained for VisualReview filter semantics) |
| enum_VisualTag | enum VisualTag | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| struct_RenderConfig | struct RenderConfig | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| struct_Position | struct Position | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| struct_ArrowEndpoints | struct ArrowEndpoints | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| struct_AnnotationElement | struct AnnotationElement | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| struct_ReviewFeedback | struct ReviewFeedback | §Verdict Table row 9; §Target Two-Level Stdlib Layout `domain/visual.ark` |
| struct_ScreenshotMeta | struct ScreenshotMeta | §Verdict Table row 9 (DROPPED with Screenshot item); pruning-catalog → OUT-OF-SCOPE → ADV-UI |
| struct_SearchQuery | struct SearchQuery | §Verdict Table row 9 (DROPPED with VisualSearch item); pruning-catalog → OUT-OF-SCOPE → ADV-UI |
| struct_SearchResult | struct SearchResult | §Verdict Table row 9 (DROPPED with VisualSearch item); pruning-catalog → OUT-OF-SCOPE → ADV-UI |
| sibling_package_dsl_consumer | sibling-package DSL consumer | §Target Two-Level Stdlib Layout — import contract; §5c host-language contract citation |
| semantic_label_propagation | semantic label propagation | design-unified-descriptor.md §6 — host-language contract bar (0 BLOCKED, ≤2 NEEDS_WORKAROUND); §5c |

### 5b. Descriptor-Bucket Dedup Rows from deduplication-matrix.md

Every row in `research/deduplication-matrix.md` with `assigned_bucket =
descriptor` is cited below.

| dedup_row_id | duplicate_forms | canonical_form | resolution |
|--------------|-----------------|----------------|------------|
| dual_grammar_parity | (ADV-001: Dual-grammar parity); (ADV-002: graph grammar rules); (ADV-003: studio grammar rules); (ADV-004: evolution grammar rules); (ADV-005: agent grammar rules); (ADV-006: visual grammar rules); (ADV-008: shape grammar consumer) | single grammar authoring contract — one source-of-truth rule file with parity test across ark_grammar.lark + ark.pest | Resolved by §Grammar Authoring Contract (Rule 1 declares Lark primary, Rule 4 specifies the grammar-parity autotest, Rule 3 enforces single-commit atomicity); also applies to verdict row 5: MERGE-INTO `domain/code_graph.ark#queries` (the code_graph_queries grammar rules merge into code_graph in a single patch). |
| skill_definitions | (ADV-003: struct Skill in studio.ark); (ADV-004: Item::EvolutionTarget over skills); (ADV-005: Item::Skill DSL item + skill_manager runtime) | single Skill struct in descriptor + single skill_manager runtime in controller | Resolved by §AST Family Spec — the descriptor side is a single `Skill` variant in the agent domain group (verdict row 8, `agent.ark` KEEP-RENAMED); `struct_Skill` in studio.ark (verdict row 6) is a data struct (Struct base variant) distinct from the `Item::Skill` DSL item; the `skill_manager` runtime is a controller concern resolved in the unified-controller design (out of scope for this delta). The two studio-side concepts (`struct_Skill` schema + `Item::Skill` procedural kind) are intentionally kept distinct. |

### 5c. Host-Language Contract Citation (TC-010)

The descriptor must remain expressive enough that a sibling package (e.g.,
`shape_grammar/`) can consume the DSL without requiring new item kinds. The
ADV-008 host-language feasibility study (T03) established the bar at 0 BLOCKED
items and at most 2 NEEDS_WORKAROUND — this is the host-language contract that
the unified descriptor must preserve. Any domain addition proposed by this delta
report (or by a downstream adventure consuming the delta) must re-run the
ADV-008 host-language feasibility study before the addition lands, verifying
that the expanded Item enum does not push the host-language binding past the
2 NEEDS_WORKAROUND threshold. The study is documented at
`.agent/adventures/ADV-008/research/feasibility-study.md` (canonical path;
implementer confirms existence at migration time). The concept-mapping row
`sibling_package_dsl_consumer` (ADV-008, bucket: descriptor) and the out-of-scope
row `host_language_contract` (ADV-008, pruning-catalog: DROP — host-language
binding is a sibling-package responsibility, not ark-core) together define the
boundary: ark-core owns the descriptor surface; the sibling package owns the
host-language binding; ADV-008's feasibility bar is the shared acceptance
criterion that keeps both sides compatible.
