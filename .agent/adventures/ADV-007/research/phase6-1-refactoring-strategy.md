---
task: ADV007-T020
adventure: ADV-007
phase: 6.1
target_conditions: [TC-022]
upstream:
  - .agent/adventures/ADV-007/research/phase6-1-complexity-analysis.md
  - .agent/adventures/ADV-007/research/phase2-entity-redesign.md
  - .agent/adventures/ADV-007/research/phase6-mcp-operations.md
  - .agent/adventures/ADV-007/research/phase1-cross-project-issues.md
researched: 2026-04-14
---

# Phase 6.1 — Iterative Refactoring Strategy

This document defines the **iterative refactoring strategy** that turns
the complexity-reduction targets (TC-021) into a sequence of landable
milestones. The strategy is expressly **non-flag-day**: every stage is
reversible, each milestone ships behind a feature flag or a rendered-view
shim, and every gate is an objective autotest or repo grep rather than a
review checkbox.

The strategy extends the Phase-2 migration phases **M0-M6** (from the
entity-redesign doc, §18.3) with the Phase 6 operational tooling (phase6
MCP-ops §3) and ties each milestone to the `lightweight_index` target
from TC-021 §3.1.

Refactoring strategy authors should read the companion
`phase6-1-complexity-analysis.md` first to ground each milestone in its
numeric target.

---

## 1. Principles

Five principles govern every milestone. They are the invariants that
must hold across every rollback and fence, so they are stated first.

### 1.1 Additive before subtractive

No milestone deletes a producer before introducing its replacement **and**
proving at least one consumer uses the replacement in production.
Corollary: every `M` milestone that renames or re-shapes an entity ships
a rendered-view shim at the legacy path for at least one full milestone
cycle.

### 1.2 Every write path behind one tool

A milestone never lands a refactor that creates a second writer to the
same surface. If two writers are required during the transition, the
milestone introduces the destination surface first and re-routes the
second writer at a later sub-milestone. Resolves X6/X7 invariant.

### 1.3 One canonical test per gate

Every milestone declares exactly one autotest that certifies
completion. If the feature needs to be partly done to unblock the next
milestone, the milestone splits; it does not acquire a second gate.

### 1.4 Rollback is a grep, not a revert

