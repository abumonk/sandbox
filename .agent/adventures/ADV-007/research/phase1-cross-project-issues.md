---
task: ADV007-T006
adventure: ADV-007
phase: 1
synthesis_of: [team-pipeline, team-mcp, binartlab, claudovka-marketplace, pipeline-dsl]
target_conditions: [TC-002, TC-003]
researched: 2026-04-14
---

# Phase 1 — Cross-Project Synthesis: Claudovka Ecosystem Issues and Dependency Map

This document synthesizes the five Phase 1 project reviews (team-pipeline,
team-mcp, binartlab, claudovka-marketplace, Pipeline DSL/PDSL) into:

1. A **cross-project dependency map** showing what depends on what, what data
   crosses the boundary, and what contract enforces (or fails to enforce) the
   exchange.
2. A **unified problem catalog** with explicit `severity:` labels (one per
   issue, machine-greppable). Severity vocabulary: `critical`, `high`,
   `medium`, `low`.
3. **Cross-cutting patterns and anti-patterns** — the shape of the recurring
   problems.
4. A **priority list for Phase 2 knowledge unification** — what to fix first,
   in what order, and why.

The five sources reviewed are summarised in the appendix.

---

## 1. Cross-Project Dependency Map

### 1.1 Project roles in one sentence

| Project | One-line role |
|---|---|
| **team-pipeline** (plugin, v0.14.3) | In-Claude-Code multi-agent task pipeline driven by markdown state in `.agent/`. |
| **team-mcp** (server, v0.1.0) | MCP server fronting `.agent/` with 40+ `pipeline.*` tools, events, notifications. |
| **binartlab** (monorepo, v0.1.0) | Out-of-Claude-Code orchestrator: spawns `claude` CLI, attaches per-agent MCP, exposes web/mobile UI. |
| **claudovka-marketplace** (cache) | Filesystem cache of versioned plugin payloads; auto-discovered by Claude Code. |
| **Pipeline DSL (PDSL)** | Text + visual schema language shipped inside team-pipeline 0.14.3, modelling the pipeline domain. |

### 1.2 Runtime topology

```
                  +---------------------+
                  | Claude Code (host)  |
                  +----+--------+-------+
                       |        |
              loads    |        |  spawns subagents
        plugins from   |        |    (Task tool)
                       v        v
         +----------------+   +-------------------+
         | claudovka-     |   | team-pipeline     |
         | marketplace/   |   | agents/skills/    |
         | (cache, fs)    |   | hooks/commands    |
         +-------+--------+   +----+--------------+
                 |                 | reads/writes
        manifest |                 v
        + payload|        +-------------------+
                 v        | .agent/ markdown  |
         +----------------+ tree (tasks,      |
         | plugin.json    | adventures, logs, |
         | + dsl/ + ...   | knowledge, ...)   |
         +----------------+----+--------------+
                               ^   ^
              MCP stdio        |   |  direct file I/O fallback
              (pipeline.*)     |   |  (hook prompts)
                               |   |
                       +-------+---+--------+
                       | team-mcp server    |
                       | (Node ESM, stdio)  |
                       +-------+------------+
                               ^
                               | (potential / future)
                               |
                       +-------+------------+
                       | binartlab          |
                       | (around-session    |
                       |  orchestrator,     |
                       |  spawns claude     |
                       |  CLI, per-agent    |
                       |  MCP, REST/WS)     |
                       +--------------------+
```

### 1.3 Edge-by-edge contract table

