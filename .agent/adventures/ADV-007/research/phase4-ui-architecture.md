---
task: ADV007-T017
adventure: ADV-007
phase: 4
target_conditions: [TC-014]
upstream:
  - .agent/adventures/ADV-007/research/phase4-ui-requirements.md
  - .agent/adventures/ADV-007/research/phase2-entity-redesign.md
  - .agent/adventures/ADV-007/research/phase2-knowledge-architecture.md
  - .agent/adventures/ADV-007/research/phase1-cross-project-issues.md
researched: 2026-04-14
---

# Phase 4 — UI Component Architecture and Data Flow (Claudovka Studio)

This document specifies the component architecture, data flow, state
model, and integration points for the Claudovka Studio UI whose
requirements are captured in `phase4-ui-requirements.md` (TC-013). It
produces the architectural input for the technology evaluation
(TC-015) and the downstream implementation adventures.

Two principles drive every decision in this document:

1. **The event log is the single source of truth.** The UI never owns
   authoritative state. Every mutation becomes an event in
   `adventures/{id}/events.jsonl` (or the equivalent substrate for
   knowledge / messenger / lead-state), and the UI renders views from
   those events.
2. **MCP is the only write path.** The UI does not touch the
   filesystem directly, even though it runs on the same machine.
   Every mutation is an MCP tool call; every read either hydrates from
   a rendered view or subscribes to `pipeline://events`.

Together these two principles give the UI the same correctness
guarantees (optimistic concurrency, single-writer arbitration, crash
recovery) that the rest of the Claudovka backend now has — without
reimplementing any of them.

---

## 1. Architecture at a Glance

```
+--------------------------------------------------------+
| Claudovka Studio UI (renderer process / browser tab)   |
|                                                        |
|  +-----------+  +-------------+  +-----------------+   |
|  | Shell     |  | Entity      |  | DSL / Graph     |   |
|  | (layout,  |  | views       |  | editors         |   |
|  |  tabs,    |  | (list /     |  |  (Monaco + LSP, |   |
|  |  panels,  |  |  detail /   |  |   ReactFlow)    |   |
|  |  palette) |  |  timeline)  |  |                 |   |
|  +-----------+  +-------------+  +-----------------+   |
|        ^              ^                  ^             |
|        +--------------+------------------+             |
|                       |                                |
|          +------------+------------+                   |
|          | UI state store (Zustand / Redux)            |
|          |  - event-sourced cache                      |
|          |  - optimistic pending queue                 |
|          |  - render-view memoiser                     |
|          +------------+------------+                   |
|                       |                                |
|           +-----------v-----------+                    |
|           | Data access layer      |                   |
|           |  - query hooks         |                   |
|           |  - mutation hooks      |                   |
|           |  - subscription hooks  |                   |
|           +-----------+-----------+                    |
+-----------------------|--------------------------------+
                        |
         WebSocket / stdio bridge (MCP client SDK)
                        |
+-----------------------v--------------------------------+
| MCP bridge (local HTTP+WS server; in-process or sidecar)|
|                                                        |
|  +--------------+  +--------------+  +-------------+   |
|  | Tool proxy   |  | Event fanout |  | Static      |   |
|  | (forward MCP |  | (pipeline:// |  | renderer    |   |
|  |  tool calls) |  |  events)     |  | serves      |   |
|  |              |  |              |  | views/*.md  |   |
|  +------+-------+  +------+-------+  +------+------+   |
|         |                 |                 |          |
+---------|-----------------|-----------------|----------+
          |                 |                 |
          v                 v                 v
+--------------------+  +-----------+  +--------------+
| team-mcp           |  | .agent/   |  | rendered     |
| (stdio MCP server) |  | events    |  | views/*.md   |
| 40+ pipeline.*     |  | .jsonl    |  | (on disk)    |
| tools              |  +-----------+  +--------------+
+--------------------+
```

The UI is three concentric layers: **shell** (layout, navigation,
input), **entity views** (list / detail / timeline / graph per entity),
and **editors** (markdown / DSL / code / graph). All three sit on a
single **UI state store** that is authoritatively populated by one
**data access layer** which talks only to the **MCP bridge**. The
bridge is the sole component that talks to team-mcp, the filesystem
rendered views, or binartlab.

