# Builder Delta

## Scope

This report classifies every module currently present under `ark/tools/verify/`,
`ark/tools/codegen/`, `ark/tools/visualizer/`, `ark/tools/visual/`, and the
code-graph verifier under `ark/tools/codegraph/graph_verify.py`. For each
module it assigns one of three verdicts (`KEEP`, `MERGE-INTO-HARNESS`, `RETIRE`)
and maps verify modules to the four canonical shared passes introduced by the
unified builder. No code is moved or modified; this is a purely classificatory
delta document produced by ADV011-T007 on 2026-04-15. The authority for the
unified builder design is `.agent/adventures/ADV-011/designs/design-unified-builder.md`.

---

## Module Verdicts

| module | current_location | verdict | canonical_target | replaced_by_pass | source_adventures | dedup_row | notes |
|--------|-----------------|---------|-----------------|-----------------|-------------------|-----------|-------|
| ark_verify | ark/tools/verify/ark_verify.py | MERGE-INTO-HARNESS | ark_verify.Harness | opaque_primitive, numeric_interval | ADV-001,ADV-002 | dedup:4 | Core Z3 harness; SymbolTable, NATIVE_PRIMITIVES, OPAQUE_PRIMITIVES, apply_opaque merge into shared Harness registrar. |
| expression_smt | ark/tools/verify/expression_smt.py | MERGE-INTO-HARNESS | ark_verify.Harness | opaque_primitive | ADV-002 | dedup:4 | PRIMITIVE_Z3 registry becomes the canonical primitive data store under the shared opaque_primitive registrar. |
| studio_verify | ark/tools/verify/studio_verify.py | MERGE-INTO-HARNESS | ark_verify.Harness | dag_acyclicity, opaque_primitive, reference_exists | ADV-003 | dedup:1,dedup:4,dedup:8 | Domain plugin; escalation acyclicity → dag_acyclicity; hook event/role refs → reference_exists; rule SAT stays as plugin residue. |
| evolution_verify | ark/tools/verify/evolution_verify.py | MERGE-INTO-HARNESS | ark_verify.Harness | numeric_interval, reference_exists | ADV-004 | dedup:8 | Domain plugin; split-ratio/fitness-weight/optimizer bounds → numeric_interval; cross-ref + constraint-ref → reference_exists; benchmark-gate tolerance stays as plugin residue. |
| agent_verify | ark/tools/verify/agent_verify.py | MERGE-INTO-HARNESS | ark_verify.Harness | dag_acyclicity, numeric_interval, reference_exists | ADV-005 | dedup:8 | Domain plugin; fallback acyclicity → dag_acyclicity; resource limits → numeric_interval; gateway/cron/model refs → reference_exists; skill-trigger overlap stays as plugin residue. |
| visual_verify | ark/tools/verify/visual_verify.py | MERGE-INTO-HARNESS | ark_verify.Harness | dag_acyclicity, numeric_interval, reference_exists | ADV-006 | dedup:1,dedup:8 | Domain plugin; review-cycle acyclicity → dag_acyclicity; render dims/annotation bounds → numeric_interval; diagram type/format/target refs → reference_exists. |
| ark_impact | ark/tools/verify/ark_impact.py | KEEP | ark_impact (unchanged) | — | ADV-001 | — | Pure AST-level dependency graph and re-verify set; no per-domain logic; remains as-is per codegen rule 4. |
| graph_verify | ark/tools/codegraph/graph_verify.py | MERGE-INTO-HARNESS | ark_verify.Harness | dag_acyclicity, reference_exists | ADV-002 | dedup:1 | check_no_inheritance_cycles → dag_acyclicity (inherits edges); check_no_dangling_edges → reference_exists (edge src/target → nodes); check_all_modules_have_names stays as plugin residue. |
| ark_codegen | ark/tools/codegen/ark_codegen.py | MERGE-INTO-HARNESS | Codegen.Pipeline:target=rust,Codegen.Pipeline:target=cpp,Codegen.Pipeline:target=proto | — | ADV-001 | — | Emits target-language source (Rust/C++/Proto); becomes emitter plugins keyed by target language per codegen rule 1. |
| expression_primitives | ark/tools/codegen/expression_primitives.py | KEEP | Codegen.Pipeline.PrimitiveRegistry | — | ADV-002 | dedup:2 | Primitive lookup table (EXPR_PRIMITIVES map) with no file output; referenced by other codegen modules; KEEP per rule 3. |
| studio_codegen | ark/tools/codegen/studio_codegen.py | MERGE-INTO-HARNESS | Codegen.Pipeline:target=claude-agent-md,Codegen.Pipeline:target=claude-command-md,Codegen.Pipeline:target=hooks-json | — | ADV-003 | dedup:6,dedup:8 | Emits configuration artefacts (agent md, command md, hooks JSON); becomes emitter plugins per codegen rule 2. |
| evolution_codegen | ark/tools/codegen/evolution_codegen.py | MERGE-INTO-HARNESS | Codegen.Pipeline:target=jsonl-dataset,Codegen.Pipeline:target=python-scorer-skeleton,Codegen.Pipeline:target=run-config-json,Codegen.Pipeline:target=report-md | — | ADV-004 | dedup:8 | Emits configuration artefacts (dataset JSONL, scorer.py, run config, report); becomes emitter plugins per codegen rule 2. |
| agent_codegen | ark/tools/codegen/agent_codegen.py | MERGE-INTO-HARNESS | Codegen.Pipeline:target=agent-yaml,Codegen.Pipeline:target=cron-entry,Codegen.Pipeline:target=skill-md,Codegen.Pipeline:target=docker-compose | — | ADV-005 | dedup:6,dedup:8 | Emits configuration artefacts (agent YAML, route YAML, crontab, skills.md, docker-compose); becomes emitter plugins per codegen rule 2. |
| visual_codegen | ark/tools/codegen/visual_codegen.py | MERGE-INTO-HARNESS | Codegen.Pipeline:target=mermaid,Codegen.Pipeline:target=html-preview,Codegen.Pipeline:target=annotation-overlay-json,Codegen.Pipeline:target=review-shell,Codegen.Pipeline:target=catalog-index-html | — | ADV-006 | dedup:8 | Emits configuration artefacts (mermaid, html preview, annotation overlay JSON, review script, catalog); becomes emitter plugins per codegen rule 2. |
| ark_visualizer | ark/tools/visualizer/ark_visualizer.py | KEEP | Visualizer.Core | — | ADV-001,ADV-003 | — | AST-level entity/bridge graph + orgchart LOD; grows overlay plugins per unified builder §3; remains as Visualizer.Core. |
| mermaid_renderer | ark/tools/visual/mermaid_renderer.py | KEEP | Visualizer.OverlayBackend:mermaid | — | ADV-006 | — | Rendering backend called through overlay interface; KEEP per visualizer rule 2. |
| annotator | ark/tools/visual/annotator.py | KEEP | Visualizer.OverlayBackend:annotator | — | ADV-006 | — | Rendering backend for annotation overlays; KEEP per visualizer rule 2. |
| html_previewer | ark/tools/visual/html_previewer.py | KEEP | Visualizer.OverlayBackend:html-preview | — | ADV-006 | — | Rendering backend for HTML preview output; KEEP per visualizer rule 2. |
| screenshot_manager | ark/tools/visual/screenshot_manager.py | KEEP | Visualizer.OverlayBackend:screenshot | — | ADV-006 | — | Rendering backend for screenshot capture; KEEP per visualizer rule 2. |
| visual_runner | ark/tools/visual/visual_runner.py | KEEP | Visualizer.OverlayBackend:visual-runner | — | ADV-006 | — | Rendering backend / runner orchestration for visual pipeline; KEEP per visualizer rule 2. |
| search | ark/tools/visual/search.py | KEEP | Visualizer.OverlayBackend:search | — | ADV-006 | — | Rendering backend for diagram search/index; KEEP per visualizer rule 2. |
| review_loop | ark/tools/visual/review_loop.py | RETIRE | — | — | ADV-006 | — | Controller concern re-classified by ADV011-T008; removed from builder scope; T008 owns the KEEP/MERGE verdict. |

