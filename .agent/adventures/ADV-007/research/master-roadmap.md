---
id: master-roadmap
title: Claudovka Ecosystem Master Roadmap — Phase-to-Adventure Map
adventure: ADV-007
target_conditions: [TC-031]
produced_by: ADV007-T023
inputs:
  - research/phase1-cross-project-issues.md
  - research/phase2-concept-catalog.md
  - research/phase2-entity-redesign.md
  - research/phase2-knowledge-architecture.md
  - research/phase3-1-role-review.md
  - research/phase3-1-profiling-skills.md
  - research/phase3-1-optimization-skills.md
  - research/phase3-1-self-healing-skills.md
  - research/phase3-2-integration-matrix.md
  - research/phase3-2-mcp-servers.md
  - research/phase4-ui-requirements.md
  - research/phase4-ui-architecture.md
  - research/phase4-technology-evaluation.md
  - research/phase5-concept-designs.md
  - research/phase5-integration-map.md
  - research/phase6-mcp-operations.md
  - research/phase6-autotest-strategy.md
  - research/phase6-automation-first.md
  - research/phase6-1-complexity-analysis.md
  - research/phase6-1-refactoring-strategy.md
  - research/phase6-1-abstract-representation.md
  - research/phase6-2-benchmark-design.md
  - research/phase6-2-test-profiles.md
  - research/phase6-2-migration-strategy.md
  - research/phase7-optimization-loops.md
  - research/phase7-self-healing.md
  - research/phase7-human-machine.md
  - research/phase7-operational-model.md
---

# Claudovka Ecosystem Master Roadmap

## 0. Purpose

