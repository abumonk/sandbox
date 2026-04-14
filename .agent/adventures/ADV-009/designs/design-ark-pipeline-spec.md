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

## Target Files

- `R:/Sandbox/adventure_pipeline/specs/adventure.ark` — entity declarations
- `R:/Sandbox/adventure_pipeline/specs/pipeline.ark` — process declarations
  (state machine, task lifecycle, review pipeline)
- `R:/Sandbox/adventure_pipeline/specs/entities.ark` — runtime entities
  (RunningAgent, ActiveTask, PendingDecision, KnowledgeSuggestion,
  ReviewArtifact)
- `R:/Sandbox/adventure_pipeline/tools/__init__.py`
- `R:/Sandbox/adventure_pipeline/tools/ir.py` — IR extractor (live directory → IR)
- `R:/Sandbox/adventure_pipeline/tools/__main__.py` — `python -m adventure_pipeline.tools.ir ADV-007` CLI
- `R:/Sandbox/adventure_pipeline/tests/__init__.py`
- `R:/Sandbox/adventure_pipeline/tests/test_ir_roundtrip.py`
- `R:/Sandbox/adventure_pipeline/tests/test_ir_entities.py`
- `R:/Sandbox/adventure_pipeline/README.md` — 1-page package overview

**Ark files that are explicitly NOT touched**: anything under
`R:/Sandbox/ark/`. If the vanilla Ark grammar/verifier cannot express a
desired constraint, we log a findings item in the package README and
continue — we do not patch Ark.

## Approach

### 1. Entity shapes (`adventure.ark`)

Declare, in vanilla Ark syntax:

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

### 2. Process shapes (`pipeline.ark`)

- `process AdventureStateMachine` — declares legal transitions between
  `State` values (concept→planning, planning→review, review→active,
  active→(blocked|completed|cancelled), blocked→active).
- `process TaskLifecycle` — `pending → in_progress → (passed | failed) → done`; `failed → in_progress` for retries.
- `process ReviewPipeline` — ordering of `Design approval → Permissions approval → Plan execution → Review artifact emission`.

### 3. Runtime entities (`entities.ark`)

- `class RunningAgent` — `name: Agent, task: Task, started_at: Timestamp`.
- `class ActiveTask` — `task: Task, wave: Wave, started_at: Timestamp`.
- `class PendingDecision` — `decision: Decision, adventure: Adventure, opened_at: Timestamp`.
- `class KnowledgeSuggestion` — `kind: String, text: String, source_task: String`.
- `class ReviewArtifact` — `task: Task, verdict: Verdict, issues[]: String, path: String`.
- `enum Verdict` — `PASSED | FAILED`.

### 4. IR extractor (`tools/ir.py`)

A pure-stdlib Python module that:
1. Takes an adventure id (e.g. `ADV-007`) or path.
2. Reads `manifest.md` frontmatter (regex-driven — no PyYAML; mirrors
   existing `server.py` pattern).
3. Walks `designs/`, `plans/`, `research/`, `reviews/`, `tasks/` and
   emits populated `Design`, `Plan`, `Research`, `Review`, `Task` records.
4. Parses the TC table from the manifest into `TargetCondition` records.
5. Parses `permissions.md` into `Permission` records (shell / file / mcp /
   external).
6. Returns a single `AdventurePipelineIR` dataclass — a Python shadow of
   the Ark entity shapes. JSON-serializable via `asdict`.
7. Exposes `to_json(ir) -> str` and a CLI `python -m adventure_pipeline.tools.ir <ADV-NNN>`
   printing JSON to stdout.

### 5. Optional verifier passes

Three passes invoked through Ark's existing verifier CLI
(`python ark/ark.py verify <spec>` — unchanged). Each is a standalone `.ark`
file under `adventure_pipeline/specs/verify/` that declares invariants:

- `state_transitions.ark` — invariants covering `AdventureStateMachine`
  legality.
- `permission_coverage.ark` — invariants: every Task has ≥1 Permission per
  assigned agent; every proof_command covered by shell permission.
- `tc_traceability.ark` — invariants: every TC references an existing
  Task id; every Task references ≥1 TC.

If any invariant cannot be expressed in vanilla Ark syntax, it's logged in
`adventure_pipeline/README.md` under "Deferred invariants" and skipped —
**Ark is not patched**.

### 6. Round-trip tests

- `test_ir_roundtrip.py` — extracts IR for ADV-007 and ADV-008; asserts
  presence of ≥1 Task, ≥1 Design, ≥1 Plan, ≥1 TargetCondition, ≥1
  Permission, and that every Task.id appears in the manifest tasks list.
- `test_ir_entities.py` — entity-level smoke tests: enums serialize
  correctly, dataclass shape matches spec field names.

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

## Target Conditions

- TC-039 — `adventure_pipeline/specs/adventure.ark` parses cleanly with
  vanilla Ark (`python ark/ark.py parse adventure_pipeline/specs/adventure.ark` exit 0).
- TC-040 — `adventure_pipeline/specs/pipeline.ark` declares all three
  processes (AdventureStateMachine, TaskLifecycle, ReviewPipeline).
- TC-041 — `adventure_pipeline/specs/entities.ark` declares the five
  runtime entities.
- TC-042 — IR extractor round-trip on ADV-007 returns a populated
  `AdventurePipelineIR` with non-empty tasks, documents, tcs, permissions.
- TC-043 — IR extractor round-trip on ADV-008 returns similarly populated IR.
- TC-044 — Every Task.id emitted by the extractor matches an id listed in
  the manifest `tasks:` frontmatter (no orphans, no missing).
- TC-045 — Optional verifier passes either verify clean OR deferred items
  are documented in `adventure_pipeline/README.md` (non-fatal).
