# Ark Pipeline Spec (Sibling Package) — Design

## Overview

Model the adventure pipeline (adventures, phases, waves, tasks, documents,
decisions, target conditions, agents, roles, permissions) as a first-class
Ark spec, and provide a Python IR extractor that lifts a live
`.agent/adventures/ADV-NNN/` directory into that spec's entity shapes.

Follows the exact pattern established by ADV-008: a **sibling package** to
`ark/`, never editing Ark itself. Ark stays domain-neutral; the pipeline
domain is expressed in vanilla Ark syntax (abstractions, classes, islands,
processes — no grammar changes).

## Target Files (T015 scope — this design)

- `R:/Sandbox/adventure_pipeline/__init__.py` — package marker (empty)
- `R:/Sandbox/adventure_pipeline/README.md` — 1-page package overview + "Deferred invariants" placeholder
- `R:/Sandbox/adventure_pipeline/specs/adventure.ark` — entity declarations
- `R:/Sandbox/adventure_pipeline/specs/pipeline.ark` — process declarations
  (state machine, task lifecycle, review pipeline)
- `R:/Sandbox/adventure_pipeline/specs/entities.ark` — runtime entities
  (RunningAgent, ActiveTask, PendingDecision, KnowledgeSuggestion,
  ReviewArtifact)
- `R:/Sandbox/adventure_pipeline/specs/verify/state_transitions.ark`
- `R:/Sandbox/adventure_pipeline/specs/verify/permission_coverage.ark`
- `R:/Sandbox/adventure_pipeline/specs/verify/tc_traceability.ark`

## Target Files (later tasks — referenced, NOT in T015)

- `R:/Sandbox/adventure_pipeline/tools/*` — IR extractor (T016)
- `R:/Sandbox/adventure_pipeline/tests/*` — round-trip tests (T016)

**Ark files that are explicitly NOT touched**: anything under
`R:/Sandbox/ark/`. If the vanilla Ark grammar/verifier cannot express a
desired constraint, log it in the package README and continue — we do
not patch Ark.

## Approach

### 1. Entity shapes (`adventure.ark`)

Declare, in vanilla Ark syntax (following `shape_grammar/specs/shape_grammar.ark`
and `ark/specs/pipeline/team/*.ark` precedents):

- `abstraction Adventure` — `id: String, title: String, state: State, tasks[]: Task, documents[]: Document, decisions[]: Decision, tcs[]: TargetCondition, phases[]: Phase`.
- `class Phase` — `name: String, waves[]: Wave`.
- `class Wave` — `index: Int, tasks[]: Task`.
- `abstraction Task` — `id: String, title: String, status: Status, depends_on[]: String, target_conditions[]: String, files[]: String, role: Role`.
- `abstraction Document` — base with subtypes via `kind: DocKind` enum `{ design, plan, research, review }`.
- `class Design : Document`, `class Plan : Document`, `class Research : Document`, `class Review : Document`.
- `class TargetCondition` — `id: String, description: String, proof_method: ProofMethod, proof_command: String, status: TCStatus, source: String, design: String, plan: String, tasks[]: String`.
- `class Decision` — `kind: DecisionKind, label: String, state_hint: String, route: String`.
- `class Permission` — `category: PermCategory, agent: String, scope: String, reason: String, tasks[]: String`.
- `class Agent` — `name: String, role: Role, permissions[]: Permission`.
- `class Role` — `name: String`.
- `enum State` — `concept | planning | review | active | blocked | completed | cancelled`.
- `enum Status` — `pending | in_progress | passed | failed | done`.
- `enum TCStatus` — `pending | passed | failed`.
- `enum ProofMethod` — `autotest | poc | manual`.
- `enum DecisionKind` — `approve_permissions | approve_design | state_transition | knowledge_suggestion`.
- `enum DocKind` — `design | plan | research | review`.
- `enum PermCategory` — `shell | file | mcp | external`.

### 2. Process shapes (`pipeline.ark`)

In vanilla Ark, "processes" are expressed as `class` entities whose
`#process[strategy: code]{}` block describes the lifecycle, with
invariants + `post` disjunctions enumerating legal next-states (mirrors
the `Task` / `Adventure` pattern in `ark/specs/pipeline/team/task.ark`
and `.../adventure.ark`). Three top-level classes:

- `class AdventureStateMachine` — field `state: State`; `#process` encoding
  transitions `concept → planning → review → active → (blocked | completed | cancelled)`
  and `blocked → active`. Temporal invariants: `completed` and `cancelled`
  are absorbing.
- `class TaskLifecycle` — field `status: Status`; `#process` encoding
  `pending → in_progress → (passed | failed) → done`; retry edge
  `failed → in_progress`.
- `class ReviewPipeline` — fields `design_approved: Bool, permissions_approved: Bool, plan_executed: Bool, artifact_emitted: Bool`;
  `#process` encoding the ordering
  `design_approved → permissions_approved → plan_executed → artifact_emitted`
  via `pre` guards.

### 3. Runtime entities (`entities.ark`)

