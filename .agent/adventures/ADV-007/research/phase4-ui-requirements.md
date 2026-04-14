---
task: ADV007-T017
adventure: ADV-007
phase: 4
target_conditions: [TC-013]
upstream:
  - .agent/adventures/ADV-007/research/phase1-cross-project-issues.md
  - .agent/adventures/ADV-007/research/phase2-concept-catalog.md
  - .agent/adventures/ADV-007/research/phase2-entity-redesign.md
  - .agent/adventures/ADV-007/research/phase2-knowledge-architecture.md
researched: 2026-04-14
---

# Phase 4 — UI Requirements (Claudovka Workflow UI)

This document catalogs the functional and non-functional requirements for
a Claudovka ecosystem UI that sits above the redesigned `.agent/` layout
(event-sourced, append-only jsonl substrate) and the team-mcp tool
surface. It is the requirements input for the architecture (TC-014) and
technology-stack (TC-015) deliverables of T017.

The UI must serve three audiences:

1. **Lead operator.** The human who proposes, approves, and monitors
   adventures/tasks. Today they work through Claude Code's chat pane plus
   text-editor views of `.agent/`. They need lower-friction state
   inspection and approval flows.
2. **Outside observer.** A stakeholder (team member, manager, reviewer)
   who is not running Claude Code but wants to follow progress, read
   lessons, browse metrics, or approve a gated transition.
3. **Self-inspecting agents (via headless API).** Agents that need to
   query UI-managed state (filtered event views, rendered knowledge
   slices) through MCP rather than file I/O.

The UI name convention used in this document is **Claudovka Studio** (or
"Studio" for short), borrowing the "studio" idiom from Linear, n8n, and
Langflow. The name is not load-bearing.

---

## 0. Requirements Map

| Section | Scope | TC coverage |
|---|---|---|
| §1 Workflow entity UI | Per-entity list / detail / edit requirements | TC-013 |
| §2 Live updates | Subscription model, latency budgets | TC-013 |
| §3 Interaction patterns | Approvals, commit gates, cascades | TC-013 |
| §4 Read/write authority | Who is allowed to mutate what | TC-013 |
| §5 Node/graph editor | Pipeline DAG, adventure graph, cascade graph | TC-013 |
| §6 DSL editor | Ark spec editing, PDSL shim, validation | TC-013 |
| §7 Tabs/panes system | Layout, persistence, multi-panel workflows | TC-013 |
| §8 Non-functional | Latency, multi-user, accessibility, offline | TC-013 |
| §9 Similar-tool survey | Linear, Notion, n8n, Langflow, Retool, Zed | supporting |

---

## 1. Workflow Entity UI Requirements

Entity list is aligned with the post-Phase-2 redesign (one append-only
jsonl per mutable entity, rendered views as read-only artefacts). For
each entity the UI must support the CRUDL operations allowed by the
redesigned writer-arbitration rules (phase2-entity-redesign §2.3).

### 1.1 Adventure

Adventures are the top-level organizational unit. The UI renders an
**adventure dashboard** as its default view.

Requirements:

- **List view**: all adventures in the project, grouped by state
  (concept / planning / active / reviewing / completed / cancelled).
  Sortable by created, updated, task count, token burn, variance.
  Filter by tags, owner, depends_on, phase. Virtualised list to handle
  100+ adventures without scroll jank.
- **Detail view**: manifest header (id, title, state, dates, tasks
  array, depends_on) visible permanently at the top; tabs beneath for
  Concept, Target Conditions, Evaluations, Environment, Permissions,
  Roles, Events, Files, Settings. The TC and Evaluations tabs are
  tables backed by `manifest.targets.jsonl` and
  `manifest.evaluations.jsonl` respectively; both live-update as new
  events land.
- **Timeline view**: chronological plot of `adventure.log` +
  `events.jsonl` with filter ribbon (by event type, agent role, task
  id). Each event row links to its source task.
- **Graph view**: a DAG node-graph of tasks with `depends_on` edges,
  colour-coded by stage; clicking a node opens that task's detail. The
  graph scrolls and zooms; layout is LR by default, TB optional.
