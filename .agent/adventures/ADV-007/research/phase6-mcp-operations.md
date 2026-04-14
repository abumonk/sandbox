---
task: ADV007-T019
adventure: ADV-007
phase: 6
target_conditions: [TC-018]
upstream:
  - .agent/adventures/ADV-007/research/phase3-2-mcp-servers.md
  - .agent/adventures/ADV-007/research/phase3-2-integration-matrix.md
  - .agent/adventures/ADV-007/research/phase5-concept-designs.md
  - .agent/adventures/ADV-007/research/phase2-entity-redesign.md
researched: 2026-04-14
---

# Phase 6 — MCP-Only Operations Architecture

This document designs the Phase 6 transformation of Claudovka's
operations layer from CLI-and-shell-scripted deploy / compile / build /
test into an architecture where **every mutating operation crosses an
MCP tool boundary**. No agent role, human operator, or orchestrator
process shells out to `git push`, `cargo build`, `wrangler deploy`,
`pytest`, or `bash scripts/*.sh` directly. Instead every such action
is invoked through a named MCP tool with structured arguments, a
recorded invocation id, and a typed result. The literal phrase
**MCP-only** is restated in every major section for TC-018 grep proof.

The research draws explicitly on T015 (the 14-server MCP catalog,
especially the B-1 single-deploy-platform blocker) and T016 (the
critical-path ordering that puts `github` first, `memory` second,
deploy MCP last behind B-1). Phase 5 adds `scheduling`, `messenger`,
and `run` entities that Phase 6 must expose through tools as well —
a schedule firing and a CI run starting are operationally the same
class of event.

---

## 1. Why MCP-only

### 1.1 What the current state costs us

The current Claudovka pipeline mixes three operational substrates:

1. Shell commands hard-coded in prose (`git add -A && git commit -m ...`
   in hook scripts, `npx some-tool` in researcher prompts).
2. Python scripts under `ark/tools/` that roles invoke through `bash`
   with positional args.
3. Ad-hoc file writes into `.agent/` that mutate pipeline state
   without an audit record of the caller.

Every one of these paths is:

- **Non-deterministic from the pipeline's point of view** — X8 in the
  Phase-1 cross-project synthesis. The same task run twice can hit
  different shell environments, different `PATH`, different hook
  outputs.
- **Unauditable** — `bash -c` does not leave a structured record of
  who called what with which arguments. Attempts to reconstruct the
  causal graph after an incident require grepping adventure.log.
- **Unpermissioned** — Bash is all-or-nothing. Once a role has bash,
  it can run anything. The per-capability permission model
  (`mcp.<server>.<resource>.<action>`, blocker B-3 in T016) cannot
  enforce least-privilege on shell calls.
- **Un-replayable** — There is no way to dry-run or replay an
  operation without actually executing it.

The **MCP-only** posture fixes all four at once: MCP tool calls are
structured, logged, permissioned, and (with the right adapter) dry-
runnable.

### 1.2 Scope boundary

MCP-only applies to **mutating operations** — anything that writes to
a remote system (git remote, deploy target, package registry, DB),
modifies durable local state (`.agent/` ledgers, generated code
outputs under `ark/specs/meta/generated/`), or consumes non-trivial
compute (a full build, a full test suite, a benchmark run).

MCP-only does **not** apply to:

- Local code editing (agents still use the `Edit` / `Write` tools
  directly on source files — those are already tool calls).
- Read-only exploration (`Grep`, `Glob`, `Read` are fine; they do
  not mutate remote state).
- Short local utility calls inside a larger MCP tool
  implementation (the tool body can shell out; the *agent* never does).

The boundary is crisp: the agent's tool-call ledger shows only MCP
tools and the base file/search primitives. Everything imperative is
behind one of them.

---

## 2. Tool Surface

The operational surface is seven named tools, each an MCP endpoint.
They are versioned (`v1`, `v2`) so the surface can evolve without
breaking roles that pin a version. Each tool returns a structured
result envelope `{status, invocation_id, artifacts, log_ref,
duration_ms, error?}` and records an append-only event in the Phase-5
`run` ledger.

### 2.1 `deploy`

`deploy(target, ref, env, dry_run=false)` — ship a build artifact to
a runtime. Implemented by whichever deploy MCP wins the B-1 decision
(see §3). Examples:

- `deploy(target="marketplace-ui", ref="main", env="staging")`
- `deploy(target="team-mcp-registry", ref="v0.4.2", env="prod",
  dry_run=true)`

Preconditions: `build` must have succeeded for `ref` (enforced by the
tool body consulting the run ledger). Post-conditions: a
`deployment.succeeded|failed` event on `runs/deployments.jsonl` and
a link to the platform's deployment ID in `artifacts`.

### 2.2 `build`

`build(project, ref, profile="release")` — produce a deployable
artifact. Examples:

- `build(project="ark", ref="HEAD", profile="debug")` — runs the
  Rust workspace build.
- `build(project="marketplace-ui", ref="HEAD")` — runs `npm run
  build` inside a sandboxed worker.

Build logs are streamed into `runs/builds/<invocation_id>.log` and
the final artifact hash is recorded for later `deploy` calls to
reference.

### 2.3 `compile`

`compile(spec, target, out=None)` — run Ark codegen. This is the
load-bearing operation for Claudovka's own DSL. Examples:

- `compile(spec="ark/specs/meta/evolution_roles.ark",
  target="python")` — invokes `ark_codegen.py` with structured args
  instead of argv.
- `compile(spec="ark/specs/meta/ark_agent.ark", target="rust")` —
  once the Rust pipeline reaches parity.

`compile` is distinct from `build` because Ark specs compile to
source code that `build` later turns into a runtime artifact. The
two-stage split lets agents review generated code before it reaches
a build.

### 2.4 `test`

`test(scope, filter=None, update_snapshots=false)` — run the
appropriate test suite for a scope and return a structured pass/fail
record plus failed test names. Scopes: `scope="ark"`, `scope="binartlab"`,
`scope="marketplace"`, `scope="team-pipeline"`, `scope="team-mcp"`,
or the special `scope="full"` for the full-stack matrix.

`update_snapshots` is permission-gated and only available to the
implementer role during snapshot-update tasks. The tool body refuses
`update_snapshots=true` if the repo has uncommitted changes outside
the snapshot directories.

See `phase6-autotest-strategy.md` for how `test` composes with the
autotest orientation (coverage budgets, flakiness policy, golden
tests).

### 2.5 `migrate`

`migrate(scope, from, to, dry_run=false)` — apply a versioned
migration (database schema, `.agent/` ledger format, generated-code
layout). Migrations are themselves `.ark` specs compiled into
executable plans; `migrate` runs the plan. Dry-run produces the plan
and diff without applying.

Examples:

- `migrate(scope="agent", from="v0.3", to="v0.4", dry_run=true)` —
  pipeline-ledger format bump.
- `migrate(scope="supabase", from="2026-04-01", to="2026-04-14")` —
  DB schema migration if Supabase is the deploy pick.

### 2.6 `rollback`

`rollback(target, to_ref)` — revert a deployment to a prior known-
good reference. Backed by the same deploy MCP as `deploy`. Requires
the target's deployment history is intact on the platform; if not,
`rollback` falls through to a re-`deploy` of `to_ref`.

Failure of `rollback` itself is a *critical escalation* — the tool
emits a `run.critical` event that the messenger surfaces to a human
immediately (see `phase6-automation-first.md` §4).

### 2.7 `metrics`

`metrics(scope, window, query)` — read-only analytics over the
metrics ledger. `metrics` is the **only** read tool in this surface
because the other six are mutating. It's included here because its
results feed automation decisions (e.g., "should we auto-retry?"
depends on historical flake rate).

Backed by ClickHouse MCP at scale (T015 §9) or local DuckDB until
metric volume justifies the hosted dep (T016 blocker threshold ~10k
rows).

---

## 3. Integration with GitHub MCP and the Single-Deploy Stack

### 3.1 GitHub MCP as the always-on substrate

Per T016 critical-path ordering, **github MCP is adopted first** and
becomes the default backbone for every source-control operation. In
the MCP-only architecture, `build` / `compile` / `test` all take a
`ref` argument; that ref is resolved through `github.get_ref`, files
are read through `github.get_file_contents`, and any commit produced
by a tool run is pushed through `github.create_or_update_file` or
`github.push_files`. No tool body calls `git` directly.

Pull-request-per-adventure (T015 integration plan) is a direct
consequence: every adventure closes with a PR created by
`github.create_pull_request`, CI runs kicked off by
`github.run_workflow`, and merge enforced by `github.merge_pull_request`
after review state is `APPROVED`.