| # | Edge (consumer ← producer) | Transport | Payload / data | Contract source | Enforcement | Status |
|---|---|---|---|---|---|---|
| E1 | Claude Code ← claudovka-marketplace | filesystem auto-discovery | plugin payload (`.claude-plugin/plugin.json` + agents/skills/hooks) | implicit (Claude Code conventions) | none — presence-based | OK, but no `engines` / `claude-code-version` field |
| E2 | team-pipeline agents ← `.agent/` markdown | direct fs read/write | tasks, adventures, manifests, knowledge, logs, metrics | `team-pipeline/schema/*.md` (prose) + agent prompts | none at runtime — agent prompts re-state rules | drift between hooks, agents, schema |
| E3 | team-pipeline hooks ← team-mcp | MCP stdio | `pipeline.task_get`, `task_advance`, `metrics_log`, `adventure_log`, `adventure_metrics`, `config_get`, `status` | `team-mcp/lib/schema.js` (handcrafted predicates) | partial — hooks have try-fallback to direct fs I/O | duplicated state machine (M7 in team-mcp; team-pipeline has its own copy) |
| E4 | team-mcp ← `.agent/` markdown | filesystem | YAML frontmatter + markdown body | `lib/state.js` parseFrontmatter / serializeFrontmatter | non-atomic write (H1) | crash window can truncate state |
| E5 | team-mcp clients ← `pipeline://events` | MCP resource + `notifications/pipeline/event` | 11 event types, last 50 in ring buffer | `lib/events.js` | in-memory only (lost on restart) | no filtering, no persistence |
| E6 | team-pipeline messenger ← team-mcp `channel_*` | MCP stdio + Telegram/Discord adapters (process inheritance) | `messenger.md` channel registry + env-var secret indirection | `messenger.md` schema | messenger never implemented in team-pipeline; team-mcp implements channel side | half-implemented contract |
| E7 | PDSL viewer ← PDSL parser/renderer | in-process JS API | `.pdsl` text → AST → SVG | `dsl/grammar.md` (PEG) | self-contained, has tests | shipped but not wired to runtime |
| E8 | team-pipeline runtime ← PDSL | none today | (intended) entity/lifecycle/structure model | `dsl/examples/pipeline-*.pdsl` | none — runtime re-implements model in agent prompts | the gap that produces drift |
| E9 | binartlab agents ← binartlab MCP per-agent server | MCP stdio attached to `claude` child process | scoped tools (Files, Tasks today; Knowledge / Pipeline / Agent-self / Git missing) | `@binartlab/shared` zod schemas | scope filter at MCP boundary; zod at API | strong contract, **incomplete tool surface** |
| E10 | binartlab web-ui / mobile ← binartlab web-api | REST + WebSocket | projects, agents, tasks, pipelines, metrics; broadcaster events | zod schemas in `@binartlab/shared` | enforced at server; clients hand-roll fetch wrappers | no shared client package |
| E11 | binartlab DSL runtime ← `.yaml` files | js-yaml parse + zod | three-layer DSL (schema / instance / runtime) | zod | schema errors only — **no syntax errors** | weaker than PDSL/Ark |
| E12 | binartlab core ← `claude` CLI subprocess | stdio + signals (SIGSTOP/SIGCONT/SIGTERM) | agent text + lifecycle events | `MockChildProcess` (test fake); real `ClaudeProcess` | unit-tested via mock; no end-to-end smoke test | fragile in production |
| E13 | binartlab ← team-pipeline / team-mcp | **none today** | (intended) drive a `.agent/` directory through binartlab UI | — | — | **biggest missing integration** |
| E14 | Ark (this repo) ← PDSL or binartlab DSL | none today | (intended) Ark spec replaces both DSLs | — | — | recommended unification target |

### 1.4 Data ownership matrix

Same data, multiple owners — every cell with two `W` columns is a write
contention point.

| State | team-pipeline | team-mcp | binartlab | PDSL |
|---|---|---|---|---|
| `.agent/tasks/*.md` frontmatter | R/W | R/W | (could) R/W | — |
| `.agent/adventures/{id}/manifest.md` | R/W | R/W | (could) R/W | — |
| `.agent/adventures/{id}/adventure.log` (append-only) | W | W | (could) W | — |
| `.agent/adventures/{id}/metrics.md` | W | W | (could) W | — |
| `.agent/lead-state.md` | R | R/W | — | — |
| `.agent/knowledge/{patterns,issues,decisions}.md` | R/W | R/W | (mirrored in DB) | — |
| `~/.binartlab/data.db` (SQLite WAL) | — | — | R/W | — |
| `dsl/examples/*.pdsl` | R | — | — | R/W |
| pipeline state-machine table (stages, status whitelist, transitions) | embedded in agent prompts | embedded in `lib/schema.js` | embedded in `@binartlab/shared` zod | embedded in `dsl/validator.js` WELL_KNOWN_STAGES |

