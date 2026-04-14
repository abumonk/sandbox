---
task: ADV007-T018
adventure: ADV-007
phase: 5
target_conditions: [TC-016]
upstream:
  - .agent/adventures/ADV-007/research/phase2-entity-redesign.md
  - .agent/adventures/ADV-007/research/phase2-concept-catalog.md
  - .agent/adventures/ADV-007/research/phase4-ui-architecture.md
researched: 2026-04-14
---

# Phase 5 — New Ecosystem Concept Designs

This document designs the seven new first-class concepts that the
Phase 5 roadmap introduces into the Claudovka ecosystem. Each concept
is treated uniformly:

1. **Purpose** — the problem the concept solves and why the existing
   entities cannot absorb it.
2. **Use cases** — three to five concrete scenarios covering typical,
   high-value, and edge cases.
3. **Entity model** — fields, states, and append-only event shapes,
   aligned with the parallelism-first substrate established in T008.
4. **Relationships** — how it composes with existing entities (Task,
   Adventure, Role, Messenger, Permissions, Run, Lesson, Project).
5. **Behavior & lifecycle** — the transitions, deadlines, retries,
   and failure modes.
6. **Permission model** — which roles may create, observe, or mutate
   instances, and how scoped permissions apply.
7. **Open questions** — unresolved trade-offs flagged for T019+.
8. **MV sketch vs growth path** — the smallest viable shape that
   proves the concept, followed by the features that arrive once
   adoption justifies them.

Every concept follows the Phase-2 substrate rules: append-only jsonl
is the primary write surface; rendered-view markdown is derived; every
mutation is an MCP tool call; the UI (phase 4) renders and subscribes,
never owns state. The literal phrase **entity model** appears in each
section below for TC-016 grep proof.

---

## 1. Scheduling

### 1.1 Purpose

Today the pipeline is fundamentally reactive: every transition is
driven by an agent spawn, a user chat, or a hook. There is no
first-class way to say "run this pipeline every morning at 08:00",
"retry this failed run in 30 minutes", "escalate if the human does not
respond within 2 hours", or "treat this target condition as overdue
after 2026-05-01". The existing `Trigger` concept (phase2 catalog
§1.2) can express *event-based* triggers but has no temporal
vocabulary. Bolting cron into hook prompts (the current workaround in
other ecosystems) is exactly the non-determinism path that X8 was
resolved away from. Scheduling therefore needs to be a deterministic,
tool-owned entity.

### 1.2 Use cases

1. **Recurring pipeline kickoff.** A user wants the
   `morning-triage` pipeline to run every weekday at 08:00, producing
   a summary adventure and posting it to the team's Slack channel.
2. **Deadline-driven escalation.** A review task gets a deadline of
   T+4h; when the deadline passes without completion, the scheduler
   triggers `pipeline.task_escalate` which reassigns to the lead.
3. **Debounced retries.** A flaky external tool failed; the scheduler
   enqueues a retry 15 minutes later, then 30, then 60, with a cap
   of 5 attempts.
4. **One-shot reminders.** A planner schedules "check external PR
   status" for tomorrow 10:00 — a one-shot trigger that runs once
   and archives.
5. **Human SLA tracking.** When a human-assignee task enters
   `reviewing.ready`, a schedule is implicitly armed to fire at
   SLA expiry; see §2 for the consumption.

### 1.3 Entity model

```
scheduling/
|-- schedules.jsonl                  APPEND-ONLY
`-- views/
    |-- active.rendered.md           DERIVED
    `-- upcoming.rendered.md         DERIVED
```

Event kinds on `schedules.jsonl`:

- `schedule.created` — carries `{id, kind, spec, target, owner,
  payload, created_at, created_by}`.
- `schedule.armed` — computed `next_fire_at` recorded when a recurring
  schedule rolls forward.
- `schedule.fired` — an execution occurred; includes `run_id` of the
  resulting pipeline run if any.
- `schedule.paused`, `schedule.resumed`, `schedule.cancelled`.
- `schedule.missed` — deadline elapsed with no fire (paused past
  deadline, or the TM was offline).

Fields:

- `id: sched-<ulid>`
- `kind: "recurring" | "one_shot" | "deadline" | "retry_backoff"`
- `spec:` one of:
  - `{"cron":"0 8 * * 1-5","tz":"Europe/Prague"}` (recurring)
  - `{"at":"2026-05-01T09:00:00Z"}` (one-shot, deadline)
  - `{"base_ms":900000,"factor":2,"max_attempts":5}` (retry)
- `target:` `{"tool":"pipeline.adventure_start","args":{...}}` or
  `{"tool":"pipeline.task_escalate","args":{"task_id":"..."}}`. The
  target is *always* a named TM tool call with bound arguments — no
  free-form prompts.
