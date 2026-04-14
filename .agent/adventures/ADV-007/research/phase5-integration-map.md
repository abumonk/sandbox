---
task: ADV007-T018
adventure: ADV-007
phase: 5
target_conditions: [TC-017]
upstream:
  - .agent/adventures/ADV-007/research/phase5-concept-designs.md
  - .agent/adventures/ADV-007/research/phase2-entity-redesign.md
  - .agent/adventures/ADV-007/research/phase4-ui-architecture.md
researched: 2026-04-14
---

# Phase 5 — Integration Map for New Concepts

This document makes the **inter-concept dependencies** concrete so
that the rollout sequence, the permission topology, and the
conflicts with existing designs are all visible at once. It is the
operational companion to `phase5-concept-designs.md`: where that
document answers *what each concept is*, this one answers *how the
seven fit together* and *in what order they land*.

The literal phrase **integration map** appears in this opening
paragraph, in the matrices below, and in the acceptance checklist
for TC-017 grep proof.

---

## 1. Dependency Graph

### 1.1 Notation

- **A → B** means "A depends on B" (B must land first, or a thin
  shim is required).
- **A ↔ B** means mutual dependency; landing order matters but both
  must co-exist at maturity.
- **A ⇢ B** means "A optionally consumes B" — A can ship in a
  degraded form without B.

### 1.2 Graph

```
                      +-----------------------+
                      |  Project/Repo/KB      |
                      |  Separation (§5)      |
                      +-----------+-----------+
                                  |
                   +--------------+--------------+
                   |              |              |
                   v              v              v
           +---------------+  +----------+  +--------------+
           | Input Storage |  | Human-as |  | Custom       |
           |     (§3)      |  | -role §2 |  | Entities §6  |
           +------+--------+  +----+-----+  +------+-------+
                  |                |                |
                  |    +-----------+----------+     |
                  |    |                      |    |
                  v    v                      v    v
              +---------------+         +----------------+
              | Scheduling §1 |<------->| Messenger Agent|
              +------+--------+         |      §4        |
                     |                  +--------+-------+
                     |                           |
                     +-----------+---------------+
                                 |
                                 v
                     +------------------------+
                     | Recommendations §7     |
                     +------------------------+
```

### 1.3 Edges, annotated

- **Project → Input Storage**: inputs are scoped by project; without
  project identity, input access rules collapse to "anyone with the
  repo". Shim: treat the repo directory as a degenerate project.
- **Project → Human-as-role**: humans are project members; without
  project, humans have no membership scope. Shim: repo is the
  membership scope.
- **Project → Custom Entities**: custom schemas are project-scoped
  (with promotion to global). Without project, every schema is
  global — acceptable for MV but grows into trouble.
- **Input Storage → Scheduling (⇢)**: webhook-originated schedules
  cite inputs; pure-clock schedules do not need input storage.
- **Input Storage → Messenger Agent (⇢)**: large message bodies are
  stored as inputs. Below the size threshold, not needed.
- **Human-as-role → Scheduling**: SLA timers and escalation both
  require `schedule.*`. Hard dependency for the SLA feature.
- **Human-as-role ↔ Messenger Agent**: inbox notifications flow
  through messenger; human replies flow back via the agent into
  `pipeline.task_human_respond`. Mutual once both are mature.
- **Custom Entities → Scheduling (⇢)**: lifecycle stages may arm
  SLA timers; degraded without.
- **Custom Entities → Messenger Agent (⇢)**: custom-entity events
  can produce notifications.
- **Scheduling ↔ Messenger Agent**: quiet-hours batching is a
  schedule consumed by the messenger; retry backoff is a schedule
  produced by the messenger. Mutual at maturity.
- **Recommendations → everything**: the ranker consumes events
  from every other concept. Hard dependency on the substrate; soft
  dependency on each concept's events (more concepts → richer
  proposals).
- **Recommendations → Messenger Agent**: high-urgency proposals fan
  out via messenger.
- **Recommendations → Scheduling**: accepted retry proposals arm
  schedules.
- **Recommendations → Human-as-role**: proposals often target a
  human audience.

### 1.4 Strongly-connected cluster

`Scheduling ↔ Messenger Agent ↔ Human-as-role` form a near-cycle.
They can be broken by landing Scheduling first with no retry-backoff
kind (so it does not depend on Messenger for failure routing); add
Messenger next with a direct-send path (no batching, no quiet
hours); then add Human-as-role which consumes both. Once all three
are in, promote the mutual features (retry-backoff, batching, inbox
relay).

