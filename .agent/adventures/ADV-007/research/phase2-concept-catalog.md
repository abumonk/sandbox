---
task: ADV007-T007
adventure: ADV-007
phase: 2
synthesis_of: [team-pipeline, team-mcp, binartlab, claudovka-marketplace, pipeline-dsl]
upstream:
  - .agent/adventures/ADV-007/research/team-pipeline.md
  - .agent/adventures/ADV-007/research/team-mcp.md
  - .agent/adventures/ADV-007/research/binartlab.md
  - .agent/adventures/ADV-007/research/marketplace-and-dsl.md
  - .agent/adventures/ADV-007/research/phase1-cross-project-issues.md
target_conditions: [TC-004]
researched: 2026-04-14
---

# Phase 2 — Unified Concept Catalog (Claudovka Ecosystem)

This document enumerates every domain concept that appears across the five
Claudovka projects, gives each concept a single canonical definition, marks
the projects that already use it (often in subtly different ways), and
flags the concepts that should be **merged**, **split**, or **renamed** as
the ecosystem unifies. It is the conceptual input for the entity-redesign
work that follows in T008.

The catalog is organised by **concept family**: Orchestration & Workflow,
Storage & State, Agent Identity & Capability, Events & Notifications,
Contracts & Schemas, DSL & Specification, Integration & Distribution, and
Knowledge & Learning. A final "organic connections" section maps the
natural compositions that emerge when the families are seen together.

The single most important upstream input is the cross-project synthesis
(T006), in particular finding **X1 — pipeline state machine duplicated in
four places** and the 14-edge contract table (E1-E14). Every concept in
this catalog that exists in more than one project is a candidate for
unification along the lines X1 prescribes.

---

## 1. Orchestration & Workflow Family

This family covers the runnable units of work, the lifecycles they move
through, and the compositions that group them.

### 1.1 Concept inventory

| Concept | TP | TM | BL | MK | PDSL | Notes |
|---|:-:|:-:|:-:|:-:|:-:|---|
| Task | YES | YES | YES | - | YES (entity) | Markdown frontmatter (TP/TM); DB row (BL); entity in PDSL examples |
| Adventure | YES | YES | (planned) | - | YES (structure) | Multi-task feature; 5-state machine in TM, 6-state in TP |
| Step (step2step) | YES | - | - | - | YES (example) | Document-only review unit; not modelled in TM |
| Cascade | YES | - | - | - | - | Downstream-impact record produced by `cascade-tracker` |
| Stage | YES | YES | YES | - | YES | 6 base stages + `BLOCKED`; duplicated in 4 places |
| Status | YES | YES | YES | - | YES | Per-stage whitelist (`in_progress`/`ready`/`passed`/`failed`) |
| Transition | YES | YES | YES | - | YES (`on X -> Y`) | `getNextStage()` in TM; PEG `transitions` block in PDSL |
| Pipeline | YES (3 types) | YES (status) | YES (executor) | - | YES (lifecycle) | Word means three different things — see §1.3 |
| Run / Execution | - | - | YES | - | - | `RunStorage` interface in BL core; absent in TP/TM |
| Trigger | YES (hook) | YES (hook tool) | YES (Triggers module) | - | YES (`trigger:` field) | Predicate that starts a stage/lifecycle |
| Hook | YES (3 prompts) | YES (`hooks_*` tools) | - | - | - | LLM prompt in TP; deterministic call in TM |
| Workflow | YES (informal) | YES (4 walkthroughs) | YES (deployment manual) | - | YES (lifecycle DAG) | Used loosely; no formal entity in any project |
| Plan | YES | YES (covered by adventure) | - | - | - | Markdown doc grouping designs into tasks |
| Design | YES | YES | YES (`docs/plans/`) | - | - | Markdown doc per-feature |
| Iteration | YES (frontmatter int) | YES (field) | - | - | - | Review/fix loop counter |
| TargetCondition (TC) | YES | YES (TC tracker) | - | - | YES (entity) | Verifiable acceptance criterion with `proof_method` |
| ProofMethod | YES | YES | - | - | - | `autotest \| poc \| manual` enum |
| Evaluation | YES | YES | - | - | - | Estimated vs actual tokens/duration/cost per task |

(TP=team-pipeline, TM=team-mcp, BL=binartlab, MK=marketplace,
PDSL=Pipeline DSL.)

### 1.2 Canonical definitions

- **Task** — a single unit of executable work owned by one assignee at a
  time, with a YAML-frontmatter header (id, stage, status, iterations,
  assignee, files, tags, depends_on, adventure_id?) and a body of
  Description / Acceptance Criteria / Design / Log. Lives at
  `.agent/tasks/{id}.md` (free-standing) or
  `.agent/adventures/{adv}/tasks/{id}.md` (adventure-scoped).
- **Adventure** — a multi-task feature with a manifest, designs, plans,
  permissions, custom roles, target conditions, evaluations, an
  append-only log, and a metrics ledger. Lives under
  `.agent/adventures/{ADV-NNN}/`.
- **Step** — a document-only review unit inside a step2step instance,
  with `depends_on`/`cascade_to` arrays. Step2step terminates with the
  emission of an Adventure.
- **Cascade** — a record of impact propagation from one modified Step to
  the downstream Steps reachable through `cascade_to`/`depends_on` edges.
- **Stage** — a named phase of the pipeline. Canonical 6 + 1 BLOCKED:
  `planning|implementing|reviewing|fixing|completed|researching` plus
  `BLOCKED`.
- **Status** — a per-stage whitelisted state inside a Stage:
  `in_progress|ready|passed|failed` (subject to per-stage restrictions
  in `getNextStage()`).
- **Transition** — a directed edge from one (Stage, Status) pair to
  another, with a default-assignee table.