---

## 2. Component Architecture

### 2.1 Shell layer

Components:

- **AppShell**: the root layout (sidebar, activity bar, main content,
  bottom panel, right panel). Owns workspace persistence and keyboard
  shortcuts. Lifts connection state banner.
- **Sidebar**: entity tree with virtualised lists per section
  (Adventures, Knowledge, Roles, Skills, Permissions, Messenger,
  Events, Metrics).
- **ActivityBar**: navigation bar (VS Code style) switching between
  Explorer / Search / Events / Extensions / Settings.
- **TabContainer**: per-pane tab strip with drag-reorder and
  split-on-drag.
- **PaneSplit**: recursive 1-4 split with resizable dividers;
  serialisable layout tree.
- **BottomPanel** and **RightPanel**: toggleable host for Problems /
  Terminal / Output / Events / Agents / Outline.
- **CommandPalette**: Cmd-K modal with fuzzy search over a command
  registry; each command is `{id, title, category, keybinding?,
  handler}`. Commands may be contributed by plugins.
- **Notifier**: toast queue plus a persistent notifications pane.

### 2.2 Entity views layer

Per entity type (Adventure, Task, Plan, Design, Role, Skill, Lesson,
Permission, Messenger, Run), a triad of views:

- **ListView**: virtualised data grid with column config, filters,
  sort, saved view presets.
- **DetailView**: split-frame with header (frontmatter / manifest
  metadata), body tabs (markdown, structured sub-entities), and a
  live-event tail panel.
- **TimelineView** (where relevant): chronological event stream
  filtered to that entity.
- **GraphView** (adventure, pipeline, cascade): node-graph with
  selectable nodes and side-panel details.

Each view consumes the state store via typed hooks
(`useAdventureList`, `useTask(taskId)`, `useEventsForTask(taskId)`,
`useMutationApproveProposal`, etc.). All hooks return `{data,
status, error, mutate}` shapes.

### 2.3 Editors layer

Editors are wrappers around third-party editor engines:

- **MarkdownEditor**: rich-text + source modes; slash-commands for
  entity inserts (e.g., `/task`, `/tc`, `/lesson`); live preview;
  cross-reference resolution (`[[task:ADV007-T017]]`).
- **DslEditor**: Monaco-based, Ark LSP client. Language registry
  supports Ark, PDSL (via Ark shim), YAML, JSON. Inline diagnostics
  gutter, problems aggregation.
- **JsonlViewer**: read-only virtualised viewer for event streams;
  structured expand/collapse per line.
- **GraphEditor**: React Flow (or Cytoscape) canvas backing the
  node-graph editor §1.5; emits graph mutations as MCP proposals.

### 2.4 Component dependency diagram

```
AppShell
  Sidebar ----> state.entities.adventures / knowledge / ...
  TabContainer
    Pane
      EntityView(route)
        ListView | DetailView | TimelineView | GraphView
          MarkdownEditor | DslEditor | JsonlViewer | GraphEditor
  CommandPalette ----> state.commandRegistry
  Notifier ----> state.notifications
```

No entity view depends on another entity view directly; cross-entity
navigation goes through the URL router (`/adventures/:id/tasks/:tid`
etc.), which is the canonical inter-component language.

---

## 3. State Model

### 3.1 Event-sourced cache

The UI state store is split into three regions:

1. **`views`**: materialised projections for list and detail views.
   Keyed by entity type + id. Updated by applying events in order.
2. **`events`**: ring buffer of the last N received events (default
   N=5000). Used for timeline view and replay scrubber.
3. **`pending`**: optimistic queue of user-initiated mutations
   awaiting server acknowledgement.

On startup the UI:

1. Fetches the last-known event offset from local storage (or 0).
2. Subscribes to `pipeline://events?offset=<saved>`.
3. Receives a hydration batch (bounded, e.g., 2000 events) that
   covers the gap.
4. Server continues streaming new events as they happen.
5. UI stops relying on local storage once the stream is flowing.

### 3.2 Source of truth

Per layer:

