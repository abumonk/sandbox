# Controller Delta Report

**Adventure:** ADV-011 Ark Core Unification  
**Produced by:** core-synthesist  
**Source design:** `designs/design-unified-controller.md`  
**Date:** 2026-04-15

---

## 1. Purpose and scope

This report classifies every controller-adjacent module under `ark/tools/agent/`, `ark/tools/evolution/`, `ark/tools/visual/review_loop.py`, and the designed-but-not-yet-implemented `.agent/telemetry/*` tree from ADV-010 using a `KEEP | MERGE | RETIRE` verdict. It enumerates the seven unified controller subsystems with source citations, specifies the single event bus and its fourteen event kinds, specifies the three-lane state model, commits to reflexive-dogfooding as the in-repo validation practice, and records the exact merge mechanics that absorb ADV-010's telemetry capture into the controller spine.

The controller is the runtime tier: it runs, observes, and adapts a built system at execution time. It never modifies the descriptor (user-authored schemas) or the builder (verification and codegen pipelines). The unified design collapses what were seven loosely coupled Python modules in `ark/tools/agent/` and six in `ark/tools/evolution/` — plus the designed telemetry subsystem from ADV-010 — into a single `ark/tools/controller/` package with named subsystems, a shared event bus, and append-only state surfaces.

Note on `.agent/telemetry/*` rows: the `.py` files for `capture.py`, `schema.py`, `cost_model.py`, `aggregator.py`, `task_actuals.py`, `tools/backfill.py`, and `tools/reconstructors/*.py` do **not yet exist on disk**. ADV-010 specifies these modules in its design documents and schemas; this report cites those design files as the authoritative source and records the intended post-unification location so that when ADV-010 implementation lands it is born inside the unified controller, not beside it.

---

## 2. Seven unified subsystems

### 2.1 Gateway

The **gateway** subsystem is the single multi-platform message ingress point for the controller. It routes incoming messages from terminal, Docker, and (eventually) external adapters to the skill-first dispatch chain. Its source is `ark/tools/agent/gateway.py` (ADV-005), which established the `GatewayRoute` struct and platform enum. In the unified design, platform adapters become plugins registered against the gateway at startup; the gateway itself remains a thin router with no business logic. Telegram, Discord, and Slack adapters are deferred to a downstream adventure and are explicitly out of scope for this unification.

### 2.2 Skill-manager

The **skill**-manager subsystem owns the canonical `Skill` struct, all skill CRUD operations, trigger matching against incoming messages, and the improvement history log. Its primary source is `ark/tools/agent/skill_manager.py` (ADV-005), with skill struct schema from ADV-003 (`struct Skill` in `studio.ark`) and skill evolution methods from ADV-004. In the unified design, skill generation (originating from the learning engine in ADV-005) and skill evolution (originating from the optimizer in ADV-004) become two methods on the same manager — `generate_skill()` and `evolve_skill()` — rather than separate runtimes. The `learning.py` module's session memory logic splits off into a controller `memory.py`; its skill-generation method folds into the skill-manager.

### 2.3 Scheduler

The **scheduler** subsystem is the sole cron and queue owner for the controller. Its source is `ark/tools/agent/scheduler.py` (ADV-005), which provides the `CronSchedule` struct and `CronTask` item kind. In the unified design, the evolution loop (previously a standalone runner in ADV-004) registers as a scheduler entry; the review loop's human-wait phase also registers as a resumable scheduler entry. No other subsystem may own a timer or queue; all periodic or deferred work goes through the scheduler. This is the mechanism by which the controller becomes a single-loop runtime rather than a collection of parallel processes.

### 2.4 Evaluator

The **evaluator** subsystem composes fitness scoring, constraint checking, and benchmark gating into a single ordered pipeline using the LLM-as-judge callback pattern established in ADV-004. Its sources are `ark/tools/evolution/fitness.py` (ADV-004) and `ark/tools/evolution/constraint_checker.py` (ADV-004). The pipeline runs: `fitness_scorer → constraint_checker → benchmark_gate`, each stage returning a typed result. The evaluator does not own the optimizer or the dataset builder; it owns only the scoring and gating logic. Domain-specific rubric dimensions are expressed as `RubricDimension` structs from the evolution descriptor; the evaluator receives them as configuration, not as hardcoded logic.