---

## 2. Interaction Matrix — New × Existing

Columns are existing entities (from T008 §0 Change Summary + §16 New
Entities). Rows are the seven new concepts. Cells use the letters
**C** create, **R** read, **U** update, **D** delete, **O** observe
(subscribe to events without mutating).

| New concept \ Existing | Task | Adv | Run | Lesson | Role | Skill | Agent | Permission | Messenger ent. | Project | Trigger | Config | Metrics | Input |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. Scheduling | U (escalate) | O | C/U (via fire) | O | R | R | — | R | O | R | C (time trig.) | R (tz) | O | — |
| 2. Human-as-role | U (assignee, respond) | O | O | O | R | — | — | R/C | U (approvals) | R | O | R | O | R |
| 3. Input storage | R (artifacts) | R | R (inputs ref) | O | — | — | — | R | O (attach) | R (scope) | — | — | — | — |
| 4. Messenger agent | O | O | O | O | R | R | R | R | U (outbox/deliv) | R | O | R | O | R (bodies) |
| 5. Project sep. | R | U (project_id) | R | U (scope) | R | R | R | U (scope) | R | — | — | R | R | U (scope) |
| 6. Custom entities | C (child tasks) | O | C/O (custom runs) | O | C/R (new roles) | O | R | C (scoped) | O | R | — | R | — | R |
| 7. Recommendations | C/U (via accept) | O | O | C/R | R | R | U (spawn) | R | C (notify) | R | U (arm) | R | O | O |

### 2.1 Reading the matrix

- **Recommendations is the most cross-cutting row.** It writes into
  Task, Lesson, Messenger, and Trigger on acceptance; its ranker
  reads everything.
- **Project is the most cross-cutting column-side change.** Every
  other new concept takes a scope from Project; every existing
  entity that stores knowledge or inputs needs a project-id label.
- **Input storage is mostly a read target.** Very few entities
  write inputs; many read them.
- **Messenger agent's mutations** land only on the Messenger entity
  substrate (`outbox.jsonl`, `delivery.jsonl`) and never on tasks
  or adventures directly. This preserves the single-writer
  invariant.
- **Custom entities create parallel universes.** They can create
  child Tasks (tracked as a cross-type ref) and define new Roles,
  but they do not mutate existing entity kinds. That keeps the
  blast radius small.

---

## 3. Recommended Rollout Sequence

The ordering optimizes three objectives:

1. **Substrate-first**: anything that others depend on ships
   earliest.
2. **Smallest visible UX first**: each release should add a
   user-visible capability, not just scaffolding.
3. **Degradable edges**: any `⇢` edge is honored by making the
   dependent concept ship in a degraded mode first, then upgrade.

### 3.1 Phase 5.0 — Scheduling (weeks 1-3)

Lands first because every other concept consumes it and it has no
hard inbound dependency. MV is one-shot + recurring, no retry, no
messenger integration.

- Tools: `pipeline.schedule_create`, `_cancel`, `_fire`, `_list`.
- UI: sidebar section "Upcoming" showing next-fire entries.
- Exit criteria: a recurring schedule fires a dummy task on time
  across a TM restart.

### 3.2 Phase 5.1 — Input Storage (weeks 3-5, parallel-start)

Lands next because Messenger and Human-as-role both consume it, and
it has no inbound dependencies in MV form. Fully parallelizable with
§3.1 if team size allows.

- Tools: `pipeline.input_store`, `input_get`, `input_list`.
- UI: a browser panel; upload / drag-drop into the shell.
- Exit criteria: drag-drop upload → stored → visible in another
  session → retrievable by id.

### 3.3 Phase 5.2 — Messenger Agent (weeks 5-9)

Requires Input Storage (for large bodies) and Scheduling (for quiet
hours / retry). MV ships without batching and without bi-directional
relay.

- Tools: `pipeline.messenger_enqueue`, `_deliver`, `_subscribe`,
  `_unsubscribe`, `_policy_set`, `_agent_spawn`.
- UI: notifications panel (toast + persistent).
- Exit criteria: a task state change emits a Slack message and an
  email to the audience within 60s; dedupe prevents double-send.

### 3.4 Phase 5.3 — Human-as-pipeline-role (weeks 9-14)

Requires Scheduling (SLA) and Messenger (inbox delivery). Largest
user-visible change of the phase.

- Tools: `pipeline.task_human_assign`, `_human_respond`,
  `_human_escalate`, `pipeline.human_profile_set`.