| State | Source of truth | UI copy |
|---|---|---|
| Adventure / task / plan headers | `{task,adventure}.md` frontmatter | hydrated from rendered view on open; updated by `*.state_change` events |
| `log.jsonl`, `events.jsonl` tails | jsonl on disk | mirrored as a ring buffer in `events` region |
| Rendered markdown (TC table, evaluations, metrics) | `views/*.rendered.md` regenerated by reconciler | lazy-fetched; invalidated on `view.regenerated` event |
| Active agent list, heartbeats | `lead-state/active.jsonl` tail | updated on `heartbeat.*` events |
| Lessons / knowledge | `knowledge/lessons.jsonl` | updated on `lesson.appended` / `lesson.amended` events |
| Approvals inbox | derived from `approvals.jsonl` tail | updated on `approval.*` events |

### 3.3 Optimistic updates

Every user mutation routes through the data access layer as
`proposeMutation(intent)`:

1. Client generates `client_request_id = uuid()` and the expected
   event payload.
2. `pending` queue gains an entry `{id, intent, ts, status: 'pending'}`.
3. UI immediately overlays the projected event onto `views` so the
   user sees the new state.
4. MCP call is sent to the bridge.
5. On success (event emitted by server matching the `client_request_id`),
   the optimistic overlay is replaced by the real event. Pending entry
   marked `applied`.
6. On rejection, optimistic overlay is rolled back; a toast cites the
   rejection reason; pending entry marked `rejected`.
7. Timeout after 10 s: rollback + offline banner; entry marked
   `timed_out` and kept in pending until the user retries or
   connection returns.

### 3.4 Sync and consistency

Total order: the server assigns a monotonically increasing `offset`
field to each event it emits. The UI orders all events by `(offset)`,
breaking ties by server-assigned `seq` within the same atomic write.

Cache invalidation: when the server regenerates a view (reconciler
pass), it emits a `view.regenerated {path}` event. The UI invalidates
any cached fetch of that path and re-fetches on next access.

Offline queue: if the connection drops, `pending` entries stay
queued. On reconnect, the UI replays them in order, using their
`client_request_id` to deduplicate against any events the server
already applied during the outage.

### 3.5 Store implementation

Zustand + Immer is the recommended technology for the state store
(see technology evaluation doc for rationale). Key invariants:

- Slices per entity type to keep reducer size manageable.
- Subscriptions are selector-based so views only re-render when
  their projection changes.
- Event application is pure: `(state, event) → state`; pure allows
  `events` to be replayed for scrubber mode.
- Optimistic overlays live in a separate slice that is merged
  on-read, so rolling them back is O(1).

---

## 4. Data Flow

### 4.1 Read path

```
User opens "ADV-007 tasks" tab
  → useTaskList(adventureId="ADV-007")
    → state store sees no cache
      → DAL.queryTaskList("ADV-007")
        → MCP bridge forwards pipeline.task_list(adventureId)
          → team-mcp returns JSON list
        → MCP bridge also subscribes to pipeline://events?filter=task.*&adventure=ADV-007
          (if not already subscribed)
      → state.views.taskList["ADV-007"] = list
    → useTaskList returns the list
```

Subsequent events for those tasks arrive on the subscription and
update `state.views.taskList["ADV-007"]` in place; the component
re-renders via Zustand selector.

### 4.2 Write path

```
User clicks "Advance to reviewing"
  → DAL.proposeMutation({
      intent: "task.advance",
      taskId: "ADV007-T017",
      toStage: "reviewing",
      client_request_id: uuid()
    })
  → pending queue += {id, intent, ts, status:"pending"}
  → optimistic overlay: state.views.task["ADV007-T017"].stage="reviewing"
  → UI re-renders instantly
  → MCP bridge.call(pipeline.task_advance, {taskId, toStage, client_request_id})
    → team-mcp:
        checks writer arbitration (fine-tier lock on task.md)
        appends event {type:"task.stage_changed", payload:{taskId,from,to},
                       client_request_id, offset:N+1}
        atomic write of tmp+rename for task.md header
        returns {offset: N+1}
  → team-mcp emits event on pipeline://events
  → UI bridge receives event, state store applies it
  → optimistic overlay is reconciled (matched by client_request_id)
  → pending queue marks applied
```

### 4.3 Subscription fan-out