### 2.5 Evolution

The **evolution** loop runs as an `EvolutionRunner` driven by the scheduler, consuming `Item::EvolutionTarget`, `Item::EvalDataset`, and `Item::Optimizer` descriptor items. Its sources are `ark/tools/evolution/evolution_runner.py` (ADV-004), `ark/tools/evolution/optimizer.py` (ADV-004), and `ark/tools/evolution/dataset_builder.py` (ADV-004). The `EvolutionRunner` calls the evaluator pipeline for each variant, feeds results to the optimizer (GEPA/MIPROv2/Darwinian engines), and writes `evolution.started` and `evolution.converged` events to the event bus. It does not run as a parallel runtime; it is a scheduler-driven task that yields between iterations so the scheduler can interleave other work.

### 2.6 Telemetry

The **telemetry** subsystem is hook-driven capture combined with cost model, aggregator, and backfill tooling, all owned inside the controller (not as a sibling package). Its design sources are ADV-010's `design-capture-contract.md`, `design-cost-model.md`, `design-hook-integration.md`, `design-aggregation-rules.md`, `design-backfill-strategy.md`, `design-error-isolation.md`, and schemas `event_payload.md` and `row_schema.md`. The `SubagentStop` and `PostToolUse` hook commands remain `python .agent/telemetry/capture.py` for back-compat, but that script becomes a thin wrapper that publishes `subagent.stopped` or `artefact.written` to the controller's event bus. The row-writer, cost lookup, and aggregator pass are event-bus subscribers — not direct hook side-effects. See §6 for the full merge mechanics.

### 2.7 Review

The **review** loop is the human-in-the-loop gate that blocks the scheduler on a pending review request, presents a rendered diagram or artefact to a human reviewer, collects structured feedback, and resumes the scheduler on approval. Its source is `ark/tools/visual/review_loop.py` (ADV-006). In the unified design, the review loop relocates to `ark/tools/controller/review_loop.py`; UI renderers (mermaid renderer, screenshot manager, HTML previewer) are called by the review loop as output formatters but are not themselves controller components. The review loop emits `review.requested` and `review.completed` events to the event bus so that the telemetry subsystem can capture review-gate latency.

---

## 3. Module verdict table

Verdict enum: `KEEP` = survives unchanged in unified structure. `MERGE` = folds into another module with rename. `RETIRE` = removed; capability subsumed elsewhere or dropped per pruning catalog.

Note: `.agent/telemetry/*` rows cite ADV-010 design documents as source because the `.py` files do not yet exist on disk at the time of writing.

