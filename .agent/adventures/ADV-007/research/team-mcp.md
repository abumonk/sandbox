---
project: team-mcp
version: 0.1.0
source: R:/Claudovka/projects/team-mcp/
research_task: ADV007-T003
researched: 2026-04-14
license: MIT
upstream: (no public repo URL declared; references team-pipeline at https://github.com/abumonk/team-pipeline)
---

# Team MCP Research

The `team-mcp` project is a local MCP (Model Context Protocol) server that
fronts the same `.agent/` markdown tree that the **team-pipeline** plugin
manages. It is a Node 18+ ESM Claude Code plugin with a single declared MCP
server (`team-pipeline`) launched over **stdio transport** by Claude Code as
a subprocess. The server exposes 40+ `pipeline.*` tools (task lifecycle,
adventure orchestration, agent coordination, knowledge base, files,
diagnostics, hooks, agent-memory, skills, messaging channels) plus one MCP
resource (`pipeline://events`) and live MCP notifications. The implementation
is small (~3.3 KLOC of library + tools, plus ~14 `node --test` test files)
and depends on only two npm packages: `@modelcontextprotocol/sdk@^1.0.0` and
`yaml@^2.4.0`.

## 1. Architecture

```
Claude Code <----stdio JSON-RPC---->  team-mcp/server/index.js
                                             |
                                             v
                                       lib/tools/*.js  (40+ MCP tools)
                                             |
                                             v
                          lib/state.js  +  lib/schema.js  +  lib/boundaries.js
                                             |
                                             v
                                       .agent/ markdown tree
                                       (tasks, adventures, knowledge,
                                        config, lead-state, metrics)
```

### Bootstrap (server/index.js, 132 lines)
1. `resolveAgentDir()` walks upward from `process.cwd()` looking for `.agent/`.
   If not found, the server prints a friendly stderr message and exits with
   code **0** (a deliberate "nothing to serve" non-error). This is a nice
   touch that prevents Claude Code from showing an MCP failure when the
   plugin is loaded in a project that simply has not run `/task-init` yet.
2. Constructs `McpServer({ name: 'team-pipeline', version: '0.1.0' })`.
3. Instantiates a singleton `LockManager` and exports it for tool modules.
4. Wires the `eventEmitter` singleton to the server (so emit can call
   `server.notification(...)` for subscribers).
5. Calls 13 `register*Tools(server)` functions in sequence.
6. Registers the `pipeline://events` MCP resource (last 50 events, JSON).
7. Manually registers `subscribe`/`unsubscribe` request handlers via the
   underlying `Server` because `McpServer` does not auto-register those for
   resource subscriptions.
8. Starts `StdioServerTransport`, then `channelManager.initialize()` and
   `startForwarding()` for Telegram/Discord, with try/catch so channel
   failures do not bring down the server. Handles SIGINT/SIGTERM cleanly.

### Storage layer (lib/state.js)
- `parseFrontmatter()` / `serializeFrontmatter()` round-trip YAML
  frontmatter + markdown body using the `yaml` package.
- `writeState()` is **not** atomic -- a single `writeFile` call. There is no
  rename-after-fsync pattern, no temp file, no fsync. A crash mid-write
  truncates the state file. This is the largest correctness gap in the
  project given the project's "single-writer" claim.
- Built-in helpers for the agents array in `lead-state.md`:
  `readAgents`, `writeAgent`, `updateAgent`, `cleanupStaleAgents` (5-min
  default). Locks are NOT used inside these helpers despite multiple writers
  potentially calling them -- locking is at the tool-handler layer.
- `LockManager` is in-memory only, 30 s TTL, lazy expiry on `acquire()`,
  re-entrant for the same session. Scope is limited to "lead-state" writes
  (`agent_spawn`, `agent_complete`); task and adventure tools do NOT take
  locks.

### Schema layer (lib/schema.js)
- 6 stages, per-stage status whitelists, automatic-transition table
  (`getNextStage`), default-assignee table.
- Adventure has its own 5-state machine (`planning|active|paused|completed|cancelled`).
- All validation lives here as plain JS predicates returning
  `{valid, errors}`. No JSON Schema, no Zod, no AJV -- handcrafted checks.
  The trade-off is fewer dependencies but no machine-readable schema for
  external consumers.

### Boundary layer (lib/boundaries.js)
- `validatePath(filePath, taskId, config, projectRoot, readTaskFn)` enforces
  three concentric boundaries: project root -> `working_folders` -> task
  `packages`. Uses `path.resolve` + trailing-separator normalization to
  prevent `/foo/bar` matching `/foo/barbaz`. `.agent/` is always allowed.
- Path traversal is handled correctly: any `..` segment that escapes
  `projectRoot` is rejected by `isInside`.

### Event layer (lib/events.js)
- 50-entry in-memory ring buffer; on `emit()`:
  1. Push to buffer (evict oldest on overflow).
  2. Write `last_event` to `lead-state.md` (try/catch, non-fatal).
  3. Send MCP notification `notifications/pipeline/event` (non-fatal).
  4. If `pipeline://events` is subscribed, also send standard
     `sendResourceUpdated`.
- 11 event types covering tasks, agents, and adventures. The buffer is lost
  on restart -- only `last_event` survives in `lead-state.md`.

## 2. Tool Surface (40+ tools, namespace `pipeline.*`)

| Category | Tools | File |
|---|---|---|
| Task | task_create, task_get, task_list, task_update, task_advance, task_log, task_archive | tools/task.js (552 LOC) |
| Adventure | adventure_create, adventure_get, adventure_list, adventure_update, adventure_advance, adventure_status | tools/adventure.js (565 LOC) |
| Agent | agent_spawn, agent_list, agent_complete | tools/agent.js (296 LOC) |
| Pipeline | status | tools/pipeline.js |
| Config | config_get, config_set | tools/config.js |
| Metrics | metrics, metrics_log | tools/metrics.js |
| Knowledge | knowledge_get, knowledge_add, knowledge_search | tools/knowledge.js |
| Files | file_read, file_write, file_search | tools/files.js (335 LOC) |
| Hooks | hooks_get, hooks_set, hooks_evaluate | tools/hooks.js |
| Memory | memory_list, memory_get, memory_set, memory_search | tools/agent-memory.js |
| Diagnostics | health, debug_task, estimation_report | tools/diagnostics.js (443 LOC) |
| Skills | skills_list, skills_get, rules_list, rules_match | tools/skills.js |
| Channels | channel_status, channel_send, channel_approvals | tools/channels.js (222 LOC) |

Resources: `pipeline://events`. Notifications: `notifications/pipeline/event`
plus standard `notifications/resources/updated`.

### Tool design
- Every tool is registered with `server.tool(name, description, inputSchema, handler)`.
- Input "schemas" are object literals with `type`/`properties` -- not strict
  JSON Schema (the SDK accepts the looser shape). A few tools (channels.js)
  pass `type: 'object', properties: {...}, required: [...]`; others
  (task.js) pass a flat properties map. **This inconsistency is real** and
  is mentioned by the documentation's tool-count caveat.
- Errors are returned via `lib/errors.js` constructors:
  `VALIDATION_ERROR | NOT_FOUND | LOCK_CONFLICT | INTERNAL_ERROR`. All set
  `isError: true` and JSON-encode `{error, message}` in the text content.

## 3. Auth, Sessions, and Concurrency

- **Auth: none.** stdio transport is parent-trusted -- the server inherits
  whatever permissions Claude Code gives it. There is no token, no API key,
  no per-call identity. This is correct for a local-only, single-user MCP
  server but means the server cannot be safely exposed over a network
  transport (HTTP/SSE) without adding a layer.
- **Sessions: none represented.** `LockManager.acquire(resource, session)`
  takes a session string but the only callers (`agent.js`) pass arbitrary
  identifiers; there is no session establishment, no session validation, no
  session cleanup beyond the 30-second TTL. Re-entrancy works only because
  the same call passes the same string.
- **Concurrency: very narrow.** Locks cover only `agent_spawn` and
  `agent_complete` writes to `lead-state.md`. Concurrent writers to the same
  task file (e.g., `task_update` from two agents) silently last-write-wins.
  This is acceptable today because Claude Code spawns subagents serially in
  most workflows, but it will become a real problem as soon as parallel
  agent execution is enabled.
- **Channel auth: env-var indirection.** Telegram reads
  `process.env[config.bot_token_env]` and `process.env[config.chat_id_env]`
  -- the config file names the env var, never the secret. This is good
  practice and lets the same `messenger.md` be committed to git.

## 4. Deployment

The deployment manual (`docs/deployment-manual.md`, ~920 lines, exceptionally
thorough -- arguably the strongest single artifact in the project) documents
two install paths:

1. **Plugin marketplace path** (preferred): plugin root contains
   `.claude-plugin/plugin.json` and `.mcp.json`. Claude Code launches the
   server with `${CLAUDE_PLUGIN_ROOT}/server/index.js`.
2. **Direct `.mcp.json` path**: project-local `.mcp.json` invokes
   `node /absolute/path/to/server/index.js` with `NODE_ENV=production`.

Steps boil down to: install Node 18+, `cd server && npm install`, register
in `.claude/settings.local.json` `enabledPlugins`, restart Claude Code.

Operational characteristics:
- No build step; pure ESM shipped as-is.
- No log directory; everything goes to stderr.
- No DB, no migrations, no on-disk lock files.
- Server walks upward from cwd to find `.agent/`, so it works whether
  Claude Code launches it from project root or a subdirectory.

## 5. Strengths

1. **Excellent boundary discipline.** `boundaries.js` is small, tested
   (`test/test-boundaries.js`), and correctly enforces project root,
   `working_folders`, and task `packages` with proper trailing-separator
   normalization. The "task packages narrow further than working_folders"
   pattern is a clean capability scope per task.
2. **Single source of truth on disk.** No DB, no parallel cache. The same
   markdown files team-pipeline reads/writes are the same files team-mcp
   reads/writes -- they coexist without conflict. A user can disable team-mcp
   and lose nothing.
3. **Handcrafted, dependency-light schema.** Two npm deps total. Schema is
   ~180 LOC of clear predicates. Easy to audit.
4. **Resource subscriptions and live notifications.** The
   `pipeline://events` resource + `notifications/pipeline/event` give
   clients a real-time stream of pipeline state changes -- this is what
   makes the MCP server materially better than direct file I/O.
5. **Clean error vocabulary.** Four error codes, used consistently.
6. **Friendly degradation.** Missing `.agent/` -> exit 0 with stderr help.
   Missing `messenger.md` -> channels disabled, server keeps running.
   Channel init failure -> caught, server keeps running.
7. **Comprehensive test coverage.** 14 `node --test` files exercise every
   tool module, schema rules, boundaries, events, integration flows, and
   adventure TC tracking. No external test runner.
8. **Deployment manual quality.** The 920-line manual covers tool
   reference, error codes, event types, MCP resource URIs, troubleshooting,
   and four end-to-end workflow walkthroughs. This level of documentation is
   uncommon for v0.1.0 software.

## 6. Problems and Failures

### High severity

- **H1 -- Non-atomic writes.** `writeState()` calls `writeFile()` directly.
  No write-to-temp-then-rename, no fsync. The README and CLAUDE.md both
  describe the server as the "single writer" for high-value state files;
  that claim is partially defeated by a crash window of arbitrary length
  during which the markdown file can be truncated to zero bytes. Fix is
  cheap: write to `${path}.tmp`, fsync, rename.
- **H2 -- Concurrency control limited to two tools.** Only `agent_spawn`
  and `agent_complete` use `LockManager`. `task_update`, `adventure_update`,
  `task_advance`, `metrics_log`, `knowledge_add` all read-modify-write
  without locks. Two parallel agents writing the same task file silently
  lose one another's changes. The README's "single writer" framing assumes
  serial execution.
- **H3 -- No persistence of lock state.** Locks live only in the server
  process. If Claude Code restarts the server (which it does freely on
  reload), locks vanish mid-flight. Acceptable today because operations
  are short, but combined with H2 it means concurrency safety is largely
  aspirational.
- **H4 -- `last_event` write inside emit() can race itself.** Every
  `emit()` does its own read-modify-write of `lead-state.md` to update
  `last_event`. Two near-simultaneous emits race; the second clobbers
  fields the first set. Same root cause as H1/H2.

### Medium severity

- **M1 -- Inconsistent input-schema shape.** Some tools declare schemas as
  `{ type: 'object', properties: {...}, required: [...] }`; others as a flat
  property map without the outer `object` envelope. The MCP SDK accepts
  both, but downstream MCP clients that introspect tool schemas will see
  inconsistent shapes.
- **M2 -- Tool-count drift in docs.** The deployment manual has an explicit
  caveat: "26 tools across 6 categories ... bringing the total to 27".
  Counting actual `server.tool()` calls across the 13 tool modules yields
  more than 27. The doc tries to apologise for the drift instead of
  generating the count from the source. Symptom of a hand-maintained
  catalog -- the same risk you see in team-pipeline's command/skill list.
- **M3 -- Stale-agent semantics inconsistent.** `state.js`
  `cleanupStaleAgents` uses 5-minute threshold; `diagnostics.js` `isStaleAgent`
  uses 30-minute warn / 2-hour critical. Two different definitions of "stale"
  in the same codebase.
- **M4 -- No way to subscribe to a subset of events.** The
  `pipeline://events` resource is one undifferentiated firehose. If you only
  care about `task.completed`, you still get every `task.advanced`. Filtering
  must be done client-side.
- **M5 -- Channel polling for inbound is opaque.** Telegram polls
  `getUpdates`; there is no documentation of poll interval, no way to
  inject a webhook, and no rate-limit handling beyond a single 2 s retry.
- **M6 -- Channel manager wraps eventEmitter.emit at runtime.** The
  monkey-patch ("Store original emit for wrapping") couples channel
  forwarding to private internals of `EventEmitter`. A safer pattern would
  be a public `on(handler)` interface on `EventEmitter`.
- **M7 -- Heavy duplication of the team-pipeline state machine.** Stage
  lists, status-per-stage, transition tables, default assignees -- all
  re-declared in `schema.js` and must be kept in sync with the team-pipeline
  plugin's own copy. There is no shared schema package.
- **M8 -- No version negotiation between plugins.** team-mcp is `0.1.0`,
  team-pipeline is `0.14.3`. There is no contract that ties them together;
  a breaking change in either plugin's `.agent/` layout silently breaks the
  pair.

### Low severity

- **L1 -- `subscribe`/`unsubscribe` handlers reach into `server.server`.**
  Comment admits "McpServer does not auto-register these". Forward-compat
  risk if the SDK changes its internal Server.
- **L2 -- Capabilities registered after the first `server.resource()` call.**
  Order-dependent on SDK behaviour: a comment notes the SDK deep-merges
  capabilities. Brittle.
- **L3 -- Event ring buffer size hard-coded to 50.** Not configurable.
- **L4 -- LockManager TTL hard-coded to 30 s.** Not configurable from
  `config.md`.
- **L5 -- README tool table is shorter than CLAUDE.md tool list, which is
  shorter than the deployment manual reference.** Three drift-prone
  catalogs.
- **L6 -- Channel adapter for inbound creates an in-memory `pendingApprovals`
  queue.** Lost on restart. Approvals can vanish silently.

## 7. Strange Decisions

- **Server name is `team-pipeline`, not `team-mcp`.** The MCP server
  identifies itself as the *plugin it serves*, not its own project. This is
  fine but surprising when reading `index.js`.
- **Exit code 0 when `.agent/` is missing.** Defensible, but surprising for
  a process supervisor that expects "no service" to be a non-zero exit.
- **Tool names use a dot prefix (`pipeline.task_create`).** MCP idiom is
  often a slash or underscore convention; the dot is unusual and the
  team-pipeline plugin docs sometimes write `/task-create` (a slash command)
  for the same operation. Easy source of user confusion.
- **`pipeline.config_set` takes `value: string` (not arbitrary JSON).**
  Forces callers to JSON-encode arrays/objects into a string -- the
  troubleshooting section of the manual literally shows
  `value: "[{\"name\":\"lib\",...}]"` as the recommended idiom. An object-
  typed parameter would be cleaner.
- **`adventure_update` rejects `state` updates with `VALIDATION_ERROR`.**
  Forces a separate `adventure_advance` call. Defensible (state machines
  should be transition-driven), but surprising: tasks allow `task_update`
  to set `status` (which can drive transitions).
- **No `task.delete` or `adventure.delete`.** Only `task_archive`. This is
  probably intentional (pipelines should be append-only) but not stated.
- **`agent_spawn` valid roles hard-coded to four** (`planner`, `implementer`,
  `reviewer`, `researcher`). team-pipeline ships 14 agent types; the MCP
  cannot record adventure-planner, step-generator, etc.

## 8. Recommendations

1. **Atomic writes everywhere.** Replace `writeFile()` with
   `writeFile(${path}.tmp) + fsync + rename`. One-day refactor.
2. **Lock scope to per-file, not per-resource.** Wrap every read-modify-
   write in `task.js`, `adventure.js`, `metrics.js`, `knowledge.js`, and
   `events.js` with `lockManager.acquire(filePath, callerId)`. Make session
   IDs an MCP-level concept (one per stdio connection).
3. **Generate the tool catalog from source.** Walk the `register*Tools`
   modules at startup, dump a JSON tool registry, and have the README and
   deployment manual cite that file rather than hand-curating.
4. **Share the schema with team-pipeline.** Extract `STAGES`, status
   tables, and transitions into a tiny published package (or an `.ark`
   spec generated to JSON, given this repo's direction). Both plugins
   import the same table.
5. **Subscribe-with-filter for the events resource.** Allow
   `pipeline://events?type=task.completed` (resource templating). Falls
   back to the firehose if no template is supported by the client.
6. **Replace channel `monkey-patch` with `eventEmitter.on(handler)`.**
   Public subscriber interface; the channel manager registers like any
   other consumer.
7. **Persist the inbound-channel approval queue.** Write
   `pendingApprovals` to `.agent/messenger-state.md` (or similar) so a
   restart does not lose pending user decisions.
8. **Add HTTP/SSE transport (gated by API key) for cross-machine use.**
   The current stdio-only design ties the MCP to one Claude Code instance
   on one machine. With auth + atomic writes (R1, R2), a network transport
   would let the same `.agent/` state be served to multiple clients.
9. **Reconcile `cleanupStaleAgents` and `isStaleAgent` thresholds.**
   Promote both to config (e.g. `agent.stale_warn_min`,
   `agent.stale_critical_min`).
10. **Allow registering arbitrary agent roles.** Change `agent_spawn`'s
    role enum to a free string with a soft-validation list pulled from
    `.agent/roles/`.
11. **Generate `.mcp.json` from the team-pipeline plugin manifest.** Pin a
    compatible team-pipeline version in `package.json` peer-deps and read
    it back at startup; refuse to start if the on-disk team-pipeline is
    incompatible.

## Findings

- **What it is.** A 132-line entry point and ~3.3 KLOC of tools/library
  code that fronts the team-pipeline `.agent/` directory with 40+ MCP
  tools, one resource, and live notifications. Pure Node 18+ ESM, two
  runtime dependencies (`@modelcontextprotocol/sdk`, `yaml`), stdio
  transport only.
- **Tool surface.** 13 modules covering tasks (7), adventures (6),
  agents (3), pipeline status (1), config (2), metrics (2), knowledge (3),
  files (3), hooks (3), agent-memory (4), diagnostics (3), skills (4),
  channels (3). Errors normalized to four codes
  (`VALIDATION_ERROR`/`NOT_FOUND`/`LOCK_CONFLICT`/`INTERNAL_ERROR`).
- **Auth model.** None at the protocol level (stdio + parent trust).
  Channel secrets read from env vars indirectly named in
  `.agent/messenger.md`. There is no notion of multi-user identity
  anywhere.
- **Concurrency model.** Single in-memory `LockManager` (30 s TTL,
  re-entrant per session string), used only by `agent_spawn` and
  `agent_complete`. Every other write is unlocked, including `task_update`
  and the implicit `last_event` write inside `emit()`. **This is the
  largest correctness gap.**
- **Durability model.** No atomic writes, no fsync, no journal.
  `writeState()` is one `writeFile`. Crash mid-write truncates state.
  Pair this with H2 and the "single-writer" claim in the README/CLAUDE.md
  is overstated.
- **Strengths to preserve.** Boundary enforcement, dependency minimalism,
  graceful degradation when `.agent/` or `messenger.md` is missing, the
  events resource + notifications stream, exhaustive deployment manual,
  full `node --test` coverage including TC integration tests.
- **High-priority fixes.** H1 (atomic writes), H2 (lock scope), H4
  (`last_event` race) are all small refactors that materially improve
  correctness. M2 (tool-count drift) and M7 (schema duplication) point at
  the same root cause -- a hand-curated catalog of state-machine rules
  that should be generated.
- **Strange decisions worth surfacing.** Server identifies as
  `team-pipeline` not `team-mcp`; `config_set` accepts only string values
  (forcing JSON-encoded literals); `agent_spawn` role enum hard-codes 4
  roles when the upstream pipeline ships 14; `adventure_update` forbids
  `state` mutations while `task_update` allows `status` mutations.
- **Roadmap implications.**
  - Team MCP is the natural seam where the team-pipeline hook prompts
    can be replaced with deterministic tool calls (this matches
    recommendation #1 in the team-pipeline review).
  - Sharing the stage/transition schema with team-pipeline (R4) is a
    prerequisite for either project moving to an `.ark`-generated state
    machine.
  - HTTP/SSE transport (R8) is a precondition for any "team" use of the
    MCP across machines or sessions; today the name "team" is aspirational.
  - The 11-event taxonomy is a strong foundation for the messenger work
    in adjacent Claudovka projects (Telegram/Discord adapters already
    consume it via the channel manager).
  - The deployment manual's quality is a model for the rest of the
    Claudovka ecosystem -- borrow its structure for binartlab and the
    marketplace.