- `owner:` role or user id (single-writer for mutation).
- `state:` derived — `armed | paused | cancelled | completed`.

### 1.4 Relationships

- Targets **Tasks**, **Adventures**, **Runs**, **Messenger
  approvals**, and any future `pipeline.*` tool.
- Consumes the **Trigger** entity (phase2 entity redesign §14): a
  schedule is a temporal trigger whose `event:"time"` record is
  appended to `registry/triggers.json` at the generation step.
- Produces **Runs**: every fire creates a Run; the scheduler records
  the resulting `run_id` so the UI can link fire → run.
- Cooperates with **Messenger**: failures and deadline misses fan out
  through `messenger/approvals.jsonl` (or the notifications channel).

### 1.5 Behavior & lifecycle

A singleton **scheduler service** inside TM (or a co-process) reads
`active.rendered.md` on start, loads the next-fire priority queue in
memory, and calls `pipeline.schedule_fire(id)` when a timer expires.
`schedule_fire` is itself an MCP tool with an idempotency key of
`(schedule_id, fire_at)` so replays after a crash never double-fire.
Clock source is wall-clock + monotonic skew detection; TM crash is
survivable because the priority queue is rebuilt from the tail of
`schedules.jsonl`.

Missed fires: if TM is offline when a fire was due, the restart emits
`schedule.missed` events for every expired timer and then decides per
`kind` whether to fire-late (`deadline` always fires-late;
`recurring` fires-late only if `catchup:true`; `one_shot` always
fires-late).

### 1.6 Permission model

- `scheduling.schedule.create` — adventure-planner, lead, user.
- `scheduling.schedule.cancel` — owner of the schedule or lead.
- `scheduling.schedule.fire` — TM only (never an agent, never a UI).
- Read view: any role; the upcoming view is surfaced in the UI
  sidebar.

### 1.7 Open questions

- **Cron expressiveness.** Full cron vs 5-field cron vs interval.
  Proposal: 5-field cron + `every <Xs/m/h/d>` shorthand.
- **Timezones per adventure.** If two adventures run in different
  timezones, whose clock wins? Proposal: per-schedule `tz` field.
- **Storm control.** 500 schedules firing at once: rate-limit? The
  run substrate handles queueing; the scheduler should not.

### 1.8 MV sketch → growth path

- **MV**: one-shot and recurring kinds only; `pipeline.schedule_*`
  tools; single TM-owned timer loop; no catchup.
- **Growth**: retry-backoff kind; deadline kind integrated with task
  escalation; multi-tenant clock; storm control; scheduler
  federation across hosts.

---

## 2. Human-as-pipeline-role

### 2.1 Purpose

Every assignee in the current model is an AI agent. Humans interact
only at the user-prompt boundary. This means human approvals, design
reviews, sign-offs, and code reviews cannot be first-class tasks; the
pipeline sees the human as an implicit, always-available oracle at the
edge. The phase1 cross-project synthesis flagged this as the single
biggest integration debt with binartlab, which already has a Run
substrate but no notion of "human-in-loop step". This concept
promotes the human to a proper `Assignee` with a distinct inbox, SLA,
and escalation path.

### 2.2 Use cases

1. **Design approval gate.** A planner produces a design and assigns
   the review task to `human:alice`. She sees the task in her inbox,
   has 4 hours to respond; on timeout the lead is paged.
2. **Manual code review step.** A code-review task is assigned to
   `human:bob`; it exposes a diff viewer in the UI and accepts
   `approve|changes_requested|reject` outcomes.
3. **Exception handling.** An AI agent escalates a blocked task to
   the human; the human either unblocks (editing the plan) or
   cancels the adventure.
4. **Marketplace moderation.** A human reviews a community-submitted
   skill before publish; outcome feeds the marketplace registry.
5. **Labeling / data tasks.** A human labels a batch of inputs; each
   label writes to `input-storage/items.jsonl` (see §3).

### 2.3 Entity model

```
humans/
|-- <human-id>/
|   |-- profile.md                  name, contact, timezone, scopes
|   |-- inbox.jsonl                 APPEND-ONLY assignment events
|   `-- availability.jsonl          APPEND-ONLY on/off/vacation
`-- registry.json                   generated index of known humans
```

The **Assignee** type in task frontmatter is extended:

```
assignee: human:alice
assignee_sla: PT4H            # ISO-8601 duration, optional
escalation: lead               # fallback assignee on SLA breach
```

Inbox events (`inbox.jsonl`):