- **Pipeline** — disambiguate (see §1.3).
- **Run / Execution** — one concrete invocation of a Pipeline with a
  bound input set, producing events and a terminal status. Currently
  modelled only in binartlab.
- **Trigger** — a boolean predicate (or named lifecycle event) that
  starts a Stage, Lifecycle, or Hook.
- **Hook** — code or prompt invoked at a defined Claude Code lifecycle
  event (`SubagentStop`, `UserPromptSubmit`, `Stop`, `SessionStart`).
- **Workflow** — an end-to-end sequence of Stages across one or more
  Tasks/Adventures from kickoff to terminal. Currently informal.
- **Plan** — a markdown doc grouping one or more Designs into a list of
  Tasks with acceptance criteria.
- **Design** — a markdown doc proposing the implementation approach for
  a Feature (or Adventure) before tasks are created.
- **Iteration** — a single review-and-fix loop on a Task; counted in
  frontmatter.
- **TargetCondition (TC)** — a verifiable acceptance criterion in an
  Adventure manifest with `proof_method` and `proof_command`.
- **ProofMethod** — `autotest | poc | manual`.
- **Evaluation** — a row in the Adventure manifest's evaluations table
  recording per-task estimated and actual duration/tokens/cost with
  variance.

### 1.3 The word "Pipeline" carries three distinct meanings

This is the most acute terminology collision in the ecosystem and is
flagged for renaming.

| Sense | Used by | Concrete artifact | Proposed name |
|---|---|---|---|
| The **lifecycle DAG** of stages (planning -> implementing -> ...) | TP, PDSL `lifecycle` items | The 6+BLOCKED state machine | **TaskLifecycle** |
| The **multi-task feature** that groups Designs/Plans/Tasks | TP (informally), Adventure docs | An Adventure | **Adventure** (already has its own name — drop "pipeline" usage) |
| The **executable workflow definition** (DSL artifact) | BL `PipelineExecutor` + YAML; PDSL examples | A YAML/DSL file describing one runnable workflow | **Pipeline** (reserve for this sense) |

After renaming, "Pipeline" means the **executable workflow definition**
in binartlab and PDSL; "TaskLifecycle" means the abstract stage DAG;
"Adventure" stays as is for the multi-task feature.

### 1.4 Divergent definitions to consolidate

- **Adventure state machine** — TP says 6 states (`concept | planning |
  review | active | reviewing | completed`) plus `cancelled`/`blocked`;
  TM says 5 states (`planning | active | paused | completed | cancelled`).
  TM is missing `concept`, `review`, `reviewing` and adds `paused`.
  **Decision needed** before unification (§7 records as recommendation).
- **Stage list** — TP/TM/BL/PDSL all enumerate stages independently;
  PDSL's `WELL_KNOWN_STAGES` adds `wait` which is not in TM. **Single
  source of truth required** (this is the X1 fix).
- **Status whitelist per stage** — only TM and PDSL encode it; TP relies
  on agent prompts; BL relies on zod schemas. **Promote to canonical
  schema.**
- **Iteration count** — TP increments during review/fix loops; TM stores
  the integer but does not transition on it; BL has no equivalent.
  **Standardise as a Task field with explicit semantics.**

---

## 2. Storage & State Family

This family covers persistence: where state lives, who can write it,
and how it is structured.

### 2.1 Concept inventory

| Concept | TP | TM | BL | MK | PDSL | Notes |
|---|:-:|:-:|:-:|:-:|:-:|---|
| .agent directory | YES | YES | (potential) | - | - | Root of markdown state tree |
| Manifest | YES (adventure manifest) | YES | YES (`.binartlab/data.db`) | YES (`plugin.json`) | - | Word reused for 4 different things |
| Frontmatter | YES (YAML) | YES (parser) | - | - | YES (entity field) | YAML header + markdown body |
| ConfigFile | YES (`config.md`) | YES (`config_get`) | YES (cli config) | YES (manifest) | - | Per-project settings |
| LeadState | YES (informal) | YES (`lead-state.md`) | - | - | - | Active-agent registry + last_event |
| LockManager | - | YES (in-mem 30s TTL) | - | - | - | Re-entrant by session string |
| Database | - | - | YES (`better-sqlite3` WAL) | - | - | Only BL uses a DB |
| FilesystemAdapter | - | - | YES (`fast-glob`) | - | - | Storage abstraction in BL |
| Permissions | YES (`permissions.md`) | YES (boundary check) | YES (scope filter) | - | - | Three different shapes of the same concept |
| Boundary | - | YES (`boundaries.js`) | YES (scope filter) | - | - | Project root + working_folders + task packages |
| WorkingFolder | YES (config field) | YES (boundary field) | YES (project field) | - | - | Allowlisted directories |
| TaskPackage | YES (config field) | YES (per-task narrowing) | (per-project) | - | - | Per-task narrower allowlist |
| EventLog (append-only) | YES (`adventure.log`) | YES (ring buffer) | YES (WS broadcaster) | - | - | Three different durabilities |
| MetricsLedger | YES (`metrics.md`) | YES (`metrics_log` tool) | YES (`MetricsCollector`) | - | - | Three independent recorders |
| KnowledgeBase | YES (`knowledge/*.md`) | YES (`knowledge_*` tools) | YES (`Knowledge` page in UI) | - | - | Patterns/Issues/Decisions split |
| AgentMemory | YES (`agent-memory/<role>/`) | YES (`memory_*` tools) | - | - | - | Per-role MEMORY.md plus topic files |
| MessengerRegistry | YES (`messenger.md`) | YES (`channel_*` tools) | (UI surfacing) | - | - | Channel registry + env-var indirection |

### 2.2 Canonical definitions