The MCP bridge maintains a single shared subscription per filter to
`pipeline://events`. Multiple UI components using the same filter
share a reference-counted upstream subscription. This matters because
team-mcp's event ring buffer is limited (phase1 TM-L3); unified
subscriptions avoid redundant replays on open.

### 4.4 Rendered-view access

Some data is served from on-disk rendered views rather than as live
events: the manifest's rendered TC table, rendered evaluations,
`knowledge/views/role-<name>.rendered.md`. The UI requests these via
`pipeline.view_read(path)` (a new MCP tool), which reads the file and
returns its contents plus its `last_regenerated_at`. The UI caches
the content keyed by path; a `view.regenerated` event invalidates the
cache.

---

## 5. Integration Points

### 5.1 team-mcp (primary backend)

- **Transport**: stdio (when Studio is bundled with team-mcp as a
  sidecar) or local loopback websocket (when Studio runs as a
  separate process).
- **Tools consumed**: ~40 `pipeline.*` tools. Every mutating UI
  action maps to exactly one tool call. New tools required for UI
  use:
  - `pipeline.view_read(path)`
  - `pipeline.event_replay(from_offset, to_offset?)`
  - `pipeline.subscribe_filtered(filter_dsl)` — adds filtering the
    current resource lacks (phase1 TM-M4)
  - `pipeline.permission_check(scope, role, action, path)` — the
    dry-run API §1.11
  - `pipeline.proposal_list(state?)`, `proposal_approve(id)`,
    `proposal_reject(id, reason)`
  - `pipeline.workspace_get()`, `workspace_set(layout)` — stores
    `.agent/ui-workspace.json`
- **Events consumed**: the 11 existing event types plus new types:
  `proposal.*`, `view.regenerated`, `lesson.appended`,
  `lesson.amended`, `approval.*`, `heartbeat.*`.
- **Version negotiation**: the UI declares `compatible-with` ranges
  for team-mcp (phase1 X4 fix); mismatch shows a banner and
  read-only mode.

### 5.2 team-pipeline (hook-producing plugin)

The UI does not talk to team-pipeline directly. It observes
team-pipeline's effects through the event substrate: hooks emit
events via team-mcp, and the UI sees them as any other event.

If a hook is still LLM-backed (phase1 X8 not yet resolved), the UI
may display the hook's natural-language output on a per-event panel
but will not re-run the hook.

### 5.3 Knowledge base

Two touchpoints:

- Reading: `pipeline.lesson_list(filter)` and `view_read` on
  rendered role slices.
- Writing: `pipeline.lesson_append` from the "Add lesson" modal;
  `pipeline.lesson_amend` for amendments.

No direct filesystem access; the UI never reads `knowledge/lessons.jsonl`
except through the MCP stream.

### 5.4 Binartlab (optional)

When binartlab is running, the UI can optionally connect to
binartlab's web-api (REST + websocket) for project/run management.
The UI exposes a "Binartlab" sidebar section that mirrors binartlab's
Projects / Agents / Runs pages. This integration is opt-in and uses a
separate DAL module (`dal/binartlab.ts`) so the core UI compiles and
runs without binartlab.

### 5.5 Messenger channels

The UI observes messenger state via `pipeline.channel_status` and
`approval.*` events. Outbound channel messages are proposed through
`pipeline.channel_send_proposal`; the user may approve directly in
the UI, bypassing the round-trip to Telegram/Discord for local
approvals.

### 5.6 Marketplace / plugins

The UI contributions plugin (a future marketplace package) may
provide custom sidebar panels. The contribution host loads the
plugin's declared contributions at startup; the plugin itself does
not execute arbitrary JS — contributions are declarative (panel
definitions, command registrations, filter bindings).

---

## 6. Event / Notification Plumbing

### 6.1 Subscription DSL

Extending the existing `pipeline://events` resource with a filter
grammar:

```
topic     ::= "task" | "adventure" | "lesson" | "approval" | "heartbeat" | "view" | "proposal"
subtopic  ::= ".*" | ".<event-name>"
filter    ::= topic subtopic ("?" arg ("&" arg)*)?
arg       ::= key "=" value
```

Examples:

- `task.*?adventure=ADV-007` — all task events in adventure 007.
- `lesson.appended?role=reviewer` — only reviewer-scoped lessons.
- `proposal.*?requested_by=@me` — proposals awaiting my approval.

