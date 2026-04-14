---
task: ADV007-T008
adventure: ADV-007
phase: 2
target_conditions: [TC-005]
upstream:
  - .agent/adventures/ADV-007/research/phase2-concept-catalog.md
  - .agent/adventures/ADV-007/research/phase1-cross-project-issues.md
  - .agent/adventures/ADV-007/research/team-pipeline.md
companion: phase2-entity-redesign.md
researched: 2026-04-14
---

# Phase 2 — Unified Knowledge Architecture (Parallelism & Token Economy)

This document specifies the **storage layout, parallelism model, event
model, and migration plan** for a unified Claudovka knowledge base that
spans team-pipeline, team-mcp, binartlab, claudovka-marketplace, and
Pipeline DSL. It is the architectural blueprint whose per-entity diffs are
elaborated in the companion entity-redesign document.

Two constraints dominate every decision below:

1. **Parallelism constraint.** Agents must be able to run concurrently
   (multiple agents in one adventure, multiple adventures in one project,
   multiple projects sharing one user) without last-write-wins corruption
   of `.agent/` state. The current layout has three separate hazards: X6
   (non-atomic writes), X7 (aspirational concurrency control), and the
   ownership-boundary matrix in phase1 §1.4 where the same file has two
   or three legitimate writers.
2. **Token-economy constraint.** Every agent invocation pays a prompt
   cost proportional to the files it must read to act. The present layout
   auto-loads the first 200 lines of per-role `MEMORY.md`, the full
   manifest, permissions, and often the full `adventure.log`. On ADV-007
   alone the manifest is ~95 lines, the concept catalog is ~820 lines,
   and the permissions doc is many KB. The architecture must shard and
   slice so that the per-spawn context is bounded by the task's needs,
   not by the adventure's history.

---

## 1. Architecture at a Glance

```
.agent/                                 (project root; unchanged name)
|-- config.md                           single-writer: user
|-- registry/                           GENERATED; read-only to agents
|   |-- stages.json                     from one Ark spec (resolves X1)
|   |-- transitions.json
|   |-- tools.json
|   |-- skills.json
|   |-- agents.json
|   |-- commands.json
|-- schema/                             canonical Ark specs + codegen
|-- tasks/                              free-standing (non-adventure) tasks
|-- adventures/
|   `-- ADV-NNN/
|       |-- manifest.md                 FROZEN after activation; small
|       |-- manifest.evaluations.jsonl  APPEND-ONLY; one row per update
|       |-- manifest.targets.jsonl      APPEND-ONLY; TC proofs as events
|       |-- events.jsonl                APPEND-ONLY; single source of truth
|       |-- views/                      DERIVED; regenerable from events
|       |   |-- manifest.rendered.md
|       |   |-- evaluations.rendered.md
|       |   `-- tc-table.rendered.md
|       |-- designs/                    one file per design; single-writer
|       |-- plans/                      one file per plan; single-writer
|       |-- tasks/
|       |   `-- ADVnnn-Tnnn/            PROMOTED from file to directory
|       |       |-- task.md             frontmatter + description only
|       |       |-- log.jsonl           APPEND-ONLY; replaces ## Log
|       |       |-- iterations.jsonl    APPEND-ONLY; review/fix cycles
|       |       `-- artifacts/          binary / large outputs
|       |-- reviews/                    one report per task-iteration
|       |-- roles/                      per-adventure custom role prompts
|       |-- permissions/                SHARDED; one file per scope
|       |-- research/                   research artefacts (this dir)
|       `-- tests/                      verification artefacts
|-- knowledge/                          collapsed (was split + memory)
|   |-- lessons.jsonl                   APPEND-ONLY union store
|   `-- views/
|       |-- patterns.rendered.md        DERIVED
|       |-- issues.rendered.md
|       |-- decisions.rendered.md
|       `-- role-<name>.rendered.md     per-role slice (replaces agent-memory)
|-- lead-state/                         SHARDED directory, not one file
|   |-- active.jsonl                    APPEND-ONLY: heartbeats & claims
|   `-- sessions/
|       `-- <session-id>.json           per-session micro-state
`-- messenger/
    |-- channels.md                     single-writer declarations
    `-- approvals.jsonl                 APPEND-ONLY; persists across restart
