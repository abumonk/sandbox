---
task: ADV007-T021
adventure: ADV-007
phase: 6.2
target_conditions: [TC-026]
upstream:
  - .agent/adventures/ADV-007/research/phase6-1-refactoring-strategy.md
  - .agent/adventures/ADV-007/research/phase6-1-abstract-representation.md
  - .agent/adventures/ADV-007/research/phase6-1-complexity-analysis.md
  - .agent/adventures/ADV-007/research/phase2-entity-redesign.md
  - .agent/adventures/ADV-007/research/phase6-mcp-operations.md
  - .agent/adventures/ADV-007/research/phase6-2-benchmark-design.md
  - .agent/adventures/ADV-007/research/phase6-2-test-profiles.md
researched: 2026-04-14
---

# Phase 6.2 — Migration Strategy

This document specifies the **migration strategy** from the current
separate projects (team-pipeline, team-mcp, binartlab, marketplace,
PDSL, Ark) to the unified post-reconstruction ecosystem. It covers
data migrations of the `.agent/` tree and equivalent stores into the
ARL-backed entities from T008, API and tool-surface migrations across
the MCP surface, co-existence windows and deprecation schedules, and
rollback playbooks.

The strategy is expressly **non-flag-day**: the refactoring strategy
(TC-022) already imposed additive-before-subtractive, feature-flagged,
rollback-by-grep constraints on every milestone. This document applies
those same constraints at the *data layer* — no migration ships that
cannot be reversed by replaying an event log through the prior
renderer.

---

## 1. Principles

### 1.1 No destructive migrations

A migration never deletes source data. Every migration reads from the
legacy shape, writes to the canonical ARL shape, and leaves the
legacy shape intact (as a rendered view, a symlink, or an archived
copy) for at least one milestone cycle. This rule is symmetric with
T020 §1.1 additive-before-subtractive.

### 1.2 Replay is the only write path

Data migrations proceed by replaying events through the target
renderer, not by point-edits or sed scripts. If the source shape
cannot be decomposed into an event stream, the migration first
generates a synthetic event stream from the current state (one event
per current value) and then replays. This guarantees the migration
is re-runnable without accumulating drift.

### 1.3 Every migration has a reverse

For every forward migration `M: legacy → canonical`, there exists a
reverse `M^(-1): canonical → legacy` that produces the original
bytes modulo canonicalisation. The reverse is tested alongside the
forward — a migration PR that cannot demonstrate the reverse path
is rejected.

### 1.4 Deprecations are time-boxed and announced

Every breaking API change ships with a deprecation window of at least
one full milestone cycle (typically ~2 weeks of main-branch commits).
Deprecations are announced via a `deprecation` event on the adventure
log at the start of the window and a final `removal` event at the
end. The window is the reviewer's grace period.

### 1.5 Co-existence is the default

During a migration window, both the legacy and the canonical surfaces
serve reads. Writes go to the canonical; the legacy is derived. The
rule: any consumer may read the legacy surface until its deprecation
removal; no consumer may write to a legacy surface after its
migration landing.

---

## 2. Migration Inventory

The migrations required to complete the reconstruction, grouped by
concern. Each row lists the source shape, the target (ARL) shape,
the milestone that lands the migration, and the tie to T008 / TC-022.

### 2.1 Data migrations