| Module path | Source ADV | Subsystem | Verdict | Target location | Rationale | Dedup ref |
|---|---|---|---|---|---|---|
| `ark/tools/agent/__init__.py` | ADV-005 | controller spine | MERGE | `ark/tools/controller/__init__.py` | Package rename: `tools/agent` → `tools/controller`; re-exports updated | — |
| `ark/tools/agent/agent_runner.py` | ADV-005 | controller spine | MERGE | `ark/tools/controller/controller.py` | Renamed to `controller.py`; becomes the `Controller` dataclass owning all injected subsystems | dedup-row-7 (Runtime orchestrator pattern) |
| `ark/tools/agent/gateway.py` | ADV-005 | gateway | KEEP | `ark/tools/controller/gateway.py` | Stays as Gateway subsystem; platform adapters become registered plugins | — |
| `ark/tools/agent/backend.py` | ADV-005 | scheduler | KEEP | `ark/tools/controller/backend.py` | Execution backend stays; now injected into Scheduler instead of AgentRunner directly | — |
| `ark/tools/agent/skill_manager.py` | ADV-005 | skill-manager | KEEP | `ark/tools/controller/skill_manager.py` | Canonical Skill struct owner; skill-generation and skill-evolution become methods here | dedup-row-6 (Skill definitions) |
| `ark/tools/agent/scheduler.py` | ADV-005 | scheduler | KEEP | `ark/tools/controller/scheduler.py` | Single Scheduler; absorbs evolution-run and review-wait registration | dedup-row-3 (canonical scheduler) |
| `ark/tools/agent/learning.py` | ADV-005 | skill-manager / memory | MERGE | split: session memory → `ark/tools/controller/memory.py`; skill-generation method → `ark/tools/controller/skill_manager.py` | Module split: session memory logic extracted to `memory.py`; skill-generation method folds into skill-manager | — |
| `ark/tools/evolution/__init__.py` | ADV-004 | evolution | MERGE | `ark/tools/controller/evolution/__init__.py` | Evolution sub-package relocates under controller; package init updated | — |
| `ark/tools/evolution/evolution_runner.py` | ADV-004 | evolution | KEEP | `ark/tools/controller/evolution/evolution_runner.py` | Becomes Scheduler-driven task inside controller; lifecycle interface extracted | dedup-row-7 (Runtime orchestrator pattern) |
| `ark/tools/evolution/fitness.py` | ADV-004 | evaluator | MERGE | `ark/tools/controller/evaluator.py` | Folds into unified Evaluator pipeline as first stage; LLM-as-judge callback retained | — |
| `ark/tools/evolution/constraint_checker.py` | ADV-004 | evaluator | MERGE | `ark/tools/controller/evaluator.py` | Folds into unified Evaluator pipeline as second stage | — |
| `ark/tools/evolution/optimizer.py` | ADV-004 | evolution | KEEP | `ark/tools/controller/evolution/optimizer.py` | GEPA/MIPROv2/Darwinian engines remain; called from Evaluator + EvolutionRunner | — |
| `ark/tools/evolution/dataset_builder.py` | ADV-004 | evolution | KEEP | `ark/tools/controller/evolution/dataset_builder.py` | Utility; stays under evolution/ sub-package | — |
| `ark/tools/visual/review_loop.py` | ADV-006 | review | MERGE | `ark/tools/controller/review_loop.py` | Relocates to controller package; renderers (mermaid, screenshot) stay out per pruning catalog | dedup-row-7 (Runtime orchestrator pattern) |
| `.agent/telemetry/capture.py` (designed in ADV-010) | ADV-010 | telemetry | MERGE | becomes controller event-bus subscriber (see §6); hook entrypoint remains `python .agent/telemetry/capture.py` for back-compat | Thin wrapper publishes `subagent.stopped`; row-write logic moves to bus subscriber | dedup-row-3b (canonical telemetry surface) |
| `.agent/telemetry/schema.py` (designed in ADV-010) | ADV-010 | telemetry | KEEP | `.agent/telemetry/schema.py` | `SubagentEvent` + `MetricsRow` dataclasses unchanged; imported by controller subscriber | dedup-row-3b (canonical telemetry surface) |
| `.agent/telemetry/cost_model.py` (designed in ADV-010) | ADV-010 | telemetry | KEEP | `.agent/telemetry/cost_model.py` | Pure rates table; called by the telemetry subscriber as a plain function | dedup-row-3b (canonical telemetry surface) |
| `.agent/telemetry/aggregator.py` (designed in ADV-010) | ADV-010 | telemetry | KEEP | `.agent/telemetry/aggregator.py` | Triggered by controller after every event write; no structural change | dedup-row-3b (canonical telemetry surface) |
| `.agent/telemetry/task_actuals.py` (designed in ADV-010) | ADV-010 | telemetry | KEEP | `.agent/telemetry/task_actuals.py` | Triggered by controller on `task.completed` event | dedup-row-3b (canonical telemetry surface) |
| `.agent/telemetry/tools/backfill.py` (designed in ADV-010) | ADV-010 | telemetry | KEEP | `.agent/telemetry/tools/backfill.py` | Stays as an offline CLI consumer of the event log; does not join the event bus | dedup-row-3b (canonical telemetry surface) |
| `.agent/telemetry/tools/reconstructors/*.py` (designed in ADV-010) | ADV-010 | telemetry | KEEP | `.agent/telemetry/tools/reconstructors/*.py` | Offline-only; unchanged; consumed by backfill.py | dedup-row-3b (canonical telemetry surface) |