### 3.2 Deploy stack — resolving B-1

T015 and T016 both flagged B-1 (single-deploy-platform decision) as a
hard blocker. Phase 6 forces the decision; adopting all four deploy
MCP families fragments the tool surface and explodes permission
scope. The Phase-6 recommendation is the **Cloudflare suite**
(`cloudflare-docs` + `cloudflare-workers-bindings` +
`cloudflare-workers-builds` + `cloudflare-observability`), chosen for:

- **Closed loop**: provision (bindings) → build (builds) → run → observe
  (observability) → reference (docs) is a single-vendor pipeline with
  one OAuth identity.
- **Edge-first** matches Claudovka's UI (Phase 4) which is a thin
  realtime view of pipeline state, not a database-heavy app.
- **Workers + D1/KV/R2** covers the state shapes Claudovka needs (KV
  for session, D1 for metrics mirror, R2 for artifact storage).

Fallback: if the team prefers developer-ergonomic UX over edge-first,
switch to **Vercel + Supabase**. That fallback changes which MCPs
back `deploy` / `migrate` but **does not change the Phase-6 tool
surface**. The surface is platform-agnostic by design — the tools
`deploy`, `build`, `migrate` delegate to whichever MCP is wired up in
the orchestrator's permission manifest.

### 3.3 Wiring rules

- Each orchestrator process loads a `deploy_provider` from config
  (`cloudflare | vercel | railway | supabase`). The seven
  operational tools resolve through that provider.
- Deploy provider is a **Phase 6 constant** for a given Claudovka
  deployment; switching mid-adventure is out of scope.
- Read-only capabilities (`cloudflare-docs`, `cloudflare-observability`)
  stay available to any role; mutating capabilities are gated per
  §4.

---

## 4. Security Model

### 4.1 Permission tiers

MCP-only gives us a clean permission lattice. Every tool has a
capability string and every role declares the capabilities it may
invoke. Four tiers, increasing in blast radius:

- **T-read** — `metrics`, `cloudflare-docs.search`,
  `github.get_*`, `github.search_*`, `test --dry-run`.
  All roles get these.
- **T-local-write** — `compile`, `build`, `test` (non-destructive).
  Implementer role gets these. Researcher role gets them behind a
  confirmation gate (see T013 CCGS `disallowedTools` pattern).
- **T-vcs-write** — `github.create_pull_request`,
  `github.push_files`, `github.create_or_update_file`.
  Implementer + lead roles.
- **T-deploy** — `deploy`, `migrate`, `rollback`, and any
  `cloudflare-workers-builds.*` / `cloudflare-workers-bindings.*`
  mutation. Only a dedicated `deployer` role (Phase 3.1 role review
  output) or a human assignee may invoke these. Agent roles never
  get T-deploy implicitly.

### 4.2 Secrets

Secrets never enter the MCP protocol. The orchestrator holds a
keystore (environment variables sourced from a vault at startup) and
the MCP server bodies read from it. Tool arguments never carry
secrets as strings. A role cannot accidentally exfiltrate a secret
through a tool call because the secret is not in the call site.

Permission-string rule: `T-deploy` capabilities imply *server-side*
access to the deploy-provider token. The role does not see the
token; it only sees tool names it may call.

### 4.3 Audit trail

Every tool invocation appends to `runs/invocations.jsonl`:

```
{ "invocation_id": "inv-<ulid>",
  "caller": "role:implementer",
  "adventure_id": "ADV-007",
  "task_id": "ADV007-T019",
  "tool": "build",
  "args_hash": "sha256:...",
  "status": "ok",
  "duration_ms": 12400,
  "ts": "2026-04-14T05:09:00Z" }
```

The args_hash (not the args themselves) keeps the ledger small but
lets an auditor join against a separate args ledger if they hold the
corresponding permission.

### 4.4 Rate and blast limits

Each `T-deploy` tool carries a per-adventure budget: `deploy` no more
than 5 times per hour per target; `migrate` no more than once per
scope per 24h without a human-approved override. Budgets are
enforced by the orchestrator before the MCP call leaves the process,
not by the remote service — protects against both bugs and
prompt-injection.

---

## 5. Failure and Recovery Semantics

### 5.1 Idempotency