---

## Shared Verify Passes

### dag_acyclicity

**Signature:**
```python
dag_acyclicity(items: list, node_kind: str, edge_kind: str,
               edge_attr: str, *, terminals_ok: bool = True) -> list[Result]
```

**Method:** Assign a Z3 `Int` ordinal per node; for every edge A→B assert
`ord(B) > ord(A)`; UNSAT implies a cycle. Subsumes every domain's hand-rolled
ordinal-chain verifier. The `terminals_ok` flag permits leaf nodes (no outgoing
edges) without requiring a fixed upper bound ordinal.

**Replaces:**
- `studio_verify.verify_escalation_acyclicity` — role.escalates_to graph cycle detection (ADV-003)
- `visual_verify` review-cycle check — visual_review.replaces_screenshot acyclicity (ADV-006)
- `agent_verify` model-fallback acyclicity — model_config.fallback_to chain (ADV-005)
- `graph_verify.check_no_inheritance_cycles` — inherits edges in the code graph (ADV-002)

---

### opaque_primitive

**Signature:**
```python
opaque_primitive(name: str, kind: str, arg_sorts: list,
                 result_sort) -> Function
```
(Registrar; returns the Z3 uninterpreted function and tags downstream obligations `PASS_OPAQUE`.)

**Method:** Lifts today's `OPAQUE_PRIMITIVES` table and `apply_opaque` function
from `ark_verify` into the shared harness; `expression_smt.PRIMITIVE_Z3`
becomes the canonical registry consumed by this pass. Per-domain primitive
lists become data passed to the registrar rather than duplicated code.