| # | Source | Target | Milestone | Tie |
|---|---|---|---|---|
| D1 | `.agent/adventures/<id>/tasks/<id>.md` (flat) | `.agent/adventures/<id>/tasks/<id>/{task.md,log.jsonl,iterations.jsonl}` | M2 | Task shard (T008 §2) |
| D2 | `.agent/adventures/<id>/manifest.md` (monolithic) | `manifest.md` header + `manifest.targets.jsonl` + `manifest.evaluations.jsonl` + `views/` | M2 | Manifest shard (T008 §3) |
| D3 | `.agent/adventures/<id>/adventure.log` (ad-hoc) | `.agent/adventures/<id>/events.jsonl` (typed) | M1 | EventLog unification |
| D4 | `.agent/metrics.md` (monolithic) | `.agent/metrics.jsonl` (typed, SDK-sourced) | M1 (shadow) / M7 (authoritative) | MetricsLedger |
| D5 | `.agent/knowledge/{patterns,issues,decisions}.md` | `.agent/knowledge/lessons.jsonl` + `views/<kind>.md` | M4 | KB unification (T008 §5) |
| D6 | `.agent/agent-memory/<role>/*.md` + `MEMORY.md` index | `.agent/knowledge/lessons.jsonl` with `role:` field + role-scoped views | M4 | Memory unification (X9) |
| D7 | `.agent/lead-state.md` (monolithic) | `.agent/lead-state/{active.jsonl, sessions/<id>.json}` | M3 | LeadState (T008 §4) |
| D8 | `.agent/messenger.md` (mixed) | `.agent/messenger/{channels.md, approvals.jsonl}` | M5 | Messenger persist (X10) |
| D9 | `.agent/permissions.md` (monolithic) | `.agent/permissions/<scope>/spec.md` (per-scope) | M3 | Permissions shard (T008 §12) |
| D10 | `claudovka-marketplace/*.md` hand-curated catalogs | generated `registry/{skills,agents,roles,triggers,tools}.json` | M6 | Catalog unification (X3) |
| D11 | Binartlab SQLite tables (existing) | SQLite remains as read-mirror; writes redirected to ARL events | M7 | SQL mirror (ARL §4.3) |
| D12 | PDSL parser outputs | Ark AST (via dialect profile) | M6 | DSL unification (X2) |
| D13 | BL YAML schemas | Ark-generated zod | M6 | Schema dialect merge |

### 2.2 API / tool-surface migrations

| # | Source surface | Target surface | Milestone | Tie |
|---|---|---|---|---|
| A1 | 40+ loose `pipeline.*` tools | 30 canonical + 7 operational (named schema) | M6-M7 | MCP-ops §2 |
| A2 | Prose hook prompts (4 hooks, ~6 KB) | `pipeline.on_subagent_stop/on_user_prompt/on_session_stop/on_session_start` tools | M5 | H1 |
| A3 | Ad-hoc shell calls in agent prompts | MCP-only operational tools (deploy, build, compile, test, migrate, rollback, metrics) | M7 | H8 |
| A4 | BL per-agent WebSocket frames (loose) | Typed Union events via ARL `render_event` | M7 | E8, E10 |
| A5 | Hand-written binartlab zod | Ark-generated zod (publication via M6 codegen) | M6 | BL-7 |
| A6 | PDSL `validator.js` + `grammar.md` | Ark dialect `pdsl-compat.ark` + auto-generated lark | M6 | PDSL-1, PDSL-2 |
| A7 | Bash-spawned agents in prompts | `pipeline.agent_spawn(role, task_id, ...)` MCP tool | M5 | X8 |
| A8 | Raw `Edit`/`Write` tool calls on shared state | `pipeline.state_write(entity, op, payload)` (ARL `set_header` / `append`) | M3-M7 (gradual) | H6, H7 |

### 2.3 Contract migrations

For each edge E1-E14, the Contract entity (T007 §10.4) lands in M8
as a first-class object. Three migrations cover the transition:

| # | Legacy state | Target state | Milestone |
|---|---|---|---|
| C1 | Implicit contract (code convention) | Declared `Contract` entity with schema + version | M8 |
| C2 | Version-free components | `compatible-with` fields everywhere; TM refuses start on mismatch (X4) | M8 |
| C3 | Half-implemented edges (E13, E14) | Fully implemented + contract-tested | M6 (E14), M8 (E13) |

---

## 3. Backward Compatibility Plan

### 3.1 The rendered-view bridge

Every data migration D1-D9 preserves the legacy path as a rendered
view for one full milestone cycle beyond the migration's landing.
Concretely:

- After M2 lands, `.agent/adventures/<id>/tasks/<id>.md` continues to
  exist — it is now a generated view over the sharded directory.
- After M3 lands, `.agent/lead-state.md` continues to exist — it is
  now a rendered projection of `active.jsonl`.