- `class RunningAgent` — `name: String, task_id: String, started_at: Int`.
- `class ActiveTask` — `task_id: String, wave_index: Int, started_at: Int`.
- `class PendingDecision` — `decision_kind: DecisionKind, adventure_id: String, opened_at: Int`.
- `class KnowledgeSuggestion` — `kind: String, text: String, source_task: String`.
- `class ReviewArtifact` — `task_id: String, verdict: Verdict, issues: String, path: String`.
- `enum Verdict` — `PASSED | FAILED`.

Re-declare enums used by runtime entities at the top of `entities.ark`
(following `shape_grammar/specs/operations.ark` precedent: each file
verifies as a standalone Ark unit; cross-file unification happens at IR
time in T016).

### 4. Optional verifier passes (`specs/verify/*.ark`)

Three standalone `.ark` files under `adventure_pipeline/specs/verify/`:

- `state_transitions.ark` — re-declares `State` enum + a minimal
  `AdventureStateMachine` stub + `verify` block with invariants covering
  legality (absorbing terminal states, blocked-reentry).
- `permission_coverage.ark` — re-declares `Permission` + `Task` stubs +
  `verify` block: every Task has ≥1 Permission per assigned agent; every
  proof_command covered by shell permission.
- `tc_traceability.ark` — re-declares `TargetCondition` + `Task` stubs +
  `verify` block: every TC references an existing Task id; every Task
  references ≥1 TC.

If any invariant cannot be expressed in vanilla Ark syntax (e.g.
cross-file existential quantification), log it in
`adventure_pipeline/README.md` under "Deferred invariants" and skip —
**Ark is not patched**.

### 5. IR extractor (`tools/ir.py`) — T016, out of scope for T015

(Retained in design for context; implemented in ADV009-T016.)

## Dependencies

- Pattern precedent: `shape_grammar/` package from ADV-008 (same
  architectural layout).
- Consumed by: design-pipeline-graph-view (the Pipeline tab backend
  endpoint lifts its node/edge graph from the IR extractor).

## Affected existing tasks

Does **not** modify T001-T014. Calls out potential future edits:
- `server.py` (T003/T004) gains one new endpoint in the sibling plan, but
  that new endpoint is **its own new task** (see design-graph-backend-endpoints).
- No changes to existing designs, plans, or task definitions.

## Implementation Steps (T015)

Author the 8 files below. No Ark source under `ark/` is touched.

**Step 1 — package scaffolding**
1. Create empty `adventure_pipeline/__init__.py`.
2. Create `adventure_pipeline/README.md` with sections:
   `# adventure_pipeline`, `## Purpose` (one paragraph: sibling Ark spec
   package for the pipeline domain), `## Layout` (bulleted file tree),
   `## Usage` (`python ark/ark.py parse adventure_pipeline/specs/adventure.ark`
   + equivalents), `## Deferred invariants` (empty bullet placeholder +
   note "populated iff T017 finds Ark-inexpressible invariants").

**Step 2 — `specs/adventure.ark`** (core entity declarations)
1. Open with `import stdlib.types` (mirrors `shape_grammar.ark`).
2. Block-comment header describing file purpose and listing declared
   entities.
3. Declare enums first (top-level, so the verifier treats variants as
   background facts): `State`, `Status`, `TCStatus`, `ProofMethod`,
   `DecisionKind`, `DocKind`, `PermCategory`.
4. Declare `abstraction Adventure` with `@in{}`, `@out[]{}`, `invariant: true`
   and `$data` for id/title/state plus list-of-id fields (`tasks`,
   `documents`, `decisions`, `tcs`, `phases`) typed as `String` (JSON
   fan-out happens at IR time — Ark `[T]` list syntax is supported per
   stdlib.types precedent).
5. Declare `class Phase` (name, waves list), `class Wave` (index, tasks list).
6. Declare `abstraction Task` with fields id/title/status/depends_on/target_conditions/files/role.
7. Declare `abstraction Document` + four subclasses via `class Design : Document`
   etc. Each subclass carries `$data kind: DocKind = design` (literal
   default), following the `ExtrudeOp`/`SplitOp` pattern in
   `shape_grammar/specs/operations.ark`.
8. Declare `class TargetCondition`, `class Decision`, `class Permission`,
   `class Agent`, `class Role`.
9. Every `class`/`abstraction` gets a minimal `#process[strategy: code]{ description: "..." }`
   stub (required by parser for classes that declare state, per
   `SemanticLabel` precedent).

**Step 3 — `specs/pipeline.ark`** (state machine processes)
1. Open with `import stdlib.types`; re-declare enums `State` and `Status`
   at top (standalone parseability per shape_grammar precedent).
2. `class AdventureStateMachine` — `$data state: State = concept`;
   `#process[strategy: code, priority: 80]` with `description:`, a
   `post:` disjunction enumerating all enum variants, and a commented
   transition table. Add `invariant:` lines and `temporal: □((state == completed) → □(state == completed))`
   (absorbing terminal), same for `cancelled`.
