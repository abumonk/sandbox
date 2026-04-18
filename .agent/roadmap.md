---
version: 1
last_updated: 2026-04-15T07:00:00Z
last_session_read: null
projects:
  - id: ark-core
    name: Ark Core (Descriptor / Builder / Controller)
    adventures: [ADV-001, ADV-002, ADV-003, ADV-004, ADV-005, ADV-006, ADV-007, ADV-008, ADV-011, ADV-DU, ADV-BC, ADV-CC, ADV-OP]
  - id: console-ui
    name: Adventure Console UI
    adventures: [ADV-009]
  - id: telemetry
    name: Pipeline Telemetry
    adventures: [ADV-010]
  - id: optional-sidebars
    name: Optional Sidebars (post-unification)
    adventures: [ADV-CE, ADV-UI]
ecosystem_stats:
  total_adventures: 11
  completed_adventures: 9
  active_adventures: 2
  review_adventures: 0
  total_tasks: 216
  completed_tasks: 177
  total_tcs: 338
  passed_tcs: 50
downstream_planned:
  - ADV-DU
  - ADV-BC
  - ADV-CC
  - ADV-OP
  - ADV-CE
  - ADV-UI
---

# Project Roadmap

## Ecosystem Overview

The Sandbox ecosystem hosts the **Ark DSL** (a declarative architecture kernel for system description, verification, codegen) and the **Claudovka pipeline** (`.agent/` adventures, roles, hooks, and the Team Pipeline orchestrator). Eleven adventures have been dispatched to date; nine are complete (ADV-001..008 + ADV-011), one is active with planning in flight (ADV-009), and one has just flipped review→active (ADV-010). ADV-011 produced the unified core design that identifies Ark's three roles — Descriptor, Builder, Controller — and pruned the research catalogue down to a **4+2 downstream chain**: four core adventures (ADV-DU, ADV-BC, ADV-CC, ADV-OP) that close the unification, plus two optional sidebars (ADV-CE, ADV-UI) that are admitted but unscheduled. The next wave is telemetry (ADV-010 lands the capture mechanism that will populate `metrics.md` for every subsequent adventure) and operator surface (ADV-009 renders adventure state as a scannable UI).

## Projects

### Ark Core (Descriptor / Builder / Controller)

Ark is the declarative DSL + toolchain that describes a system once and drives parsing, verification, codegen, and runtime from that single source of truth. Nine adventures have shipped core subsystems; four more are planned to close the unification, and two sidebars are admitted pending demand.

**Completed (9):**
- **ADV-001** — Expressif-style expression & predication system (`|>` pipes, predicate combinators, stdlib, Z3 verify, Rust codegen).
- **ADV-002** — CodeGraphContext-style code knowledge graph as an Ark island (schemas, queries, MCP surface, reflexive indexing).
- **ADV-003** — Claude-Code-Game-Studios-style studio hierarchy (roles, workflow commands, hooks, rules, templates as DSL items).
- **ADV-004** — Hermes-style agent self-evolution pipeline (DSPy+GEPA, four improvement tiers, fitness-gated deployment).
- **ADV-005** — Hermes-style autonomous agent system (multi-platform messaging, persistent learning, skill generation, execution backends).
- **ADV-006** — Snip-style visual communication layer (diagram rendering, screenshot annotation, MCP, semantic search).
- **ADV-007** — Claudovka ecosystem research & adventure planning (7 phases split into discrete adventures with designs/plans/TCs).
- **ADV-008** — ShapeML-style procedural shape grammar in Ark + semantic rendering (sibling package, Ark-as-host-language dogfooding).
- **ADV-011** — Ark Core Unification (Descriptor / Builder / Controller roles, concept inventory, pruning catalogue, 22/22 TCs pass).

**Planned downstream (4 core + 2 sidebar):**
- **ADV-DU** — Descriptor Unification (grammar, AST, parser convergence).
- **ADV-BC** — Builder Consolidation (codegen, verify, analyze, visualize as one subsystem).
- **ADV-CC** — Controller Cohesion (gateway, scheduler, skill manager, evaluator, self-evolution loop).
- **ADV-OP** — Operator surface / integration across DU+BC+CC.
- **ADV-CE** — Optional sidebar (admitted by ADV-011 pruning catalogue; not scheduled).
- **ADV-UI** — Optional sidebar (admitted; not scheduled).

### Adventure Console UI (ADV-009)

**Status: active, planning stage.** 21 tasks in planning. Delivers a reader-first UI over `.agent/adventure-console/`: custom layouts per document type (Task, Design, Plan), consolidates Designs+Plans+Research+Reviews into a single filterable `Documents` tab, replaces raw frontmatter with status pills, depends-on chains, and target-conditions checklists. Turns the console from a config viewer into a scannable operator surface.

### Pipeline Telemetry (ADV-010)

**Status: review → active (approved, awaiting state flip).** 18 tasks planned (4 task files scaffolded so far). Lands the capture mechanism that will populate `metrics.md` going forward. Today every `metrics.md` across ADV-001..007 reports `total_tokens: 0`, `total_cost: 0.00`, `agent_runs: 0` — only ADV-008 has real numbers (and those were filled after the fact). ADV-010 wires SubagentStop hooks + SDK `usage` fields into live row-append + frontmatter aggregation, validates on ADV-009 as a canary, and plans a backfill pass for ADV-001..ADV-008 from git/log trails.

### Optional Sidebars (ADV-CE / ADV-UI)

Admitted by ADV-011's pruning catalogue as forward-references from the unification design, but not scheduled. Will be revisited after the ADV-DU→BC→CC→OP chain lands and real demand is measurable. These are not on the critical path to core unification.

## Strategic Goals

1. **Unified Ark core** — complete the DU→BC→CC→OP downstream chain, then decide on CE/UI admission based on real demand.
2. **Zero-rework pipeline** — maintain the 66-task zero-iteration streak observed through ADV-011; promote the patterns captured in `.agent/knowledge/patterns.md`.
3. **Full telemetry** — land ADV-010 so every future adventure populates `metrics.md` automatically; backfill ADV-001..007 from git/log trails.
4. **Operator surface** — land ADV-009 so adventure state is readable at a glance without frontmatter parsing.

## Dependency Map

```
ADV-011 (completed, Ark Core Unification) - unblocks - ADV-DU -> ADV-BC -> ADV-CC -> ADV-OP
                                                                                        |
                                                      ADV-CE (admitted, no schedule) <--/
                                                      ADV-UI (admitted, no schedule)

ADV-010 (review -> active) - unblocks - live telemetry for every subsequent adventure
                                       - backfills ADV-001..ADV-008
                                       - ADV-009 consumes telemetry for rendering

ADV-009 (active, planning stage) - renders - every adventure's state via the console
```

## Session Notes

- **2026-04-15** — ADV-011 closed; 22/22 TCs pass (confirmed in `adventure.log`: run-all.sh exit 0, unittest discover 4/4). 7 knowledge suggestions applied. Downstream roadmap (4+2) confirmed. ADV-010 approved, moving review→active. ADV-009 dispatching task planners. Honest count note: `passed_tcs: 50` is a lower bound — only ADV-008 (28/28 `passed` written in manifest) and ADV-011 (22/22 confirmed in log) have recorded pass status. ADV-001/004/005/006/007 completed successfully but their manifest TC tables were never updated from `pending` — a retro-backfill is tracked under the telemetry adventure.