- After M4 lands, `.agent/knowledge/patterns.md` continues to exist —
  it is now a filtered view of `lessons.jsonl` where `kind == pattern`.

Consumers that grep these legacy paths continue to work; their reads
pass through the view layer, which the reconciler keeps in sync on
every event append. The bridge rule: **the legacy path is deleted
only after the next milestone closes cleanly and no in-repo grep
still references the legacy path**.

### 3.2 Feature-flag ladder

The refactoring strategy's flag matrix (T020 §4.1) already provides
the mechanism. Every migration is gated by one or more flags:

| Flag | Gates | Default |
|---|---|---|
| `events_shadow` | D3 shadow writes | on at M0 |
| `views_as_source` | D3 read-through | on at M1 |
| `canonical_task_dir` | D1, D2 | on at M2 |
| `lead_state_v2` | D7, D9 | on at M3 |
| `knowledge_lessons` | D5, D6 | on at M4 |
| `hooks_v2` | A2, A7 | on at M5 |
| `registry_generated` | D10, A5 | on at M6 |
| `mcp_only_ops` | A3 | on at M7 |
| `contract_enforcement` | C1, C2, C3 | on at M8 |
| `sql_mirror` | D11 | on at M7 |

Each flag is an independent axis; flipping one off reverts only its
migration, never a dependent's. The bidirectional bridge is the
rendered view plus the event-log substrate.

### 3.3 Deprecation windows

Every API migration (A1-A8) carries a deprecation window:

| Migration | Window start | Window end | Length |
|---|---|---|---:|
| A1 (tool rename) | M6 land | M8 close | ~2 milestones (~3 weeks) |
| A2 (hook rewrite) | M5 land | M6 close | 1 milestone |
| A3 (bash → MCP) | M7 land | M7 + 1 | 1 milestone |
| A4 (BL WS frames) | M7 land | M8 close | 1 milestone |
| A5 (zod publication) | M6 land | M6 + 1 | 1 milestone |
| A6 (PDSL dialect) | M6 land | M6 + 2 | 2 milestones |
| A7 (agent spawn tool) | M5 land | M6 close | 1 milestone |
| A8 (state_write unified) | M3 land (partial) | M7 close | ~4 milestones |

The longest window (A8) reflects that many call sites migrate
incrementally; the shortest (A3, A5, A7) reflect that the old
surface has a single call site and is trivially swappable.

### 3.4 Deprecation announcement protocol

At deprecation-window start:

1. A `deprecation.announced` event is appended to the adventure
   events.jsonl with the migration id, the target-removal milestone,
   and the replacement tool name.
2. The deprecated tool's MCP schema gains a `deprecated: true` flag
   and a `replacement: "<new tool>"` hint.
3. Every invocation of the deprecated tool emits a warning on the
   response envelope (non-blocking) and a `deprecation.used` event.

At deprecation-window end:

1. The tool is removed from the MCP surface.
2. A `deprecation.removed` event is appended.
3. Any remaining `deprecation.used` events within the last 7 days
   are escalated to the lead with the call-site attribution.

This protocol is observable and time-boxed; no surface dies silently.

---

## 4. Migration Procedure

Every data migration Dx follows the same six-step procedure.

### 4.1 Step 1 — Introduce the canonical store (additive)

Add the new path shape alongside the legacy. No reader uses the new
path; every writer writes to **both** the legacy (existing) and the
canonical (new). The new store is a *shadow*.

Gate: the shadow and legacy are byte-equal after every write, for 100
consecutive operations. Exit on gate pass.

### 4.2 Step 2 — Backfill the canonical store

Generate canonical events for every current-state row in the legacy
store, using a one-shot `pipeline.migrate(scope="Dx", from="legacy",
to="canonical")` tool. The backfill is deterministic: re-running it
is a no-op.

Gate: `canonical.replay() == legacy.parse()` for every entity. Exit on
gate pass.

### 4.3 Step 3 — Flip reads to canonical

Consumers start reading from the canonical store (through the view
layer for legacy paths). The legacy is still written but no longer
authoritative. The rendered view generator reconciles any remaining
writes to the legacy.