**Replaces:**
- `ark_verify.OPAQUE_PRIMITIVES` table + `apply_opaque` function (ADV-002)
- `expression_smt.PRIMITIVE_Z3` wrapper registry (ADV-002)
- Ad-hoc `PASS_OPAQUE` emission inside `studio_verify` (ADV-003)
- Ad-hoc `PASS_OPAQUE` emission inside `evolution_verify` (ADV-004)
- Ad-hoc `PASS_OPAQUE` emission inside `agent_verify` (ADV-005)
- Ad-hoc `PASS_OPAQUE` emission inside `visual_verify` (ADV-006)

---

### numeric_interval

**Signature:**
```python
numeric_interval(sym: Expr, lo: Optional[Num], hi: Optional[Num],
                 *, strict_lo: bool = False, strict_hi: bool = False) -> Result
```

**Method:** Asserts `lo ≤ sym ≤ hi` (or strict variants) with a Z3 Real/Int
check. Sum-to-1 constraints compose two calls: `numeric_interval(sum, 1.0,
1.0)` on the Sum expression plus `numeric_interval(x, 0, None)` per weight.
`None` bounds are treated as unbounded in that direction.

**Replaces:**
- `ark_verify` `$data` bounds check — generic numeric constraint on data fields (ADV-001)
- `evolution_verify` split-ratio sum-to-1 — train+val+test ∈ [0,1] sum = 1.0 (ADV-004)
- `evolution_verify` fitness-weight sum-to-1 — dimension weights ∈ [0,1] sum = 1.0 (ADV-004)
- `evolution_verify` tolerance bounds — tolerance ∈ (0, 1.0] (ADV-004)
- `evolution_verify` optimizer parameter bounds — iterations > 0, population_size > 0 (ADV-004)
- `agent_verify` resource limits — cpu_cores > 0, memory_mb > 0, timeout_seconds > 0 (ADV-005)
- `visual_verify` render config positivity — width > 0, height > 0, scale > 0 (ADV-006)
- `visual_verify` annotation bounds — annotation element positions within viewport bounds (ADV-006)

---

### reference_exists

**Signature:**
```python
reference_exists(ref: str, target_index: dict[str, Any],
                 *, ref_label: str = "") -> Result
```

**Method:** Pure membership check (`ref in target_index`) lifted to the
harness so every domain verifier shares one error format. No Z3 encoding
needed; the harness wraps it in the unified `Result` type. `ref_label` is an
optional human-readable label used in error messages.

