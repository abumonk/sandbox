---
id: ADV-003
title: Claude-Code-Game-Studios-style Studio Hierarchy in Ark DSL
state: completed
created: 2026-04-11T00:00:00Z
updated: 2026-04-11T00:00:00Z
tasks: [ADV003-T001, ADV003-T002, ADV003-T003, ADV003-T004, ADV003-T005, ADV003-T006, ADV003-T007, ADV003-T008, ADV003-T009, ADV003-T010, ADV003-T011, ADV003-T012, ADV003-T013, ADV003-T014]
depends_on: [ADV-002]
---

## Concept

Review the Claude Code Game Studios project (https://github.com/Donchitos/Claude-Code-Game-Studios) — a Claude Code configuration that turns a single session into a structured game studio with specialised agents, commands, hooks, rules, and templates — and define/implement an Ark-native equivalent.

### What Claude-Code-Game-Studios provides

- **Purpose**: transform Claude Code into a structured game-dev environment with **49 specialised agents** organised into a studio hierarchy, with defined roles, responsibilities, and escalation paths. Humans retain decision authority; agents provide expertise and structure.
- **Three-tier hierarchy**:
  - **Tier 1 — Directors**: Creative Director, Technical Director, Producer (vision, cross-domain coordination).
  - **Tier 2 — Leads**: Game Designer, Lead Programmer, Art Director, Audio / Narrative / QA Leads, Release Manager.
  - **Tier 3 — Specialists**: Gameplay / Engine / AI / Network / Tools programmers; Systems / Level / Economy designers; Technical Artist, Sound Designer, Writer, UX Designer, …
- **72 slash commands** organised by workflow phase: `/start`, `/brainstorm`, `/design-system`, `/create-epics`, `/dev-story`, `/code-review`, `/qa-plan`, `/release-checklist`, `/team-combat` (multi-agent orchestration).
- **12 automated hooks**: commit/push validation, asset-naming enforcement, session-lifecycle tracking, agent audit trails, gap detection.
- **11 path-scoped rules** by directory: gameplay code must be data-driven, core engine zero-alloc, AI performance budgets, network server-authority, UI no-game-state, design docs with required sections.
- **39 document templates**: GDDs, UX specs, ADRs, sprint plans, accessibility guides.
- **Engine support**: Godot 4, Unity (DOTS/ECS), Unreal Engine 5 with domain sub-specialists.
- **Workflow model**: agents present options with pros/cons and wait for approval — verification-driven, uses frameworks like MDA, Self-Determination Theory, Flow State Design.

### Goal in Ark

Define and implement a **studio-organisation system as a first-class Ark construct**, so that Ark's own agent orchestration (the existing `orchestrator/` + `.agent/` subsystem) gains a declarative, .ark-described studio hierarchy with roles, commands, hooks, rules, and templates — all auditable through the same parse/verify/codegen pipeline as everything else in Ark.

Concretely:

- **DSL surface** — introduce new Ark items (or reuse `abstraction`/`class`/`island`) to describe:
  - `role` — a specialist definition with tier, responsibilities, escalation target, required skills, and allowed tools (`Read`, `Write`, `Bash`, etc.).
  - `studio` — an island grouping roles into tiers; declares reporting graph and cross-role contracts.
  - `workflow_command` — a named slash-command binding: phase → prompt → required role → output schema.
  - `hook` — event-driven rule (already present in `.agent/hooks.md` informally; formalise in DSL).
  - `rule` — path-scoped policy (glob + constraint + severity).
  - `template` — document skeleton with required sections, bound to a role.
- **Schema** — Ark `struct`s for `Role`, `Tier`, `EscalationPath`, `WorkflowPhase`, `Command`, `Hook`, `PathRule`, `Template`, `Skill`, `Tool`; stdlib file `dsl/stdlib/studio.ark`.
- **Seed studio** — author `specs/meta/ark_studio.ark` describing the actual Ark development team (lead, planner, implementer, reviewer, researcher, etc. — the roles already present under `.agent/roles/` and `C:/Users/borod/.claude/plugins/.../team-pipeline/`) as a three-tier studio in Ark DSL. This is the **reflexive first use-case**: Ark describes its own development team declaratively.
- **Game-studio exemplar** — author `specs/meta/game_studio.ark` that ports the upstream 49-role hierarchy (Directors → Leads → Specialists), 72 commands, 12 hooks, 11 rules, 39 templates, as a full Ark instance. This is the **imported use-case**.
- **Codegen** — generate:
  - Claude Code subagent definitions (`.claude/agents/*.md`) from `role` items.
  - Slash-command files (`.claude/commands/*.md`) from `workflow_command` items.
  - Hook configuration (`settings.json` fragments) from `hook` items.
  - Template skeletons from `template` items.
  - A pipeline-task manifest from `studio` that the existing `orchestrator/` can execute.
- **Verification** — Z3 checks:
  - Every escalation path terminates (no cycles, every chain ends at a Director).
  - Every `workflow_command` resolves to an existing role and tool set.
  - Every `hook` event is in the allowed set.
  - Every path-scoped `rule`'s glob is well-formed and its constraint is satisfiable.
  - No role declares a tool it does not have permission to use (cross-check with `permissions.md`).
- **Visualisation** — extend the Ark visualiser to render the studio org-chart LOD alongside existing entity/bridge graphs.

### Why this matters

Ark already has an orchestrator, a `.agent/` pipeline, and a team of subagents (planner, implementer, reviewer, researcher, …). Today those are defined **imperatively** in Markdown and JSON scattered under `.claude/` and `.agent/`. Porting the Game Studios model into Ark gives the same workflow a **declarative, verifiable, codegen-backed** representation: one `studio.ark` file becomes the single source of truth for roles, commands, hooks, and rules — and Ark's own Z3 verifier can prove that the hierarchy is sound, that no command is orphaned, and that every tool grant has a policy justification. The upstream game-studio serves as the exemplar that forces the DSL to be expressive enough for a real, 49-role hierarchy.

## Target Conditions
| ID | Description | Source | Design | Plan | Task(s) | Proof Method | Proof Command | Status |
|----|-------------|--------|--------|------|---------|-------------|---------------|--------|

## Evaluations
| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |
|------|-------------------|-----------|---------------|-------------|-----------|-----------------|---------------|-------------|----------|

## Environment
- **Project**: ARK (Architecture Kernel) — declarative MMO game-engine DSL
- **Workspace**: R:/Sandbox (Ark tree at R:/Sandbox/ark)
- **Repo**: local (no git remote)
- **Branch**: local (not a git repo)
- **PC**: TTT
- **Platform**: Windows 11 Pro 10.0.26200
- **Runtime**: Node v24.12.0 (project runtime: Python 3 + Rust/Cargo)
- **Shell**: bash
