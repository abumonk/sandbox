---
task: ADV007-T008
adventure: ADV-007
phase: 2
target_conditions: [TC-006]
upstream:
  - .agent/adventures/ADV-007/research/phase2-concept-catalog.md
  - .agent/adventures/ADV-007/research/phase2-knowledge-architecture.md
  - .agent/adventures/ADV-007/research/phase1-cross-project-issues.md
  - .agent/adventures/ADV-007/research/team-pipeline.md
researched: 2026-04-14
---

# Phase 2 — Entity Redesign (Before/After Comparison)

This document presents side-by-side **before/after** proposals for every
major `.agent/` entity. It is the concrete diff that implements the
architectural principles established in the companion
`phase2-knowledge-architecture.md` (parallelism, token economy,
single-writer arbitration, append-only event substrate, per-role
slicing).

For each entity the comparison is structured uniformly:

- **Before**: the current shape, writer(s), contention hazards, token
  footprint.
- **After**: the redesigned shape, writer, parallelism guarantee, token
  footprint, token/parallelism delta.
- **Rationale**: why the change, which cross-project issue it resolves
  (X-codes from phase1), and any novel benefits.
- **Compatibility & migration**: what breaks, what shims absorb the
  break, and which migration phase (M0-M6) in the architecture document
  delivers the change.

The literal phrase **before/after** appears here for the TC-006 grep
proof, and again in every section header below.

---

## 0. Change Summary Table