```

The two structural moves that make this layout parallelism-friendly are
(a) **promoting every multi-writer markdown file to an append-only
jsonl** and (b) **promoting every high-contention scalar file (task.md,
lead-state.md) to a directory with single-writer files and one log**.

---

## 2. Parallelism Constraints

### 2.1 Lock granularity

The current team-mcp LockManager (phase1 H2/H3) has two flaws: locks are
in-memory only, so they are lost on server restart, and the scope is
limited to `agent_spawn` / `agent_complete`. The redesign adopts three
lock tiers:

| Tier | Scope | Backing | TTL | Acquired by |
|---|---|---|---|---|
| **Coarse** | `.agent/{adventure,tasks,knowledge,lead-state}` subtree | file-lock (`.lock` marker with pid+ts) | 30 s (renewable) | any writer |
| **Fine** | single markdown file (e.g. `tasks/T123/task.md`) | advisory: sidecar `.{file}.lock.json` with `{session, pid, acquired_at, renew_at}` | 10 s (renewable every 3 s) | single-writer file mutations only |
| **None** | append-only `.jsonl` files | atomic `O_APPEND` write of one line terminated by `\n` | n/a | any writer, any concurrency |

The *none* tier is the default for all high-traffic state. Append-only
jsonl with a single-line write is atomic on every POSIX filesystem and on
NTFS (the Claudovka runtime target: Windows + WSL) when a writer opens
with append mode and writes under the POSIX `PIPE_BUF` (4 KB). Every
event payload in the redesign is engineered to stay under 2 KB so a
single `write()` call is durable and indivisible.

### 2.2 Atomic write strategies

For every file that still requires mutation (manifest header,
permissions docs, rendered views), the canonical write sequence is:

```
1. acquire fine-tier lock on target path
2. write payload to {target}.tmp in same directory
3. fsync(tmp)
4. rename({tmp}, {target})           // atomic on POSIX; MoveFileExW on NTFS
5. release lock
```

This fixes X6 (non-atomic writes) uniformly. The same-directory
temp-file rule is essential on NTFS: `rename` across directories is not
atomic.

### 2.3 Writer arbitration

The phase1 data-ownership matrix (§1.4) listed every cell where two or
more projects legitimately write the same file. The redesign collapses
each such cell to exactly one writer using the "MCP is the single
writer" principle extended to cover every multi-owner surface:

| State | Before (writers) | After (writer) |
|---|---|---|
| `tasks/*/log.jsonl` | TP agents, TM `task_update`, BL | TM `pipeline.task_append` |
| `adventures/{id}/events.jsonl` | TP, TM, (future) BL | TM `pipeline.event_append` |
| `adventures/{id}/manifest.evaluations.jsonl` | TP researcher, TM `adventure_metrics` | TM `pipeline.eval_append` |
| `knowledge/lessons.jsonl` | TP researcher, TM `knowledge_*`, BL UI | TM `pipeline.lesson_append` |
| `lead-state/active.jsonl` | TP lead, TM heartbeat, BL agent | TM `pipeline.heartbeat` |
| `messenger/approvals.jsonl` | TM in-mem, BL UI | TM `pipeline.approval_*` |

Every writer above is a TM tool. TP agents, BL UI, and future
integrations all call TM; direct file I/O fallback (the
`try-MCP-then-fs` boilerplate in phase1 anti-pattern #5) is removed.
Write conflicts are impossible because the tool serialises all writes
through an in-process queue per file.

Read access remains free-for-all: anyone may `cat` a jsonl and
reconstruct state by replaying events. This asymmetry (one writer, many
readers) is the "event-sourced CQRS" pattern applied to a markdown
substrate.

### 2.4 Concurrency units

Three concurrency scopes are supported, each with independent contention
envelopes:

1. **Intra-adventure parallelism.** Multiple agents active on distinct
   tasks of one adventure. Contention surfaces: `events.jsonl`,
   `manifest.evaluations.jsonl`, `lead-state/active.jsonl`. All are
   append-only, so raw throughput is bounded only by tool-queue latency
   (target p50 < 50 ms).
2. **Inter-adventure parallelism.** Multiple adventures progressing in
   parallel within one project. Contention surfaces: only
   `knowledge/lessons.jsonl`, `lead-state/active.jsonl`,
   `messenger/approvals.jsonl`. All append-only.
3. **Inter-project parallelism.** The user switches between projects or
   two Claude Code sessions work two projects simultaneously. No shared
   files. Config, marketplace cache, and binartlab DB are the only
   cross-project surfaces and they are user-owned or BL-owned.

### 2.5 Crash recovery and conflict detection

Because every mutation produces one event in `events.jsonl` before the
rendered view is regenerated, a crashed agent always leaves a consistent
log plus a potentially stale view. Recovery is:

```
events.jsonl  -- truth
views/*.md    -- regenerate from events on session start
```

A reconciler runs at lead session start (replacing the current
`SessionStart` hook prompt). It reads `events.jsonl` offsets recorded in
`views/.offset`, replays new events, and re-renders every view. The
operation is deterministic, idempotent, and unit-testable.

---

## 3. Token-Economy Constraints

### 3.1 Per-agent context budget

The current ADV-007 workflow auto-injects into every researcher spawn:
~200 lines of role MEMORY.md + manifest (~95 lines) + the task file +
the design + the review report + permissions. Non-trivial tasks spawn
with 30-50 KB of context before the agent has read anything
domain-specific. The redesign sets a hard budget and aligns entity
shapes to it:

| Tier | Agent | Budget (tokens) | Must-load | May-load |
|---|---|---|---|---|
| T1 | Researcher, reviewer | 8 KB | task.md, design, review report, 1 rendered knowledge view | events.jsonl tail |
| T2 | Planner, adventure-planner | 12 KB | manifest header only, plan, designs index | targeted task files |
| T3 | Implementer, coder | 10 KB | task.md, design, permissions for its scope | events.jsonl tail for its task |
| T4 | Lead | 20 KB | config, lead-state/active.jsonl (head=20 lines), current adventure manifest header, messenger/approvals.jsonl tail | on-demand |

The auto-injected context is now **the subset of the knowledge base
scoped to the agent's role and the current task**, not the first 200
lines of a monolithic file. Budgets are enforced at spawn time: the
lead refuses to spawn an agent if the auto-prompt exceeds the tier
budget.

### 3.2 Entity-design rules that keep budgets small

Four rules follow from the budget table:

1. **Small-file rule.** Any entity that multiple agents read on every
   invocation MUST live in a file smaller than 4 KB. This bans the
   current `manifest.md` growing evaluations/TC tables inline; those
   tables move to `manifest.evaluations.jsonl` and
   `manifest.targets.jsonl` with rendered slices in `views/`.
2. **Role-sliced views.** `views/role-<name>.rendered.md` contains only
   the lessons, issues, and decisions tagged `role:<name>`. A
   researcher spawn loads the `role-researcher` slice; a coder loads
   `role-coder`. The current AgentMemory behaviour is preserved as a
   derived view, not as a parallel store.
3. **Append-only tails.** Agents load the last N lines of an
   append-only log rather than the whole log. For `events.jsonl`,
   `log.jsonl`, and `iterations.jsonl`, the default tail is 50 lines
   (~5 KB). The MCP tool `pipeline.log_tail(path, n)` is the canonical
   accessor.
4. **Directory-sharded entities.** Any entity that previously
   accumulated within one markdown file as "rows of a table" (manifest
   evaluations, TC table, permissions scopes) is sharded into a
   directory of short files or one jsonl. Agents load only the shards
   relevant to their task.

### 3.3 Token-cost measurement

Estimation proxies (X11) are replaced by authoritative measurement: TM
reads per-tool-call `usage.input_tokens`/`output_tokens` from the
Anthropic response and writes them to `events.jsonl` as an
`agent.turn.completed` event. The rolled-up figure in
`manifest.evaluations.jsonl` is computed by summing those events; no
prompt-side estimation survives. This closes the measurement gap and
makes budget enforcement (§3.1) honest.

### 3.4 Per-agent slicing rules

When a TM tool is asked for an entity, it slices by the caller's
role and the caller's bound task:

- `task_get(id)` returns the task.md header + the last 30 lines of
  `log.jsonl` and `iterations.jsonl` — not the whole task history.
- `knowledge_get(kind?, role?)` returns the rendered view scoped to
  that role (or the unscoped view if no role is passed) — not
  `lessons.jsonl` raw.
- `adventure_get(id)` returns the manifest header (frontmatter + first
  30 lines of body) — not the full manifest including the evaluations
  and TC tables. A separate `adventure_evaluations(id, task?)` returns
  only the rows requested.
- `permissions_get(scope)` returns the single scope file (see §5) —
  not the full `permissions/` directory.

This slicing is the single largest token saving available: a
researcher spawn on ADV-007 drops from ~45 KB auto-injected to ~6 KB.

---

## 4. Storage Layout: Queries and Event Model

### 4.1 Canonical event stream

`events.jsonl` is the single ordered stream per adventure. Every event
is a JSON object on one line:

```json
{"v":1,"ts":"2026-04-14T02:07:00Z","type":"task.stage.advanced",
 "actor":{"role":"coder","session":"S-123"},
 "target":{"task":"ADV007-T008"},
 "payload":{"from":"implementing.in_progress","to":"reviewing.ready",
            "iteration":1}}
```

Mandatory fields: `v` (schema version), `ts`, `type`, `actor`,
`target`. Payload is type-specific. Types are drawn from the TM 11-event
vocabulary (phase2 catalog §4) extended with
`knowledge.lesson.appended`, `eval.recorded`, `approval.requested`,
`approval.resolved`.

### 4.2 Query patterns

Because the canonical substrate is markdown + jsonl, every query is a
file read + a line scan. The common patterns are:

| Query | File | Scan cost |
|---|---|---|
| "current state of task T" | `tasks/T/task.md` frontmatter | 1 read, ~1 KB |
| "history of task T" | `tasks/T/log.jsonl` tail 50 | 1 read, ~5 KB |
| "adventure evaluations" | `manifest.evaluations.jsonl` | 1 read, ~5-10 KB for a 20-task adventure |
| "researcher role lessons" | `views/role-researcher.rendered.md` | 1 read, ~3 KB (auto-sliced) |
| "what happened in ADV-007 in the last hour" | `events.jsonl` tail with ts filter | 1 read, ~5 KB |
| "who holds a write lock on X right now" | `lead-state/active.jsonl` tail | 1 read, ~2 KB |
| "TC-005 proof status" | `manifest.targets.jsonl` | 1 read, ~2 KB |

None of these require an index. Readers scan the tail of an
append-only file; writers append. The jsonl format is greppable, which
preserves the phase1 anti-pattern fix for "hand-curated catalogs":
every catalog is generated from the events, not hand-maintained.

### 4.3 Derived views

The `views/*.rendered.md` files are for human eyes and for agents that
prefer rendered markdown over jsonl. They are regenerated on demand by:

```
pipeline.views.regenerate(adventure_id, kinds?=[...], since?=ts)
```

Idempotent. Driven by the reconciler at session start and by the
researcher after each task. Agents must not write views directly.

### 4.4 Cross-project queries

For the binartlab SQLite mirror (BL keeps a read-optimised DB), the
write path is one-way: TM → events.jsonl → BL watcher → SQLite. BL
never writes back to `.agent/` except through TM tools. This preserves
the single-writer guarantee while giving BL the indexed queries its UI
needs (lists of 100s of tasks, time-range filters, cross-project
rollups).

### 4.5 Event schema evolution

The `v` field supports schema evolution. A breaking event-shape change
bumps `v`; readers handle both versions. This is the only place
cross-version compatibility (X4) must be explicit — everywhere else,
the `compatible-with` field on plugin/tool registration covers it.

---

## 5. Concurrent Adventures and Concurrent Agents

### 5.1 Within one adventure

Multiple agents run in one adventure when the planner parallelises
independent tasks. Guarantees provided by the architecture:

- Each agent has a unique `session` string recorded at spawn.
- Writes go through TM tools; each tool takes a fine-tier lock on the
  target file for the duration of its call.
- Append-only writes (events, logs, evaluations) do not need a lock.
- The lead reconciles at spawn time: before spawning agent B on
  task T2, the lead verifies no agent holds a lock on T2's files.
- Heartbeats (every 30 s) update `lead-state/active.jsonl`; stale
  agents (> 5 min with no heartbeat) are marked `stale_warn`, > 30 min
  `stale_critical` (thresholds from config, resolving TM-M3).

### 5.2 Across adventures within one project

The `.agent/knowledge/lessons.jsonl` is the only shared append-only
surface. Two researchers in two adventures appending simultaneously is
safe because of the sub-PIPE_BUF guarantee. The `lead-state/active.jsonl`
is shared; heartbeats are append-only.

The lead session itself is the only contested surface: today
`lead-state.md` is one file read-modify-write (TM-H4). The redesign
replaces it with `lead-state/active.jsonl` (append-only claims) plus
`lead-state/sessions/<session-id>.json` (one file per session; single
writer per file). The "current lead" is whoever owns the most recent
`lead.claim.acquired` event not followed by `lead.claim.released` —
computed on demand.

### 5.3 Across projects

Each project has its own `.agent/`. The only cross-project surfaces
are:

- `~/.claude/plugins/cache/claudovka-marketplace/...` — read-only to
  agents; mutated only by `plugin install/update`.
- `~/.binartlab/data.db` — BL-owned; WAL mode; one writer per
  connection, many readers.
- User's global `.claude/` directory — single-writer: the user.

No contention.

---

## 6. Migration Path from Current `.agent/`

The migration must be incremental because ADV-007 itself lives in the
current layout and is being executed under the current runtime. The
phased plan:

### Phase M0 — Shadow events (non-breaking)

- Add `events.jsonl` to every active adventure. Every TM tool that
  writes also appends an event. Existing markdown remains the source
  of truth.
- Cost: one new file per adventure, one extra write per tool call.
- Breaks nothing. Enables observation.

### Phase M1 — Views as derivations

- Add `views/` directory. Start regenerating
  `manifest.rendered.md` from the `manifest.md` header + events.
  Diff the rendered view against the live `manifest.md` to verify
  round-trip.
- When diff is clean for 1 week of real use, promote `manifest.md` to
  "header-only, generated body" status.

### Phase M2 — Promote append-only state

- Extract evaluations table into `manifest.evaluations.jsonl`. Render
  back into `manifest.md` from jsonl. TC table → `manifest.targets.jsonl`.
- Task `## Log` section → `log.jsonl` per task. Renderer writes the
  rendered log into `task.md` at session start.

### Phase M3 — Shard lead-state and permissions

- Split `lead-state.md` into `lead-state/active.jsonl` and
  `lead-state/sessions/*.json`.
- Split `permissions.md` into `permissions/<scope>/spec.md`.

### Phase M4 — Collapse memory into knowledge

- `agent-memory/<role>/MEMORY.md` entries migrated to
  `knowledge/lessons.jsonl` with `role:<name>` tags. The lead reads
  `views/role-<name>.rendered.md` on spawn instead of MEMORY.md.
- The `agent-memory/` directory is kept as a read-only symlink /
  regenerated view for one release cycle, then removed.

### Phase M5 — Atomic writes + fine locks

- All TM writes go through the atomic write sequence (§2.2).
- LockManager extended to fine-tier per-file scope (§2.1).
- Direct-fs fallback removed from hooks (resolves X8 path).

### Phase M6 — Registry generation

- `registry/*.json` generated at server start from the Ark trunk
  spec (stages, transitions, tools, skills, agents, commands).
- Agents read `registry/` instead of hand-maintained prose
  catalogs. Resolves X3.

Each phase is independently shippable and independently rollback-able.
No phase requires a flag-day migration; new adventures can adopt the
new layout while old adventures continue on the old layout until
reconciled.

### 6.1 Compatibility shims during migration

For the overlap window, TM exposes `pipeline.layout_version(path)` so
BL and hooks can detect which scheme they are dealing with. The two
layouts share `registry/` (forward-compatible) and differ only in
`tasks/` and `adventures/`.

---

## 7. Design Checklist Against Target Conditions

- **Explicit parallelism constraints**: §2 covers lock granularity,
  atomic writes, writer arbitration, concurrency units, crash
  recovery.
- **Token-economy constraints**: §3 covers per-agent context budgets,
  small-file and role-slicing rules, authoritative measurement.
- **Storage layout, query patterns, event model**: §§1, 4.
- **Concurrent adventures and agents**: §5.
- **Migration path from current `.agent/`**: §6.
- **Context for entity-redesign side-by-side tables**:
  phase2-entity-redesign.md (companion).

---

## 8. Open Questions (carried to T009+)

1. Should `events.jsonl` rotate at an event-count threshold (e.g.
   10k events → new file with `events.NNNN.jsonl` suffix)? Proposed
   yes; reconciler handles rollover.
2. Should `knowledge/lessons.jsonl` be global to the project or
   per-adventure? Proposed global; per-adventure rollups live in
   `research/` inside the adventure.
3. How are cross-project lessons shared? Proposed: a user-level
   `~/.claudovka/lessons.jsonl` as a write-through cache, opt-in.
4. Do we need a "read lock" tier? Proposed no — readers tolerate a
   view being mid-regeneration because the preceding rendered view is
   never deleted until the new one has been atomically renamed over
   it.
5. How does the DSL trunk (Ark) encode the event schema? Proposed:
   `ark/specs/events/pipeline.ark` with codegen to JSON Schema for
   TS-side consumers.

Resolving these is the input to T016 (Phase 3.2 integration matrix)
and the DSL unification work in Phase 6.1.

---

## Appendix A — Upstream Inputs

- `phase2-concept-catalog.md` §§2, 4, 8, 11 (sub-graphs, storage
  family, event family, knowledge family).
- `phase1-cross-project-issues.md` X1, X6, X7, X8, X9, X11 and §1.4
  (data ownership matrix).
- `team-pipeline.md` §2 (Architecture Overview), §4 (Opportunities).

## Appendix B — Glossary

- **Append-only jsonl** — a file of UTF-8 JSON objects, one per line,
  each written with a single atomic `write()` call in append mode.
- **Fine lock** — an advisory sidecar lock on a single markdown file
  path; used only for mutable scalar files.
- **Rendered view** — a derived markdown file regenerated from an
  event stream; never hand-edited; readable by agents.
- **Event** — a typed one-line JSON record in `events.jsonl`
  (§4.1).
- **Reconciler** — the lead-invoked routine that replays events and
  regenerates views at session start.