- **Edit capability**:
  - Lead may advance adventure state (proposes; user approves).
  - Adventure-planner may create Target Conditions; status transitions
    append events (not direct edits).
  - Researcher may append evaluations; actuals are write-once via
    `pipeline.eval_append`.
  - Concept body is frozen post-activation; amendments go through an
    "amend event" modal (writes an amendment event to
    `events.jsonl`).

### 1.2 Task

Requirements:

- **List view**: all tasks scoped to an adventure (or free-standing),
  with columns id, title, stage, status, assignee, iterations,
  updated. Kanban board alternative grouped by stage; each column is a
  virtualised list. Filter chips for tags, assignee, depends_on,
  blocked-by.
- **Detail view**: header pane with `task.md` frontmatter (read/write
  for appropriate fields); markdown body panes for Description,
  Acceptance Criteria, Design (each editable by the right role).
  Below: three live streams:
  1. `log.jsonl` tail (last 100 events, auto-scroll, filter by agent
     step).
  2. `iterations.jsonl` cards (one card per review/fix cycle with
     diff links).
  3. Artifacts browser for `artifacts/*` with size, kind icons,
     preview for images/json.
- **Edit capability**:
  - Frontmatter scalar edits (`stage`, `status`, `iterations`) are
    proposals that emit a `task.state_change` event through
    `pipeline.task_set_header` (single writer at the MCP boundary).
  - Body edits (Description, AC, Design) go through the markdown
    editor with optimistic update + server-ack, rolled back on
    rejection.
  - Appends to `log.jsonl` are always allowed (append-only contract);
    iteration appends are allowed only by the reviewer and implementer
    roles.
- **Quick actions**: "Assign to role", "Block on…", "Append log
  entry", "Start review", "Mark completed". Each action is a command
  mapped to one or more MCP calls.

### 1.3 Plan

Requirements:

- **List view**: plans within an adventure, with column for designs
  covered and task count.
- **Detail view**: markdown renderer + editor (single-writer file).
  Nested list of tasks with inline status badges that live-update.
- **Edit capability**: adventure-planner only; read-only for other
  roles. Direct file edits surface through a "propose change"
  workflow because the file is single-writer.

### 1.4 Design

Requirements:

- **List view**: designs within an adventure, with column for plans
  that reference it.
- **Detail view**: markdown editor with three panes: source,
  rendered preview, cross-references (plans, tasks, permissions
  touching the design).
- **Edit capability**: adventure-planner for new designs;
  lead/user for amendments. Amendments record authorship metadata.

### 1.5 Manifest (Adventure Manifest, Plugin Manifest, etc.)

Requirements:

- The word is four different entities (phase2 catalog §2.3). The UI
  must distinguish them by the canonical split:
  `AdventureManifest`, `PluginManifest`, `ProjectManifest`,
  `McpManifest`.
- **Adventure manifest**: covered in §1.1.
- **Plugin manifest** (`.claude-plugin/plugin.json`): a project-scope
  view that lists all installed plugins, versions, `engines` fields,
  and the current active pin. Readable diff against the previous
  version on hover; "update" proposes a cached version swap.
- **Project manifest**: binartlab-side; not in scope for this UI
  unless binartlab-integration is enabled.
- **McpManifest** (`.mcp.json`): a server list with status dots,
  last_event, restart button, log tail.

### 1.6 Metrics

Requirements:

- **Per-task view**: sparkline of tokens_in/out per spawn, duration
  per spawn, turn count; variance vs estimate annotated.
- **Per-adventure roll-up**: stacked bar by role, total cost, budget
  remaining (from TC-033 contract). Cumulative curve over time.
- **Project roll-up**: adventures × months cost breakdown; top 10
  most expensive tasks; model-mix pie (opus/sonnet/haiku).
- **Filters**: role, model, stage, date range.
- **Export**: CSV, JSON, and "copy as markdown table" for pasting
  into `evaluations.rendered.md`.
