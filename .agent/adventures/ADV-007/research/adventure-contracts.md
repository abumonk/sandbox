---
id: adventure-contracts
title: Inter-Adventure Data Contracts
adventure: ADV-007
target_conditions: [TC-033]
produced_by: ADV007-T023
companion_docs:
  - research/master-roadmap.md
  - research/adventure-dependency-graph.md
  - research/phase2-knowledge-architecture.md
---

# Inter-Adventure Data Contracts

## 0. Why contracts matter here

Every edge in the adventure DAG (`adventure-dependency-graph.md` §3) carries at least one artifact: a schema, an MCP tool, a file-on-disk format, or a registry. ADV-001..ADV-006 post-mortem lists three incidents where a downstream adventure silently consumed a legacy shape after an upstream adventure had rewritten it (see `pipeline-management-review.md` §2). These contracts exist to eliminate that failure mode.

The contract model is adapted from `phase2-knowledge-architecture.md` §4.5 (event schema evolution) and `phase6-2-migration-strategy.md` §2.3 (contract migrations).

A contract has:

1. **Producer** — the adventure (or adventure set) that owns the shape.
2. **Consumer(s)** — adventures that read/rely on the shape.
3. **Artifact path** — where it lives (store path, file path, tool name, schema name).
4. **Schema sketch** — the minimum fields and invariants.
5. **Freshness / staleness rule** — how soon after a producer write the consumer must see it.
6. **Breaking-change policy** — what the producer must do to change the shape.

## 1. Breaking-change policy (global)

Applies to every contract in this document. Derived from `phase6-2-migration-strategy.md` §3.

- **Additive changes** (new optional field, new event type) — producer may ship at any time; no consumer action required.
- **Required-field addition** — requires a time-boxed deprecation window (minimum 14 days) during which producer emits both old + new; consumers announce completion of their switch; producer drops old field at window end.
- **Field rename or type change** — equivalent to a required-field addition for the new field plus a deprecation of the old one. Must co-ship a rendered-view bridge (§3.1 of migration strategy) for any legacy consumer.
- **Removal** — same 14-day window, plus an explicit trapdoor PR (per §4.6 of migration strategy).
- **Format/compression/encoding change** — never silent; always a new artifact path. Old path keeps serving old format until deprecation closes.

Contracts carry a `schema_version` field. Consumers must check it. Mismatch → consumer reads through rendered-view bridge if available; otherwise escalates via ADV-021 automation-first mechanism.

## 2. Integration with sharded knowledge store

`phase2-knowledge-architecture.md` §2-§4 defines the event-sourced, per-shard store that ADV-008 builds. Every contract below either:

- **(a)** names an event type in the event stream (producer appends, consumers subscribe or query a rendered view), or
- **(b)** names an MCP tool on the ADV-010 surface (producer and consumer both call the tool, not the underlying store), or
- **(c)** names a file rendered from (a) for human/UI consumption (contract applies to the rendered form too, via the view builder).

Consumers should prefer (a)/(b) over (c). Rendered file paths are a legacy-compat escape hatch. Every (c) contract MUST declare a "source of truth" (a) or (b) pointer.

Freshness rule conventions used below:

- `sync` — consumer reads after write within the same MCP call. Used only when the consumer controls the write too.
- `≤1s` — subscription-driven; view builder publishes within ~1 second.
- `≤next-invocation` — view regenerated on the next consumer run; fine for batch/planner-side consumers.
- `eventual` — consumers must tolerate arbitrarily stale views; used only for cross-project discovery queries.

## 3. Contract Catalog

Contracts are grouped by producer. Each entry ends with `{ producer → consumers: ADV-..., ADV-... }`.

### 3.1 ADV-008 — Event Store

#### C-01: EventRecord
- **Path (a)**: `events/{shard}/{yyyy-mm}/{uuid}.jsonl`
- **Tool (b)**: `knowledge.append`, `knowledge.read`
- **Schema sketch**:
  ```
  {
    "schema_version": "1.0",
    "event_id": "uuid",
    "event_type": "task.created | task.stage.changed | metric.row | ...",
    "timestamp": "ISO-8601 UTC",
    "shard": "adventure/ADV-008 | project/ark | ...",
    "producer": "agent|tool-name",
    "payload": { ... per event_type ... }
  }
  ```