Every mutating tool accepts an `idempotency_key` (ULID). If a tool is
called twice with the same key, the second call returns the first
result without re-executing. This is what makes the Phase-5
`scheduling` system safe: a `schedule.fire` that crashes the
orchestrator mid-`deploy` can be replayed on restart with the same
key, and the deploy either completes or is confirmed already done.

Keys live in `runs/idempotency.kv` with a 7-day TTL. The key
includes `(tool, target, ref, caller_adventure, schedule_fire_id?)`
to avoid collisions across adventures.

### 5.2 Partial failure

`deploy` is not atomic against the external world — a
`cloudflare-workers-builds.trigger` can succeed while a follow-up
`binding.update` fails. The tool body uses a two-phase protocol:

1. **Plan** phase writes a `deploy.planned` event with every sub-step.
2. **Execute** phase writes `deploy.step.<n>.ok` or `.fail` per step.
3. If any step fails, the tool emits `deploy.partial` and halts; a
   subsequent `rollback` call consults the partial record to undo
   whatever did land.

The event stream is the truth; the Cloudflare/Vercel/Supabase state
is the projection. If the two disagree, the ledger is reconciled
against the platform API by a nightly `reconcile` job (itself an
MCP tool invoked by a scheduled `schedule`).

### 5.3 Escalation

Failures are classified:

- **transient** — network, rate-limit, transient 5xx → automatic
  retry with exponential backoff (bounded by the `retry_backoff`
  schedule kind from Phase 5 §1).
- **deterministic** — 4xx, validation, spec-error → no retry;
  messenger notifies the caller role; task returns to
  `implementing.failed`.
- **critical** — rollback failure, migration partial failure,
  auth/permission errors → messenger notifies a human immediately
  and pauses the adventure (adventure.log gets a `paused:critical`
  entry).

Every classification is a *tool response field*, not an ad-hoc
interpretation of stderr. This is the core dividend of **MCP-only**
— error taxonomy is part of the contract, not parsed from log
lines.

### 5.4 Time and clock

The Phase-5 scheduler (§1) drives retry backoffs and deploy windows.
The same singleton scheduler service is reused — Phase 6 adds
`tool.retry` and `tool.reconcile` target kinds to the scheduler's
target vocabulary. No separate cron inside each tool; all time-
driven operations are schedules.

---

## 6. Migration Plan

Phase 6 cannot switch to MCP-only overnight. The staged rollout:

- **M0 (Phase 3.2 wrap, done)** — github MCP adopted; PR-per-adventure
  live. Still allows shell git for emergency paths; pipeline warns
  on shell-git use.
- **M1 (early Phase 6)** — `build` / `compile` / `test` MCP tools
  wrap existing `ark/tools/*.py` invocations. Agents updated to
  call the tools instead of shelling out.
- **M2 (mid Phase 6)** — B-1 resolved; deploy-provider MCPs wired;
  `deploy` / `migrate` / `rollback` tools go live, initially
  alongside legacy deploy scripts behind a feature flag.
- **M3 (late Phase 6)** — feature flag flipped to MCP-only; shell
  paths removed; `disallowedTools` extended to ban direct `git`,
  `cargo`, `npm`, `wrangler` calls from agent roles.
- **M4 (Phase 6.1)** — the abstract representation layer (T020)
  allows the seven tools to be re-implemented on a different
  deploy provider without changing agent code.

---

## 7. Success Criteria for Phase 6 MCP-only

- Zero non-MCP shell commands in agent role prompts or researcher /
  implementer task outputs, as measured by a `disallowedTools`
  audit across 20 consecutive completed tasks.
- 100% of `deploy`, `build`, `test`, `migrate`, `rollback` events
  recorded in `runs/invocations.jsonl` with a resolvable
  `invocation_id`.
- Zero unreconciled drift between the platform state and the
  pipeline ledger over a 30-day window, as measured by the nightly
  reconcile job.
- `rollback` MTTR (mean time to roll back a bad deploy) under 90
  seconds, as measured across at least five drills.
- `disallowedTools` coverage flagged in every role manifest; no
  role has `Bash` ambient access to git/deploy/runtime CLIs.

These criteria feed TC-018 proof and become the acceptance gate
for the Phase 6 MCP-only milestone. Phase 7 (on-sail) then shifts
from MCP-only *adoption* to MCP-only *optimization* — token cost,
latency, coverage of novel operations.