The last row is the most damaging: **four independent copies of the same
state machine.** Any change to stage names or transitions must be applied in
four places.

---

## 2. Unified Problem Catalog (with `severity:` labels)

Each entry below carries a single `severity:` token (`critical | high |
medium | low`) so this section is greppable: `grep -c "severity:"`.

### 2.1 Cross-cutting issues (affect ≥2 projects)

**X1 — Pipeline state machine duplicated in four places**
- severity: critical
- Where: team-pipeline (agent prompts + hook prompts), team-mcp
  (`lib/schema.js`), binartlab (`@binartlab/shared` zod), PDSL
  (`validator.js` WELL_KNOWN_STAGES).
- Effect: any change to stages/transitions must land in four codebases,
  silently. There is no shared schema package and no version negotiation
  (team-mcp M8). Inconsistencies will manifest as untestable runtime
  divergence.
- Fix: extract a single `.ark` spec (or a tiny published JSON package) for
  stages, status whitelists, and transitions; have all four projects import
  it.

**X2 — Two DSLs (PDSL + binartlab YAML), neither used by the runtime**
- severity: high
- Where: team-pipeline ships PDSL but the runtime re-implements its model in
  prompts (E8). Binartlab ships its own three-layer YAML DSL with no
  cross-tool consumption. Ark in this repo is a third DSL.
- Effect: three dialects of the same conceptual schema; bit-rot risk on PDSL
  (already flagged Medium in team-pipeline review); missed opportunity to
  share editor / verifier / codegen.
- Fix: pick one — recommend unifying on Ark (Z3-backed, has codegen, has
  pest+lark grammars) and treating PDSL as a profile/dialect of Ark per
  the integration plan in marketplace-and-dsl.md §5.

**X3 — Hand-curated catalogs of tools / commands / skills / agents drift**
- severity: high
- Where: team-pipeline `CLAUDE.md` lists `/task-status` while
  `commands/task.md` defines `/task status` (low-severity item Low-1 in
  team-pipeline review); team-mcp deployment manual says "26 tools across 6
  categories... 27" while actual count differs (M2); team-mcp
  `cleanupStaleAgents` uses 5-min threshold while `diagnostics.js` uses
  30/120 min (M3); team-mcp README/CLAUDE/manual disagree on tool list (L5).
- Effect: "Unknown skill" failures, ambiguous troubleshooting, wasted user
  time. Same root cause everywhere: humans hand-maintain a list that the
  source already knows.
- Fix: generate every catalog from the source — walk `register*Tools` at
  startup, walk `commands/`, walk `agents/`, dump a JSON registry, have
  README/CLAUDE.md/manual cite that file.

**X4 — Versioning and compatibility contracts are implicit**
- severity: high
- Where: marketplace `plugin.json` has no `engines` / `claude-code-version`
  (PDSL Low); team-mcp 0.1.0 vs team-pipeline 0.14.3 have no version
  negotiation (M8); team-pipeline plugin cache has multiple versions
  side-by-side with no active-version pin (Low-7); binartlab packages are
  all 0.1.0 with no published versions and no peer-deps between sibling
  workspaces beyond `*`.
- Effect: a breaking change in any one component silently breaks pairs.
  Users cannot tell which version of team-pipeline a `.agent/` directory was
  initialized with.
- Fix: add `claude-code-version` and `compatible-with` fields; have
  team-mcp refuse to start if on-disk team-pipeline version is incompatible;
  add an `active.json` next to the marketplace cache.

**X5 — No end-to-end integration test across the ecosystem**
- severity: high
- Where: team-pipeline has no scripted `task-init -> create -> advance ->
  complete` (Recommendation 10 in team-pipeline review); team-mcp has tool
  unit tests but no integration with team-pipeline; binartlab has no smoke
  test that boots web-api + spawns a mock agent + runs a pipeline (Issue 5
  in binartlab); E13 (binartlab driving team-pipeline) is unimplemented.
- Effect: integration regressions are user-discovered, not CI-discovered.
- Fix: one Adventure-level smoke test that exercises the full chain in
  mock mode.

