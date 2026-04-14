---
project: binartlab
version: 0.1.0
source: R:/Claudovka/projects/binartlab/
design_doc: R:/Claudovka/docs/plans/2026-02-18-binartlab-design.md
research_task: ADV007-T004
researched: 2026-04-14
license: (none declared in package.json; private workspace)
upstream: not published — local monorepo under R:/Claudovka
---

# Binartlab Research

Binartlab is the **server-side application** half of the Claudovka ecosystem — a
modular monolith that orchestrates Claude Code agents, manages projects and
repositories, and exposes a visual web UI for building and running pipelines
through a layered DSL. Where `team-pipeline` operates *inside* a single Claude
Code session as a markdown-state plugin, binartlab operates *around* sessions,
spawning the `claude` CLI as child processes, attaching scoped MCP servers to
each one, and projecting state into a SQLite + filesystem store served to a
React/Tailwind frontend over REST/WebSocket. The codebase is a TypeScript
npm-workspaces monorepo; runtime is Node ≥20 with `vitest` for tests.

## 1. Repository Location and Status

The project lives **locally** at `R:/Claudovka/projects/binartlab/`. There is no
public upstream — `package.json` is `"private": true` and no git remote is
declared in the design document. Sister artifacts:

- **Design**: `R:/Claudovka/docs/plans/2026-02-18-binartlab-design.md` (status:
  Approved, dated 2026-02-18).
- **Runtime data dir**: `R:/Claudovka/.binartlab/` containing `data.db`,
  `data.db-shm`, `data.db-wal` — confirms the SQLite store has been initialized
  and at least one process has run against it (WAL mode enabled).
- **Adventures**: Claudovka has its own `.agent/adventures/` (ADV-001 through
  ADV-022) — meaning binartlab development is itself driven by team-pipeline,
  the dogfooding loop the design's "Core Values" section calls out.

## 2. Workspace Layout — Actual vs Designed

The design document specifies **8 packages**. The repo on disk has **9** (the
mobile package is an addition not in the original design doc):

| # | Package | LOC (src) | Tests | Role |
|---|---|---:|---:|---|
| 1 | `@binartlab/shared` | 568 | 3 | Zod schemas, types, error classes, constants shared across all packages |
| 2 | `@binartlab/storage` | 1230 | 7 | `better-sqlite3` DB layer + `fast-glob` filesystem abstraction |
| 3 | `@binartlab/dsl` | 747 | 3 | YAML-based three-layer DSL: schema, instance, runtime |
| 4 | `@binartlab/core` | 2060 | 21 | Agent lifecycle, project mgmt, pipeline executor, metrics, triggers, stages |
| 5 | `@binartlab/mcp` | 410 | 3 | Per-agent scoped MCP server (`@modelcontextprotocol/sdk` ^1.26.0) |
| 6 | `@binartlab/web-api` | 1028 | 14 | REST routes (agents/health/metrics/pipelines/projects/tasks) + WebSocket broadcaster |
| 7 | `@binartlab/cli` | 281 | 3 | Admin CLI (`pino` logging) — start server, manage config |
| 8 | `@binartlab/web-ui` | 5497 | 4 | React + Vite + Tailwind + `@xyflow/react` (React Flow) + react-query |
| 9 | `@binartlab/mobile` | 9429 | 27 | **Undocumented in design** — Expo / React Native app (navigation, notifications, async-storage, netinfo) |

Total: **~21,250 LOC TypeScript**, **85 test files**. The monorepo uses npm
workspaces (no Turbo/Nx); root `package.json` simply fans out
`build`/`test`/`lint` via `--workspaces --if-present`.

### Inter-package dependency graph

```
shared  ────────────────────────────────────────────────────
   ▲        ▲        ▲        ▲          ▲          ▲
   │        │        │        │          │          │
storage  dsl ──► core ──► mcp │          │          │
   ▲              ▲           │          │          │
   │              └───────────┴── web-api │          │
   │              ▲                       │          │
   │              └───────────────────────┴── cli    │
   │                                                  │
   └── (web-ui consumes shared types only;            │
        runtime contact is via REST/WS)               │
                                                      │
mobile ──── consumes shared types; talks REST/WS only ┘
```