---

## 4. Event bus — event kinds

The controller maintains one process-wide in-memory event bus with an append-only jsonl mirror at `.agent/events.log` (per pattern "Append-only jsonl for multi-writer state" from ADV-007). The bus is the single integration point: no subsystem may read another subsystem's internal state to learn about things; it must subscribe to an event kind.

Every event carries the common envelope:

```json
{
  "event_kind": "<kind>",
  "adventure_id": "<string>",
  "task_id": "<string|null>",
  "agent": "<string>",
  "ts": "<iso8601>",
  "session_id": "<string|null>",
  "payload": {}
}
```

The fourteen enumerated event kinds are:

1. `task.created` — emitted by the controller spine when a new task enters the pipeline
2. `task.completed` — emitted when a task reaches `status: done`
3. `task.failed` — emitted when a task reaches a terminal failure state
4. `artefact.written` — emitted by the `PostToolUse` hook wrapper when a file is written (payload: `{path, sha256, size_bytes}`)
5. `subagent.started` — emitted when a subagent process begins (from `SubagentStart` hook if present, or scheduler dispatch)
6. `subagent.stopped` — emitted by the `SubagentStop` hook wrapper; payload matches `SubagentEvent` from ADV-010 `schemas/event_payload.md`
7. `skill.triggered` — emitted by the skill-manager when an incoming message matches a trigger
8. `skill.generated` — emitted when the skill-manager's `generate_skill()` method produces a new skill
9. `skill.improved` — emitted when the skill-manager's `evolve_skill()` method records an improvement entry
10. `evolution.started` — emitted by `EvolutionRunner` at the beginning of an optimization run
11. `evolution.converged` — emitted by `EvolutionRunner` when the optimizer reports convergence or max-iterations is reached
12. `review.requested` — emitted by the review loop when it presents an artefact for human feedback
13. `review.completed` — emitted by the review loop when the human approves or rejects; payload includes `{status: approved|rejected, feedback_text}`
14. `scheduler.tick` — emitted on each scheduler cron cycle; allows telemetry and logging to record heartbeat without polling

Subscribers by event kind:

| Subscriber | Event kinds consumed |
|---|---|
| Telemetry capturer | `subagent.stopped`, `artefact.written`, `task.completed`, `task.failed` |
| Scheduler | `review.completed` (to resume blocked task), `evolution.converged` (to deregister run entry) |
| Skill-manager improvement hook | `skill.improved` (to persist improvement entry to memory) |
| Review loop | `task.completed` (to trigger review gate if task has pending review) |
| Adventure log writer | all 14 kinds (append one line per event to `adventure.log`) |

---

## 5. State model — three lanes

The controller commits to exactly three persistent state surfaces. No in-place rewrites. No shared mutable state between subsystems. All rendered markdown views (metrics.md, adventure.log) are regenerable from the event log.

| Lane | File / location | Shape | Writer | Readers |
|---|---|---|---|---|
| Persistent memory | `ark/tools/controller/memory/*.json` (from ADV-005 `learning.py` split) | append-only JSON session entries and generated skill objects; one file per adventure or session | skill-manager (`generate_skill`, `evolve_skill`), memory split from `learning.py` | controller spine (on startup load), skill-manager (trigger matching), review loop (session context) |
| Metrics rows | `.agent/adventures/{ADV-ID}/metrics.md` (ADV-010 `schemas/row_schema.md`) | pipe-table append-only; one row per subagent run; frontmatter totals recomputed by aggregator | telemetry subsystem (via `subagent.stopped` subscriber) | aggregator, cost review dashboard, backfill CLI, human reviewers |
| Adventure log | `.agent/adventures/{ADV-ID}/adventure.log` | one line per step, append-only; format `[{ts}] {role} | "{message}"` | every agent role (all 14 event kinds trigger a log line); backfill reads for reconstruction | humans, backfill CLI, downstream adventure planners |