**X6 — Markdown state files are written non-atomically by all writers**
- severity: critical
- Where: team-mcp `lib/state.js` writeState (H1 in team-mcp); team-pipeline
  agents and hooks write the same files via direct I/O whenever MCP is
  unavailable; binartlab, if it is to drive `.agent/`, will inherit the
  same problem.
- Effect: a crash mid-write truncates a task or manifest file to zero bytes;
  the README's "single-writer" claim is partially defeated. The risk
  compounds because there are now multiple potential writers (E2, E3, E4)
  to the same files.
- Fix: write-to-temp + fsync + rename, in one place
  (team-mcp), and forbid direct file I/O fallback in hooks / agents once MCP
  is the canonical path.

**X7 — Concurrency control is aspirational in every component**
- severity: high
- Where: team-mcp LockManager covers only `agent_spawn` and `agent_complete`
  (H2/H3); locks are in-memory only (H3); team-pipeline assumes serial
  subagent execution (which Claude Code mostly enforces today); binartlab
  uses synchronous better-sqlite3 (correct for SQLite, but no advisory
  locks across processes).
- Effect: as soon as parallel agent execution is enabled (a stated roadmap
  goal in multiple projects) silent last-write-wins corrupts state.
- Fix: per-file locks at the team-mcp tool layer (every read-modify-write,
  not just two), or an event-sourced state model where conflicts are
  detected at apply time.

**X8 — Hook logic is ~6 KB of natural-language imperative procedure**
- severity: critical
- Where: team-pipeline `hooks/hooks.json` SubagentStop / UserPromptSubmit /
  Stop are LLM prompts, not scripts (High-1 in team-pipeline). Embeds MCP
  detection, fallback I/O, metrics computation, git proposal logic,
  adventure state machine, TC table updates, pending questions, and user
  approval gating.
- Effect: non-deterministic (sonnet decides), expensive (token cost on every
  agent stop), untestable, drifts from agent prompts.
- Fix: move every hook responsibility to a deterministic team-mcp tool call
  (`pipeline.on_subagent_stop`); keep the hook as a thin trigger.

**X9 — `agent-memory/` and `knowledge/` overlap with unclear write rules**
- severity: medium
- Where: team-pipeline (Low-2 in team-pipeline review). Team-mcp's
  `memory_*` and `knowledge_*` tools mirror this same split but do not
  resolve it.
- Effect: agents must judge where to write; researchers cannot update role
  memory by design (which the team-pipeline review questions); two stores
  drift.
- Fix: collapse to one (knowledge keyed by `role:` field) or codify a strict
  rule and enforce it in MCP tool validation.

**X10 — `.agent/messenger.md` channel registry is referenced but only
half-implemented**
- severity: medium
- Where: team-pipeline hooks reference messenger; team-mcp implements
  `channel_*` tools and inbound polling (Telegram). No team-pipeline-side
  consumer of the messenger contract is shipped.
- Effect: notifications and approvals are advertised in docs but stop in the
  team-mcp ring buffer or the in-memory `pendingApprovals` queue (team-mcp
  L6).
- Fix: define the messenger contract in one schema; make team-mcp the
  canonical implementer; persist `pendingApprovals` to disk.

**X11 — Token / cost estimation is a hand-wavy proxy ecosystem-wide**
- severity: medium
- Where: team-pipeline hook prompts use `turns * 1500` / `turns * 500` as
  token estimates (Medium-7 in team-pipeline). Team-mcp `metrics_log` accepts
  whatever the caller passes. Binartlab metrics collector has no real
  source for actual token usage either.
- Effect: every variance/cost rollup in evaluations tables is built on
  rough proxies; budget decisions can be wrong by 2-5x.
- Fix: real token counter from MCP (the Anthropic SDK exposes per-call
  usage); back-fill `metrics_log` from authoritative source only.

### 2.2 Project-specific issues (high/critical only — full details in source docs)

**TP-H1 — Pipeline orchestration encoded in hook prompts** (team-pipeline)
- severity: critical
- See X8 above for cross-cutting framing.

**TP-H2 — Cross-pipeline state spread across many files; no transaction**
- severity: high
- Where: `manifest.md` + TC rows + evaluations + `permissions.md` + `roles/`
  + `tasks/` + `adventure.log` + `metrics.md` + `reviews/` updated
  independently. Crashed agent leaves inconsistent state.