- **Live update**: as `metrics.jsonl` appends, sparklines extend.

### 1.7 Knowledge Base

Post-Phase-2 the knowledge base is a single `knowledge/lessons.jsonl`
plus rendered views. The UI must expose:

- **Unified feed** of lessons: card per entry with kind badge
  (pattern / issue / decision / role-note), source task link, tags.
  Virtualised for 10k+ entries.
- **Role-scoped view**: filter by `role:` tag; this is the successor
  to `agent-memory/<role>/MEMORY.md`. Each role has a default view at
  `/knowledge/roles/<name>`.
- **Search**: full-text across `name`, `body`, `tags` with ranked
  results; filter facets for kind, role, from-task, date. Keyboard-
  navigable (Linear-style Cmd-K).
- **Add lesson**: modal with kind selector, body markdown, tag
  typeahead. Submits through `pipeline.lesson_append`.
- **Amend**: any lesson may be amended via an amendment event; the
  UI shows edit history on demand.
- **Legacy shim**: rendered `patterns.rendered.md` / `issues.rendered.md` /
  `decisions.rendered.md` are available as tabs that read the same
  underlying jsonl.

### 1.8 Role

Requirements:

- **Catalog view**: all roles in `roles/`, both project-default and
  per-adventure custom. Badge for "project" vs "adventure-local".
  Columns: model preference, allowed tools count, skills count.
- **Role detail**: the markdown role prompt with frontmatter editor
  (`tools`, `disallowedTools`, `model`, `memory`). Permission
  references resolved into inline descriptions.
- **Role-scope knowledge slice** (see §1.7) embedded as a tab.
- **Edit capability**: user-only for project defaults;
  adventure-planner for adventure-local roles.

### 1.9 Skill

Requirements:

- **Catalog view**: generated from `registry/skills.json`. Columns:
  name, command path, agent preference, context mode (inline/fork),
  allowed-tools summary.
- **Skill detail**: SKILL.md rendered + raw tabs. "Run" button that
  opens the skill invocation as a dry-run dialog (shows what tools
  it will call, with dry-run toggle).
- **Edit capability**: user-only. Skill files are single-writer.

### 1.10 Events

Events are the source of truth for state change. The UI provides an
**Events Inspector**:

- **Live stream**: WebSocket-like push of new events from
  `pipeline://events` MCP resource. One row per event with expand for
  payload.
- **Filters**: type taxonomy (`task.*`, `agent.*`, `adventure.*`,
  `lesson.*`, `approval.*`, `metrics.*`), adventure id, task id,
  agent id, session id, time range.