- `task.assigned` — `{task_id, assigned_at, sla_deadline}`
- `task.reminded` — scheduler-driven nudge
- `task.answered` — `{task_id, answered_at, outcome, artifact_ref}`
- `task.escalated` — `{task_id, escalated_at, escalated_to}`

Availability is a single-writer append-only stream owned by the
human themselves (via the UI), used by the scheduler and the
load-balancer (future).

### 2.4 Relationships

- **Task.assignee** expands from `{role}` to
  `{role | human:<id> | agent:<id>}`.
- **Scheduling** arms the SLA timer on assignment; fires
  `task.escalated` on miss.
- **Messenger** delivers the inbox notification to the human's chosen
  channel (Slack DM, email, push).
- **Permissions** gain a `human.*` namespace covering read/respond
  rights per task.
- **Recommendations (§7)** may propose the best human assignee based
  on availability, skill, and past throughput.

### 2.5 Behavior & lifecycle

On assignment, TM appends `task.assigned` to the human's inbox,
optionally arms an SLA schedule (§1), and emits a Messenger
notification. The human responds through the UI, which maps each UI
outcome to a `pipeline.task_human_respond(task_id, outcome, body)`
tool call. On timeout, the scheduler fires `pipeline.task_escalate`
which changes `assignee` to the escalation target and appends a
`task.escalated` inbox event.

Humans are *identities*, not *sessions*: a human can have multiple
active UI sessions (laptop + phone), and the inbox is the
single-source-of-truth across devices. Unlike agents, humans do not
spawn; their "run" is the act of responding to a UI prompt.

### 2.6 Permission model

- `human.task.read` — the assigned human and any lead.
- `human.task.respond` — the assigned human only.
- `human.inbox.read` — the human themselves; leads can read during
  escalation.
- `human.profile.write` — the human themselves.

Per-adventure scopes (see T008 §12) gate which humans are assignable
to that adventure.

### 2.7 Open questions

- **Delegation.** Can a human delegate their inbox? Proposal: no for
  MV; add `delegate_to:` field later.
- **Anonymous humans.** For public marketplace moderation, is
  `human:<pseudonym>` acceptable? Likely yes with a provenance tag.
- **Multi-human tasks.** E.g., "require 2 of 3 approvals." Defer to
  growth path; MV allows single-human.

### 2.8 MV sketch → growth path

- **MV**: single-human assignee; inbox UI tab; one SLA timer;
  manual response via a generic `approve|reject|comment` form.
- **Growth**: multi-human approval quorum; delegation; per-assignee
  skill matching; anonymous identities; inbox federation across
  projects.

---

## 3. Input Storage

### 3.1 Purpose

Pipelines currently consume inputs (user prompts, file uploads,
external webhook payloads, scraped documents) without a durable
store. Each tool reads from whatever ad-hoc location it was handed,
and provenance is lost. Binartlab has a per-run `RunStorage`
interface (phase2 catalog §1.1) but nothing shared across runs or
adventures. Input storage is the persistent, provenance-rich,
content-addressed bucket that pipelines draw from, so that any run
can quote any input by a stable reference and re-consume it on replay
without re-fetching.

### 3.2 Use cases

1. **User file upload.** A user drops `design.pdf` into the UI; it is
   hashed, stored, and every downstream task references
   `input://sha256:...` instead of a local path.
2. **Scraped web page.** A researcher task fetches a URL; the raw
   HTML + extracted text are stored with the fetch timestamp and
   the originating task id.
3. **Incoming webhook.** A GitHub push webhook payload lands in
   input storage; a scheduler-armed trigger matches the event and
   kicks off a pipeline.
4. **Chat transcript.** The user's chat turn is an input; it is
   stored so the pipeline can audit what was said exactly, without
   reading the session JSON.
5. **Replay / backfill.** A past adventure is re-run on frozen inputs
   to verify determinism or regress a prompt change.

### 3.3 Entity model

```
input-storage/
|-- items.jsonl                     APPEND-ONLY metadata
|-- blobs/<sha256[0:2]>/<sha256>    content-addressed payloads
`-- views/
    |-- recent.rendered.md          DERIVED
    `-- by-source.rendered.md       DERIVED
```

Item record:

```
{
  "v":1,
  "id":"in-<ulid>",
  "ts":"2026-04-14T08:00:00Z",
  "sha256":"...",
  "size_bytes":12345,
  "mime":"application/pdf",
  "source":{"kind":"upload|url|webhook|chat|agent",
            "ref":"user:alice|https://...|hook:gh.push|sess:...|agent:researcher"},
  "labels":["design","adv:ADV-007"],
  "produced_by":"<task_id|human_id|external>",
  "retention":"permanent|ephemeral-30d",
  "access":"public|adventure|private"
}
```