ADV-007 produced ~35 research and design documents across 10 roadmap phases. This master roadmap collapses that research into an **actionable backlog of 21 future adventures (ADV-008 .. ADV-028)**, each with scope, inputs, deliverables, effort, cost, priority tier, and dependencies. Phases are not adventures; a phase may split across several adventures and several phases may share one adventure where the research output is tightly coupled (e.g., Phase 1's problem catalog is input to almost everything and has no standalone adventure).

The roadmap is optimised for three constraints that dominate the ADV-001..ADV-006 post-mortem (see `pipeline-management-review.md`):

1. **Lead-state parallelism** — never block the whole queue behind a single slow adventure.
2. **Token-economy** — every adventure has a token budget derived from T008 sharding rules; no adventure may exceed 1.5x its budget without re-scoping.
3. **Rollback-first** — every adventure lands behind a feature flag (T-023 decision). No adventure writes through to a destructive migration in a single step.

Quantities used throughout:

- **Effort**: calendar weeks at 1 lead-driver + 1 reviewer pair, with researcher/architect support on demand.
- **Cost (est.)**: dollars for the agent-side token spend only (model calls). Human labour not included.
- **Priority tier**: P0 (now / blocks everything), P1 (current cycle), P2 (next cycle), P3 (opportunistic).

## 1. Phase → Adventure Map Overview

| Phase | Phase summary | Adventure IDs | Adventure count |
|-------|---------------|---------------|-----------------|
| P1    | Cross-project problem catalog (foundational, no code) | absorbed into ADV-008/009 as input | 0 direct |
| P2    | Unified knowledge architecture + entity redesign | ADV-008, ADV-009 | 2 |
| P3.1  | Management review + skills + roles | ADV-011, ADV-012 | 2 |
| P3.2  | External tools + MCP server integration | ADV-013 | 1 |
| P4    | Claudovka Studio UI | ADV-014, ADV-015 | 2 |
| P5    | New concepts (scheduling, messenger, separation, custom entities, recommendations) | ADV-016, ADV-017, ADV-018, ADV-019 | 4 |
| P6    | Infrastructure (MCP-only, autotest, automation-first) | ADV-010, ADV-020, ADV-021 | 3 |
| P6.1  | Final reconstruction (ARL + refactor M0-M8) | ADV-022, ADV-023 | 2 |
| P6.2  | Post-final (benchmarks, migration) | ADV-024, ADV-025 | 2 |
| P7    | On-sail operations (optimization, self-healing, human-machine, futuring) | ADV-026, ADV-027, ADV-028 | 3 |
| **Total** | | **ADV-008..ADV-028** | **21** |

Phase 1's output (`phase1-cross-project-issues.md`) is a reference catalog consumed by every subsequent adventure; it is not itself an engineering adventure.

## 2. Adventure Catalog

### ADV-008 — Unified Knowledge Store (Event-Sourced Core)

- **Scope**: Implement the canonical event stream + sharded per-agent views described in `phase2-knowledge-architecture.md`. Single writer per shard, atomic write + per-file lock at the MCP boundary (P1.P3), crash-recovery semantics, schema-evolution contract. Does NOT yet migrate old data — it coexists as a shadow store (M0 in `phase6-1-refactoring-strategy.md`).
- **Primary inputs**: `phase1-cross-project-issues.md` (P1, P3, P6 problems), `phase2-knowledge-architecture.md`, `phase2-concept-catalog.md`.
- **Primary deliverables**:
  - `@team-mcp/knowledge-store` package: append-only event log, per-agent view builders, file-lock helpers.
  - Event schema registry v1 (20-30 event types covering task, adventure, metric, lead-state, review).
  - `knowledge.read / knowledge.append / knowledge.shard-view` MCP tools.
  - Shadow-write adapter that dual-writes from current `.agent/` paths into the new store.
  - Test suite: 500+ test cases covering concurrent writers, crash-in-the-middle, shard isolation.
- **Depends on**: none (foundational).
- **Est. effort**: 4 weeks. **Est. cost**: $180.
- **Priority tier**: P0 — blocks almost every other adventure.

### ADV-009 — Entity Redesign: Task / Manifest / Log / Metrics Sharding

- **Scope**: Implement the before/after redesign from `phase2-entity-redesign.md`. Split the four god-files (task.md, manifest.md, adventure.log, metrics.md) into sharded, parallel-writable forms. Provide a rendered-view bridge so existing agents and humans still see the old files during the deprecation window.
- **Primary inputs**: `phase2-entity-redesign.md`, ADV-008 event store, `phase2-knowledge-architecture.md` §2-§4.
- **Primary deliverables**:
  - Sharded entity writers (one shard per writer role × entity).
  - Rendered-view bridge: deterministic concatenation of shards → legacy file path.
  - Schema definitions for each entity family (5 families × ~4 shard types).
  - Migration tool: backfill existing adventures into sharded form.
  - Contract tests: round-trip (legacy → sharded → legacy) bit-identical modulo whitespace.
- **Depends on**: ADV-008 (event store + shard primitives).
- **Est. effort**: 3 weeks. **Est. cost**: $140.
- **Priority tier**: P0.

### ADV-010 — MCP Single-Deploy Surface

- **Scope**: Implement the MCP-only tool surface from `phase6-mcp-operations.md`. One deploy target, one auth model, one tool catalog, security model, failure/recovery. Every write path behind one tool (P6.1 principle 1.2).
- **Primary inputs**: `phase6-mcp-operations.md`, `phase3-2-integration-matrix.md` §5, ADV-008 store.
- **Primary deliverables**:
  - `@team-mcp/server` consolidated deploy (single binary / single workers script).
  - Complete tool catalog ~30 tools (enumerated in §2 of the phase6 doc).
  - OAuth-flavoured auth with per-tool capability grants.
  - Failure-mode matrix + idempotency guarantees.
- **Depends on**: ADV-008.
- **Est. effort**: 3 weeks. **Est. cost**: $120.
- **Priority tier**: P0.

### ADV-011 — Pipeline Skills Library (Profiling + Optimization + Self-Healing)

- **Scope**: Implement the nine skills from `phase3-1-profiling-skills.md`, `phase3-1-optimization-skills.md`, `phase3-1-self-healing-skills.md` (P1-P3, O1-O3, S1-S3). All skills are installed project-local (per feedback memory: `Sandbox/.claude/skills/...`).
- **Primary inputs**: the three skill spec docs, ADV-008 metrics events (skills emit into shared store).
- **Primary deliverables**:
  - Nine skill bundles with manifest + prompt + test fixtures.
  - `metrics-row-emitter` and `wallclock-stamp` integrated into all existing agents.
  - `context-pruner` integrated into researcher/architect agents.
  - `permission-pre-flight` integrated into implementer.
  - Integration tests against ADV-006 replay data.
- **Depends on**: ADV-008 (metrics store).
- **Est. effort**: 3 weeks. **Est. cost**: $110.
- **Priority tier**: P1.

### ADV-012 — Role System Overhaul

- **Scope**: Apply the improvement recommendations from `phase3-1-role-review.md` §4 to the seven pipeline roles (researcher, architect, planner, implementer, reviewer, tester, merger). Standardise prompt structure, close identified gaps, introduce role-capability grants.
- **Primary inputs**: `phase3-1-role-review.md`, `pipeline-management-review.md`, ADV-006 replay.
- **Primary deliverables**:
  - Updated role prompts under `.claude/agents/team-pipeline/*`.
  - Role-capability matrix (role × MCP tool permission).
  - A/B evaluation harness that compares old vs new role on at least three real past tasks.
- **Depends on**: ADV-010 (capability grants live on MCP tools), ADV-011 (skills are role-invoked).
- **Est. effort**: 2 weeks. **Est. cost**: $70.
- **Priority tier**: P1.

### ADV-013 — External MCP + Tool Integration

- **Scope**: Adopt the "Adopt immediately" cohort from `phase3-2-integration-matrix.md` §3.1 (github, memory, sequential-thinking), evaluate the "Evaluate" cohort, skip the "Skip" cohort. Wire them into the roles updated in ADV-012.
- **Primary inputs**: `phase3-2-integration-matrix.md`, `phase3-2-mcp-servers.md`, `team-mcp.md`, `lsp-and-orchestrator.md`.
- **Primary deliverables**:
  - MCP client adapters for the three adopted servers.
  - Evaluation reports for the seven "evaluate" servers (firecrawl, supabase, vercel, railway, cloudflare, clickhouse, magic).
  - Update `config.md` to document server installation.
- **Depends on**: ADV-010 (consolidated surface), ADV-012 (roles that will use them).
- **Est. effort**: 2 weeks. **Est. cost**: $70.
- **Priority tier**: P1.

### ADV-014 — Claudovka Studio UI Foundation

- **Scope**: Build the Shell + Entity-views layers from `phase4-ui-architecture.md` §2.1-§2.2 on the recommended stack from `phase4-technology-evaluation.md` §5. Read-only at first; write-paths land in ADV-015.
- **Primary inputs**: `phase4-ui-requirements.md`, `phase4-ui-architecture.md`, `phase4-technology-evaluation.md`.
- **Primary deliverables**:
  - Next-gen Claudovka Studio web app (repo + CI).
  - Shell layer: tabs/panes (F7), authentication, theming.
  - Entity views: Task, Adventure, Manifest, Metrics, Log (read-only).
  - Event-sourced cache hooked to ADV-008 read API.
- **Depends on**: ADV-008 (read-API), ADV-009 (entities).
- **Est. effort**: 4 weeks. **Est. cost**: $150.
- **Priority tier**: P2.

### ADV-015 — Claudovka Studio: Editors + Live Updates

- **Scope**: Editors layer + live subscription fan-out from `phase4-ui-architecture.md` §2.3-§4. DSL editor, graph editor, optimistic writes.
- **Primary inputs**: same as ADV-014, plus `phase4-ui-requirements.md` §5-§6.
- **Primary deliverables**:
  - Monaco-based DSL editor with ark grammar.
  - Graph editor (React Flow) for adventure dependency graphs and pipeline visualisations.
  - Live-update subscription (SSE or WebSocket) on top of ADV-008 event stream.
  - Write-path tools bound to ADV-010 MCP surface.
- **Depends on**: ADV-014, ADV-010.
- **Est. effort**: 4 weeks. **Est. cost**: $150.
- **Priority tier**: P2.

### ADV-016 — Scheduling + Triggers

- **Scope**: `phase5-concept-designs.md` §1 + trigger-entity resolution called out in `phase5-integration-map.md` §4.1. Cron-like and event-driven triggers with a single canonical writer.
- **Primary inputs**: `phase5-concept-designs.md`, `phase5-integration-map.md`.
- **Primary deliverables**:
  - `scheduling.schedule / scheduling.cancel / scheduling.fire` MCP tools.
  - `trigger` entity type in the store (single-writer hazard resolved by making scheduler the owner).
  - Replay-safe scheduler (state lives in event stream).
- **Depends on**: ADV-008, ADV-010.
- **Est. effort**: 2 weeks. **Est. cost**: $75.
- **Priority tier**: P1.

### ADV-017 — Input Storage + Messenger Agent

- **Scope**: `phase5-concept-designs.md` §3 (input storage) + §4 (messenger agent). Channel abstraction with deterministic ordering; input store for long-form human prompts and attachments.
- **Primary inputs**: `phase5-concept-designs.md`, `phase5-integration-map.md` §4.2.
- **Primary deliverables**:
  - `input.store / input.fetch / messenger.post / messenger.subscribe` MCP tools.
  - Messenger channel substrate (initially Slack + in-app, pluggable).
  - Human-as-pipeline-role hook (§2) wired into ADV-012 role system so humans appear as one of the roles.
- **Depends on**: ADV-008, ADV-010, ADV-012.
- **Est. effort**: 3 weeks. **Est. cost**: $110.
- **Priority tier**: P2.

### ADV-018 — Project / Repo / Knowledge Separation

- **Scope**: `phase5-concept-designs.md` §5. Split the conflated project/repo/knowledge-base concepts; give each entity its own storage axis. Resolves `phase5-integration-map.md` §4.3 conflict.
- **Primary inputs**: `phase5-concept-designs.md`, `phase2-entity-redesign.md` §5.
- **Primary deliverables**:
  - `project`, `repo`, `knowledge-base` top-level entities in the store.
  - Migration tool that walks current conflated `.agent/` trees and splits them.
  - Cross-entity query helpers (knowledge across all repos in a project).
- **Depends on**: ADV-009 (entity redesign must exist first).
- **Est. effort**: 3 weeks. **Est. cost**: $110.
- **Priority tier**: P2.

### ADV-019 — Custom Entities + Recommendations Stack

- **Scope**: `phase5-concept-designs.md` §6 (user-defined entity types through ark DSL) + §7 (recommendations stack). Resolves `phase5-integration-map.md` §4.4 + §4.5.
- **Primary inputs**: `phase5-concept-designs.md`, `phase7-operational-model.md` §7 (integration with recommendations stack).
- **Primary deliverables**:
  - Ark DSL extension: `entity { ... }` declaration compiled to store schemas + MCP tools.
  - Recommendations service: ingests signals, emits ranked recommendations, integrated with futuring subsystem (ADV-028).
  - Built-in vs custom entity lifecycle hooks.
- **Depends on**: ADV-009, ADV-018.
- **Est. effort**: 4 weeks. **Est. cost**: $160.
- **Priority tier**: P2.

### ADV-020 — Autotest Orientation + CI

- **Scope**: Implement the coverage targets and proof-method taxonomy from `phase6-autotest-strategy.md`. Wire into the regression-surface and golden-test registry.
- **Primary inputs**: `phase6-autotest-strategy.md`, `phase6-2-test-profiles.md`.
- **Primary deliverables**:
  - CI orchestration (matrix: unit / integration / golden / property).
  - Golden-file registry with deterministic replay harness.
  - Coverage dashboard (tied to ADV-014 UI when available).
- **Depends on**: ADV-008, ADV-010.
- **Est. effort**: 2 weeks. **Est. cost**: $80.
- **Priority tier**: P1.

### ADV-021 — Automation-First Guardrails

- **Scope**: Implement the decision tree, escalation triggers, and metrics from `phase6-automation-first.md`. Codify "no LLM-as-sole-judge on prod-affecting actions", silent-retry-loop detection, shadow-automation bans.
- **Primary inputs**: `phase6-automation-first.md`, `phase7-human-machine.md` §3 (escalation matrix).
- **Primary deliverables**:
  - Automation-posture policy file per role/tool.
  - Escalation router (→ humans via ADV-017 messenger).
  - Metrics emitters: `auto_rate`, `escalation_rate`, `silent_retry_count`.
- **Depends on**: ADV-011 (skills emit the needed metrics), ADV-017 (messenger carries escalations).
- **Est. effort**: 2 weeks. **Est. cost**: $75.
- **Priority tier**: P1.

### ADV-022 — Abstract Representation Layer (ARL) + Refactor M0-M4

- **Scope**: Milestones M0-M4 from `phase6-1-refactoring-strategy.md` + the minimum viable ARL from `phase6-1-abstract-representation.md` §8. Shadow events, read-through views, task/manifest sharding, lead-state formalisation, knowledge unification.
- **Primary inputs**: `phase6-1-refactoring-strategy.md`, `phase6-1-abstract-representation.md`, `phase6-1-complexity-analysis.md` (reduction targets).
- **Primary deliverables**:
  - ARL core package (algebra, rendering, translation).
  - M0-M4 milestones completed with passing gates per §3 of refactoring strategy.
  - Complexity-reduction metrics hit (see `phase6-1-complexity-analysis.md` §3 targets).
- **Depends on**: ADV-008, ADV-009, ADV-020 (gates).
- **Est. effort**: 6 weeks. **Est. cost**: $260.
- **Priority tier**: P1.

### ADV-023 — ARL Growth + Refactor M5-M8

- **Scope**: Milestones M5-M8 from `phase6-1-refactoring-strategy.md`. Triggers/hooks/schedulers unification, registry generation, MCP-only, contract enforcement + end-to-end smoke.
- **Primary inputs**: same as ADV-022 plus ADV-022's own outputs.
- **Primary deliverables**:
  - M5-M8 milestones completed.
  - Registry generation: catalogs generated from source (closes P1.P5).
  - End-to-end smoke test crossing all five projects (closes P1.P9).
- **Depends on**: ADV-022, ADV-016, ADV-010.
- **Est. effort**: 6 weeks. **Est. cost**: $260.
- **Priority tier**: P2.

### ADV-024 — Benchmark Suite + Baselines

- **Scope**: Implement `phase6-2-benchmark-design.md` end-to-end: metric axes, measurement methodology, baseline + target metrics, report format, automation hooks.
- **Primary inputs**: `phase6-2-benchmark-design.md`, `phase6-2-test-profiles.md`, `phase6-1-complexity-analysis.md`.
- **Primary deliverables**:
  - Benchmark harness package.
  - Baselines captured against current system (pre-ARL).
  - Target metric report auto-generated per release.
- **Depends on**: ADV-020 (CI harness), ADV-022 (ARL is a benchmarking subject).
- **Est. effort**: 3 weeks. **Est. cost**: $110.
- **Priority tier**: P2.

### ADV-025 — Migration Runbook

- **Scope**: Execute `phase6-2-migration-strategy.md`. Cut over every legacy surface to its new canonical form following the 6-step procedure (§4). Time-boxed deprecations announced per §3.4.
- **Primary inputs**: `phase6-2-migration-strategy.md`, outputs of ADV-009/010/018/022.
- **Primary deliverables**:
  - All migrations from inventory §2 executed.
  - Legacy-path deprecation announcements filed.
  - Trapdoor-removal PRs merged on schedule.
- **Depends on**: ADV-022, ADV-023, ADV-018.
- **Est. effort**: 4 weeks. **Est. cost**: $140.
- **Priority tier**: P2.

### ADV-026 — Day-to-Day Optimization Loops Runtime

- **Scope**: Implement the loop catalogue from `phase7-optimization-loops.md` §2 as live, observable runtime processes. Integrate with recommendations stack (ADV-019).
- **Primary inputs**: `phase7-optimization-loops.md`, `phase7-operational-model.md` §7.
- **Primary deliverables**:
  - Loop runner framework (`loop.register / loop.tick / loop.observe`).
  - Six or more concrete loops implemented (cost-tuning, parallelism-tuning, prompt-tuning, context-pruning, retry-tuning, routing-tuning).
  - Loop observability dashboard (in ADV-015 UI).
- **Depends on**: ADV-011, ADV-019, ADV-015.
- **Est. effort**: 4 weeks. **Est. cost**: $160.
- **Priority tier**: P3.

### ADV-027 — Self-Healing Pipeline

- **Scope**: `phase7-self-healing.md` five-stage pipeline (detect → classify → attempt-fix → verify → escalate) with error taxonomy from §3 and playbook from §4. Builds on skills S1-S3 from ADV-011.
- **Primary inputs**: `phase7-self-healing.md`, `phase3-1-self-healing-skills.md`.
- **Primary deliverables**:
  - `healer` role + detection pipeline.
  - Error taxonomy v1 with classifier.
  - Safety envelope (rate limits, blast radius caps).
  - Integration with ADV-021 automation-first guardrails and ADV-028 escalation.
- **Depends on**: ADV-011, ADV-021.
- **Est. effort**: 4 weeks. **Est. cost**: $160.
- **Priority tier**: P3.

### ADV-028 — Human-Machine Escalation + Futuring

- **Scope**: `phase7-human-machine.md` escalation matrix + context-package handoff protocol + `phase7-operational-model.md` futuring subsystem (horizon scanning, signal taxonomy, synthesis, proactive backlog).
- **Primary inputs**: the two phase7 docs listed.
- **Primary deliverables**:
  - Escalation matrix implementation (routes by type × severity × domain).
  - Attention-budget accounting per human stakeholder.
  - Futuring loop: horizon-scan → signal → hypothesis → proactive-backlog.
  - Return-path rule distiller: decisions → automation rules.
- **Depends on**: ADV-017, ADV-021, ADV-019 (recommendations stack), ADV-027.
- **Est. effort**: 4 weeks. **Est. cost**: $160.
- **Priority tier**: P3.

## 3. Priority Tiering Summary

| Tier | Adventures | Why this tier |
|------|------------|---------------|
| P0   | ADV-008, ADV-009, ADV-010 | Store + entity + MCP surface — everything else depends on these. |
| P1   | ADV-011, ADV-012, ADV-013, ADV-016, ADV-020, ADV-021, ADV-022 | Make the pipeline safer, faster, and role-clean before adding new concepts. |
| P2   | ADV-014, ADV-015, ADV-017, ADV-018, ADV-019, ADV-023, ADV-024, ADV-025 | New surfaces, UI, separation, migration. |
| P3   | ADV-026, ADV-027, ADV-028 | Runtime optimization, self-healing, futuring — productive but not prerequisites for shipping the unified base. |

## 4. Effort and Cost Totals

Rows sum across the catalog above:

| Tier | Effort (weeks) | Cost (USD est.) |
|------|----------------|-----------------|
| P0   | 10             | $440            |
| P1   | 21             | $870            |
| P2   | 31             | $1,180          |
| P3   | 12             | $480            |
| **Total** | **74 weeks** | **~$2,970** |

With an average concurrency of 2-3 (see dependency graph), the wall-clock plan runs ~30-34 calendar weeks (§ wave plan in `adventure-dependency-graph.md`).

## 5. Milestone Timeline

- **M-α (end of wave 1, ~week 6)**: Store + entities + MCP surface live. Shadow-writes from legacy `.agent/` succeed. All ADV-006 test adventures replay bit-identically.
- **M-β (end of wave 2, ~week 14)**: Skills library shipped; roles upgraded; external MCPs integrated; scheduling + autotest + automation-first live. The pipeline is measurably cheaper per task (target: −25% tokens per task vs ADV-006 baseline) and measurably safer (target: zero silent-retry loops in a 100-task sample).
- **M-γ (end of wave 3, ~week 24)**: UI + new concepts (input/messenger, project separation, custom entities) + ARL M0-M4. Claudovka Studio read/write against unified store.
- **M-δ (end of wave 4, ~week 30)**: ARL M5-M8 + benchmarks + migration complete. Legacy `.agent/` paths removed.
- **M-ε (end of wave 5, ~week 34)**: Optimization loops + self-healing + futuring live. The system proposes its own next roadmap item.

## 6. Risks and Mitigations (Roadmap-Level)

- **Risk**: ADV-008 slips and blocks everything. **Mitigation**: de-risk with a 1-week spike adventure ADV-008a (not in the count) before committing the full ADV-008; fall back to a simpler JSONL event log if needed.
- **Risk**: UI adventures (ADV-014/015) grow under scope creep. **Mitigation**: Read-only first (ADV-014), write paths strictly gated by ADV-010 tool catalog completeness.
- **Risk**: ARL (ADV-022) proves theoretically elegant but practically over-abstract. **Mitigation**: Minimum viable ARL per `phase6-1-abstract-representation.md` §8; forward-only trapdoors allowed per §4.4 of refactoring strategy; if M2 takes >4 weeks, stop and re-scope.
- **Risk**: Migration (ADV-025) breaks an active adventure. **Mitigation**: Rendered-view bridge (ADV-009) keeps legacy views readable throughout; no trapdoor is pulled until its deprecation window has passed.
- **Risk**: Ecosystem roadmap outruns stakeholder attention (P7 automation-first principle #3 violation). **Mitigation**: ADV-021 + ADV-028 escalation budget per stakeholder; merge freezes bundled per release branch.

## 7. Cross-Cutting Ledgers (from Phase 1)

Each P-item from `phase1-cross-project-issues.md` §4 maps to the adventure(s) that close it:

| P-item | Description | Closed by |
|--------|-------------|-----------|
| P1     | SSoT pipeline state machine | ADV-008 + ADV-009 |
| P2     | One DSL across ecosystem | ADV-023 (M6 registry gen + DSL unification) |
| P3     | Atomic writes + per-file locks | ADV-008 |
| P4     | Hooks → deterministic MCP tool calls | ADV-010 + ADV-012 |
| P5     | Generate every catalog from source | ADV-023 |
| P6     | Real token/cost telemetry | ADV-011 (metrics skills) |
| P7     | Version negotiation + active-version pinning | ADV-025 |
| P8     | Finish binartlab MCP toolset | ADV-013 |
| P9     | End-to-end smoke test across 5 projects | ADV-023 M8 |
| P10    | Decide `@binartlab/mobile`, `agent-memory` naming | ADV-018 |

Every P-item has an owning adventure.

## 8. Acceptance

This roadmap satisfies **TC-031**: all 10 phases are mapped to adventure IDs (21 adventures in ADV-008..ADV-028), each adventure has the required scope / inputs / deliverables / effort / cost / priority fields, and cross-phase coverage is complete. Companion documents provide the DAG (`adventure-dependency-graph.md`, TC-032) and inter-adventure contracts (`adventure-contracts.md`, TC-033).