Concrete `dependencies:` blocks (verified by reading each
`package.json`):

- `shared`: zod (no internal deps — root of the graph).
- `storage`: shared, better-sqlite3, fast-glob.
- `dsl`: shared, js-yaml.
- `core`: shared, storage, dsl, js-yaml.
- `mcp`: shared, core, @modelcontextprotocol/sdk.
- `web-api`: shared, core, storage, ws, pino (peer pino-pretty).
- `cli`: shared, core, storage, web-api, pino (peer pino-pretty).
- `web-ui`: shared, react/react-dom, react-router-dom, @tanstack/react-query,
  @xyflow/react.
- `mobile`: shared, react, react-native, expo, expo-haptics,
  expo-notifications, @react-navigation/*, @tanstack/react-query, async-storage,
  netinfo.

Notable: **mcp depends on core** (rather than core depending on mcp). The MCP
server is treated as an *outward-facing surface* parameterized by core
capabilities, not as a transport that core uses internally. This is the right
direction.

## 3. Internal Architecture per Package

### core (the biggest internal subsystem at 2060 LOC, 21 tests)

`core/src/index.ts` exports:

- **Projects**: `ProjectManager`, `ProjectScanner`, `ProjectStorageAdapter`.
  Adapters indirect over storage so core doesn't depend on better-sqlite3
  directly.
- **Agents**: `AgentManager`, `AgentMonitor` (heartbeat/health), and
  `spawnAgent` / `ClaudeProcess` / `MockChildProcess`. The mock variant is the
  testing seam — agent spawning is the one place that hits a real subprocess.
- **Pipelines**: `PipelineExecutor` with explicit `RunStorage` and
  `ExecutorDependencies` interfaces (dependency injection for testability).
- **DSL bridge**: `dsl/loader.ts` + `dsl/pipeline-parser.ts` re-export and
  specialise `@binartlab/dsl` for pipeline definitions.
- **Metrics**: `MetricsCollector` with pluggable `MetricsStorage`.
- **Stages, Triggers**: barrel exports.

### dsl (747 LOC)

Three-layer YAML DSL exactly as designed:
```
dsl/src/
  schema/    -- Layer 1: entity/field type definitions
  instance/  -- Layer 2: instances of schemas (pipeline configs)
  runtime/   -- Layer 3: parser, validator, ${} variable resolver, executor
```
Single `js-yaml` parser; no custom grammar. Validation comes from zod schemas
in `@binartlab/shared`.

### web-api (1028 LOC)

Routes per resource (`agents.ts`, `health.ts`, `metrics.ts`, `pipelines.ts`,
`projects.ts`, `tasks.ts`) plus `ws/server.ts` and `ws/broadcaster.ts`. The
broadcaster is a separate object from the server — clean separation between
"accept and authenticate WS clients" and "fan out events to subscribers". Every
`.ts` file has a corresponding `.js` and `.d.ts` on disk, indicating the
package is **also checked in built**, which is unusual for a workspace-internal
package and bloats diffs (see Issues §6).

### web-ui (5497 LOC, 4 tests)

Pages: `Dashboard`, `Projects`, `Tasks`, `PipelineEditor`, `PipelineRunner`,
`AgentMonitor`, `SchemaEditor`, `Knowledge`, `ApprovalQueue`, `System`,
`Settings`. Component dirs: `dashboard`, `layout`, `metrics`, `pipeline`,
`projects`, `shared`. Stack: react-query for server state, react-router for
navigation, `@xyflow/react` (React Flow) for the visual pipeline editor.
**Test density is dramatically lower than backend** (4 component tests vs 21
core tests for ⅓ the LOC) — see Issues §3.

### mcp (410 LOC)

`server.ts` (createMcpServer), `scope.ts` (createScopeFilter — limits which
files/projects an agent can touch), and `tools/` (`files.ts`, `tasks.ts`).
Notably the design promised **6 tool categories** (Files, Tasks, Knowledge,
Pipeline, Agent self-management, Git). Reality: only **Files and Tasks** are
implemented. Knowledge, Pipeline, Agent-self, and Git tools are absent — see
Issues §1.

### mobile (9429 LOC, 27 tests — the elephant in the room)

Not in the design doc but ~44% of total source. Includes: `api/`, `components/`,
`hooks/`, `navigation/`, `notifications/`, `screens/`, `store/`, `theme/`,
`__mocks__/`. Uses Expo SDK 52, React Native 0.76, react-navigation v7,
react-query, expo-notifications. The app talks to web-api over REST/WS and
duplicates a substantial portion of web-ui's domain logic in mobile-native
shape. Ironically, mobile has **more tests than any other package**.

### cli (281 LOC)

Three subcommands wrapping web-api startup, config management, and process
lifecycle. Uses `pino` for structured logs.

## 4. TypeScript / Agent / Storage Patterns

- **Zod-first contracts.** `@binartlab/shared` declares zod schemas; everything
  else imports types via `z.infer`. Single source of truth across HTTP, WS, DB,
  and DSL boundaries.
- **Adapter pattern at every storage seam.** `ProjectStorageAdapter`,
  `AgentStorageAdapter`, `RunStorage`, `MetricsStorage` are all
  interface-typed. The DB-backed implementations live in `core/src/adapters/`.
  Lets core be tested against in-memory fakes.
- **Mock child process pattern.** `MockChildProcess` in
  `core/src/agents/process.ts` substitutes for the real `claude` CLI in tests.
  Agent lifecycle code (spawn → running → complete/error, plus pause/resume via
  SIGSTOP/SIGCONT, kill via SIGTERM) is exercised entirely against the mock.
- **better-sqlite3 + WAL.** Synchronous DB access (no async DB layer overhead).
  `~/.binartlab/data.db` with WAL mode enabled (`-shm`/`-wal` files present).
- **Logger as peer dep.** `web-api` and `cli` declare `pino-pretty` as an
  optional peer dependency — pretty-printing in dev, plain JSON in prod, no
  forced bundle bloat.
- **YAML over JSON for DSL artifacts.** Schemas and instances are YAML
  (js-yaml). Choice rationale per design: human-readable, comment-friendly,
  Monaco/VS Code support, maps cleanly to zod.
- **WebSocket broadcaster decoupled from server.** Subscribers register against
  the broadcaster, not the WS server — clean fanout.

## 5. Deployment

- **Local-first**, by explicit design decision. The design defers
  auth/HTTPS/multi-user to "Future". CLI starts a single Node process exposing
  REST + WS on a configurable port; SQLite at `~/.binartlab/data.db`; project
  files on local disk.
- **No Dockerfile, no CI config visible** in the workspace root. Production
  packaging is an open question.
- **No publish step**: every package is `"private": true`, intended for
  intra-monorepo consumption only.

## Findings

### Strengths

1. **Clean modular monolith.** 9 packages, 21k LOC, one-direction dependency
   graph (shared → storage/dsl → core → mcp/web-api → cli/web-ui/mobile). No
   circular deps. Each package would be extractable if/when the monolith needs
   to split.
2. **Adapter/dependency injection at every storage and process seam.** Core
   takes `RunStorage`, `MetricsStorage`, `AgentProvider`, `MockChildProcess` as
   inputs. This is the right pattern for a system whose hardest-to-test
   component is "spawn `claude` and watch it".
3. **Zod as the single source of truth.** One schema definition flows to HTTP
   validation, WS payloads, DB rows, and TS types. Eliminates a large class of
   drift bugs that team-pipeline (markdown-only) has.
4. **MCP per agent, scoped, stdio.** This is the architectural answer to the
   permission-prompts problem team-pipeline papers over with prose. Each agent
   gets a `createScopeFilter`-bounded MCP server attached to its stdio — tools
   the agent doesn't have access to don't exist for it, full stop.
5. **Good backend test density.** Core has 21 test files for 2060 LOC (~1 test
   file per 100 LOC). Storage and web-api are similarly well-covered.
6. **Dogfooding declared as a core value.** Design §"Core Values" insists every
   diagram/pipeline/design/plan/entity must have a DSL representation. If
   actually executed (TBD), this gives binartlab the same self-referential
   property Ark has.

### Problems and Failures

1. **MCP toolset is ⅓ implemented.** Design promised 6 tool categories (Files,
   Tasks, Knowledge, Pipeline, Agent self-management, Git). Code ships 2
   (Files, Tasks). Knowledge/Pipeline/Agent-self/Git scopes are absent.
   Severity: **high** — agents can't query their own pipelines or commit code.
2. **Mobile package is undocumented and untriaged.** 9429 LOC + 27 test files
   = the largest package by far, not mentioned in the design doc or the
   manifest's "8 npm workspaces" framing. No clear product hypothesis. Either
   document and own it, or excise it.
3. **Frontend test deficit.** Web-ui has 4 test files for 5497 LOC (1 per
   ~1374 LOC) versus the backend's ~1 per 100. Visual regression and
   integration tests for `PipelineEditor` (the React Flow surface) are
   conspicuously missing. Severity: **medium**.
4. **Built artifacts checked in.** web-api, core, dsl, etc. have `.js`,
   `.d.ts`, `.d.ts.map` files alongside `.ts` sources. Inflates diffs, breaks
   on stale-build, defeats the purpose of `tsc --build`. Severity: **medium**.
5. **No CI / no Dockerfile / no deploy story.** Package scripts are
   `tsc --build` / `vitest run` only. There is no smoke test that boots
   web-api + spawns a mock agent + drives a pipeline end to end.
6. **No git remote / no license.** The project is invisible outside
   `R:/Claudovka/`. Bus factor and contributor onboarding are both worst-case.
7. **DSL is ad-hoc YAML, not a real grammar.** Three layers (schema/instance/
   runtime) are all `js-yaml.parse` + zod validation + `${}` string
   interpolation. Compared to Ark's pest+lark grammar this is fragile (no
   syntax errors, only schema errors; no formatter; no LSP; no codegen). For a
   project whose value prop is "the DSL is the universal language" this
   undersells the DSL.

### Strange Decisions

1. **`mcp` depends on `core`, not the other way around.** Architecturally
   correct (the MCP server is an outward surface) but means the agent
   subprocess in `core/src/agents/process.ts` cannot use MCP types directly to
   describe what tools an agent has — a circular-dep hazard that has been
   averted by simply not modelling it. May want a `@binartlab/mcp-types` split.
2. **`@binartlab/cli` depends on `@binartlab/web-api` directly** rather than
   spawning it as a subprocess. Means starting the CLI links the entire web-api
   into the same Node process — fine for `start-server`, weird for `manage
   config` operations that don't need HTTP.
3. **No shared HTTP client package.** web-ui and mobile both call REST
   endpoints; the contract is enforced by zod schemas in `shared` but each
   client hand-rolls fetch wrappers. A `@binartlab/client` package wrapping the
   REST/WS surface would eliminate two parallel re-implementations.
4. **better-sqlite3 (synchronous) inside an event-loop server.** Justified by
   simpler code paths and SQLite's actual perf characteristics, but unusual
   enough that it deserves a comment in the README — long-running queries will
   stall the event loop and throttle WS broadcast.
5. **Mobile app uses react-query but no explicit offline strategy** despite
   declaring `@react-native-async-storage/async-storage` and
   `@react-native-community/netinfo`. Either remove the offline deps or commit
   to an offline-first design.
6. **Pipeline DSL is a YAML schema, but the visual editor is React Flow** —
   round-trip integrity (visual → YAML → visual) is not tested. A
   "pipeline-editor produces equivalent YAML for round-trip" property test is
   missing and is the single most valuable test the project does not have.

### Recommendations

1. **Finish the MCP toolset.** Implement Knowledge, Pipeline, Agent-self, and
   Git tool categories. Without them an agent inside a pipeline can read/write
   project files but cannot ask "what stage am I in?" or "commit my changes" —
   making the pipeline runtime opaque to the agents it runs.
2. **Decide about `@binartlab/mobile`.** Either: (a) update the design doc to
   include it, document its product hypothesis, and bring frontend test density
   up to mobile's level; or (b) freeze it and remove from the workspace until
   web-ui is feature-complete.
3. **Add a `@binartlab/client` package** wrapping the REST + WS API as typed
   methods (using `shared`'s zod schemas). Consume from both web-ui and
   mobile. Eliminates parallel fetch wrappers and gives a single place to add
   retry/auth/telemetry.
4. **Enforce `dist/` exclusion via `.gitignore`** and remove the checked-in
   `.js`/`.d.ts` files. Add a CI check for "no build artifacts in git".
5. **Add an end-to-end smoke test**: CLI start → POST /api/projects → POST
   /api/pipelines → trigger run with a `MockChildProcess` agent → assert
   pipeline reaches `complete` and WS events were broadcast in order. This is
   the test that catches integration regressions the unit-test fleet misses.
6. **Decide whether the DSL is YAML-forever or evolves to a real grammar.**
   If the latter, look at Ark (`R:/Sandbox/ark/`) — it already has the
   pest+lark dual-grammar, codegen pipeline, and verifier infra binartlab's
   DSL would benefit from. A potential merger: replace `@binartlab/dsl` with a
   thin Ark wrapper, so binartlab's "everything is the DSL" promise is
   backed by Ark's grammar discipline.
7. **Round-trip property test for PipelineEditor.** For any saved pipeline
   YAML, loading into React Flow and re-emitting must produce identical YAML
   (modulo formatting). Single highest-leverage frontend test to add.
8. **Publish a license file and create a git remote** even if internal. Bus
   factor on a 21k-LOC TypeScript codebase with one author is a real risk.
9. **Document the `~/.binartlab/data.db` schema** (currently only inferable
   from `storage/src/db/`). Migration strategy is unstated; SQLite WAL is
   already in use which is good, but no `migrations/` directory exists.
10. **Run binartlab inside team-pipeline (or vice versa) as the
    integration smoke test.** The two projects are designed as complementary
    halves of the same ecosystem; today they live in separate worlds. A
    Claudovka adventure that uses team-pipeline to drive binartlab development
    (already happening, per `R:/Claudovka/.agent/adventures/`) should
    eventually invert: use binartlab's web-ui to monitor a team-pipeline
    adventure in flight. That's the dogfooding loop the design's "Core Values"
    section actually demands.

### Integration with Other Claudovka Projects

| Project | Relationship | Integration Point |
|---|---|---|
| **team-pipeline** | Conceptually paired (in-session vs around-session). Currently disjoint at runtime. | binartlab's `mcp/tasks.ts` could expose team-pipeline's task lifecycle as an MCP tool, letting binartlab-spawned agents drive a `.agent/` directory transparently. |
| **team-mcp** | binartlab *is* a team-mcp implementation, with web-api + WS as the surface. | Replace team-mcp with binartlab as the canonical MCP server for the ecosystem, or absorb team-mcp's tool definitions into `binartlab/mcp/tools/`. |
| **claudovka-marketplace** | Separate distribution channel for plugins. binartlab consumes none today. | binartlab could be the *runtime* that loads marketplace plugins (skills/agents) into spawned Claude processes. |
| **Pipeline DSL (PDSL)** | binartlab has its own YAML DSL; PDSL is a separate JS DSL inside team-pipeline for visualization. | Two DSLs is one too many. Unify on either binartlab's YAML or on Ark's `.ark` grammar. |
| **Ark** (this repo) | Sibling — Ark is a DSL/codegen platform, binartlab is an orchestrator. | Strong fit: Ark could replace `@binartlab/dsl` and provide grammar-checked specs; binartlab could host an Ark studio web-ui. |

---

**Word count:** ~2,350