Blobs are immutable; mutations produce new items that reference the
prior id via `supersedes:`. Retrieval is by `id` or by `sha256`.

### 3.4 Relationships

- **Run** (new entity from T008 §16) consumes inputs by `id`;
  `run.started` events list `inputs:[in-...]`.
- **Task.artifacts** directory may copy-on-read an input for local
  use; the canonical pointer is the input id.
- **Knowledge/Lesson** may cite an input as evidence.
- **Messenger** attaches inputs (rather than embedding) when a
  payload exceeds a threshold.
- **Project** (see §5) scopes inputs to a namespace.

### 3.5 Behavior & lifecycle

Every input goes through three stages: `captured`, `referenced`,
`retained-or-expired`. `captured` is the append of an `input.stored`
event. `referenced` is automatic: when any `run.started` or
`task.*` event cites the id. `retention` governs expiry; the
reconciler runs a sweep that moves expired blobs to cold storage (or
deletes if allowed) without removing the jsonl record, so provenance
is preserved even when the bytes are gone.

Content-addressing means duplicate uploads deduplicate at the blob
level. The item record, however, is always appended (same sha256 may
have different sources).

### 3.6 Permission model

- `input.capture` — any agent or UI.
- `input.read` — gated by `access` field + per-project scope.
- `input.delete` — lead only; marks `deleted_at` on the item and
  drops the blob.
- `input.retention.set` — owner or lead.

### 3.7 Open questions

- **Binary blob storage backend.** Start with local filesystem;
  growth to S3-compatible for sharing across machines.
- **PII scrubbing.** Chat transcripts may contain secrets. Policy
  hooks at capture time? MV: opt-in via `scrub:true`.
- **GC of unreferenced blobs.** Reference counting vs mark-and-sweep;
  defer, keep everything initially.

### 3.8 MV sketch → growth path

- **MV**: local blobs, items.jsonl, one MCP tool
  `pipeline.input_store(bytes, meta)` and one `input_get(id)`.
- **Growth**: S3 backend; encryption at rest; retention policies;
  PII scrub hooks; deduplication across projects; streaming large
  uploads; signed URLs for the UI.

---

## 4. Messenger Agent

### 4.1 Purpose

The existing Messenger entity (phase2 entity redesign §11) is a
channel declaration + approval queue — fundamentally a *routing
record*, not an active participant. A **Messenger agent** is a
deterministic, long-lived agent whose job is to ferry messages across
session boundaries, across channels, and to humans, applying policy
(digest, dedupe, escalate, quiet-hours). It is the bridge between the
append-only event substrate and the unruly world of Slack/Discord/
email/push.

### 4.2 Use cases

1. **Cross-session chat.** User asks in session A "what did agent X
   do yesterday?"; the messenger agent replays the relevant events
   from a different session's scope, respecting permissions.
2. **Notification routing.** A task escalation fans out to Slack for
   the lead, email for the assignee, and a UI toast for any active
   session, with dedupe so the same event never pings twice.
3. **Quiet hours / batching.** After 22:00 local, non-critical
   messages are batched into a morning digest.
4. **Human-to-agent relay.** A human replies in Slack; the messenger
   agent interprets and calls
   `pipeline.task_human_respond(task_id, outcome, body)` on their
   behalf (with their identity, via signed message).
5. **Cross-project broadcast.** An incident in one project must
   notify subscribers in other projects; the messenger agent
   consults the project registry (see §5) for subscriber lists.

### 4.3 Entity model

The messenger *agent* is distinct from the messenger *entity*. The
entity stays as `messenger/channels.md` + `approvals.jsonl` + the new
event substrate. The agent consumes:

```
messenger/
|-- channels.md                     declarations (preserved)
|-- approvals.jsonl                 approval events (preserved)
|-- outbox.jsonl                    APPEND-ONLY: pending messages
|-- delivery.jsonl                  APPEND-ONLY: delivery attempts + outcomes
|-- subscriptions.jsonl             APPEND-ONLY: who subscribes to what
`-- policies/                       per-channel routing policies
    |-- <policy-id>.md              e.g., "quiet-hours-Europe-Prague"
    `-- index.json                  generated
```

Message envelope (outbox entry):

```
{
  "id":"msg-<ulid>",
  "ts":"...",
  "source_event":"evt-<id>",
  "audience":[{"kind":"human","id":"alice"},
              {"kind":"channel","id":"#adv-007"}],
  "priority":"critical|high|normal|low",
  "body_ref":"input://sha256:...",   # large bodies stored as inputs
  "policy_id":"<optional>",
  "ttl_s":3600
}
```

The agent itself is one of the existing `agents/*.md` entries, with a
role prompt that describes its contract but a body of logic that is
deterministic (routing, dedupe, batching) and only occasionally
LLM-assisted (summarization for digests).