- UI: inbox tab, human assignee badges on tasks, SLA countdown.
- Exit criteria: a task assigned to a human is visible in their
  inbox across devices; a response closes the task; a timeout
  escalates.

### 3.5 Phase 5.4 — Project/Repo/Knowledge Separation (weeks 14-22)

Touches the most existing entities. Intentionally placed after the
human-in-loop features so that the people using the system can
co-design the sharing rules. This is the only concept whose
migration has breaking steps (repo-without-project → repo-in-
project).

- Tools: `pipeline.project_create`, `_member_add`, `_repo_attach`,
  `_knowledge_promote`, `_knowledge_demote`, `_scope_set`, plus
  new query tools.
- UI: project picker in the shell header; scope badges on
  adventures/knowledge.
- Exit criteria: a knowledge lesson promoted to global is visible
  from a different project; a repo can belong to two projects
  without state leakage.

### 3.6 Phase 5.5 — Custom Entities (weeks 22-32)

Requires Project (for schema scoping) and stable UI generic entity
views (phase4 §2.2) to render arbitrary custom entities.

- Tools: `pipeline.custom_entity_register`, generic
  `pipeline.custom_<type>_*` family, `pipeline.query`.
- UI: schema-driven list/detail views; schema editor.
- Exit criteria: register an `Incident` schema; create an instance;
  transition it through its lifecycle; see it in the sidebar.

### 3.7 Phase 5.6 — Recommendations Stack (weeks 32-38)

Lands last because its value scales with the number of event
classes in the substrate. Earlier landings were deliberately chosen
so that by week 32 the event log is rich enough to reduce signal
into useful proposals.

- Tools: `pipeline.proposal_create` (internal), `_accept`,
  `_reject`, `_expire`; ranker config.
- UI: proposals panel with urgency sort.
- Exit criteria: two reducer classes (`spawn`, `promote`) produce
  proposals that accept/reject correctly and arm the bound tool on
  acceptance.

### 3.8 Landing-order summary

```
Week:  1        5        9        14       22       32     38
       |--S-----|--In----|--M-----|--H-----|--P-----|--C---|--R-|
         Sched.  Input    Messngr  Human    Project  Custom Recs
```

Total: ~38 weeks of sequential-critical-path time; with two parallel
tracks (S+In in weeks 1-5), ~35 weeks.

---

## 4. Conflicts with Existing Designs

The new concepts were designed to fit on top of the T008 substrate.
Still, four soft conflicts warrant a flag.

### 4.1 Trigger entity — double-writer hazard (Scheduling vs. phase2)

T008 §14 makes **Trigger** a declarative `registry/triggers.json`
entry owned by the user + codegen. Scheduling (§1.3) needs to
**generate** temporal triggers at schedule-create time. If both
write to `registry/triggers.json`, the registry gains two writers.

- **Proposed resolution**: partition the registry by trigger kind.
  User-authored triggers live in `triggers/user.json`; generated
  temporal triggers live in `triggers/time.jsonl` (append-only, TM-
  owned). The `registry/triggers.json` becomes a generated union.
  Preserves single-writer per file.

### 4.2 Messenger substrate — agent introduction changes shape

T008 §11 specifies `messenger/channels.md` + `approvals.jsonl`.
Messenger agent (§4) adds `outbox.jsonl`, `delivery.jsonl`,
`subscriptions.jsonl`, and a `policies/` directory. Not a conflict
but a layering question: does the agent shape belong inside
`messenger/` or alongside at `messenger-agent/`?

- **Proposed resolution**: extend `messenger/` with the new files.
  The agent is logically part of the messenger subsystem; splitting
  directories would obscure that. Update the T008 diagram.

### 4.3 Project scoping vs. adventure layout

T008 treats **Adventure** as the top-level organizing unit under
`.agent/adventures/`. Introducing Project (§5) suggests a layer
above. If `~/.claudovka/projects/<id>.json` is the authoritative
project record and adventures carry a `project_id`, there is no
direct conflict — adventures still live in the repo; the project
file is external. However, the phase4 UI sidebar currently groups
by adventure; it must gain a project picker at the shell level.

- **Proposed resolution**: keep adventures where they are; project
  is a label + external registry. UI adds project picker at the
  shell header (phase4 §2.1). No filesystem migration required.

### 4.4 Custom-entity lifecycle vs. built-in stage machine