### 6.2 Notification taxonomy

UI notification priority levels:

- **silent**: feed-only (e.g., lesson appended).
- **toast**: transient in-UI toast (e.g., optimistic rollback).
- **persistent**: sticky banner until dismissed (e.g., connection
  lost, version mismatch).
- **approval**: interrupts the user — modal or approval-inbox badge
  counter increments.

The priority for each event type is declared in a table
(`notificationPolicy.json`) user-overridable in settings.

### 6.3 Delivery guarantees

At-least-once within the UI session (dedup by offset). Across
sessions the UI loads missed events on reconnect (§3.1). For
messenger approvals the guarantees are stronger: approvals persist
to `approvals.jsonl` so they survive MCP restart (phase2 messenger
fix, §11 in entity redesign).

### 6.4 Back-pressure

If events arrive faster than the UI can render, the bridge batches:

- Coalesce same-type events on the same entity to the latest one
  (e.g., rapid `heartbeat.tick` → keep the latest).
- Drop low-priority events first if the buffer fills (silent tier).
- Never drop approval or persistent events.

---

## 7. Router and URL Conventions

URLs are entity-addressable and shareable:

```
/adventures/ADV-007                    adventure detail
/adventures/ADV-007/tasks              task list
/adventures/ADV-007/tasks/ADV007-T017  task detail
/adventures/ADV-007/graph              dependency graph view
/adventures/ADV-007/timeline           timeline view
/knowledge?role=reviewer               knowledge feed, filtered
/knowledge/lessons/<lesson-id>         lesson detail
/permissions/ADV-007/<scope>           permission scope editor
/events?filter=proposal.*              events inspector with filter
/metrics?adventure=ADV-007             metrics dashboard
/roles/<name>                          role catalog entry
/skills/<name>                         skill detail
/runs/<run-id>                         run detail
```

Query parameters are bookmarkable filter state. Share-link mode wraps
these URLs behind a token-scoped proxy that strips mutation
capabilities.

---

## 8. Plugin / Extension Architecture

### 8.1 Contribution points

- **Sidebar panel**: `{id, title, icon, order, component-ref}`.
- **Command palette action**: `{id, title, category, handler-ref}`.
- **Right panel widget**: `{id, title, filter (event-filter DSL),
  component-ref}`.
- **Entity view tab**: `{entityType, label, component-ref}`.

### 8.2 Host protocol

Plugins run in-process with a capability-scoped API surface
(`registerPanel`, `registerCommand`, `useQuery`). No direct
filesystem or network access; all data goes through the shared DAL.

### 8.3 Authoring

Plugins are TypeScript packages shipped in the claudovka-marketplace
cache. The plugin descriptor declares contribution types in
`plugin.json`:

```json
{
  "name": "studio-burndown",
  "version": "0.1.0",
  "contributes": {
    "panels": [{"id":"burndown","title":"Burndown","icon":"📉","component":"./dist/Burndown.js"}]
  }
}
```

---

## 9. Error Handling

### 9.1 Error categories

- **Network**: bridge disconnected → banner + retry, pending queue
  preserved.
- **Version mismatch**: UI newer than MCP or vice versa → read-only
  banner, user prompted to upgrade.
- **Authorization**: mutation rejected by server policy → toast +
  rollback.
- **Schema**: event with unknown shape → logged to Problems panel;
  UI continues with best-effort rendering.

### 9.2 Problems pane

All schema errors, version mismatches, and unknown-event warnings
accumulate in the Problems pane (bottom panel), similar to VS Code's
Problems tab. Each entry links to the source event or request.

### 9.3 Crash recovery

On UI crash / reload:

1. Workspace layout restored from `.agent/ui-workspace.json`.
2. Pending queue restored from local storage.
3. Subscription resumed from last persisted event offset.
4. Server replays missed events (bounded).

---

## 10. Observability of the UI Itself

### 10.1 Metrics

The UI reports its own metrics back through MCP:

- Event ingest rate, render frame time, memory usage, connection
  uptime.
- Reported as a periodic `ui.metrics` event at 10-second intervals.
- Visible in the Metrics dashboard under a "UI" row.