**Replaces:**
- `studio_verify` command.required_role → role index lookup (ADV-003)
- `studio_verify` hook.event → ALLOWED_HOOK_EVENTS set membership (ADV-003)
- `evolution_verify` cross-ref integrity — evolution_run refs must resolve (ADV-004)
- `evolution_verify` constraint ref integrity — evolution_target constraint refs must resolve (ADV-004)
- `agent_verify` gateway.agent_ref → agents dict, gateway platforms → platforms dict (ADV-005)
- `agent_verify` cron.agent_ref and cron.platform_delivery lookups (ADV-005)
- `agent_verify` agent.model_ref → model_configs, backend refs → execution_backends (ADV-005)
- `visual_verify` visual_review.target → diagram/preview/screenshot index (ADV-006)
- `visual_verify` diagram.type ∈ VALID_DIAGRAM_TYPES (ADV-006)
- `visual_verify` render format ∈ VALID_RENDER_FORMATS (ADV-006)
- `graph_verify.check_no_dangling_edges` — edge source/target → nodes dict (ADV-002)

---

## Domain Verifier → Canonical Passes

| domain_verifier | dag_acyclicity | opaque_primitive | numeric_interval | reference_exists | residue |
|----------------|---------------|-----------------|-----------------|-----------------|---------|
| ark_verify | — | OPAQUE_PRIMITIVES table + apply_opaque | $data bounds check | — | SymbolTable, NATIVE_PRIMITIVES, expression-body verification (stays as harness core) |
| expression_smt | — | PRIMITIVE_Z3 registry (opaque entries) | — | — | PRIMITIVE_Z3 native entries feed Codegen.Pipeline.PrimitiveRegistry |
| studio_verify | verify_escalation_acyclicity (role.escalates_to) | PASS_OPAQUE emission (any opaque primitive in rule constraints) | — | command.required_role lookup; hook.event ∈ ALLOWED_HOOK_EVENTS | rule-constraint SAT (Z3 satisfiability of user-written predicate); tool permission consistency |
| evolution_verify | — | PASS_OPAQUE emission | split_ratio sum-to-1; fitness_weight sum-to-1; tolerance ∈ (0,1]; iterations > 0; population_size > 0 | evolution_run cross-ref; constraint ref integrity | benchmark-gate tolerance semantics (domain-specific wrapper around numeric_interval) |
| agent_verify | model_config.fallback_to chain acyclicity | PASS_OPAQUE emission | cpu_cores > 0; memory_mb > 0; timeout_seconds > 0 | gateway.agent_ref; gateway platforms; cron.agent_ref; cron.platform_delivery; agent.model_ref; backend refs | skill-trigger overlap warning (pattern-matching heuristic, not SAT/interval) |
| visual_verify | visual_review.replaces_screenshot acyclicity | PASS_OPAQUE emission | width > 0; height > 0; scale > 0; annotation coords within viewport | visual_review.target → index; diagram.type ∈ VALID_DIAGRAM_TYPES; render format ∈ VALID_RENDER_FORMATS | — |
| graph_verify | check_no_inheritance_cycles (inherits edges) | — | — | check_no_dangling_edges (edge src/target → nodes) | check_all_modules_have_names (naming convention check, stays as plugin residue) |

---

## Domain-Specific Residue

The following checks are **not** subsumed by the four canonical passes. They
remain as domain-specific plugins registered with the unified harness.

### studio_verify residue

- **Rule-constraint SAT** — `studio_verify` checks that each rule's constraint
  expression is satisfiable (Z3 `sat` check on the user-authored predicate).
  This is a domain-specific satisfiability test, not a structural check
  expressible via `dag_acyclicity`, `numeric_interval`, or `reference_exists`.
  Stays as a plugin named `studio.rule_sat`.

- **Tool permission consistency** — verifies that no role declares an
  unauthorised tool. This is a set-membership check too specific to the studio
  permission model to generalise; stays as `studio.tool_permission`.

### agent_verify residue

- **Skill-trigger overlap warning** — warns when two active skills share a
  trigger pattern with overlapping priorities. This is a pattern-matching
  heuristic (string prefix/suffix comparison), not a SAT or interval check.
  Stays as `agent.skill_overlap_warn` (warning-only, not blocking).

### evolution_verify residue