The event log mirror at `.agent/events.log` is a fourth file but is ephemeral infrastructure (the jsonl source-of-truth from which the three lanes above are derived or validated). It is not a state lane itself.

---

## 6. ADV-010 telemetry merge mechanics

This section specifies how ADV-010's telemetry capture is absorbed into the controller spine. The core commitment: **telemetry is inside the controller, not a sibling package**. The six mechanics are:

**1. Hook ingress stays declarative.**  
The `SubagentStop` and `PostToolUse` hooks defined in `.claude/settings.local.json` per ADV-010 `design-hook-integration.md` remain the trigger. Their command stays `python .agent/telemetry/capture.py` for back-compat so that `.claude/settings.local.json` requires no changes. The `capture.py` entrypoint becomes a thin wrapper that parses the hook payload, constructs a `SubagentEvent`, and publishes `subagent.stopped` (or `artefact.written` for `PostToolUse`) to the controller's event bus — then returns immediately without writing any files directly.

**2. Capture becomes a subscriber.**  
The row-writer logic specified in ADV-010 `design-capture-contract.md` — the `SubagentEvent → MetricsRow → cost lookup → idempotent append` pipeline — becomes an event-bus subscriber registered on `subagent.stopped`. Idempotency via Run ID (`sha1(adventure_id|agent|task|model|timestamp|session_id)`) is enforced at the subscriber, not at the hook. This means the hook is stateless and can be invoked multiple times safely.

**3. Cost model and aggregator are controller services.**  
`cost_model.cost_for(model, tokens_in, tokens_out)` from ADV-010 `design-cost-model.md` and the aggregator pass from ADV-010 `design-aggregation-rules.md` are plain functions called by the `subagent.stopped` subscriber after appending the row. They are not parallel processes. The cost model is a pure lookup table; the aggregator rewrites the frontmatter totals in `metrics.md` atomically using the pattern from `design-aggregation-rules.md`.

**4. Backfill stays offline.**  
The `backfill.py` tool specified in ADV-010 `design-backfill-strategy.md` remains a human-invoked CLI. It reads `adventure.log`, git history, and existing rows to reconstruct missing telemetry entries. It does not subscribe to the event bus; it writes to `metrics.md.new` with the `Confidence` column set to `medium`, `low`, or `estimated` depending on reconstruction fidelity. Hook-written rows keep `Confidence: high`. The offline nature of `backfill.py` is a design invariant from ADV-010 `design-backfill-strategy.md` and must not be changed when the controller is implemented.

**5. Error isolation preserved.**  
The `capture.py` wrapper keeps the exit-0-on-failure guarantee from ADV-010 `design-error-isolation.md`. Any exception inside the controller's `subagent.stopped` subscriber is caught, written to a `metrics-capture-error` entry in `metrics.md` per `design-error-isolation.md`, and swallowed before returning to the hook. A controller-internal failure must never propagate back through the Claude Code hook mechanism and interrupt an agent run.

**6. Schema imports.**  
The `SubagentEvent` dataclass from ADV-010 `schemas/event_payload.md` is the canonical shape for the `subagent.stopped` event payload inside the controller. The `MetricsRow` dataclass from ADV-010 `schemas/row_schema.md` is the canonical shape for the appended row. No second shape for either. All controller telemetry code imports from `.agent/telemetry/schema.py` which re-exports both dataclasses.

**ADV-010 design file citations summary:**

| Citation | Role in merge |
|---|---|
| ADV-010 `design-capture-contract.md` | Row-writer logic → event-bus subscriber |
| ADV-010 `design-hook-integration.md` | Hook command stays `python .agent/telemetry/capture.py`; `.claude/settings.local.json` unchanged |
| ADV-010 `design-cost-model.md` | Cost lookup called by subscriber as plain function |
| ADV-010 `design-aggregation-rules.md` | Aggregator pass called by subscriber after row append |
| ADV-010 `design-backfill-strategy.md` | Backfill stays offline CLI; not on event bus |
| ADV-010 `design-error-isolation.md` | Exit-0 guarantee preserved in `capture.py` wrapper |
| ADV-010 `schemas/event_payload.md` | `SubagentEvent` dataclass = canonical `subagent.stopped` payload |
| ADV-010 `schemas/row_schema.md` | `MetricsRow` dataclass = canonical append shape |