Gate: for one full milestone cycle, every legacy-path read passes
through the view layer with zero divergence between canonical and
legacy. Exit on gate pass + cycle complete.

### 4.4 Step 4 — Stop writing to legacy

Every writer ceases direct legacy writes. The legacy path continues
to exist as a rendered view (regenerated from canonical). The
feature flag is default-on; rollback is available.

Gate: `grep -r "legacy_writer_pattern"` across the source tree
returns zero hits in mutating contexts. Exit on gate pass.

### 4.5 Step 5 — Announce deprecation

`deprecation.announced` event published; removal milestone scheduled.
The legacy path is marked `read-only`; consumers are warned.

### 4.6 Step 6 — Remove legacy (trapdoor)

At the scheduled milestone, the legacy path is deleted. A
`deprecation.removed` event is emitted; the feature flag is retired.
Rollback after this point requires git-history resurrection (forward-
only trapdoor per T020 §4.4).

### 4.7 Sequence per migration

| Migration | M of step 1 | M of step 4 | M of step 6 |
|---|---|---|---|
| D1 Task shard | M1 | M2 | M4 |
| D2 Manifest shard | M1 | M2 | M4 |
| D3 Event log | M0 | M1 | M3 |
| D4 Metrics ledger | M0 | M7 | M8 |
| D5 Knowledge lessons | M3 | M4 | M6 |
| D6 Agent memory merge | M3 | M4 | M6 |
| D7 Lead-state shard | M2 | M3 | M5 |
| D8 Messenger persist | M4 | M5 | M7 |
| D9 Permissions shard | M2 | M3 | M5 |
| D10 Registry generated | M5 | M6 | M8 |
| D11 SQL mirror | M6 | M7 | never (read mirror, not removed) |
| D12 PDSL dialect | M5 | M6 | M7 (parser removed) |
| D13 BL YAML → zod | M5 | M6 | M7 |

Step 6 is the earliest **removal** milestone; actual removal may be
further deferred if the cycle-free-of-legacy-reads constraint has not
been met. No removal proceeds automatically.

---

## 5. Data Migration Specifications

A sample of the more load-bearing migrations; full specs live in
`.agent/adventures/<id>/migrations/Dx.md`.

### 5.1 D1 — Task shard

- **Source**: `.agent/adventures/<id>/tasks/<id>.md` — YAML
  frontmatter + prose body + `## Log` section.
- **Target**:
  - `tasks/<id>/task.md` — header (frontmatter) + description + AC.
  - `tasks/<id>/log.jsonl` — one event per log line, typed.
  - `tasks/<id>/iterations.jsonl` — one event per iteration.
- **Generator**: parse the `## Log` section line-by-line; each line
  becomes a `LogEvent` with timestamp, role, message. Each numbered
  iteration becomes an `IterationEvent`.
- **Reverse**: render task.md as frontmatter + body; regenerate the
  `## Log` section by folding log.jsonl.
- **Loss budget**: none. Free prose in the description body is
  preserved verbatim in `task.md`.
- **Gate test**: `test_task_migration_roundtrip.py` — 50 historical
  task files round-trip with byte equality after canonicalisation.

### 5.2 D5/D6 — Knowledge + agent-memory merge

- **Source**: three files (`patterns.md`, `issues.md`, `decisions.md`)
  + per-role directories under `agent-memory/`.
- **Target**: `.agent/knowledge/lessons.jsonl` — one event per
  lesson, with fields `{id, kind, role?, title, body, source_task,
  timestamp}`.
- **Generator**: parse the markdown `- **Title**: body (from task-id)`
  bullets; map to `LessonEvent` with `kind ∈ {pattern, issue,
  decision}`. For `agent-memory/<role>/*.md`, each file becomes a
  lesson with `role: <role>` and `kind: memory`.
- **Views**: `knowledge/patterns.md`, `knowledge/issues.md`,
  `knowledge/decisions.md` regenerated from `lessons.jsonl` filtered
  by `kind`. Per-role views regenerate from `lessons.jsonl` filtered
  by `role`.
- **Loss budget**: none for the bullet-structured content; free prose
  outside bullet sections is preserved under an `extra_body:` field.