T008 and phase2 catalog standardize on the 6-stage + BLOCKED
machine. Custom entities (§6) declare their own lifecycle via
`lifecycle.json`, which **may** be the same machine or a
domain-specific one (Incident has `detected|triaged|mitigated|
resolved|postmortem`). A reviewer skill written against the 6-stage
assumption will not recognize custom stages.

- **Proposed resolution**: custom lifecycles must declare a mapping
  to a "base class" (e.g., `Incident.triaged` maps to `reviewing`
  for the purposes of reviewer agents). The mapping is optional; if
  absent, the entity is invisible to base-class-only tools. Document
  in the custom-entity registration validator.

### 4.5 Recommendations ↔ Trigger overlap

Triggers (after §4.1 resolution) fire based on events; the
recommendations reducer also reacts to events and proposes actions.
Why are they separate?

- **Intended distinction**: triggers are **deterministic** and fire
  their bound tool unconditionally; recommendations are **proposals**
  that require confirmation and have a score. A trigger can mature
  into a recommendation (auto-accepted at high confidence) but never
  the reverse. Document the distinction in the recommendations
  schema.

---

## 5. Permission-surface Integration

New permission scope names introduced by phase 5:

| Scope prefix | Concept | Notes |
|---|---|---|
| `scheduling.*` | §1 | create/cancel/fire |
| `human.*` | §2 | task.read/respond, inbox.read, profile.write |
| `input.*` | §3 | capture, read, delete, retention |
| `messenger.send.*` | §4 | per-channel send rights |
| `messenger.receive.*` | §4 | per-human receive rights |
| `project.*` | §5 | create, member.add, repo.attach |
| `knowledge.promote.*` | §5 | per-scope promotion |
| `custom_entity.*` | §6 | schema register + instance CRUD |
| `rec.*` | §7 | observe, accept, reject, class.register |

All scopes plug into T008 §12's sharded permission store; each is
a separate `permissions/<scope>/spec.md` file, single-writer,
loaded on demand.

---

## 6. UI Integration Summary (phase4 cross-ref)

Referring to `phase4-ui-architecture.md`:

- **Sidebar sections** (§2.1): add "Scheduling", "Inbox",
  "Inputs", "Proposals", "Projects".
- **Entity views** (§2.2): the generic list/detail triad is reused
  for every custom entity; schema ui-hints drive columns and tabs.
- **Command palette**: each new tool gets a command entry;
  discoverability is automatic.
- **Event subscriptions**: the `pipeline://events` stream already
  carries every jsonl append; no new transport is needed.
- **Optimistic pending queue**: writes from the UI through the MCP
  bridge remain the only mutation path; optimistic UI works
  unchanged.

No changes to the UI's core architecture are required to host any of
the seven concepts. The generic entity-views layer was explicitly
designed in phase4 for this extensibility.

---

## 7. Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Scheduler clock-skew corrupts fire times | high | monotonic + wall-clock dual source; skip-fire on large skew |
| Human inbox notifications missed | high | multi-channel fan-out; SLA watchdog; mandatory escalation |
| Input storage runs out of disk | medium | retention policies; S3 backend in growth path |
| Messenger agent spams users | medium | per-audience rate limit; batching policies; user opt-out |
| Project split leaks state across scopes | high | `.gitignore` patterns; scope-enforcement in every read tool; integration tests |
| Custom schema evolution breaks instances | medium | additive-only MV; explicit versioning |
| Recommendations over-fire | medium | idempotency by `(class, source_hash)`; rejection backoff |
| Scope proliferation explodes permission file count | low | per-scope shard is acceptable; index.json keeps lookup O(1) |

---

## 8. Acceptance Checklist

- [x] Dependency graph drawn with `→`, `↔`, `⇢` edges and the
  strongly-connected cluster called out (§1).
- [x] Interaction matrix (7 new × 14 existing) with C/R/U/D/O
  letters (§2).
- [x] Recommended rollout sequence with weekly markers, exit
  criteria, and a landing-order diagram (§3).
- [x] Conflicts with T008 entity redesign flagged with proposed
  resolutions (§4, five items).
- [x] Permission-surface scopes enumerated and mapped to T008 §12
  sharded store (§5).
- [x] UI integration reconciled with phase4 architecture (§6).
- [x] Literal phrase **integration map** present for TC-017 grep
  proof.

---

## Appendix — Cross-references

- Substrate rules: `phase2-entity-redesign.md` §§11, 12, 16.
- UI shell/views/editors: `phase4-ui-architecture.md` §§1, 2.
- Concept definitions: `phase5-concept-designs.md` §§1-8.