---

## 7. Reflexive-dogfooding validation practice

> The controller's first consumer is Ark itself. Every subsystem is validated by running it over an in-repo artefact before any external consumer is considered: Scheduler drives `.agent/adventures/*` task progression; EvolutionRunner evolves `.agent/roles/*.md` prompts; Evaluator scores generated Ark specs; Telemetry captures this very adventure's runs into `.agent/adventures/ADV-011/metrics.md`; Review loop gates the unified-controller design itself. This is a *validation practice*, not a subsystem — it is how we know the design survives contact with a real consumer before we cut a downstream adventure.

This practice is documented as a recurring pattern across ADV-002 (reflexive self-indexing over 771 nodes), ADV-004 (`evolution_skills.ark` consumed at runtime by the evolution subsystem), ADV-005 (`hermes_skills.ark` consumed at runtime by the agent runner), and ADV-008 (shape grammar sibling package). The deduplication matrix (row: "Reflexive dogfooding practice") confirms this is an intentional technique, not accidental duplication, and assigns its canonical form as the `controller` bucket.

Validation checklist — every subsystem must satisfy at least one item:

- [ ] Subsystem has been exercised over an in-repo artefact during this adventure.
- [ ] That exercise produced an observable side-effect (a row, a log line, a file).
- [ ] The side-effect is the same shape it will produce for an external consumer.

Subsystem-to-dogfood target mapping:

| Subsystem | In-repo dogfood target | Expected side-effect |
|---|---|---|
| Gateway | terminal input during adventure task execution | message routed to skill-first dispatch |
| Skill-manager | `.agent/roles/*.md` skill definitions | trigger matched, `skill.triggered` event emitted |
| Scheduler | `.agent/adventures/ADV-011/tasks/*.md` task queue | `scheduler.tick` events, task progression |
| Evaluator | generated Ark spec documents (descriptor/builder deltas) | fitness score row appended to evaluation log |
| Evolution | `.agent/roles/*.md` prompt variants | `evolution.started` + `evolution.converged` events |
| Telemetry | ADV-011 adventure runs | rows appended to `.agent/adventures/ADV-011/metrics.md` |
| Review | unified-controller design documents | `review.requested` + `review.completed` events |

---

## 8. Controller-bucket dedup row citations

Every row in `research/deduplication-matrix.md` with `assigned_bucket = controller` is cited below. Each citation records the row's canonical form and the controller subsystem that consumes it.

From the deduplication matrix:

- **dedup-row-3 (Telemetry / metrics capture):** canonical form `tools/telemetry/capture.py + cost_model + aggregator trio (ADV-010)` — consumed by the **telemetry** subsystem. Unification action: retire per-adventure "unsolved telemetry" placeholders; adopt ADV-010 `capture.py` as the single runtime hook. Source ADVs: ADV-001, ADV-002, ADV-005, ADV-006, ADV-010.

- **dedup-row-5 (Reflexive dogfooding practice):** canonical form `recurring practice — "validation-by-consumption" technique cited in controller design; no shared symbol required; dogfood is the pattern keyword` — consumed by the **controller design** as a documented validation practice (§7 of this report). Unification action: document as recurring practice in the controller unified design; no code consolidation. Source ADVs: ADV-002, ADV-004, ADV-005, ADV-008.

- **dedup-row-6 (Skill definitions):** canonical form `single Skill struct in descriptor + single skill_manager runtime in controller` — consumed by the **skill-manager** subsystem. Unification action: collapse three skill representations (ADV-003 `struct Skill`, ADV-004 `Item::EvolutionTarget` over skills, ADV-005 `Item::Skill` DSL item + `skill_manager` runtime) into one descriptor struct consumed by the unified controller's skill-manager. Source ADVs: ADV-003, ADV-004, ADV-005.