Each milestone deposits a marker in `.agent/config.md`
(`layout_version: M4`) plus a feature flag
(`flags.canonical_task_dir: true`). Rollback flips the flag and replays
events from the most recent known-good tail; it never requires
`git revert`. Resolves "documentation that is better than the code"
anti-pattern (phase1 §3.1 #7).

### 1.5 Every milestone shrinks the lightweight index

No milestone ships that raises `lightweight_index` above its current
value. Temporary increases are permitted within a milestone during the
"additive" step; the milestone is not closed until the scalar is back
below its previous ceiling.

---

## 2. Stage Plan (Milestones M0-M8)

M0-M6 are the Phase-2 migration stages; M7-M8 are Phase 6 additions
(operational tooling, catalog cleanup). Each milestone states the
invariants that must hold **during** the stage and the gate that closes
it.

### M0 — Shadow events (two-write bridge)

- **Scope**: every writer that mutates `.agent/` also appends a typed
  event to `events.jsonl` at the same path. No consumer reads the
  events yet.
- **Invariants during**: the legacy markdown is still authoritative;
  the shadow stream is read-only for sanity checks.
- **Rollback**: delete `events.jsonl`; no other state is affected.
- **Gate (autotest)**: `pipeline.test(scope="ark", filter="events.shadow")`
  passes: for 100 sample operations, the replay of `events.jsonl`
  reconstructs the md state byte-for-byte (after canonicalisation).
- **Duration estimate**: 1 adventure; no user-visible change.
- **Resolves**: nothing directly; prerequisite for M1-M5.
- **Lightweight index delta**: 0 (pure addition).

### M1 — Read-through views (views derive from events)

- **Scope**: consumers that previously grepped `manifest.md`,
  `metrics.md`, `knowledge/*.md` start reading from the rendered views
  derived from `events.jsonl`. Writers still mutate the legacy files
  directly (M0 shadow still on).
- **Invariants during**: both the legacy file and the rendered view
  are kept in sync; reconciler runs on every event append.
- **Rollback**: flip `flags.views_as_source: false`; consumers revert
  to grepping legacy files.
- **Gate**: `pipeline.test(scope="team-mcp", filter="views.parity")`
  shows zero divergence between rendered view and legacy file across
  the last 1 000 events.
- **Resolves**: prerequisite for view-based reads in M2+.
- **Lightweight index delta**: 0.

### M2 — Task and manifest sharding

- **Scope**: `tasks/<id>.md` → `tasks/<id>/{task.md, log.jsonl,
  iterations.jsonl}`; `manifest.md` + tables →
  `manifest.md + manifest.targets.jsonl + manifest.evaluations.jsonl
  + views/`. Legacy paths become generated rendered views.
- **Invariants during**: legacy paths remain readable through the
  rendered view generator; every legacy-path read passes through the
  view; direct reads are grep-blocked in CI.
- **Rollback**: flip `flags.canonical_task_dir: false`; the event log
  + rendered view generator rebuilds the legacy md from the tail.
- **Gate**: `pipeline.test(scope="full", filter="task.crud.v2")` — a
  task goes through all stages end-to-end writing only to the sharded
  layout; legacy rendered view still matches manifest schema v1 byte
  layout.
- **Resolves**: X6 (partial), X7 (manifest writers), TP-H2.
- **Lightweight index delta**: reduces `L_tokens` and
  `L_source`; target index ≤ 0.75.

### M3 — Lead-state, permissions, session formalisation

- **Scope**: `lead-state.md` → `lead-state/{active.jsonl,
  sessions/<id>.json}`; `permissions.md` → `permissions/<scope>/spec.md`
  with per-scope loading; Session concept split into LeadSession /
  LockSession / ClientConnection (T007 §3.3).
- **Invariants during**: every TM `emit()` appends to `active.jsonl`
  (no RMW); legacy `lead-state.md` regenerated from tail; permission
  reads go through `pipeline.permissions_get(scope)`.
- **Rollback**: `flags.lead_state_v2: false` reverts writers; the
  sharded files remain on disk as shadow.
- **Gate**: `pipeline.test(scope="team-mcp", filter="leadstate.race")` —
  a 50-concurrent-emit stress harness shows zero lost events.
- **Resolves**: TM-H4, X7 (partial).
- **Lightweight index delta**: reduces `L_tokens` further; target ≤ 0.65.

### M4 — Knowledge unification

- **Scope**: `knowledge/{patterns,issues,decisions}.md` +
  `agent-memory/<role>/` → `knowledge/lessons.jsonl` + `views/` (T008
  §5, §6).
- **Invariants during**: `lesson_append` is the only writer; legacy md
  files are symlinks to rendered views for one full cycle; every
  entry carries `kind:` and optional `role:`.
- **Rollback**: regenerate legacy files from `lessons.jsonl` (the
  rendered views already do this); agents keep reading the legacy paths.
- **Gate**: `pipeline.test(scope="team-mcp", filter="lesson.views")`
  shows round-trip identity between any legacy md file and the
  rendered view for that kind.
- **Resolves**: X9, TP-L-Memory-knowledge.
- **Lightweight index delta**: reduces `L_tokens` (role-scoped views
  -80 %). Target ≤ 0.55.

### M5 — Triggers, hooks, schedulers

- **Scope**: hook prompts → 3-line shims forwarding to deterministic
  `pipeline.on_subagent_stop` / `pipeline.on_user_prompt` /
  `pipeline.on_session_stop` tools. Scheduling entity (phase5 §1)
  lands; messenger approvals persist to `approvals.jsonl` (T008 §11).
- **Invariants during**: legacy hook prompts retained behind
  `flags.hooks_v2: false` for one cycle as fallback; feature-flag in
  `config.md` selects which path is live.
- **Rollback**: flip `flags.hooks_v2: false`; the LLM-driven hooks
  resume.
- **Gate**: `pipeline.test(scope="team-pipeline",
  filter="hook.deterministic")` — the same hook input produces the
  same output across 100 runs (zero non-determinism); hook prompt LOC
  < 0.5 KB.
- **Resolves**: X8, TP-H1, TP-M-Reviewer-echo, L6 (approvals), X10
  (messenger persistence).
- **Lightweight index delta**: reduces prompt LOC dramatically (H1
  -92 %). Target ≤ 0.45.

### M6 — Registry generation and DSL unification

- **Scope**: `registry/{skills,agents,roles,triggers,tools}.json`
  generated at TM start; README/CLAUDE.md/deployment-manual cite via
  include; PDSL becomes an Ark dialect (PDSL parser retired; PDSL
  viewer + editor retained, re-pointed at Ark AST); binartlab YAML
  replaced by Ark-generated zod.
- **Invariants during**: every hand-curated catalog entry is compared
  against the generated registry in CI; discrepancies fail the build.
- **Rollback**: revert the CI check; hand-curated catalogs continue to
  work (but drift again).
- **Gate**: `pipeline.test(scope="full", filter="catalog.parity")` —
  every listed skill/agent/role/command matches exactly the generated
  registry; PDSL examples round-trip through Ark AST.
- **Resolves**: X2 (DSL unification), X3 (catalogs), PDSL-1, PDSL-2,
  BL-7, partial X1 (state machine absorbed into Ark trunk).
- **Lightweight index delta**: reduces `L_schema` (23 → 8), `L_api`
  (hand-curated → 0). Target ≤ 0.42 (complete).

### M7 — Operational MCP-only

- **Scope**: the 7 operational tools (deploy, build, compile, test,
  migrate, rollback, metrics) from phase6 MCP-ops §2 land; every prior
  bash/shell call in roles / hooks / scripts migrates to the
  corresponding MCP call.
- **Invariants during**: `bash` capability remains in agent prompts
  but CI asserts no mutating bash strings in prompts (grep gate);
  `active.jsonl` shows 100 % of mutations attributed to an
  `invocation_id`.
- **Rollback**: flip `flags.mcp_only_ops: false`; agents can shell out
  again; the MCP tools remain available as a preferred path.
- **Gate**: `pipeline.test(scope="full", filter="ops.mcp_only")` —
  zero bash mutations found in role prompts; every CI run logs exactly
  one `run.started` / `run.finished` pair per build.
- **Resolves**: X8 completion; operational auditability (phase6 §1.1).
- **Lightweight index delta**: reduces `L_api` further (bash removed
  from mutating surface). Target ≤ 0.40.

### M8 — Contract enforcement and end-to-end smoke

- **Scope**: every edge E1-E14 promoted to a first-class `Contract`
  entity in `schema/contracts/<edge>.ark` (T007 §10.4); autogenerated
  contract tests run in CI; one end-to-end smoke test
  (`adventure.smoke`) exercises TP + TM + BL + marketplace in mock
  mode.
- **Invariants during**: missing contract ⇒ CI fail; version mismatch
  between components ⇒ TM refuses to start (X4 completion).
- **Rollback**: flip `flags.contract_enforcement: false`; contracts
  remain declared but non-blocking.
- **Gate**: `pipeline.test(scope="full", filter="contracts.all")` —
  14 of 14 contract tests pass; `adventure.smoke` runs green; binary
  reproducible build hash equality across the two previous adventures.
- **Resolves**: X4, X5, X11 (metrics back-filled from authoritative
  source), BL-5.
- **Lightweight index delta**: final target **≤ 0.42** and all 11
  X-issues closed.

---

## 3. Test Coverage Gates per Milestone

Each milestone names exactly one autotest (principle §1.3) but ships
with an expanded **coverage budget** that CI enforces at gate time.

| Milestone | Gate autotest | Coverage budget (ARK + TM + BL + TP) |
|---|---|---|
| M0 | `events.shadow` | unchanged; only new file exists |
| M1 | `views.parity` | +5 % TM unit (view generator); no change elsewhere |
| M2 | `task.crud.v2` | +10 % TM; +3 % TP hook reader tests |
| M3 | `leadstate.race` | +15 % TM concurrent; +8 % boundary adapter |
| M4 | `lesson.views` | +5 % knowledge-view generator; +5 % researcher agent |
| M5 | `hook.deterministic` | +25 % TP (hook → tool migration); +10 % TM |
| M6 | `catalog.parity` | +10 % TM (registry generator); +5 % Ark codegen |
| M7 | `ops.mcp_only` | +20 % TM (7 new tools); +5 % role-prompt linter |
| M8 | `contracts.all` | +14 contract tests; +1 smoke adventure |

Sum of budgets brings backend (TM + Ark) to ~90 % line coverage and
frontend (TP + BL web) to ~70 % — the ecosystem-wide test-density
target from phase1 §3.2 lesson #1.

### 3.1 Flaky-test policy

A gate autotest may not be flagged as "flaky" to close a milestone.
Flakes are triaged within the milestone; if the root cause cannot be
removed, the milestone shrinks (not the gate). Maximum 3 attempts per
autotest in CI before the milestone is marked `at-risk`.

### 3.2 Golden-file policy

Generated artefacts (rendered views, Ark codegen outputs, contract
schemas) are tested by golden files checked into the repo. Updating a
golden is a review-required step; CI blocks a PR that updates a golden
without a human approval.

---

## 4. Rollback / Fence Strategy

### 4.1 Feature-flag matrix

A single `config.md` block lists every in-flight flag:

```
flags:
  events_shadow: on          # M0
  views_as_source: on        # M1
  canonical_task_dir: on     # M2
  lead_state_v2: on          # M3
  knowledge_lessons: on      # M4
  hooks_v2: on               # M5
  registry_generated: on     # M6
  mcp_only_ops: on           # M7
  contract_enforcement: on   # M8
```

Each flag is independent; flipping one does not require flipping
another. The rendered-view shims provide the bidirectional bridge.

### 4.2 Fences (preventing forward-only breakage)

A "fence" is a CI check that refuses a PR that would make rollback
impossible. Fences per milestone:

- M2 fence: no PR may delete `views/manifest.rendered.md`.
- M3 fence: no PR may delete `lead-state.rendered.md` generator.
- M4 fence: `knowledge/patterns.md` must remain a readable path
  (symlink or regenerated file).
- M5 fence: legacy hook prompts must remain parseable (linted) even
  while `hooks_v2` is on.
- M6 fence: a skill/agent/role present in the generated registry
  **must** have a source file; a source file without a registry entry
  fails startup.
- M8 fence: every contract's current-version schema must remain
  backward-compatible for one release cycle.

### 4.3 Rollback playbook

1. Identify the milestone whose flag to flip from the active symptom
   (e.g., manifest corruption ⇒ M2; hook non-determinism surfacing
   despite determinism test ⇒ M5).
2. Flip the flag in `config.md`; reload TM (`pipeline.reload_config`).
3. Run `pipeline.state_rebuild(scope=<entity>)` — replays the event
   log through the legacy-shape generator and writes the legacy md
   files.
4. Verify by running the previous milestone's gate autotest; it
   should pass.
5. Open a post-mortem adventure to land the fix; once the fix is in,
   flip the flag back.

### 4.4 Forward-only trapdoors (explicitly permitted)

Some decisions are one-way by design — typically when the legacy shape
is demonstrably broken. Explicit trapdoors for this refactor:

- **Deleting hook prompts** (M5 → M6 boundary): once hooks are tools
  and the determinism gate has held for one full release, the prompts
  are removed. Rollback after this point requires re-authoring hooks
  from git history.
- **Retiring PDSL parser** (M6): the Ark dialect profile must pass
  every PDSL test case before the PDSL parser is removed. Rollback
  after removal requires re-adopting the Ark dialect.
- **Removing `agent-memory/` directory** (end of M4, one cycle after
  symlink): the knowledge lessons must be canonical for one full
  cycle first.

Each trapdoor requires an explicit entry in `adventure.log` citing
the gate autotest run that authorises the one-way step.

---

## 5. Dependencies and Ordering

The milestones form a partial order. The strict dependencies:

```
M0 ── M1 ── M2 ── M3 ── M5 ── M6 ── M7 ── M8
              \       /
               M4 ───┘
```

- M4 (knowledge) depends on M1 (views) but not M2/M3; it can
  parallelise with M2 or M3.
- M5 (hooks/triggers) depends on M3 (lead-state formalisation) because
  hook tools read session state.
- M7 (ops MCP) depends on M5 (deterministic triggers) because some ops
  are scheduled or hook-triggered.
- M8 (contracts + smoke) depends on M6 (DSL unification) because
  contract schemas compile from Ark.

No milestone has more than one upstream hard dependency. This keeps
the critical path at 8 milestones long and offers one parallel track
(M4) to absorb staffing variance.

---

## 6. Estimation and Evaluation Budget

Each milestone corresponds to roughly one Adventure (3-6 tasks).
Estimated budgets (per Phase-2 architecture §18.3 and T008 §18.2 token
model):

| Milestone | Tasks | Estimated tokens | Est. duration |
|---|---:|---:|---|
| M0 | 3 | 60 000 | 2 h |
| M1 | 4 | 90 000 | 3 h |
| M2 | 6 | 180 000 | 5 h |
| M3 | 5 | 150 000 | 4 h |
| M4 | 4 | 110 000 | 3 h |
| M5 | 6 | 200 000 | 5 h |
| M6 | 6 | 200 000 | 5 h |
| M7 | 5 | 160 000 | 4 h |
| M8 | 4 | 120 000 | 3 h |
| **Total** | **43** | **~1.27 M** | **~34 h** |

Variance budget: ±40 % per milestone (phase2 estimates have held at
about that accuracy across ADV-004 through ADV-007). Researchers
update evaluations after each milestone so the running total tracks
against the global budget.

### 6.1 Milestone completion criteria

A milestone is closed when **all** of the following hold:

1. The gate autotest passes on three consecutive commits on trunk.
2. The `lightweight_index` has dropped to ≤ the milestone's target.
3. The feature-flag block in `config.md` marks the milestone's flag
   as `default: on`.
4. The corresponding X-issue row in T006 §2 has a `resolved_by:
   M<n>` field referencing this milestone.
5. The milestone's adventure is marked `completed` in its manifest,
   with all TCs green and the retrospective appended to
   `knowledge/lessons.jsonl` with `kind: decision`.

Criteria 4 and 5 are what turn this strategy document from a plan into
a progress tracker: each closure writes an auditable trail.

---

## 7. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| View generator becomes a bottleneck at high event rates (§19 open trade-off, T008) | medium | medium | Incremental rendering; lazy regen (T008 §19.1). Gate: M1 perf test ≤ 100 ms per event. |
| Trapdoor milestone opens before the gate is trusted | low | high | Section 4.4 policy: three consecutive green CI runs required before one-way step. |
| Binartlab mobile rescoping (H5) delays M8 | high | medium | Excise mobile from the smoke gate; it is out of scope for `adventure.smoke` v1. |
| Ark codegen parity with PDSL tests | medium | high | M6 blocks on passing every PDSL test case; buffer 1 extra adventure for the dialect profile. |
| Token estimation variance stays high after M5 (X11) | medium | low | M7 adds authoritative SDK-based metrics; M8 back-fills ≥ 90 days of history. |
| Rollback from M7 fails (bash path atrophied) | low | high | `flags.mcp_only_ops: false` retains the bash path in role prompts behind a flag for two cycles after M7 close. |

---

## 8. Acceptance Checklist (this document)

- [x] Principles of iterative refactoring articulated (§1).
- [x] Milestone stage plan M0-M8 with scope / invariants / rollback /
  gate per milestone (§2).
- [x] Test coverage gates per milestone (§3).
- [x] Flaky-test and golden-file policies (§3.1, §3.2).
- [x] Rollback / fence strategy with feature-flag matrix (§4).
- [x] Forward-only trapdoors enumerated (§4.4).
- [x] Milestone dependencies / ordering graph (§5).
- [x] Estimation and evaluation budget (§6).
- [x] Milestone completion criteria tied to T006 catalog (§6.1).
- [x] Risk register with mitigations (§7).