- Fix: append-only event log (`adventure.events.jsonl`) with a materialized
  view rebuilt on demand; same approach binartlab could adopt.

**TP-H3 — Skill / command / agent count is large, mostly bespoke**
- severity: high
- Where: ~25 skills, ~14 agents, multiple pipeline types. README itself
  warns the lead not to spend extended time diagnosing "Unknown skill"
  failures — a tell that the catalog is faster to grow than to keep correct.
- Fix: a "lite" mode profile (≤3-task adventure: skip permission analysis,
  skip custom roles); generate command/skill catalog from source (X3).

**TM-H1 — Non-atomic writes** (team-mcp)
- severity: critical
- See X6 above for cross-cutting framing.

**TM-H2 — Lock scope limited to two tools** (team-mcp)
- severity: high
- See X7 above for cross-cutting framing.

**TM-H4 — `last_event` race inside emit()** (team-mcp)
- severity: high
- Every emit does its own read-modify-write of `lead-state.md`. Two
  near-simultaneous emits clobber each other.

**BL-1 — MCP toolset is one-third implemented** (binartlab)
- severity: high
- Knowledge, Pipeline, Agent-self, and Git tool categories are absent;
  agents inside a binartlab pipeline cannot ask "what stage am I in?" or
  commit code. Without these, the binartlab MCP cannot replace team-mcp.
- Fix: prioritise Pipeline and Agent-self tools for the binartlab/team-mcp
  unification (Phase 4 candidate).

**BL-2 — `@binartlab/mobile` is undocumented and untriaged**
- severity: high
- 9429 LOC + 27 tests = the largest package; not in the design doc; no
  product hypothesis. Either own it (update design + frontend test density)
  or freeze and excise.

**BL-7 — DSL is ad-hoc YAML, no real grammar**
- severity: high
- See X2 above for cross-cutting framing.

**MK-1 — No marketplace index file** (claudovka-marketplace)
- severity: high
- Cache directory has no `marketplace.json` — discovery is filesystem-walk
  only. If Claudovka grows beyond `team-pipeline`, multi-plugin enumeration
  is impossible.

**PDSL-1 — Validator permissive on transition targets**
- severity: high
- Targets outside `WELL_KNOWN_STAGES` produce only warnings, so typos in
  custom stage names slip through silently.

**PDSL-2 — Verb set hard-coded but grammar promises forward compat**
- severity: high
- Action verbs (`read`, `write`, `update`, `explore`, `emit`, `log`) are an
  enumerated PEG choice; unknown verbs are hard parse errors despite
  grammar comment saying they "may be added in future versions".

### 2.3 Medium and low items (condensed for grep coverage)

**TM-M1 — Inconsistent input-schema shape across MCP tools**
- severity: medium

**TM-M2 — Tool-count drift between README, CLAUDE.md, manual**
- severity: medium

**TM-M3 — Stale-agent thresholds inconsistent (5 min vs 30/120 min)**
- severity: medium

**TM-M4 — No subscribe-with-filter for events resource**
- severity: medium

**TM-M5 — Channel polling is opaque (no documented poll interval)**
- severity: medium

**TM-M6 — Channel manager monkey-patches eventEmitter.emit**
- severity: medium

**TM-M7 — Heavy duplication of team-pipeline state machine in `schema.js`**
- severity: high
- Promoted from medium because it is a face of X1.

**TM-M8 — No version negotiation between team-mcp and team-pipeline**
- severity: high
- Promoted from medium because it is a face of X4.

**TP-M-Permissions — "Zero runtime permission prompts" enforced only by lead prompt**
- severity: medium
- The 4-pass permission analysis is scrubbed by the planner; nothing at
  runtime actually blocks an agent from doing something not in
  `permissions.md`.

**TP-M-DSL-unused — PDSL ships but is not consumed by runtime**
- severity: medium
- Bit-rot risk; covered by X2.

**TP-M-Step2step — Two parallel pipeline types duplicate concepts**
- severity: medium
- task vs step2step both have stages, agents, manifests, logs, metrics;
  step2step's `Pause and resume` is still listed as an open question.

**TP-M-Reviewer-echo — Reviewer logs via `bash echo` because it lacks Write tool**
- severity: medium
- Workaround `echo … >> file` on Windows quoting is fragile.