### 4.4 Relationships

- **Messenger entity** — the agent's read/write substrate.
- **Scheduling** — quiet-hours batching uses a schedule to flush
  batched digests.
- **Input storage** — bodies above a size threshold are stored and
  referenced by input id.
- **Human-as-role** — inbox notifications flow through the agent.
- **Permissions** — outbound sends are gated per channel and per
  audience; see §4.6.
- **Recommendations (§7)** — may propose new subscription rules
  based on observed interaction patterns.

### 4.5 Behavior & lifecycle

On every event of interest (task state changes, approval requests,
deadline misses, recommendation events), TM appends an `outbox`
entry. The messenger agent runs on a tick (or event) and processes
outbox: dedupe by `(audience, source_event, audience_kind)`; apply
policy (quiet hours, batching); attempt delivery through the channel
adapter; record `delivery.attempted` and `delivery.succeeded` or
`delivery.failed`. Failed deliveries enqueue a retry schedule (§1).

The agent is *not* the author of content; it only routes events
produced elsewhere. This keeps the LLM surface small and preserves
determinism.

### 4.6 Permission model

- `messenger.send.channel:<id>` — gated per channel; lead and
  adventure-planner may authorize subscriptions.
- `messenger.receive.human:<id>` — the human themselves only.
- `messenger.policy.write` — lead.
- `messenger.agent.spawn` — TM only (long-lived worker).

### 4.7 Open questions

- **Threading model.** One outbox global vs one per channel?
  Proposal: one outbox, partitioned by audience at dispatch.
- **Retroactive dedupe.** If two events arrive within ms of each
  other, batch or send both? Start with a 250ms debounce window.
- **Human-to-agent relay authentication.** Signed replies via a
  per-human token; channel adapter verifies.

### 4.8 MV sketch → growth path

- **MV**: outbox + one Slack adapter + one email adapter + UI toast;
  no quiet hours, no batching.
- **Growth**: policies and batching; multi-channel dedupe;
  bidirectional relay (human replies become tool calls); digest
  summarization via LLM; per-subscriber preferences.

---

## 5. Project / Repo / Knowledge Separation

### 5.1 Purpose

The ecosystem today conflates three axes into the filesystem
implicitly: the **repository** (a git working tree), the **project**
(a logical product with members, budget, settings), and the
**knowledge base** (portable, possibly cross-project lessons). One
working directory implies one of each, which breaks the moment a
single user has multiple projects sharing one repo, or one project
spans many repos, or knowledge is intended to be portable across
projects. Explicit separation of these three namespaces, with
defined sharing rules, unblocks binartlab's multi-project UI and the
marketplace's cross-project skill sharing.

### 5.2 Use cases

1. **One repo, many projects.** A monorepo hosts four products;
   each product is a Project with its own adventures, members,
   budgets, and permissions. They share the repo but not project
   state.
2. **One project, many repos.** A "platform" project owns three
   repos; adventures may touch any of them; the project holds the
   cross-repo plan.
3. **Knowledge portability.** A lesson learned in project A
   (`"append-only jsonl beats RMW"`) is promoted to a global
   knowledge namespace and becomes visible to project B.
4. **Private vs shared knowledge.** A lesson about a specific
   customer stays project-scoped; a generic pattern is promoted.
5. **Marketplace publishing.** A skill becomes shareable only once
   it has been tagged `knowledge:global`.

### 5.3 Entity model

Three top-level registries:

```
~/.claudovka/
|-- projects/
|   |-- <project-id>.json           single-writer per file
|   `-- index.jsonl                 APPEND-ONLY project lifecycle
|-- repos/
|   |-- <repo-id>.json              remote URL, clone path, fingerprint
|   `-- index.jsonl
`-- knowledge/
    |-- lessons.jsonl               global lessons union (from T008 §5)
    `-- views/...
```

Project record:

```
{
  "id":"prj-claudovka",
  "name":"Claudovka",
  "members":[{"id":"alice","role":"lead"}, ...],
  "repos":["rep-sandbox","rep-binartlab"],
  "knowledge_scopes":["prj-claudovka","global"],
  "adventures":["ADV-007","ADV-008"],
  "settings":{"default_tz":"Europe/Prague","budget_tokens":1000000}
}
```

Per-repo `.agent/` carries **only repo-scoped state** (tasks,
adventures, runs, messenger). Project-scoped state (members,
budgets, cross-repo adventures) lives in the project file. Knowledge
is stored once per scope: project-scoped at
`~/.claudovka/projects/<id>/knowledge/lessons.jsonl`; global at
`~/.claudovka/knowledge/lessons.jsonl`. Views materialize the union
per-reader.