- **Invariants**: monotonic timestamp per shard; `event_id` globally unique; `payload` conforms to registry entry for `event_type`.
- **Freshness**: `sync` for producer, `≤1s` for subscribers.
- **Breaking-change policy**: new `event_type` always additive. Payload changes follow global policy; bump minor version for additive, major for breaking.
- **Producer → consumers**: ADV-008 → ADV-009, ADV-010, ADV-011, ADV-014, ADV-015, ADV-016, ADV-020, ADV-022, ADV-026.

#### C-02: ShardView
- **Path (c)**: rendered view file per shard, e.g. `.agent/adventures/{ADV}/rendered/manifest.md` (view of the sharded manifest; see ADV-009).
- **Tool (b)**: `knowledge.shard-view`
- **Schema sketch**: producer-specific; each view builder declares its own sub-schema and registers it.
- **Invariants**: view is a pure function of the event stream up to a `watermark` timestamp. Rebuild from scratch must produce identical output.
- **Freshness**: `≤1s` for subscribed views; `≤next-invocation` for pull-only views.
- **Breaking-change policy**: renaming a view path = breaking (requires deprecation window + legacy-path shim).
- **Producer → consumers**: ADV-008 → ADV-009 (legacy bridge), ADV-014/015 (UI renders views), all humans.

### 3.2 ADV-009 — Sharded Entities

#### C-03: Task shards
- **Path (a)**: event types `task.shard.description`, `task.shard.ac`, `task.shard.log`, `task.shard.eval`.
- **Path (c)**: rendered `.agent/adventures/{ADV}/tasks/{task_id}.md` (composed from shards).
- **Schema sketch** (payload per shard):
  ```
  task.shard.description: { task_id, markdown }
  task.shard.ac:          { task_id, items: [{id, text, checked}] }
  task.shard.log:         { task_id, append-only: [{timestamp, message}] }
  task.shard.eval:        { task_id, fields: {...from phase2-entity-redesign §1...} }
  ```
- **Invariants**: `task_id` stable across shards; exactly one `description` and `eval` per task; `log` append-only.
- **Freshness**: rendered file `≤1s`; individual shards `sync`.
- **Breaking-change policy**: per global.
- **Producer → consumers**: ADV-009 → every pipeline role, ADV-014/015, ADV-022 (ARL renders to these).