- **Persist filters**: bookmarkable URLs.
- **Replay mode**: scrubber over the last N events; views re-render
  as the scrubber moves (using the reconciler's replay capability).
- **Export**: selected events as jsonl for reproduction cases.

### 1.11 Permissions (per-scope)

Post-Phase-2 permissions are sharded per scope (phase2 entity-redesign
§12). The UI provides:

- **Scope tree**: visual hierarchy of project → working_folders →
  task packages with badges for allow/deny size.
- **Scope editor**: rendered spec.md + raw, with a structured editor
  for allow/deny rules. Diff against previous version. Proofs tab
  for each scope (phase2 allowing proof artifacts).
- **Dry-run**: "given role X executing action Y on path Z, does the
  permission stack allow it?" — answered by calling
  `pipeline.permission_check(scope, role, action, path)`.

### 1.12 Messenger

Requirements:

- **Channels view**: rows for Telegram / Discord / other channels
  with status (configured, connected, errors), env-var refs
  resolved through `pipeline.channel_status`.
- **Approvals inbox**: pending approvals (from `approvals.jsonl`
  unresolved tail). Each card shows requester, target event, deadline,
  approve/reject buttons. Approvals persist across MCP restart
  (phase2 messenger fix).

### 1.13 Runs (new entity)

Phase-2 catalog §10.4 introduces `Run` as a first-class entity (one
invocation of a Pipeline with bound input set). UI requirements:

- **List**: runs per adventure, with start/end, status, triggering
  event, total cost.
- **Detail**: linked task/adventure, input payload viewer, output
  events stream, timing waterfall.

---

## 2. Live Update Requirements

### 2.1 Latency budgets

| Surface | p50 target | p95 target | Backing |
|---|---|---|---|
| Task status change | 150 ms | 400 ms | MCP notification → WS → UI |
| Log line append | 200 ms | 500 ms | event resource subscription |
| Metrics sparkline | 500 ms | 1000 ms | debounced stream |
| Knowledge feed | 500 ms | 1000 ms | lesson_append event |
| Approval inbox | 150 ms | 400 ms | approval.requested event |
| View regen (derived md) | 1 s | 3 s | reconciler async |

The event resource `pipeline://events` is the single real-time source
of truth. The UI must not poll the filesystem; it subscribes to the
MCP resource and hydrates initial state from the rendered views.

### 2.2 Reconnection and catch-up

If the UI loses connection to the MCP server:

1. Show an unobtrusive banner: "disconnected — reconnecting" with
   retry countdown.
2. On reconnect, re-subscribe with the last-seen event `offset`; the
   server replays missed events from `events.jsonl` (bounded to a
   configurable window, default 10k events).
3. If the window is exceeded, the UI falls back to a full refetch of
   rendered views and drops in-memory event cache.

### 2.3 Optimistic updates

Interactive mutations (status change, log append, lesson add) apply
optimistically in the UI cache and wait for the confirming event. On
server rejection (e.g., permission denied), the optimistic change is
rolled back with a toast that cites the rejection reason.

### 2.4 Multi-client consistency

Two browsers connected to the same MCP server see the same timeline
because events are totally ordered in `events.jsonl`. The UI carries
the last event offset in every optimistic request so the server can
reject stale writes (optimistic concurrency at the event layer).

---

## 3. Interaction Patterns

### 3.1 Lead-proposes / user-approves

This is the "full authority, zero autonomy" principle (phase1 §3.2,
pattern 3). Every mutating action that is not an append has two
layers:

1. **Proposal**: the lead agent's UI submits a proposal (e.g., advance
   a task to `reviewing`). The server records an event
   `proposal.created` and places it in the approvals inbox.
2. **Approval**: the user clicks approve (or the messenger relays
   approval). Server records `proposal.approved`, applies the change,
   emits the downstream event (e.g., `task.stage_changed`).

The proposal layer is skippable in "auto" mode (configured per
category: e.g., auto-approve log appends but always confirm
stage changes).

### 3.2 Approval from offline devices

A user away from Claudovka Studio receives an approval request via
the configured messenger channel. They respond by replying to the
message; the server parses the reply into `approval.resolved` and the
UI updates in real time.

### 3.3 Cascade propagation

When a step2step `Step` is modified, the cascade-tracker emits
`cascade.computed` events. The UI shows cascade edges highlighted in
the graph view and lists affected downstream steps in a side panel;
user may approve the cascade in bulk or per-step.

### 3.4 Commit gating

After implementation passes review, the lead proposes a commit. The
UI surfaces the proposed commit in a dedicated "commits" pane with
diff preview (from git), then sends the approval through the same
proposal pipeline.

### 3.5 Batch operations

Selecting multiple tasks enables batch actions: assign role, advance
stage, add tag, close. Each selected item generates its own proposal
event; batch UI shows per-item progress.

---

## 4. Read/Write Authority

### 4.1 Writers matrix (post-Phase-2)