- **Gate test**: `test_lesson_roundtrip.py` — round-trip identity
  between any legacy md file and the rendered view for that kind.
- **Deprecation**: legacy paths are retained as symlinks to the
  rendered view for one full cycle; hard removal deferred to M6.

### 5.3 D10 — Registry generation

- **Source**: hand-curated tables in `README.md`, `CLAUDE.md`, and
  marketplace listings.
- **Target**: `registry/{skills,agents,roles,triggers,tools}.json`
  generated at TM start by scanning the source directory trees
  (`.agent/skills/`, `.agent/agents/`, etc.).
- **Generator**: a directory walker emits one registry entry per
  source file, with schema validation against the Ark spec.
- **Reverse**: none — the registry is a view, not a source. Rollback
  is flag-flip (`registry_generated: false`) plus restoring the
  hand-curated tables from git history.
- **Loss budget**: any hand-curated description string not present
  in the source file's frontmatter is flagged as a migration-gap
  event (`registry.missing_description`) for backfill.
- **Gate test**: `test_catalog_parity.py` — every listed skill /
  agent / role / command matches exactly the generated registry;
  PDSL examples round-trip through Ark AST.

### 5.4 D11 — SQL mirror (binartlab)

- **Source**: existing SQLite tables written by binartlab backends.
- **Target**: SQLite remains, but as a derived read-mirror of the
  ARL substrate. The write path becomes an ARL `append` to
  `.agent/events.jsonl` (or BL-shared event stream); a materialiser
  service reads events and updates SQL rows.
- **Generator**: materialiser subscribes to the event stream and
  applies idempotent upserts; re-running from offset 0 rebuilds the
  SQL state.
- **Reverse**: flip `sql_mirror: false`; BL backends resume direct
  SQL writes; the event stream remains but is no longer
  authoritative for BL concerns.
- **Loss budget**: per ARL §5.2, SQL may drop fields not declared in
  the table schema; every dropped field must be recoverable from the
  event stream.
- **Gate test**: `test_sql_mirror_consistency.py` — for 1 000 events,
  the SQL state and the event-replayed state are query-equivalent
  on all declared projections.

---

## 6. API Migration Specifications

### 6.1 A1 — Tool rename (40+ → 30 canonical + 7 operational)

Each renamed tool gets a shim: the old name continues to route to
the implementation for the full deprecation window, emitting a
`deprecation.used` event on each call. The shim is generated (not
hand-written) from an `alias_map.json` consumed by the TM bootstrap.

At deprecation end, the alias map entries are removed; calls to the
old names return a structured `tool_not_found` error.

### 6.2 A2 — Hook rewrite (prose → deterministic tool)

The legacy hook prompts are retained as backup behind
`hooks_v2: false`. Switching the flag reverts to the LLM-driven
hooks. After the M5 determinism gate has held for three consecutive
commits, the flag defaults on; after M6 close, the legacy prompts
are deleted (forward-only trapdoor).

### 6.3 A3 — Shell → MCP operational tools

Role prompts are linted in CI: `grep -E "^\s*(bash|sh)\b"` under
agent prompt files returns zero matches after M7 lands. The lint is
a fence, not a deprecation — bash call sites must be converted
before M7 lands, not retrofit during the window.

### 6.4 A8 — Unified state_write (gradual)

The state_write tool is introduced in M3 with a small initial scope
(lead-state). Each subsequent milestone expands the scope: M4 adds
lessons, M5 adds messenger approvals, M7 adds metrics. Legacy direct
writes continue to work behind `flags.state_write_exclusive: false`;
a per-migration fence prevents regression into a legacy write path
that has already been removed.

### 6.5 Contract migrations C1-C3

Contract migrations are aggregated into M8. The per-edge procedure:

1. Author the Contract entity in `schema/contracts/<edge>.ark`.
2. Generate the contract test (Ark codegen).
3. Ensure the producer and consumer both pass the contract test.
4. Promote the Contract's `enforcement: off → on` field at M8 close.