3. `class TaskLifecycle` — `$data status: Status = pending`; `#process`
   with disjunctive `post:` over all Status variants; invariants
   `status == done → □(status == done)`.
4. `class ReviewPipeline` — four Bool fields plus a `#process` whose `pre:`
   guards enforce ordering (e.g. `pre: design_approved == true or permissions_approved == false`
   expressing "permissions_approved ⇒ design_approved"). Invariants
   repeat these orderings for the verifier.

**Step 4 — `specs/entities.ark`** (runtime observational snapshots)
1. Open with `import stdlib.types`; re-declare `DecisionKind` and
   `Verdict` enums at top (standalone parseability).
2. Declare `class RunningAgent`, `class ActiveTask`, `class PendingDecision`,
   `class KnowledgeSuggestion`, `class ReviewArtifact` — each with
   `$data` fields per §3 above and a minimal `#process[strategy: code]{ description: "..." }`
   stub.

**Step 5 — `specs/verify/state_transitions.ark`**
1. Re-declare `State` enum.
2. Re-declare minimal `class AdventureStateMachine` stub (only `state: State`).
3. `verify AdventureStateMachine { check terminal_absorbing: ...; check blocked_reentry_only_to_active: ...; }`
   mirroring the `verify TeamPipeline { check ... }` block at the bottom
   of `ark/specs/pipeline/team_pipeline.ark`.

**Step 6 — `specs/verify/permission_coverage.ark`**
1. Re-declare `Permission`, `Task`, `PermCategory` minimally.
2. `verify PermissionCoverage { check every_task_has_permission: for_all Task as t: ...; }`
   — note: cross-entity existential (`exists Permission as p: p.tasks contains t.id`)
   may exceed vanilla Ark; if parser rejects, drop that check and add an
   entry to README "Deferred invariants" (rationale: "Ark verify block
   lacks existential cross-entity quantifier; deferred to Python
   post-IR pass in T017").

**Step 7 — `specs/verify/tc_traceability.ark`**
1. Re-declare `TargetCondition`, `Task` minimally.
2. `verify TCTraceability { check tc_has_tasks: for_all TargetCondition as tc: ...; check task_has_tc: for_all Task as t: ...; }`
   — same deferral protocol as Step 6.

**Step 8 — Validate**
1. Run (manually, by the coder agent in T015 execution):
   - `python ark/ark.py parse adventure_pipeline/specs/adventure.ark` → exit 0.
   - `python ark/ark.py parse adventure_pipeline/specs/pipeline.ark` → exit 0.
   - `python ark/ark.py parse adventure_pipeline/specs/entities.ark` → exit 0.
2. Confirm `git diff ark/` is empty.
3. Record any parse failures in README "Deferred invariants" with
   rationale if they stem from Ark grammar limits; otherwise iterate
   until parse exits 0.

## Testing Strategy

- T015 passes iff all three `ark/ark.py parse` invocations in Step 8
  return exit 0.
- Declared-entity checks (acceptance criteria 4-6 on the task) verified
  by `grep`-ing the three spec files for the required identifiers.
- `ark/**` immutability verified by `git status -- ark/` showing no
  changes.
- IR round-trip tests (TC-042..TC-044) are T016's responsibility, not T015.
- Verifier-clean-or-deferred (TC-045) is T017's responsibility, not T015.

## Risks

- **Ark grammar rejection of list fields in `abstraction`** — stdlib uses
  `[T]` list syntax, but `abstraction` blocks historically accept only
  `@in/@out/invariant`. Mitigation: model list-of-id fields as `$data …: String`
  and JSON-serialize at IR time, mirroring `Task.repos_json: String = "[]"`
  in `ark/specs/pipeline/team/task.ark`.
- **Subclass syntax (`class Design : Document`)** — team/task.ark uses
  `class Task : WorkItem` and notes "наследование резолвится в рантайме".
  Parser accepts the syntax but semantic checks are lenient. Acceptable.
- **Re-declaration collisions** — enums declared in `adventure.ark` and
  again in `pipeline.ark` / `entities.ark`. Per shape_grammar precedent
  (`operations.ark` re-declares `Operation`), this is a documented
  idiom: each file parses standalone; IR extractor unifies by name.
- **`verify` block semantics for cross-entity quantifiers** — may fail
  to parse. Mitigation: README "Deferred invariants" protocol, zero Ark
  patches.
- **Russian-language comments in team/ precedent** — not adopted here;
  all comments in English for consistency with shape_grammar/.

## Target Conditions (T015 scope)

- TC-039 — `adventure_pipeline/specs/adventure.ark` parses cleanly.
- TC-040 — `adventure_pipeline/specs/pipeline.ark` declares all three
  processes (AdventureStateMachine, TaskLifecycle, ReviewPipeline) and
  parses cleanly.
- TC-041 — `adventure_pipeline/specs/entities.ark` declares the five
  runtime entities and parses cleanly.

## Target Conditions (deferred to later tasks)

- TC-042, TC-043, TC-044 — IR extractor round-trip (T016).
- TC-045 — Verifier clean-or-deferred (T017).