| Surface | Sole writer | UI write path |
|---|---|---|
| `tasks/T/task.md` header | TM `task_set_header` | Frontmatter editor → MCP |
| `tasks/T/log.jsonl` | any (append) via `task_append_log` | Log append modal |
| `tasks/T/iterations.jsonl` | reviewer/implementer via `task_append_iter` | Iteration card action |
| `adventures/A/events.jsonl` | TM `event_append` | all mutation paths |
| `adventures/A/manifest.evaluations.jsonl` | TM `eval_append` | researcher-only dialog |
| `adventures/A/manifest.targets.jsonl` | TM `tc_set` | TC toggle control |
| `knowledge/lessons.jsonl` | TM `lesson_append` | "Add lesson" modal |
| `lead-state/active.jsonl` | TM `heartbeat` | (internal) |
| `messenger/approvals.jsonl` | TM `approval_*` | Approval actions |
| `designs/*.md` | adventure-planner | Design editor → MCP commit proposal |
| `plans/*.md` | adventure-planner | Plan editor → MCP commit proposal |
| `roles/*.md` | user | Role editor (local save + proposal) |
| `permissions/<scope>/spec.md` | adventure-planner | Scope editor → MCP |

### 4.2 Reader authority

Everyone may read every rendered view. Raw jsonl is readable but not
the canonical UI surface. Role-scoped views hide no information; they
simply rank differently.

### 4.3 Auth

Claudovka Studio is local-first (same machine as MCP). For the
outside-observer use case, a "share link" mode generates a read-only
snapshot URL served by a companion HTTP server that reads the jsonl
event substrate and proxies to MCP read-only tools. No write
operations are exposed on the share link.

---

## 5. Node / Graph Editor Requirements

The UI must render three distinct graphs:

### 5.1 Adventure dependency graph

- Nodes: Tasks; edges: `depends_on`.
- Clustering by stage (swim lanes) optional.
- Click node → task detail overlay.
- Drag-edge to propose a new dependency (writes `depends_on` update
  proposal).

### 5.2 Pipeline lifecycle DAG (TaskLifecycle)

- The 6+BLOCKED state machine from phase2 catalog §1.2.
- Read-only visualization; clicking a transition shows recent events
  matching that transition and the count per role.

### 5.3 Cascade graph

- Nodes: Steps (step2step); edges: `cascade_to` / `depends_on`.
- Live-updating when cascade events arrive.
- Selection box for bulk-approving a cascade.

### 5.4 Engine requirements

- Determinsitic layout (same graph → same layout across sessions).
- LR / TB / radial options.
- Edge labels for transition predicates.
- Pan / zoom / focus-to-fit.
- Export as SVG for reports.
- 500+ node performance target (React Flow / Sigma / Cytoscape).

### 5.5 Visual editor for DSL/Ark pipelines

When an Ark `.ark` spec is opened, the node graph shows the spec's
items (classes, islands, lifecycles) and their references. Editing a
node writes back to the spec via the Ark codegen API (round-trippable,
as PDSL already supports for its subset).

---

## 6. DSL Editor Requirements

### 6.1 Languages supported

- **Ark** — the canonical DSL (phase1 P2). First-class support.
- **Pipeline DSL (PDSL)** — legacy, accessed via Ark dialect shim.
- **Markdown** — task/plan/design bodies.
- **JSONL** — read-only structured viewer for event streams.
- **YAML** — plugin.json / package.json editing.

### 6.2 Editor features per language

| Feature | Ark | PDSL | Markdown | JSONL | YAML |
|---|:-:|:-:|:-:|:-:|:-:|
| Syntax highlight | yes | yes | yes | yes | yes |
| Inline validation | yes (Ark verify) | yes (PDSL validator) | schema-of-frontmatter | schema-of-event | schema |
| Autocompletion | yes (LSP) | partial | frontmatter keys | — | schema keys |
| Hover doc | yes | — | — | — | yes |
| Formatter | yes | yes | — | — | yes |
| Round-trip to graph | yes (§5.5) | yes | — | — | — |
| Go-to-def | yes | yes | anchor links | — | — |
| Diff view | yes | yes | yes | yes | yes |

### 6.3 LSP integration

Ark ships a language server (planned in ark-orchestrator crate per
recent commit). The UI's DSL editor must speak LSP over websocket so
hover / completion / diagnostics work uniformly.

### 6.4 Validation gutter

Inline error squiggles with severity colours; hover shows the full
error. Errors also aggregate in a "Problems" pane (VS Code style)
with severity filters.