C2 (version-negotiated pairs) is a global switch: TM refuses to
start on any component whose `compatible-with` does not include
TM's version. The switch is gated by `contract_enforcement: true`.

---

## 7. Rollback Plan

### 7.1 Rollback taxonomy

Four rollback tiers, in increasing severity:

- **Tier 1 — flag flip**: one migration's flag is flipped off; the
  rendered-view bridge keeps consumers live. No event replay needed.
- **Tier 2 — state rebuild**: the canonical store is corrupt or
  inconsistent; `pipeline.state_rebuild(scope=<entity>)` replays the
  event tail through the previous-milestone renderer.
- **Tier 3 — trapdoor re-entry**: a post-removal rollback requires
  restoring the legacy code path from git history plus re-running
  the reverse migration on historical events. This is a one-adventure
  operation and is the most expensive rollback.
- **Tier 4 — full rollback**: every flag flipped off; used only in
  an ecosystem-wide incident. Documented but not expected.

### 7.2 Per-migration rollback mapping

| Migration | Rollback tier | Procedure |
|---|---|---|
| D1-D4, D7-D9 | Tier 1 | flip the governing flag; rendered view regenerates legacy |
| D5, D6 | Tier 1 → Tier 2 | symlinks restore legacy path; if corrupt, state_rebuild from lessons.jsonl |
| D10 | Tier 1 | flip `registry_generated: false`; hand-curated tables resume authoritative |
| D11 | Tier 2 | BL resumes direct SQL writes; stop materialiser |
| D12 | Tier 3 (after M7) | restore PDSL parser from git history |
| D13 | Tier 2 | restore hand-written zod from prior commit; Ark codegen output remains but is ignored |

### 7.3 Rollback playbook (standard procedure)

1. **Identify**: the symptom maps to one migration; the flag matrix
   (T020 §4.1) names the gating flag.
2. **Announce**: a `rollback.started` event is emitted on the
   adventure events.jsonl with the migration id and the tier.
3. **Flip**: `pipeline.config_set(flag, false)`; TM hot-reloads.
4. **Rebuild** (if tier ≥ 2): `pipeline.state_rebuild(scope)`.
5. **Verify**: the corresponding milestone's gate autotest passes.
6. **Triage**: an adventure is opened to address the root cause; the
   flag remains off until the fix lands and re-gates green.
7. **Resume**: the flag is flipped on; a `rollback.completed` event
   is emitted.

Each step is an MCP tool call; the sequence is scriptable and
auditable.

### 7.4 Rollback SLAs

- Tier 1: < 5 minutes from decision to flag flip.
- Tier 2: < 30 minutes to rebuild + verify on medium profile.
- Tier 3: < 1 day (one adventure).
- Tier 4: declared incident; no SLA, but post-mortem mandatory.

### 7.5 Rollback test drills

Every milestone closure includes a **rollback drill**: the closing
adventure's test plan forces one tier-1 flag-flip + state-rebuild and
asserts the gate autotest still passes in the rolled-back state.
This keeps the rollback path exercised, not theoretical.

---

## 8. Co-existence Periods

### 8.1 Schedule

The co-existence period for each migration is the interval from
"step 4 complete" (writes stop to legacy) to "step 6 complete" (legacy
removed). Durations from §4.7:

- D1, D2: ~2 milestones (M2 → M4).
- D3: ~2 milestones (M1 → M3).
- D4: ~1 milestone (M7 → M8) — final authoritative source pass.
- D5, D6: ~2 milestones (M4 → M6).
- D7, D9: ~2 milestones (M3 → M5).
- D8: ~2 milestones (M5 → M7).
- D10: ~2 milestones (M6 → M8).
- D11: never removed (read-mirror is permanent).
- D12, D13: ~1 milestone (M6 → M7).

Median co-existence: 2 milestones ≈ 3 weeks of main-branch commits.

### 8.2 Co-existence invariants

During co-existence:

- Writes: canonical only.
- Reads: either (via the rendered view); divergence is a CI failure.
- Consumers may use either path; new consumers **should** use
  canonical (reviewer enforces).
- The reconciler regenerates the legacy view on every canonical
  append; regeneration SLO < 100 ms per event.