- **`.agent/` directory** — the root of project-scoped markdown state
  managed by team-pipeline; the canonical substrate for tasks,
  adventures, knowledge, config, lead state, metrics, and roles.
- **Manifest** — a structured description of an entity's identity and
  contents. **The word is overloaded** (see §2.3).
- **Frontmatter** — YAML header on a markdown file carrying typed
  fields (id, stage, status, ...). The body is free markdown.
- **ConfigFile** — `.agent/config.md` with project-level settings
  (working_folders, model rates, thresholds).
- **LeadState** — `.agent/lead-state.md`: active-agent registry,
  `last_event`, and lead session metadata.
- **LockManager** — an in-memory advisory lock store; today scoped only
  to LeadState writes. Should expand to per-file scope (X7 fix).
- **Database** — binartlab's `~/.binartlab/data.db` (SQLite WAL); the
  only RDBMS in the ecosystem.
- **FilesystemAdapter** — interface around file I/O so storage layer can
  be swapped or tested.
- **Permissions** — the declared allow/deny set for an Agent; combines
  Capability (tool list) and Boundary (path list).
- **Boundary** — concentric path containment: project root ⊇
  working_folders ⊇ task packages, with `.agent/` always allowed.
- **WorkingFolder** — a directory listed in config as writable by any
  agent.
- **TaskPackage** — a directory listed in a Task's frontmatter as
  writable by that Task only — narrower than WorkingFolder.
- **EventLog (append-only)** — a chronologically-ordered, append-only
  record of state changes; `adventure.log` is the gold-standard model.
- **MetricsLedger** — per-agent rows of (tokens_in, tokens_out,
  duration, turns, status) keyed by task and agent.
- **KnowledgeBase** — a project-scoped store of cross-task learnings,
  split into Patterns / Issues / Decisions files.
- **AgentMemory** — per-role `MEMORY.md` index plus on-demand topic
  files; first 200 lines auto-injected by the lead.
- **MessengerRegistry** — `.agent/messenger.md`: channel definitions
  (Telegram, Discord, ...) referencing env-var names rather than
  secrets directly.

### 2.3 The word "Manifest" carries four meanings — split it

| Sense | Used by | Concrete artifact | Proposed name |
|---|---|---|---|
| **Adventure** root descriptor | TP, TM | `.agent/adventures/{id}/manifest.md` | **AdventureManifest** |
| **Plugin** descriptor | MK, TP | `.claude-plugin/plugin.json` | **PluginManifest** |
| **Project** descriptor | BL | (implicit; `package.json` and DB rows) | **ProjectManifest** (formalise) |
| **MCP server** descriptor | TM | `.mcp.json` | **McpManifest** |

After renaming, callers always say which Manifest they mean. Tools that
operate on multiple kinds (e.g. a future "lint all manifests" task) can
treat them uniformly via a shared `Manifest` interface, but the word
alone never appears.

### 2.4 Divergent definitions to consolidate