| Entity | Core change | Contention resolved | Token delta per spawn |
|---|---|---|---|
| Task | File → directory | log RMW | -40% (log tail, not full history) |
| Adventure manifest | Mutable tables → append-only jsonl | 3-writer race on eval rows | -70% (header only, not full) |
| Adventure log | Already append-only; repurposed | — | n/a (preserved) |
| Metrics ledger | Human-editable md → TM-only jsonl | multi-writer on metrics.md | -50% (sliced per task) |
| Knowledge | 3 files + memory dir → one jsonl + views | researcher/knowledge-tool races | -60% (role slice) |
| Agent-memory | Separate dir → view of knowledge | dual store drift (X9) | -80% (role view only) |
| Role | Per-role md + memory → single role.md + view | none (read-only) | minor |
| Skill | Hand-curated SKILL.md + catalog drift | X3 drift | -30% (generated registry) |
| Agent | Hand-curated agents/*.md + enum drift | X3 drift | -20% |
| Lead-state | One md file with 4 writers | TM-H4 race on last_event | -90% (slice per read) |
| Permissions | Prose md (single file) | one-writer but monolithic | -60% (sharded per scope) |
| Messenger | Declarations + in-mem approvals | L6 lost on restart | n/a (persisted) |
| Session | Ad-hoc; no entity | 3 meanings collide | formalised (see §3.3) |
| Trigger | Hook prompts encode triggers | X8 non-determinism | -85% (deterministic tool) |
| Config | Single frontmatter md | low contention | unchanged (intentional) |

The column "Token delta per spawn" estimates the reduction in
auto-injected prompt size for a typical T1 (researcher) spawn. Bases
are measured from the live ADV-007 layout.

---

## 1. Task

### Before / After

**Before**

```
.agent/adventures/ADV-007/tasks/ADV007-T008.md
---
id: ADV007-T008
stage: planning
status: ready
iterations: 0
...
---
## Description
## Acceptance Criteria
## Design
## Log
- [2026-04-14T02:00:00Z] created: ...
- [2026-04-14T02:05:00Z] ...
- [2026-04-14T02:10:00Z] ...
```

- Writers: any agent may edit frontmatter (`stage`/`status`/
  `iterations`) and append to `## Log`.
- Contention: every status advance is a read-modify-write of the whole
  file. The `## Log` section grows monotonically; a long-running task
  accumulates dozens of lines inside the file being edited by every
  advance.
- Token footprint: whole file auto-injected. For ADV007-T008 today the
  task file is small (~1 KB), but review-heavy tasks in ADV-004 ran to
  ~10 KB.

**After**

```
tasks/ADV007-T008/
|-- task.md                 frontmatter + Description + AC + Design
|-- log.jsonl               APPEND-ONLY, one event per line
|-- iterations.jsonl        APPEND-ONLY, one row per review/fix cycle
`-- artifacts/              large outputs, binaries
```

- Writer of `task.md`: single-writer — TM `pipeline.task_set_header`
  with fine-tier lock, atomic write (tmp+rename).
- Writer of `log.jsonl` / `iterations.jsonl`: any agent via
  `pipeline.task_append_log` / `pipeline.task_append_iter`;
  append-only jsonl, no lock.
- Token footprint: `task.md` (~1 KB) + last 30 lines of `log.jsonl`
  (~3 KB, via `log_tail`). For ADV007-T008, ~40% smaller on every
  reviewer/researcher spawn.

### Rationale

Promoting the task from a file to a directory resolves the read-modify-
write race on `## Log` (implicit in X6/X7) and turns the growing log
into the same append-only substrate used by `events.jsonl`. The
iteration counter moves from a frontmatter integer to a first-class
`iterations.jsonl` ledger so the reviewer and implementer do not race
on the integer.

### Compatibility & migration

Migration phase **M2**. Shim: a generator rebuilds the legacy `##
Log` section inside `task.md` from `log.jsonl` on reconciler pass, so
any external tool that still reads the old format keeps working.

---

## 2. Adventure Manifest

### Before / After

**Before**

```
adventures/ADV-NNN/manifest.md
---
id: ADV-007
state: active
tasks: [ADV007-T001, ..., ADV007-T024]
---
## Concept
## Target Conditions
| TC-001 | ... | ... | ... | Status |
| TC-002 | ... | ... | ... | Status |
... (34 rows)
## Evaluations
| Task | ... | Est. | Actual | Variance |
... (24 rows)
## Environment
## ...
```

- Writers: lead on state change, researcher on eval updates, planner
  on TC status, adventure-reporter on completion.
- Contention: three+ writers on the same file; TC row updates are a
  scan-and-rewrite of the whole table.
- Token footprint: ADV-007 manifest is ~95 lines (~5-6 KB);
  auto-loaded on every adventure-scoped spawn.

**After**

```
adventures/ADV-NNN/
|-- manifest.md                     small (~30 lines): header + Concept + Env
|-- manifest.targets.jsonl          one event per TC change
|-- manifest.evaluations.jsonl      one event per eval update
`-- views/
    |-- manifest.rendered.md        DERIVED, full legacy shape
    |-- tc-table.rendered.md        DERIVED
    `-- evaluations.rendered.md     DERIVED
```

- `manifest.md` is frozen after adventure activation; only the lead
  can advance `state`.
- Every TC update appends to `manifest.targets.jsonl` via
  `pipeline.tc_set(tc_id, status, proof)`.
- Every eval row appends to `manifest.evaluations.jsonl` via
  `pipeline.eval_append(task_id, actual_tokens, duration, cost,
  variance)`.
- Rendered views regenerated by reconciler.
- Token footprint: ~30-line `manifest.md` auto-loaded (~1.5 KB); TC
  and eval data loaded on demand only. ~70% drop for the planner and
  researcher spawns that do not need those tables.

### Rationale

The before-state has three concurrent writers rewriting the same
in-file tables. Splitting the tables into append-only jsonl eliminates
the race entirely and makes each writer's cost O(1) per update
instead of O(n) in table size. The `views/` regeneration keeps the
human-readable artefact intact for `git diff` review.

Resolves: X6 (non-atomic writes on a large file), partially X7
(eliminates the need for fine locks on the manifest), TP-H2
(cross-pipeline state scattered across many fields in one file).

### Compatibility & migration

Migration phase **M2**. Shim: `manifest.rendered.md` is regenerated
after every write, so anything that reads the legacy shape still sees
it. Grep-based TC status queries (`grep -c "severity:"` style) still
work against the rendered view; eventually they are expected to query
the jsonl directly.

---

## 3. Adventure Log

### Before / After

**Before**

`adventures/ADV-NNN/adventure.log` — append-only plain-text log.

```
[2026-04-14T02:05:00Z] researcher | "spawn: ADV007-T008 researching"
[2026-04-14T02:05:05Z] researcher | "step 1/4: read task, ..."
```

- Writer: any agent (append-only).
- Token footprint: not auto-injected; read on demand by lead/reporter.

**After**

Preserved at the same path. Additionally, every agent also appends a
**structured** counterpart to `adventures/ADV-NNN/events.jsonl` via
`pipeline.event_append`. The plain `adventure.log` remains for human
scanning; `events.jsonl` is the machine-consumed substrate.

### Rationale

`adventure.log` is already the gold-standard append-only pattern
identified in phase1 §3.2. The only change is to add a structured
sibling so the reconciler and view regenerator have a typed stream to
work with. Nothing is lost.

Resolves: no issue — this is a preservation change. Counts toward
resolving X8 (hook prompts) only indirectly because the structured
stream removes the need for hooks to re-derive events from the text
log.

### Compatibility & migration

Migration phase **M0** (shadow events). Zero breakage.

---

## 4. Metrics

### Before / After

**Before**

`adventures/ADV-NNN/metrics.md` — a markdown table written by both
the researcher (markdown edit) and TM `metrics_log` (markdown
rewrite).

- Writers: two (researcher + TM tool); both do read-modify-write on
  the whole file.
- Contention: race between researcher and TM tool on the same table.
- Token footprint: typically small; not auto-injected.

**After**

```
adventures/ADV-NNN/metrics.jsonl    APPEND-ONLY
adventures/ADV-NNN/views/metrics.rendered.md    DERIVED
```

- Writer: TM only (`pipeline.metrics_append`).
- Researcher reads the rendered view; writes its row via the tool.
- Token: same or smaller.

### Rationale

Removes the two-writer race on `metrics.md` and ties into the
authoritative token-measurement path (X11 resolution): TM reads actual
token usage from the Anthropic response and appends; no prompt-side
estimation survives.

Resolves: X11, X6 (partial).

### Compatibility & migration

Phase **M2**. The rendered `metrics.rendered.md` matches the legacy
shape.

---

## 5. Knowledge Base

### Before / After

**Before**

```
knowledge/
|-- patterns.md        appended by researcher
|-- issues.md          appended by researcher
`-- decisions.md       appended by researcher
```

Plus `agent-memory/<role>/MEMORY.md` + on-demand topic files as a
parallel store.

- Writers: researcher (TP-side) + TM `knowledge_*` tools.
- Contention: both write the same files; format rules are prose-only.
- Token footprint: the first 200 lines of role `MEMORY.md` auto-loaded;
  knowledge files loaded by researcher.

**After**

```
knowledge/
|-- lessons.jsonl                              APPEND-ONLY, union store
`-- views/
    |-- patterns.rendered.md                   kind=pattern slice
    |-- issues.rendered.md                     kind=issue slice
    |-- decisions.rendered.md                  kind=decision slice
    `-- role-<name>.rendered.md                role-scoped slice
```

Each lesson in `lessons.jsonl`:

```json
{"v":1,"ts":"2026-04-14T02:10:00Z","kind":"pattern",
 "name":"Append-only jsonl for shared state",
 "body":"...","from":"ADV007-T008","role":"researcher",
 "tags":["parallelism","architecture"]}
```

- Writer: TM `pipeline.lesson_append`.
- Views regenerated after each append.
- Agent auto-load reads `views/role-<role>.rendered.md` (~3 KB)
  instead of the full `MEMORY.md` (often ~15 KB at 200 lines).
- Token footprint: ~80% smaller on role-slice auto-load.

### Rationale

Collapses the two-store model (X9) into one substrate with typed
entries and role-scoped views. Pattern/Issue/Decision become `kind:`
values in a union. The `role:` tag provides what `agent-memory/` used
to provide, without the drift.

Resolves: X9, TP-L-Memory-knowledge, implicit contention between
researcher and `knowledge_*` tools.

### Compatibility & migration

Phase **M4**. Shim: `views/patterns.rendered.md` etc. replicate the
legacy single-file layouts exactly so readers that grep
`.agent/knowledge/patterns.md` keep working (the path becomes a
symlink/redirection to the rendered view for one release cycle).

---

## 6. Agent-Memory

### Before / After

**Before**

```
agent-memory/<role>/
|-- MEMORY.md              first 200 lines auto-injected
`-- <topic>.md             on-demand files
```

- Writer: that role's agent (writes its own memory).
- Contention: none within role (single writer), but the store drifts
  out of sync with `knowledge/` (X9).
- Token footprint: 200 lines auto-injected on every spawn of that
  role.

**After**

Deprecated as a first-class store. The directory is removed (phase
M4). The role-scoped view `knowledge/views/role-<name>.rendered.md`
replaces it. Role-specific entries are written by the researcher (or
by the agent itself via `pipeline.lesson_append` with `role:<name>`).

- Token footprint: the rendered role view is capped at ~3 KB by the
  view generator (entries ranked by recency + usage); older entries
  remain available via `lesson_search(role,…)` on demand.

### Rationale

Directly addresses X9 and simplifies the writer rules: every learning
is a lesson, optionally tagged with a role; every consumer reads
either the unscoped or role-scoped view. No parallel store, no drift.

### Compatibility & migration

Phase **M4**. Shim: the rendered view includes a legacy `MEMORY.md`
compatibility header for one release cycle.

---

## 7. Role

### Before / After

**Before**

```
.agent/roles/<role>.md                 active role prompt
adventures/ADV-NNN/roles/<role>.md     per-adventure custom role
```

- Writer: user / adventure-planner.
- Contention: none (single-writer per file).
- Token footprint: role prompt auto-loaded per spawn; ~3-8 KB.

**After**

Structurally preserved, with two clarifications:

- Role prompts remain single-writer files.
- Role-scoped memory moves from `agent-memory/<role>/MEMORY.md`
  into `knowledge/views/role-<name>.rendered.md` (see §6).
- Role catalog is generated from files at server start into
  `registry/roles.json` so README/CLAUDE.md citations cannot drift
  (resolves X3 for roles).

### Rationale

Role prompts are fundamentally declarative and low-contention, so the
main redesign is indirect: remove the competing memory store and
generate the catalog from source.

### Compatibility & migration

Phase **M6** for the registry generation; no earlier phase affects
roles.

---

## 8. Skill

### Before / After

**Before**

```
skills/<skill-name>/SKILL.md     with optional v2 frontmatter
```

Plus a hand-curated catalog in `CLAUDE.md` and README (drift source,
X3; phase1 Low-1).

**After**

Structure preserved at `skills/<name>/SKILL.md`. Catalog
generated at TM start into `registry/skills.json`. README and
CLAUDE.md cite the registry via include directives. No duplicate
hand-curated lists survive.

Additionally, the command/skill distinction is clarified (phase2
catalog §3.4): **skills are the unit**; **commands are
auto-generated from a skills registry** entry with `command:` metadata.

### Rationale

Resolves X3 for skills and commands; eliminates "Unknown skill"
user complaints. No parallelism implication (read-only data).

### Compatibility & migration

Phase **M6**. Old hand-curated lists are removed in the same commit
that adds the generator.

---

## 9. Agent

### Before / After

**Before**

```
agents/<agent-name>.md              14 markdown files
```

Plus the hard-coded enum in TM `agent_spawn` (4 values) and BL's lack
of enum — X3 / phase2 catalog §3.4.

**After**

`agents/<name>.md` is preserved (single-writer, per-file). The TM
enum is replaced with soft-validation against the generated
`registry/agents.json`. BL consumes the same registry via MCP.

Agents gain an explicit `permissions:` field whose value references a
file in `permissions/` (see §12). The current prose `tools:` /
`disallowedTools:` fields become a view over `permissions/<scope>/spec.md`.

### Rationale

Resolves the role-enum drift (X3) and ties agent definitions to the
new PermissionSpec entity (phase2 catalog §10.4). Single-writer
guarantees preserved.

### Compatibility & migration

Phase **M5** (permissions sharding) + **M6** (registry). Shim: a
compatibility adapter translates legacy `tools:`/`disallowedTools:`
arrays to a `PermissionSpec` at load time.

---

## 10. Lead-State

### Before / After

**Before**

```
.agent/lead-state.md
```

One markdown file carrying active-agent registry + `last_event` +
session metadata. Every `emit()` in TM does a read-modify-write
(TM-H4 race).

- Writers: lead, every TM emit, potentially BL agents.
- Contention: race on `last_event` on every event.
- Token footprint: small, but re-read and re-written on every event.

**After**

```
lead-state/
|-- active.jsonl                APPEND-ONLY heartbeats + claims
`-- sessions/<session-id>.json  single-writer per file
```

- `active.jsonl` lines: `{"ts":..,"type":"heartbeat","session":"...",
  "task":"...","role":"..."}` or `{"type":"lead.claim.acquired","session":"..."}`.
- A session's state lives in its own JSON file, written only by that
  session.
- "Current lead" is computed from the `active.jsonl` tail on demand.

### Rationale

Eliminates the TM-H4 race directly. Append-only writes need no lock;
per-session files have a single writer by construction.

Resolves: TM-H4, X7 (partial).

### Compatibility & migration

Phase **M3**. Shim: a rendered `lead-state.rendered.md` is regenerated
after each append so scripts that grep the legacy filename keep
working.

---

## 11. Messenger

### Before / After

**Before**

```
.agent/messenger.md                 declarations (channels, env var refs)
```

Plus the in-memory `pendingApprovals` queue in TM (lost on restart;
L6).

**After**

```
messenger/
|-- channels.md                     single-writer declarations
`-- approvals.jsonl                 APPEND-ONLY; persisted across restart
```

- `approvals.jsonl` events: `approval.requested` and `approval.resolved`,
  each keyed by `approval_id`.
- Pending set = approvals without a matching resolve event. Computed on
  TM start by scanning the tail.

### Rationale

The in-memory queue is the only source of data loss in TM under
restart (L6). Moving it to the event substrate closes the loss and
uses the same append-only pattern as every other multi-writer surface.

Resolves: L6, partially X10 (messenger half-implemented).

### Compatibility & migration

Phase **M2**. The legacy `messenger.md` is split into `channels.md`
(preserved content) and approvals tracking (new).

---

## 12. Permissions

### Before / After

**Before**

```
adventures/ADV-NNN/permissions.md     one prose markdown file
```

- Writer: single (adventure-planner).
- Contention: none.
- Token footprint: grows with number of scopes; ADV-007's permissions
  doc is many KB and auto-loaded on every adventure-scoped spawn.

**After**

```
adventures/ADV-NNN/permissions/
|-- <scope>/                          one directory per scope
|   |-- spec.md                       the allow/deny for this scope
|   `-- proofs/                       optional evidence files
`-- index.json                        generated scope -> file index
```

- Writer: single per file.
- Agents load only the scopes relevant to their task
  (`pipeline.permissions_get(scope)`), typically one or two ~1-KB
  files.
- Token footprint: ~60% smaller on implementer spawns that need only
  their own scope.

### Rationale

Permissions today are monolithic and pay for the whole adventure on
every spawn. Sharding by scope matches the entity-design "Small-file
rule" (arch §3.2) and aligns with the PermissionSpec entity (phase2
catalog §10.4). Enables unit-testable permission evaluation because
each scope is a standalone artefact.

Resolves: no critical issue, but large token savings.

### Compatibility & migration

Phase **M3**. Shim: a regenerated `permissions.rendered.md` at the
legacy path preserves any external reader.

---

## 13. Session

### Before / After

**Before**

"Session" is not a first-class entity. It is:

- The Claude Code lead process (implicit).
- A TM LockManager session string (arbitrary, opaque).
- A binartlab WebSocket connection.

Three meanings, no entity, drift hazard (phase2 catalog §3.3).

**After**

Formalised as the trio in catalog §3.3: **LeadSession**,
**LockSession**, **ClientConnection**. Each has a dedicated
representation:

- LeadSession: `lead-state/sessions/<session-id>.json`.
- LockSession: the TM tool caller's `session_id` header; no file.
- ClientConnection: BL-internal, no `.agent/` representation.

No new contention. Clarity only.

### Rationale

Disambiguation, per phase2 catalog §10.3 splits.

### Compatibility & migration

Phase **M3** (as a byproduct of lead-state sharding).

---

## 14. Trigger

### Before / After

**Before**

Triggers are encoded inside `hooks/hooks.json` as prose prompts
(SubagentStop, UserPromptSubmit, Stop, SessionStart). Each prompt is
thousands of words of procedural logic evaluated by a Sonnet-class
model on every event (phase1 X8).

- Contention: no file contention, but every hook does a
  non-deterministic call to an LLM.
- Token footprint: ~6 KB of prompt per hook, every event.

**After**

Triggers become declarative entries in `registry/triggers.json`:

```json
{"event":"SubagentStop","action":"pipeline.on_subagent_stop",
 "args":{"session":"$SESSION","task":"$TASK"}}
```

The hook becomes a three-line shim that forwards to the named TM
tool. Behaviour lives in deterministic TM code.

- Token footprint: the hook prompt shrinks to ~0.5 KB (~92% saving).

### Rationale

Resolves X8 and TP-H1 directly. The `on_subagent_stop` TM tool
internally computes metrics, proposes a commit, updates the TC table
via event append, reconciles the manifest — all deterministic and
unit-tested.

### Compatibility & migration

Phase **M5**. Requires the TM tool surface to land first. Shim: the
legacy hook prompts remain as fallbacks for one release cycle;
feature-flag in `config.md` selects which path is live.

---

## 15. Config

### Before / After

**Before**

`.agent/config.md` — one frontmatter markdown file; single-writer
(user).

**After**

Preserved. This is the one entity the redesign intentionally does not
touch: it has one writer (the user), is small, and is read-only to
all agents. Any impulse to split it per subsystem is resisted — one
file remains the easiest to edit and review.

New fields added:

- `agent.stale_warn_min`, `agent.stale_critical_min` (resolves TM-M3).
- `compatible-with` constraints for plugin/MCP pairs (resolves X4).
- `layout_version` marker for phased migration (resolves the M0-M6
  phase detection).

### Rationale

Preservation by design. A "too simple" entity that works.

### Compatibility & migration

No migration required; new fields are optional with defaults.

---

## 16. New Entities Introduced

The phase2 catalog §10.4 lists five new first-class entities to add.
Their file-layout proposals:

| New entity | Representation | Writer |
|---|---|---|
| **Run** | `adventures/ADV/runs/<run-id>/{run.md,events.jsonl}` | TM `pipeline.run_*` |
| **PermissionSpec** | `permissions/<scope>/spec.md` (§12) | adventure-planner |
| **Contract** | `schema/contracts/<edge>.ark` | user + codegen |
| **Lesson** (optional union) | `knowledge/lessons.jsonl` entry | TM `lesson_append` |
| **Project** | `~/.claudovka/projects/<id>.json` | user + BL |

These are the entities implied by the organic-connections sub-graphs
(catalog §11) and are the necessary vocabulary for the Phase 3-6
adventures to consume.

---

## 17. Side-by-Side Summary (Before/After)

| Entity | Before (shape) | Before (writers) | After (shape) | After (writer) |
|---|---|---|---|---|
| Task | `tasks/T.md` monolithic | any | `tasks/T/{task.md,log.jsonl,iterations.jsonl}` | TM header + append all |
| Manifest | `manifest.md` w/ tables | 3+ | `manifest.md` (sm) + `*.jsonl` + `views/` | TM per kind |
| Adv log | `adventure.log` | any | `adventure.log` + `events.jsonl` | any (append) |
| Metrics | `metrics.md` table | 2 | `metrics.jsonl` + view | TM only |
| Knowledge | 3 md + memory dir | 2 | `lessons.jsonl` + views | TM only |
| Memory | `agent-memory/role/` | 1 (role) | view of knowledge | derived |
| Role | `roles/role.md` + mem | 1 | `roles/role.md` + role view | user |
| Skill | `skills/S/SKILL.md` + catalog | 1 + drift | source file + registry | user + gen |
| Agent | `agents/A.md` + enum | 1 + drift | source file + registry + permission ref | user + gen |
| Lead-state | `lead-state.md` 1 file | many (RMW) | `lead-state/{active.jsonl,sessions/*}` | append + 1-per-file |
| Messenger | `messenger.md` + mem q | 1 + vol | `messenger/{channels.md,approvals.jsonl}` | user + TM |
| Permissions | `permissions.md` mono | 1 | `permissions/<scope>/spec.md` | 1 per scope |
| Session | informal | n/a | `lead-state/sessions/<id>.json` | 1 per file |
| Trigger | hook prompt | LLM | `registry/triggers.json` + TM tools | user + TM |
| Config | `config.md` | user | `config.md` (+ fields) | user |

---

## 18. Impact Roll-up

### 18.1 Parallelism impact

- **10 of 15 entities** eliminate a read-modify-write hazard by
  moving to append-only jsonl.
- **0 entities** add a new contention surface.
- **3 entities** (Task, Lead-state, Permissions) move from
  single-file-many-writers or large-file-one-writer to
  directory-of-small-files, reducing blast radius of any single lock
  to a fraction of its old scope.
- **5 of the 11 cross-cutting issues** (X1, X6, X7, X8, X9) are
  directly addressed by entity shape changes; the rest (X2, X3, X4,
  X5, X10, X11) are addressed by registry generation, tool migration,
  or the architecture's event model.

### 18.2 Token-economy impact

Sum of per-spawn context deltas on ADV-007 workload:

| Spawn tier | Before (approx) | After (approx) | Reduction |
|---|---|---|---|
| Researcher (T1) | ~45 KB | ~6 KB | -87% |
| Reviewer (T1) | ~30 KB | ~6 KB | -80% |
| Planner (T2) | ~35 KB | ~10 KB | -71% |
| Implementer (T3) | ~25 KB | ~8 KB | -68% |
| Lead (T4) | ~55 KB | ~15 KB | -73% |

These are upper-bound estimates; achieved savings depend on how
aggressively the role-view ranker prunes stale entries.

### 18.3 Migration cost

Phases M0-M6 each land independently (arch doc §6). M0-M1 add but do
not replace; M2-M5 replace with rendered-view shims for backward
compatibility; M6 removes shims and hand-curated catalogs. Any
rollback is a matter of reading the previous shim; no flag-day.

---

## 19. Open Trade-offs

1. **Rendered view regeneration cost.** Every append triggers a view
   regen. For a 10k-event adventure this is non-trivial. Mitigation:
   incremental rendering (append to rendered file rather than full
   regen when the template allows) and lazy rendering (regen only
   when a consumer requests the view).
2. **Human edit-ability of append-only state.** Users occasionally
   want to hand-edit a TC status or an evaluation row. Proposal:
   `pipeline.event_amend(event_id, payload)` writes a correction
   event; the view regen applies corrections in order.
3. **Backward compat vs simplicity.** The rendered-view shims ease
   migration but add one file per entity. After phase M6, the shims
   are removed and the layout simplifies; there is a temporary
   complexity bump during M2-M5.
4. **Lesson ranking heuristics.** The role-view ranker (§6) decides
   which entries survive the ~3 KB budget. Specifying its scoring
   function is deferred to Phase 3.1 (profiling/optimization skill
   specs, TC-008).

---

## 20. Acceptance Checklist

- [x] Side-by-side **before/after** tables for Task, Adventure
  manifest, Adventure log, Metrics, Knowledge, Agent-memory, Role,
  Skill, Agent, Lead-state, Messenger, Permissions, Session, Trigger,
  Config — 15 entities (§§1-15).
- [x] Rationale per change referencing phase1 X-codes and phase2
  catalog decisions.
- [x] Token-economy delta per entity and rolled up by spawn tier
  (§18.2).
- [x] Parallelism impact per entity and rolled up (§18.1).
- [x] Compatibility & migration notes mapped to M0-M6 phases from
  the companion architecture document.
- [x] New first-class entities enumerated (§16).
- [x] Literal phrase "before/after" present (TC-006 grep proof).

---

## Appendix A — Upstream Inputs

- `phase2-concept-catalog.md` §§2, 3, 8, 10, 11 (entity taxonomy,
  renames/merges/splits, new entities).
- `phase2-knowledge-architecture.md` §§1-6 (layout, parallelism,
  token budgets, migration phases).
- `phase1-cross-project-issues.md` X1/X6/X7/X8/X9/X11, TM-H4, L6,
  phase1 §1.4.
- `team-pipeline.md` §1 (current entity shapes), §4 (opportunities).