### 8.3 Post-removal invariants

After removal:

- The legacy path does not exist on disk.
- A `deprecation.removed` event is present in the adventure events.jsonl.
- No grep hits for the legacy path exist in the source tree.
- Tier-3 rollback is required to restore the legacy path, by design.

---

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Shadow-write performance regression (D3-D9) | medium | medium | Bench gate on write latency at step 1; throttle shadow if breach |
| Rendered-view drift during co-existence | medium | high | Reconciler CI test on every append; zero-divergence SLO |
| Registry generator misses hand-curated description (D10) | high | medium | `registry.missing_description` events logged; backfill task created automatically |
| BL materialiser falls behind event stream (D11) | medium | medium | Lag SLO 10s; alert via github MCP; stop-the-world rebuild on lag > 60s |
| PDSL dialect incomplete (D12) | high | high | M6 blocks on all PDSL test cases passing; one buffer milestone |
| Deprecation window too short for consumers | medium | medium | `deprecation.used` events show real usage; extend window if non-trivial usage at T-3 days |
| Tier-3 rollback actually needed after trapdoor | low | high | Rollback drills at each milestone close keep the path current |
| Flag ladder interaction bug (independent flags coupled in practice) | medium | medium | Full matrix test at M5 and M8 (2^9 combinations sampled) |
| Event-log replay produces off-canonical state | low | high | Canonical-form property test on every replay; CI blocks |
| Data loss during backfill (D1-D9) | low | critical | Read-only source; new store written first; legacy untouched until step 4 |

---

## 10. Relation to Other Phase-6 Docs

- **phase6-autotest-strategy** (TC-019): every migration step gate
  is an autotest. `pipeline.migrate` registers test hooks for
  pre/post-migration verification.
- **phase6-1-complexity-analysis** (TC-021): the migration targets
  (D1-D13, A1-A8, C1-C3) collectively deliver the `lightweight_index
  ≤ 0.42` reduction goal.
- **phase6-1-refactoring-strategy** (TC-022): the milestone plan
  M0-M8 is the migration timeline; every milestone's gate is a
  migration completion gate.
- **phase6-1-abstract-representation** (TC-023): the ARL is the
  migration target shape. Every target column in §2.1 is an ARL
  construct. Migration procedures follow the ARL's append/set_header
  semantics.
- **phase6-2-benchmark-design** (TC-024): the migration process is
  benchmarked — `op.migrate`, `op.state_rebuild`, and the reconciler
  latency budgets from §4.3 of the bench design come from here.
- **phase6-2-test-profiles** (TC-025): migrations are exercised by
  the `adventure.recovery` and `adventure.contract_drift` scenarios;
  chaos wrappers inject migration faults.

---

## 11. Success Criteria for TC-026

- Every migration in §2 has: source shape, target shape, generator,
  reverse, loss budget, gate test, deprecation schedule.
- Rollback procedure defined per migration, keyed to a tier (§7.2).
- Feature-flag matrix exhaustively covers migrations (§3.2).
- Co-existence windows bounded and enumerated (§8.1).
- Rollback drills scheduled at every milestone close (§7.5).
- Deprecation protocol produces observable events (§3.4).
- No migration permits data loss; every migration re-runnable (§1.1,
  §1.2).

These criteria feed TC-026 proof. Phase 7's futuring loop inherits
this migration pattern for ongoing evolution.

---

## 12. Acceptance Checklist (this document)

- [x] Principles articulated (§1).
- [x] Migration inventory: data, API, contract (§2).
- [x] Backward compatibility plan with rendered-view bridge and
  flag ladder (§3).
- [x] Six-step migration procedure with per-migration sequence (§4).
- [x] Data-migration specifications for load-bearing cases (§5).
- [x] API-migration specifications for tool-surface changes (§6).
- [x] Rollback plan with tiers, playbook, SLAs, drills (§7).
- [x] Co-existence periods bounded and invariants stated (§8).
- [x] Risk register with mitigations (§9).
- [x] Relation to other Phase-6 docs (§10).
- [x] Success criteria for TC-026 proof (§11).