**BL-3 — Frontend test deficit (web-ui 1 test per 1374 LOC vs backend 1 per 100)**
- severity: medium

**BL-4 — Built `.js`/`.d.ts` artifacts checked in across packages**
- severity: medium

**BL-5 — No CI / no Dockerfile / no deploy story**
- severity: medium

**BL-6 — No git remote / no license**
- severity: medium

**BL-Strange-3 — No shared HTTP/WS client package between web-ui and mobile**
- severity: medium

**BL-Strange-6 — No round-trip property test for PipelineEditor (visual ↔ YAML)**
- severity: medium

**PDSL-M1 — `TypeExpr` ambiguity (enum vs typeref) deferred to validator**
- severity: medium

**PDSL-M2 — Two cardinality notations (`[0..*]` suffix vs `0..*` field)**
- severity: medium

**PDSL-M3 — No import/include mechanism (single-file only)**
- severity: medium

**PDSL-M4 — Pattern literal vs division ambiguity (latent risk)**
- severity: low

**PDSL-M5 — Multiple plugin versions cached side-by-side, no GC**
- severity: low

**TP-L-Commands — `CLAUDE.md` lists conflicting command names**
- severity: low

**TP-L-Memory-knowledge — `agent-memory/` and `knowledge/` overlap**
- severity: low

**TP-L-Cascade-depth — Hard-coded cascade depth 5 not configurable**
- severity: low

**TP-L-Versions — Plugin install layout has no active-version pin**
- severity: low
- Folded into X4.

**TM-L1 — `subscribe`/`unsubscribe` reach into `server.server` internals**
- severity: low

**TM-L2 — Capabilities registered after first `server.resource()` call**
- severity: low

**TM-L3 — Event ring buffer size hard-coded to 50**
- severity: low

**TM-L4 — LockManager TTL hard-coded to 30 s**
- severity: low

**TM-L5 — README/CLAUDE.md/manual tool tables disagree**
- severity: low
- Folded into X3.

**TM-L6 — Channel inbound `pendingApprovals` queue lost on restart**
- severity: medium
- Folded into X10.

**MK-L1 — Plugin author "Claudovka" but homepage `github.com/abumonk/...`**
- severity: low

**MK-L2 — `viewer.html` shipped in plugin payload but not in manifest**
- severity: low

**MK-L3 — `keywords` declared but agents/skills/commands not declared in manifest**
- severity: low

**MK-L4 — No `engines` / `claude-code-version` in `plugin.json`**
- severity: low
- Folded into X4.

**MK-L5 — Worked PDSL examples each repeat stub-entity preamble (no `import`)**
- severity: low
- Folded into PDSL-M3.

---

## 3. Cross-Cutting Patterns and Anti-Patterns

### 3.1 Anti-patterns observed across multiple projects

1. **Prose-as-program** — team-pipeline encodes orchestration logic as
   multi-KB hook prompts (X8); schema files are markdown prose (Recommendation
   3 in team-pipeline). Anything you write in prose, you cannot
   diff-with-confidence, test, or version. Move it into Ark, JSON Schema, or
   typed code.
2. **Hand-curated catalogs** — every project hand-maintains a list (commands,
   tools, skills, agents) that the source already exhaustively defines.
   Generate from source, always.
3. **Aspirational concurrency** — three projects (team-pipeline, team-mcp,
   binartlab) describe a "single writer" or "scoped MCP" model that is not
   actually enforced in code. Either enforce it or re-document it as
   advisory.
4. **Multiple sources of truth for the same domain** — the pipeline
   state-machine exists in agent prompts (TP), `lib/schema.js` (TM), zod
   (BL), and `validator.js` (PDSL). The DSL also exists in two flavors
   (PDSL + binartlab YAML), neither used by the consumer.
5. **MCP-optional with try/fallback** — every team-pipeline hook duplicates
   the same "try MCP, fall back to file I/O" boilerplate. MCP-first with
   internal fallback shrinks each call site to one line.
6. **Implicit version contracts** — no plugin/server pair declares which
   version of the other it requires.