- **Permissions** — TP encodes them as prose in `permissions.md`, TM as
  `boundaries.js` runtime checks plus tool allowlists, BL as MCP scope
  filters. The three are not interchangeable. **Proposal:** unify on a
  single PermissionSpec entity (declared in TP/manifest, enforced by TM
  at the MCP boundary, projected into BL's per-agent MCP).
- **EventLog** — TP's `adventure.log` is durable and append-only; TM's
  in-memory ring buffer is volatile (lost on restart); BL's WebSocket
  broadcaster is ephemeral fanout. **Proposal:** unify on a durable
  append-only `events.jsonl` with derived in-memory views.
- **MetricsLedger** — TP's `metrics.md` is human-edited markdown table;
  TM's `metrics_log` writes to the same file via tool call; BL's
  `MetricsCollector` writes DB rows. **Proposal:** the MCP tool is the
  only writer; markdown is derived; DB is the read-optimised mirror.
- **KnowledgeBase** vs **AgentMemory** — overlapping concerns (X9).
  **Proposal:** collapse to a single KnowledgeBase keyed by an optional
  `role:` field; AgentMemory becomes a query view, not a separate store.

---

## 3. Agent Identity & Capability Family

This family covers who can do what.

### 3.1 Concept inventory

| Concept | TP | TM | BL | MK | PDSL | Notes |
|---|:-:|:-:|:-:|:-:|:-:|---|
| Agent | YES (14 in agents/) | YES (`agent_*` tools) | YES (`AgentManager`) | - | - | Three definitions |
| AgentInstance / Spawn | YES (Task tool) | YES (`agent_spawn`) | YES (`spawnAgent` + ClaudeProcess) | - | - | Concrete process |
| Role | YES (15 templates) | YES (`agent_spawn` enum, hard-coded 4) | - | - | - | TM's enum is too narrow |
| Capability / Tool | YES (`tools` field) | YES (40+ pipeline.* tools) | YES (per-agent MCP) | - | - | Word "tool" overloaded |
| Skill | YES (~25 SKILL.md) | YES (`skills_list`) | - | - | - | Slash-command-invoked unit |
| Command | YES (4 dispatcher MD) | - | - | - | - | Slash command |
| Lead | YES (informal "lead" role) | YES (lead-state.md) | - | - | - | The orchestrator session |
| Session | YES (lead session) | YES (LockManager session string) | YES (websocket connection) | - | - | Three meanings (see §3.3) |
| Heartbeat / Health | - | YES (cleanupStaleAgents) | YES (AgentMonitor) | - | - | Two stale thresholds in TM (M3) |
| Channel (messaging) | YES (`messenger.md`) | YES (`channel_*` tools) | (UI notifications) | - | - | Telegram/Discord adapters in TM |
| ChannelApproval | - | YES (in-mem queue) | (UI ApprovalQueue page) | - | - | Lost on restart in TM (L6) |

### 3.2 Canonical definitions

- **Agent** — a *type* of worker (planner, implementer, reviewer,
  researcher, ...) defined by a markdown prompt with frontmatter for
  `tools`/`disallowedTools`/`model`/`maxTurns`/`memory`.
- **AgentInstance** — a *running* spawn of an Agent type, identified by
  spawn timestamp and parent task; has heartbeat, status, and
  permissions.
- **Role** — synonym for Agent type from the user-facing side. Should
  collapse to the same vocabulary as Agent.
- **Capability** — a single permission to invoke a Tool or write a
  Path. Composed into PermissionSpecs.
- **Tool** — disambiguate (see §3.3).
- **Skill** — a bundled procedure invokable as a slash command, with
  optional frontmatter (`context: inline|fork`, `agent`, `model`,
  `allowed-tools`).
- **Command** — a thin slash-command dispatcher that routes to one of
  many Skills or in-line procedures.
- **Lead** — the orchestrator session that proposes actions and waits
  for user approval ("full authority, zero autonomy" principle).
- **Session** — disambiguate (see §3.3).
- **Heartbeat / Health** — periodic liveness signal and the derived
  status (active / stale_warn / stale_critical).
- **Channel** — a named outbound/inbound messaging adapter (Telegram,
  Discord, ...).
- **ChannelApproval** — a pending user decision required to advance
  state; today held only in memory.

### 3.3 Words "Tool" and "Session" carry multiple meanings — split them

**Tool**
| Sense | Where | Proposed name |
|---|---|---|
| Claude Code built-in (Read, Write, Bash, ...) | TP frontmatter `tools: [...]` | **ClaudeTool** |
| MCP-exposed function (`pipeline.task_get`) | TM tool registry | **McpTool** |
| Binartlab MCP per-agent capability | BL `mcp/tools/*.ts` | **McpTool** (same family) |

**Session**
| Sense | Where | Proposed name |
|---|---|---|
| Claude Code lead session | TP lead loop | **LeadSession** |
| LockManager session (arbitrary string) | TM `agent.js` | **LockSession** (or replace with per-MCP-connection ID) |
| WebSocket / HTTP connection | BL web-api | **ClientConnection** |

### 3.4 Divergent definitions to consolidate

- **Agent role enum** — TM hard-codes 4 (`planner | implementer |
  reviewer | researcher`); TP ships 14; BL has no enum. **Proposal:**
  free-string with soft-validation list pulled from `.agent/roles/`.
- **Capability scoping** — TP declares `tools`/`disallowedTools` per
  Agent file; BL enforces via per-agent MCP scope filter; TM has no
  scoping. **Proposal:** unify under PermissionSpec, enforced at the
  MCP boundary (TM/BL converge).
- **Stale-agent thresholds** — TM has 5-min and 30/120-min in two
  modules (M3). **Proposal:** promote to config (`agent.stale_warn_min`,
  `agent.stale_critical_min`).
- **Skill vs Command** — TP's 4 Commands dispatch to ~25 Skills; the
  distinction is fuzzy in user-facing docs (X3 / Low-1). **Proposal:**
  Skills are the unit; Commands are auto-generated from a Skills
  registry.

---

## 4. Events & Notifications Family

### 4.1 Concept inventory

| Concept | TP | TM | BL | MK | PDSL | Notes |
|---|:-:|:-:|:-:|:-:|:-:|---|
| Event | YES (log lines) | YES (11 typed events) | YES (WS messages) | - | - | TM's typed taxonomy is the strongest model |
| EventEmitter | - | YES (singleton) | YES (broadcaster) | - | - | Both implementations are ad-hoc |
| Subscription | - | YES (`pipeline://events`) | YES (WS subscribe) | - | - | TM has no filtering (M4) |
| Notification | YES (messenger refs) | YES (`notifications/pipeline/event`) | YES (UI notifications) | - | - | Uses MCP standard in TM |
| Resource (MCP) | - | YES (`pipeline://events`) | (per-agent MCP) | - | - | MCP-spec resource subscription |

### 4.2 Canonical definitions

- **Event** — a typed, immutable record of one state change with
  `{type, ts, payload}`. Vocabulary: 11 types in TM (task.*, agent.*,
  adventure.*).
- **EventEmitter** — the in-process broker that routes Events to
  subscribers and persists them to the Event Log.
- **Subscription** — a typed filter registered by a client to receive
  matching Events.
- **Notification** — an outbound delivery of an Event over a Channel
  (MCP notification, WebSocket frame, Telegram message, ...).
- **Resource (MCP)** — an addressable read/subscribe surface exposed by
  an MCP server (`pipeline://events`).

### 4.3 Divergent definitions to consolidate

- **Event durability** — TP's adventure.log is permanent; TM's ring
  buffer is volatile; BL's broadcaster is ephemeral. **Proposal:**
  durable jsonl event log is canonical; volatile views derive from it.
- **Subscription filtering** — TM has none (M4); BL filters by
  websocket topic. **Proposal:** adopt MCP resource templating
  (`pipeline://events?type=task.completed`).
- **Notification ordering** — none of the three projects guarantees
  ordering across Channels. **Proposal:** Event log offsets are the
  canonical order; Channels deliver best-effort with offset attached.

---

## 5. Contracts & Schemas Family

### 5.1 Concept inventory

| Concept | TP | TM | BL | MK | PDSL | Notes |
|---|:-:|:-:|:-:|:-:|:-:|---|
| Schema (data) | YES (3 prose schemas) | YES (`lib/schema.js`) | YES (zod) | YES (plugin.json shape) | YES (entity items) | 5 dialects |
| Validation | (agent prompt rules) | YES (handcrafted predicates) | YES (zod) | - | YES (validator.js) | Three engines |
| Contract (inter-service) | (implicit) | YES (MCP tool I/O) | YES (REST/WS via zod) | - | - | E1-E14 in T006 |
| Boundary (path) | (config) | YES (`boundaries.js`) | YES (scope filter) | - | - | Same concept (see §2) |
| ToolSchema (MCP) | - | YES (per-tool input shape) | YES (per-tool zod) | - | - | TM has shape-drift (M1) |
| ErrorCode | - | YES (4 codes) | YES (error classes) | - | - | TM's vocabulary is cleanest |
| Version (compat) | YES (plugin version) | YES (server version) | YES (package versions) | YES (plugin.json) | YES (PDSL 0.1.0) | No negotiation between any pair |

### 5.2 Canonical definitions

- **Schema (data)** — a typed description of a record's fields,
  types, cardinalities, and constraints. The ecosystem currently has
  five dialects; the recommended trunk is Ark (with codegen to zod
  for TS-side projects).
- **Validation** — checking an instance against a Schema and returning
  `{valid, errors}`.
- **Contract (inter-service)** — the agreed I/O shape and semantics of
  one Edge in the dependency graph (E1-E14 in T006). Each Contract has
  a producer, a consumer, a transport, a payload, a Schema, and an
  enforcement mechanism.
- **Boundary (path)** — already canonical; see §2.
- **ToolSchema (MCP)** — input/output shape for one McpTool, declared
  to MCP clients during registration.
- **ErrorCode** — `VALIDATION_ERROR | NOT_FOUND | LOCK_CONFLICT |
  INTERNAL_ERROR` (TM vocabulary; adopt across BL and TP).
- **Version (compat)** — semver string plus a `compatible-with`
  constraint expressing which other components this one accepts.
  Currently absent in every pair (X4).

### 5.3 Divergent definitions to consolidate

- **Five schema dialects** — Ark grammar, prose markdown (TP), JS
  predicates (TM), zod (BL), PDSL PEG. **Proposal (X1/X2 fix):** Ark
  is the trunk; codegen emits zod for BL, JSON for TM, prose tables
  for TP `schema/`.
- **Tool input schema shape inconsistency** (TM M1) — some tools wrap
  in `{type:'object', properties, required}`, others use a flat
  property map. **Proposal:** lint at `register*Tools` time; fail
  startup on shape divergence.
- **Error vocabulary** — TM has 4 codes used everywhere; BL has
  `class`-based errors; TP has none (markdown only). **Proposal:** TM
  vocabulary is canonical; BL maps its classes to it; TP adopts in
  agent prompts.

---

## 6. DSL & Specification Family

### 6.1 Concept inventory

| Concept | TP | TM | BL | MK | PDSL | Notes |
|---|:-:|:-:|:-:|:-:|:-:|---|
| DSL | (consumes prose schemas) | (consumes JS schema) | YES (3-layer YAML) | - | YES (PEG grammar, .pdsl) | + Ark in this repo = three DSLs |
| Grammar | - | - | (none — js-yaml only) | - | YES (PEG in `parser.js`) | Ark has pest+lark |
| Entity | - | - | YES (zod schema) | - | YES (entity X { ... }) | Same concept, two syntaxes |
| Lifecycle (DSL item) | - | - | - | - | YES (lifecycle X { ... }) | Stage DAG declaration |
| Structure (DSL item) | - | - | - | - | YES (structure X { ... }) | Hierarchical container |
| Relation (DSL item) | - | - | - | - | YES (relation A -> B) | Directed link |
| Schema (DSL layer) | - | - | YES (Layer 1) | - | YES (entity = schema layer) | Two dialects |
| Instance (DSL layer) | - | - | YES (Layer 2) | - | (implicit in examples) | YAML in BL |
| Runtime (DSL layer) | - | - | YES (Layer 3 — parser/validator/`${}` resolver) | - | YES (cli + viewer) | Two engines |
| Renderer / Viewer | - | - | YES (React Flow) | - | YES (SVG via layout.js) | Both unused for runtime feedback |
| Editor (programmatic) | - | - | (UI only) | - | YES (`editor.js` AST mutations) | PDSL's editor.js is the strongest pattern |
| Codegen | - | - | (no codegen — only zod inference) | - | (no codegen) | Ark has codegen |

### 6.2 Canonical definitions

- **DSL** — a declarative language describing a domain (entities,
  relations, lifecycles, structures). Three exist today (PDSL,
  binartlab YAML, Ark); the trunk should be one.
- **Grammar** — a formal syntax (PEG, pest, lark). PDSL has PEG; Ark
  has pest+lark; binartlab has no grammar (only zod over js-yaml).
- **Entity** — a typed data record with named fields. PDSL `entity`,
  Ark `class`/`abstraction`, binartlab zod schemas all denote this.
- **Lifecycle** — a declared stage DAG with optional sub-blocks
  (`input`, `execute`, `transitions`, `completion`).
- **Structure** — a hierarchical container of other Structures or
  Entities (`contains`, `spawns`, `delegates`, `checkpoints`).
- **Relation** — a directed association between two Entities or
  Structures with `type:`, `via:`, `cardinality:`, `constraint:`,
  `lifecycle:`.
- **Schema layer** — the type-definition layer (PDSL `entity` blocks;
  binartlab zod schemas).
- **Instance layer** — the per-pipeline configuration that fills in
  the schema (binartlab YAML files; PDSL examples).
- **Runtime layer** — parser + validator + variable resolver +
  executor.
- **Renderer / Viewer** — produces a visual (SVG, React Flow) from the
  parsed AST.
- **Editor (programmatic)** — typed mutation API for the AST
  (`addField`, `removeField`, `renameEntity`, ...). PDSL's
  `editor.js` is the gold-standard pattern.
- **Codegen** — emits target-language artifacts (Rust, Python, TS) from
  the canonical DSL spec. Ark has it; PDSL/binartlab do not.

### 6.3 Divergent definitions to consolidate

- **Three DSLs to one** (X2) — pick Ark as the trunk; PDSL becomes a
  profile/dialect of Ark; binartlab YAML maps via codegen. The PDSL
  `viewer.html` and `editor.js` carry over as Ark's browser editor and
  spec-mutation API.
- **Stage names** — PDSL `WELL_KNOWN_STAGES` (7 incl. `wait`) vs TM
  `STAGES` (6). **Proposal:** Ark spec defines the canonical 7;
  WAIT becomes a sub-state of BLOCKED (TBD).

---

## 7. Integration & Distribution Family

### 7.1 Concept inventory

| Concept | TP | TM | BL | MK | PDSL | Notes |
|---|:-:|:-:|:-:|:-:|:-:|---|
| Plugin | YES | (consumed by Claude Code) | - | YES (versioned cache) | - | Marketplace artifact |
| Marketplace | - | - | - | YES (cache only — no index) | - | Missing index file (MK-1) |
| Version | YES (0.14.3) | YES (0.1.0) | YES (per-pkg) | YES (4 cached) | YES (0.1.0) | No negotiation (X4) |
| MCP server | (consumes) | YES (canonical) | YES (per-agent) | - | - | Two implementations |
| MCP transport | (stdio via plugin) | YES (stdio only) | YES (stdio per agent) | - | - | No HTTP/SSE anywhere |
| Project | YES (cwd) | YES (resolveAgentDir) | YES (`ProjectManager`) | - | - | BL's is the richest model |
| Repo | (implied by project) | (implied) | YES (per-project) | - | - | Only BL distinguishes |
| Workspace (npm) | - | - | YES (9 packages) | - | - | Internal monorepo concept |
| Adapter (storage) | - | - | YES (interfaces) | - | - | Pattern to propagate (T008) |

### 7.2 Canonical definitions

- **Plugin** — a Claude Code plugin: a `.claude-plugin/plugin.json`
  manifest plus agents/skills/commands/hooks/templates. Distributed
  via Marketplace.
- **Marketplace** — a registry of installable Plugins. Today the
  ecosystem has only a filesystem cache; a real `marketplace.json`
  index is missing (MK-1).
- **Version** — semver string; needs a `compatible-with` peer for
  cross-component negotiation.
- **MCP server** — a server speaking the Model Context Protocol over
  stdio (today; HTTP/SSE recommended in TM R8).
- **MCP transport** — `stdio` or `http+sse`. Currently stdio only.
- **Project** — a working directory with a `.agent/` and (in BL) a DB
  row plus a `Repo` reference.
- **Repo** — git repository associated with a Project (BL only).
- **Workspace (npm)** — the npm-workspaces concept inside binartlab.
- **Adapter (storage)** — interface around a storage backend so
  consumers can be tested against in-memory fakes.

### 7.3 Divergent definitions to consolidate

- **MCP server identity** — TM names itself `team-pipeline` (the
  plugin it serves), not `team-mcp`. **Proposal:** rename to
  `team-mcp` to match the project; advertise the served Plugin via a
  separate field.
- **Project boundaries** — TP/TM use `cwd` walk-up; BL uses DB rows
  with explicit `repo` paths. **Proposal:** unify on a Project entity
  with `path`, `repo`, `agent_dir` fields; both implementations
  resolve to the same record.

---

## 8. Knowledge & Learning Family

### 8.1 Concept inventory

| Concept | TP | TM | BL | MK | PDSL | Notes |
|---|:-:|:-:|:-:|:-:|:-:|---|
| KnowledgeBase | YES (`knowledge/`) | YES (`knowledge_*`) | YES (UI page) | - | - | Three writers, one store |
| Pattern | YES (`patterns.md`) | YES (typed entry) | (UI category) | - | - | Reusable approach |
| Issue | YES (`issues.md`) | YES (typed entry) | (UI category) | - | - | Common problem + fix |
| Decision | YES (`decisions.md`) | YES (typed entry) | (UI category) | - | - | Architecture decision record |
| AgentMemory | YES (`agent-memory/<role>/`) | YES (`memory_*`) | - | - | - | Per-role |
| Researcher (agent) | YES | - | - | - | - | Knowledge writer |
| Knowledge-extractor (agent) | YES | - | - | - | - | Adventure-scoped extractor |
| Lesson / Learning | (informal in patterns) | (informal) | (none) | - | - | No first-class entity |

### 8.2 Canonical definitions

- **KnowledgeBase** — the project-scoped store of cross-task learnings.
  One KnowledgeBase per Project; subdivided into Patterns, Issues,
  Decisions.
- **Pattern** — a reusable approach with `name`, `description`, and
  `from: {task-id}`.
- **Issue** — a recurring problem with `description`, `solution`, and
  `from: {task-id}`.
- **Decision** — an architecture decision record with
  `Context`/`Decision`/`From`.
- **AgentMemory** — overlapping with KnowledgeBase (X9). **Proposed
  resolution:** collapse — KnowledgeBase entries get an optional
  `role:` field; AgentMemory becomes a query view filtered by `role`.
- **Researcher** — the agent that updates KnowledgeBase after every
  task and updates evaluations.
- **Knowledge-extractor** — adventure-scoped agent that produces a
  rolled-up learning report.
- **Lesson / Learning** — proposed first-class entity (currently
  informal). Would unify Pattern / Issue / Decision under a single
  type with a `kind:` field.

---

## 9. Concept Overlap and Duplicate Matrix

The following matrix marks the cells where the same word means different
things across projects (✗) or where different words mean the same thing
(=). It is the input for §10 (rename/merge/split decisions).

| Concept | TP | TM | BL | PDSL | Status |
|---|---|---|---|---|---|
| Pipeline | lifecycle DAG | DB status | executor | lifecycle item | ✗ split (§1.3) |
| Manifest | adventure | -- | -- | plugin | ✗ split (§2.3) |
| Tool | Claude built-in | MCP function | MCP function | -- | ✗ split (§3.3) |
| Session | lead loop | lock string | WS connection | -- | ✗ split (§3.3) |
| Stage | YES | YES | YES | YES | = unify (X1) |
| Status | YES | YES | YES | YES | = unify (X1) |
| Transition | YES | YES | YES | YES | = unify (X1) |
| Schema | prose md | JS preds | zod | PEG | = unify (Ark trunk) |
| EventLog | durable md | volatile ring | WS fanout | -- | = unify (durable jsonl) |
| Permissions | prose md | boundaries | scope filter | -- | = unify (PermissionSpec) |
| Agent vs Role | both used | role enum | AgentManager | -- | = collapse to Agent |
| KnowledgeBase vs AgentMemory | two stores | two tool families | one UI | -- | = collapse to one |
| Skill vs Command | dispatcher to skill | skills tools | -- | -- | = generate Commands from Skills |
| Plugin vs MCP server | distinct | distinct | distinct | -- | OK — keep separate |
| Project | cwd walk-up | cwd walk-up | DB row | -- | = unify (Project entity) |

---

## 10. Rename / Merge / Split Recommendations

### 10.1 Renames

| Current name | New name | Reason |
|---|---|---|
| Pipeline (sense: lifecycle DAG) | TaskLifecycle | Disambiguate from executable Pipeline |
| Pipeline (sense: multi-task feature) | (drop — use Adventure) | Already named Adventure |
| Manifest (sense: adventure) | AdventureManifest | Disambiguate |
| Manifest (sense: plugin) | PluginManifest | Disambiguate |
| Manifest (sense: MCP) | McpManifest | Disambiguate |
| Tool (sense: Claude built-in) | ClaudeTool | Disambiguate |
| Tool (sense: MCP function) | McpTool | Disambiguate |
| Session (sense: lead loop) | LeadSession | Disambiguate |
| Session (sense: lock string) | LockSession | Disambiguate |
| Session (sense: WS conn) | ClientConnection | Disambiguate |
| MCP server name `team-pipeline` | `team-mcp` | Match the project |

### 10.2 Merges

| Inputs | Output | Reason |
|---|---|---|
| Stage (4 copies) | one Ark spec | X1 |
| Status whitelist (3 copies) | one Ark spec | X1 |
| Transition table (3 copies) | one Ark spec | X1 |
| PDSL + binartlab YAML + Ark | one Ark trunk | X2 |
| KnowledgeBase + AgentMemory | KnowledgeBase with `role:` field | X9 |
| Permissions: prose + boundaries + scope filter | PermissionSpec entity | X1-style consolidation |
| EventLog: adventure.log + ring buffer + WS fanout | durable jsonl + derived views | X6/X7 prerequisite |
| Pattern + Issue + Decision (optional) | Lesson with `kind:` | Optional simplification |
| Agent + Role | Agent (single vocabulary) | Reduce confusion |

### 10.3 Splits

| Input | Outputs | Reason |
|---|---|---|
| Pipeline (3 senses) | TaskLifecycle, Adventure, Pipeline | Word collision |
| Manifest (4 senses) | AdventureManifest, PluginManifest, ProjectManifest, McpManifest | Word collision |
| Tool (2 senses) | ClaudeTool, McpTool | Word collision |
| Session (3 senses) | LeadSession, LockSession, ClientConnection | Word collision |

### 10.4 New first-class entities to introduce

| New entity | Justification |
|---|---|
| **Run** (Pipeline execution) | Today only BL has a `RunStorage`; making Run a top-level entity in TP/TM enables history, replay, and cross-pipeline metrics. |
| **PermissionSpec** | Unifies prose permissions, boundaries, and scope filters under one declaration enforced at one boundary. |
| **Contract** | Promotes E1-E14 from documentation to first-class entities with producer/consumer/transport/schema/enforcement/version fields. |
| **Lesson** (optional) | Single store covering Pattern/Issue/Decision; cleaner write rules than the current three-file split. |
| **Project** (formal) | Today inferred from cwd walk-up (TP/TM) or DB row (BL); promoting it to a first-class entity unifies the two paths. |

---

## 11. Organic Connections — How the Concepts Compose

Concepts that naturally link form sub-graphs. Recognising them shapes
the entity redesign in T008.

### 11.1 Identity sub-graph

```
Agent ── (instance-of) ── AgentInstance ── (heartbeat) ── Health
   │                              │
   │ (declares)                   │ (writes to)
   ▼                              ▼
PermissionSpec               EventLog
   │
   │ (composes)
   ▼
Capability + Boundary + WorkingFolder + TaskPackage
```

- An **Agent** type declares a **PermissionSpec**.
- An **AgentInstance** is bound by that spec, emits **Events** during
  its life, and reports **Health** via heartbeat.
- The PermissionSpec composes **Capability** (tool list) with
  **Boundary** (path containment of WorkingFolder narrowed to
  TaskPackage when a Task is bound).

### 11.2 Work sub-graph

```
Adventure ── contains ──> Plan ── covers ──> Design ── decomposes ──> Task
    │                                                                │
    │ tracks                                                          │ proceeds-through
    ▼                                                                 ▼
TargetCondition ── proven-by ──> ProofMethod              TaskLifecycle (Stage + Status)
    │
    │ measured-by
    ▼
Evaluation ── derives-from ──> MetricsLedger
```

- An **Adventure** contains **Plans**, which cover **Designs**, which
  decompose into **Tasks**.
- The Adventure tracks **TargetConditions**; each is proven by a
  **ProofMethod** (autotest / poc / manual).
- Each Task proceeds through the **TaskLifecycle** (Stage + Status).
- **Evaluation** rolls up **MetricsLedger** rows for the Adventure's
  Tasks and computes variance against estimates.

### 11.3 Execution sub-graph

```
Pipeline (DSL) ── executed-by ──> Run ── spawns ──> AgentInstance
     │                              │
     │ uses                         │ emits
     ▼                              ▼
Lifecycle items + Entity items   Event ── ordered-by ──> EventLog ── delivered-via ──> Channel
                                                                                          │
                                                                                          ▼
                                                                                 ChannelApproval (pending user decision)
```

- A **Pipeline** (DSL artifact) is executed by a **Run** that spawns
  one or more **AgentInstances**.
- Every state change emits an **Event** appended to the **EventLog**.
- Events flow over **Channels** as **Notifications**; some require a
  **ChannelApproval** before the Run advances.

### 11.4 Knowledge sub-graph

```
Task ── completed-by ──> Researcher ── extracts ──> Lesson (Pattern|Issue|Decision)
                              │                            │
                              │ updates                    │ scoped-by
                              ▼                            ▼
                     KnowledgeBase                       Role (optional)
                              ▲
                              │ queried-by
                     AgentMemory (view)
```

- After a Task completes, the **Researcher** extracts **Lessons** into
  the **KnowledgeBase**.
- A Lesson optionally carries a `role:` scope; **AgentMemory** is a
  read-only view filtered by role.

### 11.5 Distribution sub-graph

```
Marketplace ── lists ──> Plugin ── declares ──> McpServer requirement
     │                      │                      │
     │ versioned-via        │ contains             │ provides
     ▼                      ▼                      ▼
PluginManifest        Agents + Skills + Commands + Hooks   McpTool registry
                          │
                          │ registered-with
                          ▼
                     Project (.agent/) on init
```

- A **Marketplace** lists **Plugins** by **PluginManifest**.
- A Plugin contains Agents + Skills + Commands + Hooks and declares an
  **McpServer requirement**.
- McpServers expose **McpTool** registries.
- On init, a Plugin is registered with a **Project** which materialises
  the `.agent/` substrate.

### 11.6 The connecting edges (cross-family)

The five sub-graphs are connected by the following organic edges:

| Edge | Connects | Meaning |
|---|---|---|
| Adventure → Project | Work ↔ Distribution | An Adventure runs in a Project. |
| Task → AgentInstance | Work ↔ Identity | A Task is assigned to an AgentInstance. |
| Run → EventLog | Execution ↔ Storage | A Run writes to the EventLog. |
| Lesson → Task | Knowledge ↔ Work | A Lesson is sourced from a Task. |
| Permission → McpTool | Identity ↔ Distribution | A PermissionSpec gates which McpTools an AgentInstance can call. |
| Contract → Edge | Schemas ↔ Integration | A Contract describes an Edge in the dependency graph (E1-E14). |
| TargetCondition → Run | Work ↔ Execution | A Run advances or satisfies TargetConditions. |

These cross-family edges are the seams along which T008's entity
redesign must minimise contention: every edge that crosses a family
also crosses an ownership boundary, and every ownership boundary is a
concurrency hazard.

---

## 12. Summary — Unification Recommendations with Rationale

The catalog crystallises the following unification work, ordered by
leverage (matches T006 §4 priority list):

1. **One TaskLifecycle (Stage/Status/Transition) spec** — collapse 4
   copies into one Ark spec, codegen to TM/BL/PDSL. Resolves X1.
2. **One DSL trunk (Ark)** — PDSL becomes an Ark dialect, binartlab
   YAML maps via codegen. Resolves X2.
3. **One PermissionSpec entity** — unifies prose permissions,
   boundaries, and scope filters; enforced at the MCP boundary.
   Resolves X1-style permission drift.
4. **One durable EventLog substrate** — `events.jsonl` is canonical;
   ring buffer and WS fanout derive from it. Resolves X6/X7.
5. **One KnowledgeBase store** — collapse AgentMemory into KnowledgeBase
   with optional `role:` scope. Resolves X9.
6. **First-class Run, PermissionSpec, Contract entities** — promotes
   today's implicit concepts to typed records that participate in
   schema codegen and verification.
7. **Disambiguate Pipeline / Manifest / Tool / Session** — the four
   word collisions identified in §10.3 must be resolved before any
   shared schema package can use them as identifiers without
   confusion.
8. **Generate Catalogs from source** — Skills, Commands, Tools,
   Agents, Roles all hand-curated today (X3). After §1 lands, generate
   them from the canonical Ark spec.

These eight unifications, taken together, are the conceptual
preconditions for the entity redesign in T008. T008 will turn the
sub-graphs in §11 into a concrete file/directory layout that minimises
write contention and the per-agent context size.

---

## Appendix A — Source Documents

- `R:/Sandbox/.agent/adventures/ADV-007/research/team-pipeline.md` (T002)
- `R:/Sandbox/.agent/adventures/ADV-007/research/team-mcp.md` (T003)
- `R:/Sandbox/.agent/adventures/ADV-007/research/binartlab.md` (T004)
- `R:/Sandbox/.agent/adventures/ADV-007/research/marketplace-and-dsl.md` (T005)
- `R:/Sandbox/.agent/adventures/ADV-007/research/phase1-cross-project-issues.md` (T006 — synthesis, 14-edge contract table, X1-X11)
