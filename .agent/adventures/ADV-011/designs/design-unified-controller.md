# Unified Controller — Design

## Overview

Specifies the unified runtime surface: one gateway, one skill manager, one
scheduler, one evaluator, one self-evolution loop, one telemetry capture
(merged from ADV-010). The controller executes a built system, observes it,
and feeds observations back into the evolution loop.

## Target Files

- `.agent/adventures/ADV-011/designs/design-unified-controller.md` (this file)
- `.agent/adventures/ADV-011/research/controller-delta.md` — per-module delta:
  which `tools/agent/*`, `tools/evolution/*`, `tools/visual/review_loop.py`,
  `.agent/telemetry/*` modules merge, rename, or remain. NEW.

## Approach

### 1. Runtime spine — AgentRunner as orchestrator

ADV-005 established `AgentRunner` as the top-level orchestrator with dependency
injection over gateway, skill_manager, learning, backend, scheduler. This
pattern becomes the controller spine. The unified design:

- One `Controller` dataclass that owns the injected subsystems.
- Skill-first routing (from ADV-005 decision) remains the dispatch rule.
- No parallel orchestrator for evolution — the evolution loop (from ADV-004)
  runs as a scheduler-driven task inside the controller, not a separate
  runtime.

### 2. Subsystem inventory

**Gateway** (ADV-005): multi-platform message ingress. Unified target: single
`gateway.py` with platform adapters as plugins (terminal + docker in v1;
telegram/discord/slack deferred to a downstream adventure).

**Skill manager** (ADV-005 + ADV-003 + ADV-004): CRUD, trigger matching,
improvement loop. Canonical `Skill` struct comes from descriptor dedup row 6.
Skill generation (ADV-005) and skill evolution (ADV-004) are two *methods* on
the same manager, not separate runtimes.

**Scheduler** (ADV-005 cron + ADV-004 optimizer as scheduled task): one
`Scheduler` owning cron entries; evolution runs register as entries.

**Evaluator** (ADV-004 fitness + constraint_checker + benchmark_gate): single
`Evaluator` with the LLM-as-judge callback pattern (from ADV-004 decision).
Fitness + constraint checks compose as a pipeline, not separate services.

**Evolution loop** (ADV-004 evolution_runner): retained as an
`EvolutionRunner` driven by the scheduler, consuming descriptor
`evolution_target` / `eval_dataset` / `optimizer` items.

**Telemetry capture** (ADV-010): merge `.agent/telemetry/capture.py` +
`cost_model.py` + `aggregator.py` + `task_actuals.py` into the controller's
observation surface. The hook integration (`SubagentStop` / `PostToolUse`)
stays as the ingress trigger.

**Visual review loop** (ADV-006 `review_loop.py`): retained as a controller
subsystem that blocks on human feedback and resumes the scheduler. The
UI-adjacent pieces (mermaid render, screenshot manager) are *renderers* called
by the review loop, not controllers themselves.

### 3. Event model

Single event bus with a small set of event kinds:

- `subagent.started`, `subagent.stopped` — from ADV-010 hooks.
- `task.completed`, `task.failed` — from pipeline.
- `skill.triggered`, `skill.generated`, `skill.improved` — from skill manager.
- `evolution.started`, `evolution.converged` — from evolution runner.
- `review.requested`, `review.completed` — from visual review loop.

Every event carries: `{adventure_id, task_id?, agent, ts, payload}`. The
telemetry capturer is one subscriber; the scheduler is another; backfill tools
consume the event log.

### 4. State model

Three state surfaces:

- **Persistent memory** (ADV-005 learning): session memory, generated skills.
- **Metrics rows** (ADV-010): `metrics.md` per adventure, append-only.
- **Adventure log** (`adventure.log`): append-only, one line per step.

The controller design commits to append-only jsonl for event log (ADV007-T008
pattern "Append-only jsonl for multi-writer state"), with regenerable rendered
views for markdown consumers.

### 5. Reflexive dogfooding as validation

Per pattern from ADV-002/004/005/008: the controller's first real consumer is
Ark's own pipeline. Any controller subsystem should be validated by running it
over Ark itself (e.g. evolution loop runs over `.agent/roles/*`, scheduler
drives adventure tasks). This is a *validation practice* documented here, not
a separate subsystem.

### 6. Boundary with descriptor and builder

Controller reads builder outputs (generated code, verified AST) and
descriptor (schemas for event payloads, skill struct). Controller never
modifies descriptor or builder.

## Dependencies

- `design-unified-descriptor.md` (schema imports for event payloads + skill)
- `design-unified-builder.md` (consumes built artefacts)
- `design-deduplication-matrix.md` (dedup rows assigned to controller)
- ADV-010 designs and schemas (telemetry capture, cost model, aggregation)

## Target Conditions

- This design enumerates at least the 7 subsystems above with a source
  citation to ADV-004/005/006/010 for each.
- `controller-delta.md` classifies every current controller-adjacent module
  with `KEEP | MERGE | RETIRE`.
- Every dedup row with `assigned_bucket = controller` is cited here.
- Telemetry capture (ADV-010) is explicitly merged into the controller spine,
  not kept as a sibling.