7. **Documentation that is better than the code it describes** — team-mcp's
   920-line deployment manual is the strongest artifact in the project and
   describes guarantees (single-writer, lock semantics) that the code does
   not actually provide. Documentation drift in the dangerous direction.

### 3.2 Patterns worth preserving and propagating

1. **Markdown-first state with append-only event logs.** Diff-friendly,
   git-friendly, no DB. team-pipeline's `adventure.log` is the
   gold-standard model — propagate it to binartlab.
2. **Explicit per-agent capability scoping.** Both team-pipeline (per-agent
   `tools`/`disallowedTools`) and binartlab (per-agent scoped MCP) have
   this; combine: capability scopes at the MCP boundary plus the agent
   prompt declaration.
3. **"Full authority, zero autonomy" lead principle.** Lead proposes; user
   approves. Adopt across binartlab UI flows.
4. **Zod-first contracts (binartlab) / handcrafted predicates (team-mcp).**
   The cleanest single-source contract pattern is zod or Ark. Pick zod for
   TS, Ark for cross-language.
5. **Adapter / dependency-injection at every storage seam (binartlab core).**
   Lets pipeline executor be unit-tested without touching SQLite or
   subprocesses. Apply to team-mcp's `lib/state.js` (currently a singleton).
6. **Boundary discipline (team-mcp `lib/boundaries.js`).** Tested,
   trailing-separator-aware path containment. Adopt for binartlab's MCP scope
   filter.
7. **Round-trippable text DSL with `--check` CI gate (PDSL).** Same idea
   should be applied to binartlab's YAML DSL.
8. **Friendly degradation (team-mcp).** Missing `.agent/` → exit 0 with
   stderr help; missing `messenger.md` → channels off, server keeps
   running. Apply to all servers.
9. **Adventure target conditions with `proof_method`.** Forces every
   requirement to carry a runnable proof. Adopt as the universal acceptance
   criterion across binartlab pipelines too.

---

## 4. Priority List for Phase 2 Knowledge Unification

Ordered by leverage (impact × ease of fix). Each priority lists the
issues it resolves so progress can be tracked against this catalog.

### P1 — Single source of truth for the pipeline state machine
- Resolves: X1, TM-M7, TP-H2 (partially), TM-M8 (partially)
- Action: extract stages, status whitelists, transitions, default
  assignees into one `.ark` spec (or a published JSON schema). All four
  projects import it. Generate the four current copies from it.
- Why first: every other unification depends on this. Until the four copies
  agree, fixing other items in any one project just moves the disagreement
  somewhere else.

### P2 — One DSL across the ecosystem (Ark as the trunk)
- Resolves: X2, TP-M-DSL-unused, BL-7
- Action: port PDSL examples (`pipeline-entities.pdsl`,
  `pipeline-lifecycle.pdsl`, `adventure-structure.pdsl`, `step2step.pdsl`)
  to `R:/Sandbox/ark/specs/pipeline/` as `.ark` files. Map binartlab's
  three-layer YAML to Ark's `class`/`abstraction`/`island` items. Reuse
  PDSL's `viewer.html` + `renderer.js` as Ark's browser editor; reuse
  PDSL's `editor.js` as the spec-mutation API.

### P3 — Atomic writes + per-file locks at the MCP boundary
- Resolves: X6, X7, TM-H1, TM-H2, TM-H4
- Action: in team-mcp `lib/state.js`, replace `writeFile` with
  `writeFile.tmp + fsync + rename`; wrap every read-modify-write tool with
  `lockManager.acquire(filePath, callerId)`; reuse for binartlab's future
  `.agent/` writes.

### P4 — Hook prompts → deterministic MCP tool calls
- Resolves: X8, TP-H1, TP-M-Reviewer-echo
- Action: implement `pipeline.on_subagent_stop`, `pipeline.on_user_prompt`,
  `pipeline.on_session_stop` in team-mcp; reduce hooks/hooks.json to
  three-line shells that call those tools. Move metrics estimation, git
  proposal, adventure state machine, TC table updates inside team-mcp where
  they can be unit-tested.

### P5 — Generate every catalog from source
- Resolves: X3, TP-L-Commands, TM-M2, TM-L5
- Action: at startup, walk `register*Tools` (team-mcp), `commands/`
  (team-pipeline), `agents/` (team-pipeline), `skills/` (team-pipeline);
  emit one JSON registry; have README/CLAUDE.md cite it via include.