- **Benchmark-gate tolerance semantics** — benchmark-gate `tolerance` has a
  domain-specific meaning (a threshold for acceptable regression, not a
  generic numeric bound). The bounds check delegates to `numeric_interval`
  for the ∈ (0, 1.0] constraint, but the semantics of what `tolerance` means
  in evaluation context stays wrapped in `evolution.benchmark_gate_tolerance`.

### graph_verify residue

- **Module naming convention** — `check_all_modules_have_names` verifies that
  every node in the code graph has a non-empty name string. Stays as
  `graph.module_names` (pure structural check, no domain logic, but too
  graph-specific to add to the shared pass set).

---

## Codegen Emitter Catalog

The following canonical target keys are defined for `Codegen.Pipeline` emitters
in v1. Every target listed here corresponds to at least one domain codegen
module that transitions to `MERGE-INTO-HARNESS`.

**Target-language emitters (from `ark_codegen`):**
- `rust` — Rust source (AoS + SoA batch structs, process bodies)
- `cpp` — C++ / Unreal Engine 5 USTRUCT
- `proto` — Protobuf schema

**Configuration-artefact emitters:**

| target key | producing module | artefact description |
|-----------|-----------------|---------------------|
| `claude-agent-md` | studio_codegen | Claude subagent markdown from role items |
| `claude-command-md` | studio_codegen | Claude command definition markdown |
| `hooks-json` | studio_codegen | Hook event configuration JSON |
| `jsonl-dataset` | evolution_codegen | Evaluation dataset in JSONL format |
| `python-scorer-skeleton` | evolution_codegen | scorer.py skeleton for fitness functions |
| `run-config-json` | evolution_codegen | Evolution run configuration JSON |
| `report-md` | evolution_codegen | Evolution results report markdown |
| `agent-yaml` | agent_codegen | Agent configuration YAML |
| `cron-entry` | agent_codegen | Crontab entry for scheduled agent tasks |
| `skill-md` | agent_codegen | skills.md capability manifest |
| `docker-compose` | agent_codegen | docker-compose.agent.yaml |
| `mermaid` | visual_codegen | Mermaid diagram source |
| `html-preview` | visual_codegen | HTML diagram preview |
| `annotation-overlay-json` | visual_codegen | Annotation overlay JSON |
| `review-shell` | visual_codegen | Review automation shell script |
| `catalog-index-html` | visual_codegen | Visual catalog index HTML |

---

## Dedup Coverage

This section proves that every builder-bucket dedup row from
`research/deduplication-matrix.md` is cited at least once across the module
verdicts table above.

| dedup row | canonical form | delta rows that cite it |
|-----------|---------------|------------------------|
| dedup:1 | DAG acyclicity via Z3 ordinals (ADV-003 + ADV-006; canonical `verify.dag_acyclicity`) | `studio_verify` (dedup:1), `visual_verify` (dedup:1), `graph_verify` (dedup:1) |
| dedup:2 | Dual Lark+Pest grammar parity (descriptor bucket; surfaces in codegen via `expression_primitives`) | `expression_primitives` (dedup:2) |
| dedup:4 | PASS_OPAQUE Z3 pattern (ADV-002/003/004/006/008; canonical `verify.opaque_primitive`) | `ark_verify` (dedup:4), `expression_smt` (dedup:4), `studio_verify` (dedup:4) |
| dedup:6 | Skill definitions (ADV-003/004/005; single Skill struct + skill_manager) | `studio_codegen` (dedup:6), `agent_codegen` (dedup:6) |
| dedup:8 | Domain verify+codegen module pair pattern (ADV-003 named; ADV-004/005/006 implement) | `studio_verify` (dedup:8), `evolution_verify` (dedup:8), `agent_verify` (dedup:8), `visual_verify` (dedup:8), `studio_codegen` (dedup:8), `evolution_codegen` (dedup:8), `agent_codegen` (dedup:8), `visual_codegen` (dedup:8) |

All five builder-bucket dedup rows are accounted for. The four rows named in
the task design as mandatory (`dedup:1`, `dedup:2`, `dedup:4`, `dedup:6`) are
each cited by at least one delta row, satisfying the `## Dedup Coverage`
requirement. Row `dedup:8` (domain verify+codegen pair pattern) is additionally
cited across all eight domain-pair modules.