---

## 7. Tabs / Panes System

### 7.1 Layout model

Inspired by Zed / VS Code / Notion:

- **Sidebar**: entity tree (Adventures → Tasks → Designs / Plans;
  Knowledge; Roles; Skills; Permissions; Messenger; Events; Metrics).
- **Main area**: tab container with split-pane support (vertical /
  horizontal splits, 1-4 panes).
- **Bottom panel**: Problems, Terminal, Output, Events (toggleable).
- **Right panel**: Agents / Channels / Outline (toggleable).
- **Command palette**: Cmd-K / Ctrl-K with fuzzy search over
  entities, actions, settings, recently viewed.

### 7.2 Tab requirements

- Entities open as tabs. Closing a tab preserves its scroll + filter
  state in memory until reopened.
- Pinned tabs survive session restart.
- Drag-reorder tabs; drag-across-panes to split.
- "Link tabs": open a second tab that follows selection in the first
  (e.g., a "preview" tab that mirrors whichever task is selected in
  a list).

### 7.3 Workspace persistence

- Workspace = {sidebar state, open tabs, pane splits, filter
  settings, terminal state}. Persisted to `.agent/ui-workspace.json`
  per user.
- Named workspaces ("Reviewing ADV-007", "Metrics dashboard") allow
  quick context switching.

### 7.4 Multi-monitor

Panes may be torn off into separate windows (Electron/Tauri); each
window shares the same MCP subscription. Layout state of torn-off
windows persists separately.

---

## 8. Non-Functional Requirements

### 8.1 Performance

- First meaningful paint: < 1 s on a warm cache; < 3 s on cold cache.
- Event ingestion rate: sustain 100 events/s without UI jank.
- Memory envelope: < 500 MB resident for a 10k-event adventure.
- Startup: open to last workspace in < 2 s.

### 8.2 Multi-user

Primary target is single-user local. Multi-user scenarios:

- **Same machine, same MCP**: multiple browser tabs see coherent
  state via event ordering. Supported.
- **Share link, read-only**: multiple outside observers on a
  read-only HTTP view. Supported.
- **Two machines, shared `.agent/`**: out of scope for Phase 4; sync
  is assumed to happen via git.

### 8.3 Accessibility

- WCAG 2.1 AA baseline: keyboard navigability, visible focus,
  sufficient contrast, ARIA roles for dynamic regions (events feed,
  approvals inbox).
- Screen-reader live regions for "new approval requested" and "task
  blocked" notifications.
- High-contrast theme + configurable text size.
- No colour-only encoding: every colour-coded status also has a glyph
  (badge icon, text label).

### 8.4 Internationalisation

Copy strings externalised (en-US default). Dates/times in user
locale. Right-to-left layout support deferred.

### 8.5 Offline operation

The UI is local-first; its MCP backend runs on the same machine. If
`.agent/` is mounted from a cloud drive that goes offline, the UI
shows a read-only banner and queues proposals locally, flushing on
reconnect.

### 8.6 Security

- Local MCP connection via stdio or loopback websocket only.
- Share-link mode requires explicit user opt-in with a generated
  token, never serves the raw filesystem, and supports expiration.
- Secrets (env vars for messenger) are never displayed; only their
  variable names.

### 8.7 Windows-first

Claudovka targets Windows + WSL primarily (phase2 §2.1). The UI
toolkit must behave natively on Windows 10/11: HiDPI correct, native
window chrome optional, file-path handling is Windows-aware (forward
slashes accepted but displayed as the host style).

### 8.8 Extensibility

Plugins (Claudovka-marketplace plugins) may contribute UI panels. A
minimal panel API:

- Register a sidebar entry with icon, label, target URL.
- Register a right-panel widget subscribed to a filter of events.
- Register a command palette action.

No arbitrary code execution in the UI process — panels render
markdown + a constrained DSL (similar to VS Code's webview
contribution model).

---

## 9. Survey of Similar Tools (Informing Choices)

### 9.1 Linear