#### C-04: Adventure Manifest shards
- **Path (a)**: events `manifest.shard.concept`, `manifest.shard.target-conditions`, `manifest.shard.evaluations`, `manifest.shard.environment`.
- **Path (c)**: rendered `.agent/adventures/{ADV}/manifest.md`.
- **Schema sketch**: mirrors `phase2-entity-redesign.md §2` before/after.
- **Invariants**: at most one of each shard type per adventure; `target-conditions` rows have stable IDs (TC-###).
- **Freshness**: rendered `≤1s`; individual shards `sync`.
- **Producer → consumers**: ADV-009 → ADV-014, ADV-022, all pipeline roles.

#### C-05: Metrics row
- **Path (a)**: event `metric.row`.
- **Path (c)**: rendered `.agent/adventures/{ADV}/metrics.md` table.
- **Schema sketch**:
  ```
  {
    "task_id": "...", "role": "researcher|architect|...",
    "model": "opus|sonnet|...", "tokens_in": int, "tokens_out": int,
    "duration_sec": int, "turns": int, "status": "complete|failed|..."
  }
  ```
- **Invariants**: one row per (task_id, role); monotonic writes; columns match schema.
- **Freshness**: rendered `≤1s`.
- **Producer → consumers**: ADV-009 (writer) → ADV-011 (skills read), ADV-021 (auto-1st thresholds), ADV-024 (benchmarks), ADV-026 (loops).

### 3.3 ADV-010 — MCP Tool Surface

#### C-06: Tool catalog
- **Path (a)**: event `mcp.tool.registered` + registry snapshot.
- **Tool (b)**: `mcp.list-tools`.
- **Schema sketch**:
  ```
  {
    "tool_name": "knowledge.append",
    "schema_version": "1.0",
    "input_schema": { /* JSON Schema */ },
    "output_schema": { /* JSON Schema */ },
    "capabilities_required": ["knowledge.write"],
    "idempotency": "sync-exact | replay-safe | none"
  }
  ```
- **Invariants**: `tool_name` globally unique; `input_schema`/`output_schema` validate on every call; removing a tool requires a deprecation window.
- **Freshness**: `sync` — any consumer's next `mcp.list-tools` call sees the new tool.
- **Breaking-change policy**: adding a tool is additive. Changing an input schema is breaking unless it only adds optional fields. Removing a tool follows global removal policy + a visible shim that returns a structured deprecation error.
- **Producer → consumers**: ADV-010 → ADV-012, ADV-013, ADV-015, ADV-016, ADV-017, ADV-023.

#### C-07: Capability grants
- **Path (a)**: event `mcp.capability.granted`.
- **Tool (b)**: `mcp.grant / mcp.revoke`.
- **Schema sketch**: `{ grantee: "role:researcher", capability: "knowledge.read", scope: "adventure/ADV-008" }`.
- **Invariants**: grants are the only permission source; no implicit grants; `scope` narrowing is always legal, broadening requires `automation-first` escalation (ADV-021).
- **Freshness**: `sync`; revocations propagate immediately.
- **Producer → consumers**: ADV-010 → ADV-012, ADV-021.

### 3.4 ADV-011 — Skills Library

#### C-08: Skill metrics stream
- **Path (a)**: events `skill.metric.row`, `skill.decision.logged`.
- **Schema sketch**:
  ```
  skill.metric.row:       { skill_id, input_tokens, output_tokens, wallclock_ms, outcome }
  skill.decision.logged:  { skill_id, context_hash, decision, confidence }
  ```
- **Invariants**: every skill invocation MUST emit one `skill.metric.row`; every automation-first-relevant decision MUST emit a `skill.decision.logged`.
- **Freshness**: `≤1s`.
- **Breaking-change policy**: additive fields fine; renaming `skill_id` is breaking.
- **Producer → consumers**: ADV-011 → ADV-021, ADV-024, ADV-026, ADV-027.

#### C-09: Skill manifest
- **Path (c)**: `.claude/skills/{skill_id}/SKILL.md` + `.claude/skills/{skill_id}/manifest.json`.
- **Schema sketch** (manifest.json): `{ skill_id, version, inputs, outputs, capabilities_required, owners }`.
- **Invariants**: `skill_id` unique; `version` is semver.
- **Freshness**: `≤next-invocation`.
- **Producer → consumers**: ADV-011 → ADV-012 (roles reference skills), ADV-021, ADV-026, ADV-027.

### 3.5 ADV-012 — Role System

#### C-10: Role prompt bundle
- **Path (c)**: `.claude/agents/team-pipeline/{role}.md` + `{role}.json` (capability manifest).
- **Schema sketch** (capability manifest):
  ```
  { role, version, capabilities: [...], skills_used: [...],
    escalation_policy: "auto | ask | never" }
  ```
- **Invariants**: `role` enum-stable; `capabilities` subset of MCP surface (C-06); `skills_used` subset of skill registry (C-09).
- **Freshness**: `≤next-invocation`.
- **Breaking-change policy**: changing `capabilities` is a required-field-change-equivalent; must go through ADV-010 grant mechanism first.
- **Producer → consumers**: ADV-012 → ADV-013 (external MCPs gated by capabilities), ADV-017 (human-as-role reuses the bundle), ADV-021.

### 3.6 ADV-016 — Scheduler

#### C-11: Trigger / ScheduleEntry
- **Path (a)**: event `scheduler.trigger.registered` / `scheduler.trigger.fired`.
- **Tool (b)**: `scheduling.schedule / scheduling.cancel / scheduling.fire`.
- **Schema sketch**:
  ```
  { trigger_id, kind: "cron|event", expr, target_tool,
    target_input, owner, next_fire_at }
  ```
- **Invariants**: `scheduler` is the single writer of `trigger` shape (P5 conflict §4.1 resolution); consumers only read.
- **Freshness**: `≤1s`.
- **Producer → consumers**: ADV-016 → ADV-023 (M5 unification), ADV-026 (loop.tick fires through scheduler), ADV-028 (futuring cadence).

### 3.7 ADV-017 — Messenger + Input

#### C-12: MessageRecord + InputBlob
- **Path (a)**: events `messenger.message.posted`, `input.blob.stored`.
- **Tool (b)**: `input.store / input.fetch / messenger.post / messenger.subscribe`.
- **Schema sketch**:
  ```
  messenger.message.posted: { channel, from, to, kind, body_ref }
  input.blob.stored:        { blob_id, mime, size, sha256, origin }
  ```
- **Invariants**: `body_ref` is either inline (≤4KB) or a blob_id referring to `input.blob.stored`; ordering-per-channel guaranteed.
- **Freshness**: `≤1s` for subscribers; `sync` for direct `fetch`.
- **Producer → consumers**: ADV-017 → ADV-021 (escalations routed through messenger), ADV-028 (futuring surfaces to humans).

### 3.8 ADV-018 — Project / Repo / KB Separation

#### C-13: Project / Repo / KnowledgeBase entities
- **Path (a)**: events `project.created|updated`, `repo.created|updated`, `kb.created|updated`.
- **Schema sketch**:
  ```
  project: { project_id, name, owners, knowledge_bases: [...], repos: [...] }
  repo:    { repo_id, project_id, vcs_url, default_branch }
  kb:      { kb_id, project_id, scope: "project|repo|adventure", root_path }
  ```
- **Invariants**: every adventure/task carries `project_id` + optional `repo_id`; KB scopes are disjoint at the same level.
- **Freshness**: `≤1s`.
- **Breaking-change policy**: splitting a previously conflated entity is a migration (goes through ADV-025).
- **Producer → consumers**: ADV-018 → ADV-019, ADV-025, all adventures (project_id becomes mandatory).

### 3.9 ADV-019 — Custom Entities + Recommendations

#### C-14: CustomEntityType
- **Path (c)**: DSL file `*.ark` with `entity { ... }` block, compiled to store schema + MCP tools.
- **Schema sketch** (compiled): entity spec same shape as built-in entities in `phase2-entity-redesign.md`.
- **Invariants**: custom `entity_type` must not clash with built-ins; compilation produces deterministic tool names.
- **Freshness**: `≤next-invocation` of the compiler.
- **Producer → consumers**: ADV-019 → every downstream consumer of entity data, especially ADV-026/028.

#### C-15: Recommendation record
- **Path (a)**: event `reco.recommendation.issued`, `reco.recommendation.acted-on`.
- **Tool (b)**: `reco.query / reco.issue / reco.act`.
- **Schema sketch**:
  ```
  { reco_id, kind, target, confidence, rationale, issued_by: "loop|futuring|human",
    priority, expires_at }
  ```
- **Invariants**: a reco is immutable once issued; `acted-on` references `reco_id`.
- **Freshness**: `≤1s`.
- **Producer → consumers**: ADV-019 → ADV-026 (loops issue recos), ADV-028 (futuring issues recos), ADV-015 (UI shows reco inbox).

### 3.10 ADV-020 — Autotest + CI

#### C-16: Test / Golden registry
- **Path (c)**: `tests/registry.json` (generated from source).
- **Tool (b)**: `test.list / test.run / golden.diff`.
- **Schema sketch**: `{ test_id, proof_method: "unit|integration|golden|property", owners, last_run }`.
- **Invariants**: every `target_condition` in an adventure manifest must reference at least one `test_id` here (closes P1 pattern gap).
- **Freshness**: `≤next-CI-run`.
- **Producer → consumers**: ADV-020 → ADV-022 (refactor gates), ADV-024 (benchmark harness reuses CI).

### 3.11 ADV-021 — Automation-First Policies

#### C-17: AutomationPolicy
- **Path (a)**: event `automation.policy.set`; `automation.decision.escalated`.
- **Schema sketch**:
  ```
  automation.policy.set: { target: "tool|role|skill", posture: "full-auto|ask|never",
                            thresholds: {...}, owner }
  automation.decision.escalated: { policy_id, context, reason, escalated_to }
  ```
- **Invariants**: no prod-affecting tool runs without an active policy; default posture is `ask` (see `phase6-automation-first.md` §2).
- **Freshness**: `sync` — policy changes take effect on next tool invocation.
- **Producer → consumers**: ADV-021 → ADV-027 (safety envelope), ADV-028 (escalation budget accounting).

### 3.12 ADV-022 / ADV-023 — ARL + Refactor

#### C-18: ARL program
- **Path (c)**: ARL source files under `ark/arl/*.arl`; compiled IR at `ark/arl/build/*.irl`.
- **Schema sketch**: see `phase6-1-abstract-representation.md` §2 (core algebra).
- **Invariants**: ARL compiles deterministically to entity shapes; diff of two compilations over identical input is empty.
- **Freshness**: `≤next-compile`.
- **Breaking-change policy**: core-algebra changes are major-version ARL releases; require explicit migration entry in ADV-025.
- **Producer → consumers**: ADV-022/023 → ADV-009 (entities rendered from ARL), ADV-025 (migrations use ARL translation).

#### C-19: Milestone gate report
- **Path (a)**: event `refactor.milestone.passed`.
- **Schema sketch**: `{ milestone: "M0..M8", gate_results: {...}, complexity_deltas: {...} }`.
- **Invariants**: no M_n+1 work starts without a `refactor.milestone.passed` for M_n.
- **Freshness**: `sync`.
- **Producer → consumers**: ADV-022/023 → ADV-025, ADV-024, all future readers.

### 3.13 ADV-024 — Benchmarks

#### C-20: BenchmarkRun
- **Path (a)**: event `bench.run.completed`.
- **Path (c)**: `bench/reports/{run_id}.md`.
- **Schema sketch**: metric axes from `phase6-2-benchmark-design.md` §2 — `{ run_id, suite, axes: {tokens, dollars, wallclock, success_rate}, targets_met: bool, baseline_ref }`.
- **Invariants**: reproducible — rerun with same `run_id` parameters yields within tolerance; tolerance declared in the registry.
- **Freshness**: `≤next-run` (benchmarks are batch).
- **Producer → consumers**: ADV-024 → ADV-025 (migrations gated on "benchmarks don't regress"), ADV-026 (loop input).

### 3.14 ADV-025 — Migration

#### C-21: DeprecationAnnouncement
- **Path (a)**: event `migration.deprecation.announced / closed`.
- **Schema sketch**: `{ target_path, replacement_path, deadline, affected_consumers: [...] }`.
- **Invariants**: deadline ≥ 14 days from announcement; `affected_consumers` explicitly listed; closing requires each consumer to have confirmed migration (event `migration.consumer.switched`).
- **Freshness**: `sync`.
- **Producer → consumers**: ADV-025 → every active adventure (consumers must subscribe during deprecation windows).

### 3.15 ADV-026/027/028 — On-Sail Runtime

#### C-22: Loop run record
- **Path (a)**: event `loop.tick.observed`.
- **Schema sketch**: `{ loop_id, tick_id, inputs_hash, outputs: {...}, duration_ms, next_reco_id }`.
- **Freshness**: `≤1s`.
- **Producer → consumers**: ADV-026 → ADV-019 (recos), ADV-028 (futuring observes loop behaviour).

#### C-23: HealEvent
- **Path (a)**: event `heal.detected`, `heal.classified`, `heal.fix.attempted`, `heal.verified`, `heal.escalated`.
- **Schema sketch**: per-stage from `phase7-self-healing.md` §2.
- **Invariants**: each heal incident follows the five-stage order; stages are immutable once emitted.
- **Freshness**: `≤1s`.
- **Producer → consumers**: ADV-027 → ADV-021 (policy engine consumes outcomes), ADV-028.

#### C-24: Futuring proposal
- **Path (a)**: event `futuring.signal.collected`, `futuring.hypothesis.formed`, `futuring.proposal.issued`.
- **Path (c)**: `futuring/proposals/{id}.md`.
- **Schema sketch**: from `phase7-operational-model.md` §6 (proactive backlog schema).
- **Invariants**: every proposal cites ≥2 signals; issued proposals become candidate ADV-### entries for the next roadmap cycle.
- **Freshness**: `eventual`.
- **Producer → consumers**: ADV-028 → roadmap-cycle planner, ADV-019 (recos), ADV-017 (humans receive proposals).

## 4. Contract Summary Matrix (upstream × downstream)

| Contract | Producer | Primary Consumers | Freshness | Breaking-change path |
|----------|----------|-------------------|-----------|----------------------|
| C-01 EventRecord | ADV-008 | 008/009/010/011/014/016/020/022/026 | ≤1s | schema_version bump |
| C-02 ShardView | ADV-008 | 009/014/015, humans | ≤1s | deprecation + bridge |
| C-03 Task shards | ADV-009 | roles, 014/015/022 | ≤1s | migration runbook |
| C-04 Manifest shards | ADV-009 | roles, 014/022 | ≤1s | migration runbook |
| C-05 Metrics row | ADV-009 | 011/021/024/026 | ≤1s | additive preferred |
| C-06 Tool catalog | ADV-010 | 012/013/015/016/017/023 | sync | tool-level deprecation |
| C-07 Capability grants | ADV-010 | 012/021 | sync | scope narrowing any time |
| C-08 Skill metrics | ADV-011 | 021/024/026/027 | ≤1s | additive preferred |
| C-09 Skill manifest | ADV-011 | 012/021/026/027 | ≤next-inv | semver |
| C-10 Role bundle | ADV-012 | 013/017/021 | ≤next-inv | grant-before-use |
| C-11 Trigger | ADV-016 | 023/026/028 | ≤1s | single-writer invariant |
| C-12 Message + Input | ADV-017 | 021/028 | ≤1s | additive preferred |
| C-13 Project/Repo/KB | ADV-018 | 019/025, all | ≤1s | routed through ADV-025 |
| C-14 Custom entity type | ADV-019 | downstream store | ≤next-inv | DSL version |
| C-15 Recommendation | ADV-019 | 015/026/028 | ≤1s | additive |
| C-16 Test/Golden registry | ADV-020 | 022/024 | ≤next-CI | registry version |
| C-17 AutomationPolicy | ADV-021 | 027/028 | sync | additive default=ask |
| C-18 ARL program | ADV-022/023 | 009/025 | ≤next-compile | ARL semver |
| C-19 Milestone gate | ADV-022/023 | 024/025 | sync | gate pinning |
| C-20 BenchmarkRun | ADV-024 | 025/026 | ≤next-run | tolerance-declared |
| C-21 Deprecation | ADV-025 | all | sync | the mechanism itself |
| C-22 Loop tick | ADV-026 | 019/028 | ≤1s | additive |
| C-23 HealEvent | ADV-027 | 021/028 | ≤1s | stage-immutable |
| C-24 Futuring proposal | ADV-028 | planner, 019/017 | eventual | additive |

## 5. How contracts land in the sharded store

From `phase2-knowledge-architecture.md` §2.4 (concurrency units), each contract above maps to one or more *concurrency units* in the store:

- (a) events → single-writer-per-shard, multi-reader.
- (b) tools → no storage of their own; they read/write the store.
- (c) rendered files → single builder per view; readers are unbounded.

Producer adventures publish a *schema registry entry* during their first milestone. The registry itself is a view built from `schema.registered` events; consumers read it via `knowledge.shard-view("schema-registry")`. This closes P1.P5 ("generate every catalog from source") — the contract catalog itself is machine-readable.

An automated linter (owned by ADV-020) asserts that every adventure manifest's `depends_on` links align with the contract edges in §4: if ADV-X consumes a contract owned by ADV-Y, then ADV-X must list `ADV-Y` in its depends_on, or the CI job refuses the manifest.

## 6. Acceptance

This document satisfies **TC-033**: contracts defined for every producer→consumer edge implied by the DAG (24 contracts covering 21 adventures), each with producer/consumer/artifact-path/schema-sketch/freshness/breaking-change-policy fields, plus the global policy in §1, plus integration with the sharded store per §5. Companions: `master-roadmap.md` for per-adventure scope, `adventure-dependency-graph.md` for which edge each contract corresponds to.