- **dedup-row-7 (Runtime orchestrator pattern):** canonical form `domain_runtime_runner — per-domain orchestrator following a common lifecycle interface` — consumed by the **evolution**, **review**, and **controller spine** subsystems. Unification action: extract a shared orchestrator lifecycle interface (`run/observe/stop`) implemented by `EvolutionRunner`, `review_loop`, and the `Controller` itself. Source ADVs: ADV-004, ADV-005, ADV-006.

Canonical scheduler (from concept-mapping.md controller rows, not a dedup matrix row but a distinct controller concept):
- **scheduler (ADV-005):** `ark/tools/agent/scheduler.py` — consumed by the **scheduler** subsystem. The deduplication matrix does not record the scheduler as a duplicate because it has a single source (ADV-005); however the concept-mapping.md confirms its bucket as `controller` and the verdict table (§3) records its KEEP verdict.

Concept-mapping.md controller-bucket rows not in the dedup matrix (single-source concepts, no duplication, but relevant to verify completeness):
- `AgentRunner` (ADV-005) → controller spine (§3: `agent_runner.py` MERGE → `controller.py`)
- `gateway_module` (ADV-005) → gateway subsystem (§3: `gateway.py` KEEP)
- `skill_manager` (ADV-005) → skill-manager subsystem (§3: `skill_manager.py` KEEP)
- `learning_engine` (ADV-005) → memory split (§3: `learning.py` MERGE)
- `execution_backend` (ADV-005) → scheduler (§3: `backend.py` KEEP)
- `evolution_runner` (ADV-004) → evolution subsystem (§3: `evolution_runner.py` KEEP)
- `review_loop` (ADV-006) → review subsystem (§3: `review_loop.py` MERGE)
- All ADV-010 telemetry concepts → telemetry subsystem (§3, §6)

---

## 9. Boundary notes (what is NOT in the controller)

The following items are explicitly excluded from the controller. Each line points at the pruning catalog row or design document that owns the disposition.

- **Mermaid rendering, screenshot manager, HTML previewer** — these are output formatters, not runtime orchestrators. Disposition: pruning catalog (UI renderers, `out-of-scope` forward reference to ADV-UI). The review loop *calls* these renderers; it does not own or subsume them. Source: concept-mapping.md rows `mermaid_renderer`, `html_previewer`, `annotator` (bucket: builder).

- **Telegram / Discord / Slack gateway adapters** — platform adapters for external messaging platforms. Disposition: deferred to a downstream adventure (noted in design-unified-controller.md §2 Gateway, and pruning catalog). The gateway subsystem's plugin slot is reserved for these but they are not implemented in this unification.

- **Hermes speculative evolution modes** — speculative optimizer extensions and Hermes-specific evolution loops referenced in ADV-007 phase documents. Disposition: pruning catalog (ADV-007 ecosystem artefacts, `OUT-OF-SCOPE -> ADV-007`). These are not ADV-004/ADV-005 evolution concepts; they are phase-5 speculative items.

- **ADV-007 ecosystem roadmap items** — synthesis matrices, MCP tier catalogues, interaction matrices, phase-by-phase research documents, UI architecture studies, and operational model artefacts from ADV-007. Disposition: out-of-scope by manifest (concept-mapping.md, 33 rows tagged `OUT-OF-SCOPE -> ADV-007`). None of these land in the controller.

- **Descriptor and builder internals** — the controller reads builder outputs (generated code, verified AST) and descriptor schemas (event payload shape, skill struct). It never modifies the descriptor or the builder. Z3 verification passes, codegen modules, and grammar rules are builder concerns. The boundary is stated in design-unified-controller.md §6.

- **Static analysis and code indexing tools** — `CodeIndexer`, `QueryEngine`, `GraphStore`, `Watcher` from ADV-002. These are builder-tier tools that analyse descriptor graphs; they are not runtime execution surfaces. Disposition: builder bucket (concept-mapping.md rows).

- **MCP query surface** — external MCP tooling. Disposition: `OUT-OF-SCOPE -> ADV-007` (concept-mapping.md row `mcp_query_surface`).