- Strong at keyboard-first navigation (Cmd-K command palette),
  instant sync via a websocket-backed client, well-tuned list
  virtualisation for issues.
- Kanban views, swim lanes, "workflow" state machines per project.
- Adopt: command palette prominence; keyboard navigation as a
  first-class citizen; crisp list virtualisation.

### 9.2 Notion

- Inline editing with slash-command insertions, database views
  (table / board / calendar), nested page hierarchy.
- Adopt: markdown-first editing with slash-commands for structured
  inserts (e.g., /task, /tc); nested entity navigation.
- Reject: the "everything is a page" model collapses entity type,
  which the redesigned `.agent/` explicitly separates.

### 9.3 n8n

- Node-based workflow editor with live execution preview;
  drag-to-connect; per-node configuration panel on the right.
- Adopt: node-graph UX with side-panel details; execution preview
  with live-updating nodes.

### 9.4 Langflow

- Python-centric DAG editor with runtime visualisation; emphasizes
  flow + parameter editing.
- Adopt: parameter editing inline with node selection.

### 9.5 Retool

- Low-code internal tool UI; component drag-and-drop onto a canvas;
  server-backed data bindings.
- Adopt: binding expressions for custom panels (e.g., a user-defined
  "Top tasks by cost today" list).

### 9.6 Zed

- Rust-native editor; remarkably fast; collaborative cursors;
  LSP-native.
- Adopt: Zed's pane model (nested splits), collaborative cursor
  design if multi-user is added, LSP integration quality.

### 9.7 VS Code

- Extension model, command palette, Problems / Terminal / Output
  panel pattern, activity bar.
- Adopt: the activity bar + bottom panel paradigm for a familiar
  developer feel.

### 9.8 Summary of adopted patterns

- Kanban + list + graph views per entity type (Linear + Notion).
- Cmd-K command palette (Linear, VS Code).
- Node/graph editor for pipelines (n8n, Langflow).
- Pane-and-tab editor shell (VS Code, Zed).
- Slash-commands in markdown editor (Notion).
- Bottom panel for Problems/Terminal/Events (VS Code).

---

## 10. Out of Scope (Phase 4)

- Real-time collaborative editing of the same design document
  (Zed-style co-cursors). Phase 7 candidate.
- Mobile app. Binartlab already has a mobile package (BL-2 in
  phase1) that is undocumented; UI strategy for mobile is deferred.
- In-UI AI chat (beyond surfacing agent events). The UI observes
  agents; it does not replace the Claude Code chat pane.
- Schema migration UI. Migration phases M0-M6 in phase2 are run by
  scripts; UI only displays migration progress, not driving it.

---

## 11. Acceptance Checklist (TC-013)

- [x] Requirements for all workflow entity types (adventure, task,
  plan, design, manifest, metrics, knowledge, role, skill, events,
  permissions, messenger, runs) — §§1.1-1.13.
- [x] Live update requirements with latency budgets, reconnection,
  optimistic updates — §2.
- [x] Interaction patterns (lead-propose/user-approve, cascades,
  approvals, batch) — §3.
- [x] Read/write authority matrix aligned with phase2 writer
  arbitration — §4.
- [x] Node/graph editor requirements for adventure, lifecycle,
  cascade, DSL round-trip — §5.
- [x] DSL editor requirements (Ark, PDSL, markdown, JSONL, YAML)
  with LSP integration — §6.
- [x] Tabs/panes system requirements — §7.
- [x] Non-functional requirements: latency, multi-user,
  accessibility, offline, Windows-first — §8.

---

## Appendix A — Upstream Inputs

- `phase1-cross-project-issues.md` §§3.1-3.2 (anti-patterns to
  avoid, patterns to preserve including "lead-proposes,
  user-approves").
- `phase2-concept-catalog.md` §§1-10 (entity vocabulary, renames,
  new entities).
- `phase2-entity-redesign.md` §§1-17 (per-entity before/after and
  writer arbitration tables).
- `phase2-knowledge-architecture.md` §§1-2 (event substrate, lock
  tiers, latency budget).