Sharing rules:

- `knowledge_scope: "local"` — pinned to the repo; never visible
  outside.
- `knowledge_scope: "project"` — visible to all repos/adventures of
  that project.
- `knowledge_scope: "global"` — visible everywhere.

Promotion between scopes is an explicit MCP tool call
(`pipeline.lesson_promote(id, to_scope)`) that appends a promotion
event.

### 5.4 Relationships

- **Adventure** gains `project_id` in its manifest header.
- **Task.files** + **Repo** — every modified file path belongs to
  exactly one repo; the task records the repo id.
- **Permissions** gain a `project:<id>` prefix layer above adventure
  scopes.
- **Input storage** is project-scoped by default with promotable
  subsets.
- **Messenger channels** can be project- or global-scoped.

### 5.5 Behavior & lifecycle

Project creation is a one-time operation recorded in
`~/.claudovka/projects/index.jsonl`. Member add/remove are append
events. Repo attach/detach to a project is an append event. Knowledge
promotion and demotion are append events. The UI resolves a user's
active project from session metadata and applies the scope filter to
every query.

The critical invariant: **a repo never contains project-scoped
state**. Accidentally committing `~/.claudovka/` to a repo is
prevented by default `.gitignore` patterns.

### 5.6 Permission model

- `project.create` — user only (never an agent).
- `project.member.add` — project lead.
- `project.repo.attach` — project lead.
- `knowledge.promote:<scope>` — authorized promoter per scope
  (global requires user approval via Messenger).

### 5.7 Open questions

- **Cross-machine sync.** How does `~/.claudovka/` sync across a
  user's laptops? Proposal: optional git-backed remote.
- **Multi-tenant.** Is a "team" a project, or a group of projects?
  Defer; MV treats project as the unit.
- **Private knowledge encryption.** Sensitive lessons may need at-
  rest encryption; add a `encrypted:true` flag on lesson records.

### 5.8 MV sketch → growth path

- **MV**: one project = one repo = one knowledge namespace; the three
  directories exist but point at each other.
- **Growth**: many-to-many relationships; promotion tool;
  project-level budget accounting; team/tenant level; encrypted
  knowledge; sync backends.

---

## 6. Custom Entities

### 6.1 Purpose

The built-in entity set (Task, Adventure, Run, Lesson, Role, Skill,
Permission, Messenger, Project, …) is finite. Real users have
domain-specific entities: `Incident`, `Customer`, `Experiment`,
`RFC`, `DataSet`, `ModelCheckpoint`. Today they would shoe-horn
these into tasks or markdown docs, losing structure. Custom entities
give users a way to register a new typed entity with a schema, a
state machine, UI hooks, and role-level permissions — while
inheriting the append-only substrate, rendered views, and MCP
tooling for free.

### 6.2 Use cases

1. **Incidents.** A `Incident` entity with fields `severity`,
   `impacted_system`, `responders`, `status`; lifecycle
   `detected → triaged → mitigated → resolved → postmortem`; post-
   mortems are created as child tasks.
2. **Customer.** A CRM-lite `Customer` entity with
   `name`, `email`, `plan`, linked to inputs and messenger channels.
3. **Experiment.** An ML `Experiment` with `hypothesis`,
   `dataset_id`, `metric`, `result`; runs kick off binartlab jobs.
4. **Decision record.** Domain-specific `ArchitectureDecision` with
   stronger structure than the generic knowledge/decisions bucket.
5. **Marketplace listing.** Community skills registered as
   `MarketplaceListing` entities gated by custom moderation roles.

### 6.3 Entity model

Custom entity **schemas** are the meta-entity; **instances** are the
data. Schemas live at:

```
custom-entities/
|-- schemas/
|   |-- <type>/
|   |   |-- schema.md               frontmatter + body (prose docs)
|   |   |-- lifecycle.json          stage/status/transitions
|   |   `-- ui-hints.json           icons, list columns, detail tabs
|   `-- registry.json               generated type index
`-- instances/
    `-- <type>/
        |-- <id>/
        |   |-- instance.md         frontmatter + body
        |   `-- events.jsonl        APPEND-ONLY per-instance events
        `-- index.jsonl             APPEND-ONLY type-wide lifecycle
```

Schema record (frontmatter of `schema.md`):

```
id: incident
title: Incident
version: 1
fields:
  - {name: severity, type: enum, values: [p0,p1,p2,p3], required: true}
  - {name: impacted_system, type: string}
  - {name: responders, type: list[human]}
relationships:
  - {name: postmortem, kind: child, type: task}
  - {name: related_inputs, kind: ref, type: input}
permissions:
  create: [incident-commander, lead]
  mutate: [incident-commander, responder]
  observe: any
```