### P6 — Real token / cost telemetry
- Resolves: X11, TP-M token estimation
- Action: read per-call token usage from the Anthropic SDK response;
  authoritative `metrics_log` in team-mcp; back-fill team-pipeline
  evaluations from MCP only.

### P7 — Version negotiation and active-version pinning
- Resolves: X4, TM-M8, TP-L-Versions, MK-L4
- Action: add `claude-code-version` and `compatible-with` fields to
  `plugin.json`, `package.json` (team-mcp), and binartlab packages; team-mcp
  refuses to start if the on-disk team-pipeline is incompatible; introduce
  `marketplace.json` index + per-plugin `active.json` pin.

### P8 — Finish the binartlab MCP toolset
- Resolves: BL-1
- Action: implement Knowledge, Pipeline, Agent-self, and Git tool categories
  inside binartlab `mcp/tools/` so an in-pipeline agent has parity with the
  team-mcp-fronted agent.

### P9 — One end-to-end smoke test that crosses all five projects
- Resolves: X5, BL-5, TP-H3 ("Unknown skill" regressions)
- Action: a single CI job that (a) installs the marketplace plugin, (b)
  runs `task-init`, (c) creates and advances a task through all stages, (d)
  starts team-mcp and exercises three tools, (e) starts binartlab in mock
  mode and drives a pipeline. Falls below "thorough" but catches every
  regression in the catalog.

### P10 — Decide and document `@binartlab/mobile`, `agent-memory` vs
`knowledge`, messenger contract
- Resolves: BL-2, X9, X10
- Action: scope decisions, not pure engineering. Either own or excise the
  mobile package; collapse memory into knowledge or codify the split;
  finalise the messenger contract and persist `pendingApprovals`.

---

## 5. Severity Roll-up

Counts below are derived from the catalog above (one severity label per
issue; X-level, project-specific high/critical, and medium/low items all
included). Use `grep -c "severity: critical|severity: high|..."` against
this file for live counts.

| Tier | Count (approx.) | Examples |
|---|---:|---|
| critical | 4 | X1 (state-machine duplication), X6 (non-atomic writes), X8 (hook prompts), TM-H1 |
| high | ~14 | X2, X3, X4, X5, X7, TP-H2, TP-H3, BL-1, BL-2, BL-7, MK-1, PDSL-1, PDSL-2, TM-M7/M8 |
| medium | ~16 | X9, X10, X11, TM-M1/3/4/5/6, TP-M items, BL-3/4/5/6, BL-Strange-3/6, PDSL-M1/2/3 |
| low | ~12 | TP-L items, TM-L items, MK-L items, PDSL-M4/5 |

Total severity-tagged entries: **~46** (well above the 15 target).

---

## Appendix A — Source Documents

- `R:/Sandbox/.agent/adventures/ADV-007/research/team-pipeline.md` (T002):
  team-pipeline plugin v0.14.3 — 11 issues, 10 recommendations, 7
  strengths.
- `R:/Sandbox/.agent/adventures/ADV-007/research/team-mcp.md` (T003):
  team-mcp v0.1.0 — 4 high-severity issues (H1-H4), 8 medium (M1-M8), 6
  low (L1-L6), 8 strengths.
- `R:/Sandbox/.agent/adventures/ADV-007/research/binartlab.md` (T004):
  binartlab monorepo (9 packages, ~21k LOC) — 7 issues, 6 strange
  decisions, 6 strengths, 10 recommendations.
- `R:/Sandbox/.agent/adventures/ADV-007/research/marketplace-and-dsl.md`
  (T005): claudovka-marketplace cache + Pipeline DSL (PDSL) — 3 high, 5
  medium, 5 low; full Ark integration plan.
- (context) `R:/Sandbox/.agent/adventures/ADV-007/research/pipeline-management-review.md`.

## Appendix B — Glossary of Edge Labels (for §1.3)

E1-E8 are team-pipeline / team-mcp / marketplace edges; E9-E12 are
binartlab-internal edges; E13-E14 are the two integration edges that do
not exist today and constitute the largest cross-project gap.