### 10.2 Trace log

A structured trace log captures every DAL call with timing,
outcome, and related event offsets. Accessible via the Output panel.

---

## 11. Security Model

### 11.1 Trust boundaries

- **Inside the boundary**: UI renderer, MCP bridge, team-mcp, local
  filesystem, local binartlab.
- **Outside the boundary**: messenger endpoints (Telegram cloud,
  Discord), share-link viewers.

### 11.2 Secret handling

- Env-var names displayed; values never fetched.
- Share-link tokens scoped to read-only tools and optional
  per-adventure allowlist.
- Messenger outbound sends require explicit user approval (or a
  pre-configured auto-approve per channel).

---

## 12. Deployment Topologies

### 12.1 Bundled desktop

Electron or Tauri shell containing the renderer + MCP bridge + (as a
spawned subprocess) team-mcp. One binary to install; one MCP server.
Target topology for the lead operator.

### 12.2 Sidecar

Team-mcp already running (standard team-pipeline install); Studio
runs as a separate desktop app or a browser tab pointed at a local
bridge on loopback. Same UX, different packaging.

### 12.3 Share-link proxy

A tiny HTTP server (part of the MCP bridge) listens on a secondary
port when share-link mode is enabled. Serves a read-only
single-page-app that talks to a token-scoped MCP proxy. Suitable for
remote stakeholders; not suitable for untrusted networks.

---

## 13. Migration Strategy from Today's State

Today there is no UI; the lead operator works through the Claude
Code chat pane and a text editor. Phase 4 introduces the UI
incrementally:

1. **M4-UI-0 — read-only snapshot viewer.** A web-based read-only
   view of `.agent/` that loads rendered views and streams events.
   Delivers observability wins without mutation complexity.
2. **M4-UI-1 — approval-only writes.** Adds approve/reject actions
   for proposals. Still no direct mutations.
3. **M4-UI-2 — entity editing (task/log/lesson).** Adds writes for
   the lowest-risk entities first (log appends, lesson appends).
4. **M4-UI-3 — full mutation surface.** Adds design/plan/role
   editing, permission-scope editing, and batch actions.
5. **M4-UI-4 — graph editor and DSL round-trip.** The heavy
   investment: Ark LSP integration and round-trippable graph editor.
6. **M4-UI-5 — plugins and share links.** Extensibility and
   outside-observer support.

Each milestone is shippable independently; earlier milestones do not
block later ones beyond the state-store contract.

---

## 14. Acceptance Checklist (TC-014)

- [x] Component architecture with shell / entity-views / editors
  layers — §2.
- [x] State model: source of truth, sync, optimistic updates — §3.
- [x] Data flow diagrams for read, write, subscription, rendered
  view — §4.
- [x] Integration points with team-mcp, team-pipeline, knowledge
  base, binartlab, messenger, marketplace — §5.
- [x] Event/notification plumbing reusing pipeline://events MCP
  resource with filter DSL — §6.
- [x] Router / URL conventions — §7.
- [x] Plugin/extension architecture — §8.
- [x] Error handling, observability, security — §§9-11.
- [x] Deployment topologies — §12.
- [x] Migration strategy — §13.

---

## Appendix A — Upstream Inputs

- `phase4-ui-requirements.md` §§1-8 (requirements input).
- `phase2-entity-redesign.md` §§1-17 (writer arbitration matrix,
  rendered views, event substrate).
- `phase2-knowledge-architecture.md` §§1-2 (lock tiers, event log
  authority, reconciler).
- `phase1-cross-project-issues.md` X1, X4, X6, X7, X8, TM-L3, TM-M4
  (resolved by MCP-only writes, filtered subscriptions, offset
  ordering).

## Appendix B — Related tooling choices deferred to TC-015

- Renderer technology (Electron / Tauri / browser / plain web).
- UI framework (React + Next.js / SvelteKit / Solid / Lit).
- State store (Zustand / Redux Toolkit / Valtio / Jotai).
- Graph engine (React Flow / Cytoscape / Sigma).
- Editor engine (Monaco / CodeMirror 6).
- Styling (Tailwind + shadcn / CSS modules / vanilla-extract).

These choices are evaluated in
`phase4-technology-evaluation.md`.