Instance frontmatter matches the schema; the TM enforces via a JSON-
schema validator generated from the schema record.

### 6.4 Relationships

- **Task** — a custom entity can declare tasks as children (e.g.,
  postmortem tasks on incident resolution).
- **Permissions** — custom entities live inside the same scoped
  permission substrate; their schema registers a new permission
  scope name.
- **UI** — schema `ui-hints.json` drives list columns and detail
  tabs; the UI Entity views layer (phase4 §2.2) is generic enough
  to render any custom entity once its hints are loaded.
- **Role** — a schema may require or define new roles (e.g.,
  `incident-commander`).
- **Recommendations (§7)** may index custom entities and propose
  transitions.

### 6.5 Behavior & lifecycle

Schema registration is an MCP tool
`pipeline.custom_entity_register(schema_md)` that validates and
appends to the registry index. Once registered, a family of tools is
available: `pipeline.custom_<type>_create`, `_update`, `_transition`.
Instances follow a generic stage/status machine defined by
`lifecycle.json`. Schema versioning: a new version is a new record;
instances carry `schema_version` and the TM reads the matching
version for validation.

Schemas are read-only at runtime for agents; they are authored by
humans and loaded by the UI. Instances are writable per permissions.

### 6.6 Permission model

- Each schema declares its own permission rules at registration.
- A **meta-permission** gates who may register or evolve a schema
  (`custom_entity.schema.register` — lead only).
- Schema version bumps require that no running instance on the old
  version is mid-transition; enforced at promote time.

### 6.7 Open questions

- **Schema evolution / migrations.** Renamed field? Start with
  additive-only evolution; defer migrations.
- **Cross-entity queries.** Need an ad-hoc query tool
  (`pipeline.query(type, filter)`)? Yes; MV supports exact-match.
- **Schema portability via marketplace.** A `Incident` schema could
  be shared; this ties to the global-knowledge scope (§5.3).

### 6.8 MV sketch → growth path

- **MV**: register one schema (e.g., `Incident`); generate
  CRUD+transition tools; list/detail views auto-rendered from hints.
- **Growth**: schema evolution with migrations; per-field
  validation rules; cross-type joins; schema marketplace;
  user-defined reducers that compute derived views.

---

## 7. Recommendations Stack

### 7.1 Purpose

The ecosystem produces a continuous stream of signals (failed tasks,
stale designs, rejected proposals, knowledge gaps, high-variance
evaluations, recurring user corrections). None of this is routinely
converted into proactive suggestions. A **recommendations stack**
ranks system-generated proposals (spawn this agent, run this skill,
revisit this task, promote this lesson, create this custom entity
instance) and exposes them to humans or agents for confirmation /
rejection. It is the feedback loop that turns the event log into a
learning system.

### 7.2 Use cases

1. **"Spawn a reviewer now."** The reviewer spawn was skipped
   yesterday; tonight the stack proposes to run it. The lead
   confirms.
2. **"Promote this lesson to global."** A pattern has been cited 5
   times across 3 adventures; the stack proposes promotion to
   global scope.
3. **"Escalate this human."** Alice has ignored 3 pings; proposal:
   reassign to Bob. Human confirms.
4. **"Create incident."** Two failed runs in a row on the same
   tool; proposal: create an `Incident` custom entity with the
   runs attached.
5. **"Retry with backoff."** A failed call with a transient error
   class; proposal: arm a retry schedule (§1).

### 7.3 Entity model

```
recommendations/
|-- proposals.jsonl                 APPEND-ONLY events
|-- models/                         per-class scoring rules
|   `-- <class-id>.md
`-- views/
    |-- open.rendered.md            DERIVED
    `-- by-class.rendered.md        DERIVED
```

Proposal record:

```
{
  "id":"rec-<ulid>",
  "ts":"...",
  "class":"spawn|promote|escalate|retry|create|cancel|...",
  "source_events":["evt-..."],      # causal evidence
  "action":{"tool":"pipeline.agent_spawn","args":{...}},
  "rationale":"...",                # human-readable explanation
  "score":0.78,                     # ranker output in [0,1]
  "urgency":"high|normal|low",
  "audience":["lead","human:alice"],
  "ttl_s":3600
}
```

State events: `proposal.created`, `proposal.viewed`,
`proposal.accepted`, `proposal.rejected`, `proposal.expired`,
`proposal.superseded`.

### 7.4 Relationships

- **Every entity.** Any event in the system can be a source event;
  the stack is a universal consumer.
- **Scheduling** — accepted retry-proposals arm a schedule.
- **Messenger** — high-urgency proposals fan out via messenger.
- **Knowledge** — proposals cite lessons (`why: "pattern X applies
  here"`) and accepted proposals produce new lessons.
- **Human-as-role** — proposals often target a human for
  confirmation; the response flows through the inbox.
- **Custom entities** — the class taxonomy is extensible via a
  custom schema (`ProposalClass`).

### 7.5 Behavior & lifecycle

A set of **signal reducers** (one per class) subscribe to the event
log, detect their trigger pattern, and append `proposal.created`
events. A **ranker** (deterministic scoring + optional LLM
rationale-generation) assigns scores. The UI surfaces open
proposals; acceptance calls the bound tool, which may itself produce
further events. Rejection is recorded with a reason so the ranker
can learn (future).

Proposals are idempotent by `(class, source_events_hash)`: the same
situation does not produce duplicate open proposals. Expiry is
governed by `ttl_s` or by a superseding event (e.g., the underlying
condition self-resolved).

### 7.6 Permission model

- `rec.observe` — any.
- `rec.accept` — matches the `audience` of the proposal, else lead.
- `rec.reject` — same.
- `rec.class.register` — lead.
- `rec.ranker.tune` — lead (via a ranker config file).

### 7.7 Open questions

- **Spam control.** Reducers can over-fire; per-class rate limits
  and exponential backoff on rejection.
- **Ranker bias.** Scores should incorporate recent rejections
  without collapsing to "never suggest again"; this is a known
  exploration/exploitation trade-off.
- **Privacy.** Proposals cite source events; scope visibility to
  match the audience's read permissions.

### 7.8 MV sketch → growth path

- **MV**: two classes (`spawn` and `promote`); deterministic
  reducer; constant score; open-proposals UI panel; accept/reject
  tools.
- **Growth**: additional classes; LLM-assisted rationale; ranker
  tuning from acceptance history; per-user ranking; proactive
  proposals that require no confirmation for low-risk actions;
  "auto-accept" thresholds per class.

---

## 8. Cross-concept Summary

Every concept above adheres to five shared invariants, which makes
their integration cheap:

1. **Append-only event substrate.** `*.jsonl` per concept; no
   read-modify-write on shared state.
2. **MCP-tool-only writes.** Every mutation is a named
   `pipeline.*` tool. The UI (phase 4) and agents share this path.
3. **Rendered views for humans.** Markdown views are derived, never
   authoritative. The UI subscribes to `pipeline://events`.
4. **Single-writer per file.** When a non-append file exists
   (`schema.md`, `channels.md`, `profile.md`), it has one writer.
5. **Scoped permissions.** Every concept declares its permission
   namespace, consumable by T008 §12's sharded permission store.

### 8.1 Complexity estimates

| Concept | Schema | Tool surface | UI delta | Est. effort |
|---|---|---|---|---|
| 1. Scheduling | small | 4 tools | small | M (~3 wk) |
| 2. Human-as-role | medium | 5 tools | large (inbox) | L (~5 wk) |
| 3. Input storage | small | 3 tools | medium (browser) | M (~3 wk) |
| 4. Messenger agent | medium | 6 tools | small | L (~5 wk) |
| 5. Project sep. | large | 8 tools | large | XL (~8 wk) |
| 6. Custom entities | large | generic | large (generic) | XL (~10 wk) |
| 7. Recommendations | medium | 4 tools + ranker | medium | L (~6 wk) |

Totals: ~40 developer-weeks spread across concepts; see
`phase5-integration-map.md` for the recommended rollout order and
the dependency graph that justifies it.

---

## 9. Acceptance Checklist

- [x] All seven concepts designed with **purpose**, **use cases**,
  **entity model**, **relationships**, **behavior & lifecycle**,
  **permission model**, **open questions**, and **MV/growth**.
- [x] Literal phrase **entity model** present in each section
  (TC-016 grep proof).
- [x] Implementation complexity estimated per concept (§8.1).
- [x] Upstream references to T008 entity redesign honored (substrate
  rules §8, single-writer, append-only, scoped permissions).
- [x] Upstream references to T017 UI architecture honored (generic
  Entity views layer consumes custom entities; messenger agent
  feeds UI toasts; recommendations surface in UI panel).
- [x] Cross-concept integration deferred to `phase5-integration-map.md`.

---

## Appendix — Upstream Inputs

- `phase2-entity-redesign.md` §§11, 12, 16 (messenger, permissions,
  new entities including Run and Project).
- `phase2-concept-catalog.md` §1, §10 (concept inventory and new
  first-class entities proposed by the catalog).
- `phase4-ui-architecture.md` §§1, 2.2, 2.3 (shell + entity views +
  editor layers — how custom entities and recommendations surface).
