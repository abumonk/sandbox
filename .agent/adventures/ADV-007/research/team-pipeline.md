---
project: team-pipeline
version: 0.14.3
source: C:/Users/borod/.claude/plugins/cache/claudovka-marketplace/team-pipeline/0.14.3/
research_task: ADV007-T002
researched: 2026-04-14
license: MIT
upstream: https://github.com/abumonk/team-pipeline.git
---

# Team Pipeline Research

The `team-pipeline` plugin is a Claude Code plugin that turns a working directory
into a multi-agent task processing pipeline. Tasks are markdown files with YAML
frontmatter; agents (subagents spawned via the `Task` tool) move them through a
6-stage lifecycle (planning -> implementing -> reviewing -> fixing -> completed
-> researching). On top of that base pipeline, two additional pipeline types are
layered: the **adventure** pipeline (multi-task feature work with manifests,
target conditions, evaluations, permissions, custom roles) and the **step2step**
pipeline (document-only, theme-driven decision review with cascade tracking).
The plugin ships ~15 agents, ~25 skills, 4 commands, a hooks system, a roles
template directory, a JSON-Schema-style `schema/` folder, and a small
JavaScript DSL (PDSL) for visualizing pipelines as SVG.

## 1. Core Concepts and Entities

### Task
A markdown file under `.agent/tasks/{TASK-NNN}.md` (or
`.agent/adventures/{ADV-NNN}/tasks/{ADVnnn-Tnnn}.md`). Frontmatter carries
`id`, `stage`, `status`, `iterations`, `assignee`, `files`, `tags`,
`adventure_id?`, `depends_on?`. Body has `## Description`, `## Acceptance
Criteria`, `## Design`, `## Log`. The 6 stages plus a `BLOCKED` terminal
appear in the README diagram. Status flow inside a stage:
`in_progress -> ready -> passed/failed`.

### Adventure
A multi-task feature, located at `.agent/adventures/ADV-NNN/`. The directory
holds `manifest.md`, `designs/`, `plans/`, `schemas/`, `tasks/`,
`permissions.md`, `roles/`, `tests/`, `metrics.md`, `adventure.log`,
`reviews/`. Adventure states: `concept -> planning -> review -> active ->
reviewing -> completed`, with `cancelled` / `blocked` as off-ramps. Adventures
introduce four artefacts the base pipeline does not have: target conditions
(TC-NNN, with `proof_method` of `autotest|poc|manual`), evaluations table
(estimated vs actual tokens/duration/cost per task), exhaustive permission
analysis (4-pass strategy aimed at zero runtime prompts), and per-adventure
custom roles in `.agent/adventures/ADV-NNN/roles/`.

### Step (step2step)
A document-only review unit under `.agent/step2step/S2S-NNN/steps/step-NNN.md`.
Each step has `depends_on` and `cascade_to` arrays; statuses are `pending ->
analyzed -> decided -> cascaded` with extra `modified|replaced|cascade_pending`
markers used by the cascade tracker. Step2step instances are theme-anchored
(not feature-anchored) and produce an adventure as their final output via
`/start-adventure`.

### Cascade
A record at `cascades/cascade-NNN.md` produced by the `cascade-tracker` agent.
It documents, for one trigger step that was modified or replaced, the
downstream steps reachable through `cascade_to`/`depends_on` edges (DFS, max
depth 5, cycle-detected). Each affected step gets a severity (low/medium/high)
and a proposed textual fix.

### Knowledge / Memory
Two complementary stores: shared `.agent/knowledge/{patterns,issues,decisions}.md`
written by the researcher after every task, and per-role
`.agent/agent-memory/<role>/MEMORY.md` (first 200 lines auto-injected by the
lead) plus on-demand topic files curated by each role.

## 2. Architecture Overview

### Agents (`agents/*.md`)
14 agents, each a markdown file with YAML frontmatter declaring `name`, `tools`,
`disallowedTools`, `model` (`opus|sonnet|haiku`), `maxTurns`, `memory`. Core
six: `planner` (opus, no Bash), `implementer` (sonnet, full toolset),
`reviewer` (sonnet, no Write/Edit), `researcher` (opus), plus the adventure
quartet `adventure-planner`, `adventure-preparer`, `adventure-reviewer`,
`adventure-task-reviewer`, `adventure-reporter`, `knowledge-extractor`, and
the step2step quartet `step-generator`, `step-analyzer`, `cascade-tracker`,
`proof-reviewer`. Agents log every step to `.agent/adventures/{id}/adventure.log`
(append-only) and write metrics rows.

### Skills (`skills/*/SKILL.md`)
~25 SKILL.md files, each invoked by a slash command. Notable ones:
`task-init`/`reinit` (schema-driven `.agent/` upgrades), `task-create`,
`task-status`, `task-migrate`, `start-adventure`, `adventure-status`,
`adventure-review`, `dashboard`, `simplify`, `batch`, `debug-pipeline`,
`step2step-{start,analyze,cascade,prove,status}`, `team-update`,
`init-roles`, `init-skills`, `learn`, `roadmap`, `roadmap-init`. Skills v2
adds optional frontmatter fields (`context: inline|fork`, `agent`, `model`,
`allowed-tools`).

### Commands (`commands/*.md`)
Only four thin dispatcher commands: `task.md`, `step2step.md`, `learn.md`,
`wrapup.md`. The `/task` command is a giant inline state machine that handles
create / status / advance / complete / cancel / migrate / lead — much of the
real orchestration logic lives here as natural-language dispatch rules rather
than code.

### Hooks (`hooks/hooks.json`)
Three Claude Code hooks (`SubagentStop`, `UserPromptSubmit`, `Stop`) defined
as **prompts**, not shell commands. Each hook prompt is several thousand words
of inline procedural instructions for a sonnet/haiku model. The
`SubagentStop` prompt alone embeds: MCP-tool-availability detection,
fallback file I/O, metrics computation, git proposal logic, adventure state
machine, target-condition table updates, pending-questions plumbing, and
user-approval gating.

### Roles (`roles/templates/*.md`)
15 user-facing role templates (lead, planner, implementer, coder, reviewer,
code-reviewer, qa-tester, designer, devops, ux-designer, researcher,
messenger, adventure-planner, adventure-preparer, pr-template) copied into
`.agent/roles/` by `task-init`. Adventure-planner customizes role files
per-adventure into `.agent/adventures/{id}/roles/`.

### DSL (`dsl/`)
A standalone Node.js library — PDSL — implementing tokenizer, parser, AST
validator, layout engine, SVG renderer, CLI (render/validate/format), browser
viewer, and a Node `--test` test suite. Supports `lifecycle`, `structure`,
`entity`, `relation` blocks. It is shipped but not wired into the runtime
pipeline; an example `*.pdsl` of the actual pipeline lives in `dsl/examples/`.

### Schema (`schema/`)
Three markdown schemas: `agent-schema.md`, `hooks-schema.md`,
`step2step-schema.md`. Schema files describe what `reinit` should sync into
target projects.

## 3. Integration Points with Other Claudovka Projects

- **`.claude/skills/` discovery** — Plugin auto-discovery requires
  `.claude-plugin/plugin.json` (not present in this version dir). Skills are
  individually addressable as `team-pipeline:<skill-name>`.
- **MCP gateway** — Hooks optionally call `pipeline.task_get`,
  `pipeline.task_advance`, `pipeline.metrics_log`, `pipeline.adventure_log`,
  `pipeline.adventure_metrics`, `pipeline.config_get`, `pipeline.status`
  with an explicit fallback to direct file I/O. This is the natural seam for
  the Claudovka **MCP server** (project mentioned in the roadmap docs at
  `docs/concepts/mcp-server.md`) to plug in.
- **Messenger** — `.agent/messenger.md` is the channel registry; hooks
  reference it but do not implement it. A separate `messenger` project would
  consume those notify actions.
- **Visualizer / Studio** — The PDSL DSL produces SVG. Ark's own
  `tools/visualizer/` and the `ark_studio.html` artifact in this repo could
  consume PDSL output; conversely, PDSL could be replaced by Ark's `.ark`
  spec language.
- **Roles / skills bootstrap** — `init-roles`, `init-skills`, and `learn`
  are explicit roadmap items meant to integrate per-project automation
  (likely the Claudovka **roles** and **learn** sub-projects).

## 4. Opportunities for Improvement

1. **Replace hook-prompt scripts with code or Ark specs.** The
   `hooks/hooks.json` `SubagentStop` prompt is ~6 KB of imperative procedure
   given to a sonnet-class model on every agent stop. It is brittle, hard to
   diff, hard to test, and mixes concerns (metrics, git, adventure state, MCP
   detection). A typed orchestrator (Ark spec or TypeScript service) would
   give deterministic behavior and unit tests.
2. **Wire PDSL to the runtime, not just the viewer.** The DSL already encodes
   lifecycle/structure/entity. The runtime currently reimplements the same
   data model in agent prompts. A single source of truth would prevent drift
   between hook prompts, agent prompts, and the DSL spec.
3. **Schema validation for `.agent/`.** `schema/*.md` is human-readable
   prose. A machine-checkable schema (JSON Schema or Ark) would let `reinit`
   detect drift without the agent rereading prose every time.
4. **MCP-first instead of MCP-optional.** Every hook duplicates the same MCP
   try-fallback pattern. A thin shim that always presents the MCP API and
   falls back internally would shrink hook prompts dramatically.
5. **Adventure plan templates.** The adventure-planner runs 9 phases for
   every adventure; small adventures pay the same ceremony cost as large
   ones. A "lite" adventure mode (skip permissions analysis, skip custom
   roles) for ≤3-task adventures would reduce overhead.

## Issues

- **High — Pipeline orchestration encoded in hook prompts.** `hooks.json`
  embeds many KB of natural-language state-machine logic interpreted by an
  LLM at every event. Non-deterministic, untestable, expensive on tokens,
  drifts from agent prompts that re-state the same rules. Tested behavior is
  whatever sonnet decides on a given run.
- **High — Cross-pipeline state spread across many files.** Adventure state
  lives in `manifest.md`, target-condition rows, evaluations table,
  `permissions.md`, `roles/`, `tasks/`, `adventure.log`, `metrics.md`,
  `reviews/`. There is no transactional update — partial-writes by a crashed
  agent leave the adventure in inconsistent states the lead must rediscover
  on `SessionStart`.
- **High — Skill/command/agent count is large and mostly bespoke.** ~25
  skills, ~14 agents, multiple pipeline types. The README warns about
  "Unknown skill" failures and tells the lead to "not spend extended time
  diagnosing." Onboarding cost is high.
- **Medium — Two parallel pipeline types (task vs step2step) duplicate
  concepts.** Both have stages, agents, manifests, logs, metrics; both feed
  adventures. Concept `step2step.md` even lists "Pause and resume" as an
  open question — basic lifecycle behavior is unsettled.
- **Medium — Permission analysis claims "zero runtime permission prompts"
  but is enforced only by lead prompt.** The 4-pass permission analysis is
  scrubbed by the planner; nothing at runtime actually blocks an agent from
  doing something not in `permissions.md`.
- **Medium — Reviewer logs via `bash echo` because it lacks Write tool.**
  The reviewer is intentionally read-only, but workaround `echo … >> file`
  on Windows quoting is fragile. A dedicated `pipeline.adventure_log` MCP
  call solves it but the agent still has to know which path to use.
- **Medium — DSL ships unused.** The `dsl/` library is fully tested and
  documented but is not consumed by the runtime; risk of bit-rot.
- **Medium — Token estimation in hooks is `turns * 1500` / `turns * 500`.**
  The hook prompt explicitly admits these are estimates. All variance
  calculations and cost rollups are built on this rough proxy.
- **Low — `CLAUDE.md` lists conflicting command names.** Lists
  `/task-status`, `/task-create` as the valid forms while `commands/task.md`
  defines `/task status`, `/task create`. This is the source of "Unknown
  skill" complaints.
- **Low — `agent-memory/` and `knowledge/` overlap.** Both store learnings;
  rules to choose between them are documented but agents must judge.
- **Low — Hard-coded depth 5 for cascade tracking.** Reasonable default but
  not configurable in `.agent/config.md`.
- **Low — Plugin install layout assumes versioned cache dirs (`0.14.3/`)
  side-by-side.** No mechanism described for selecting which version is
  active per project.

## Recommendations

1. **Adopt one orchestrator.** Move the `SubagentStop` hook logic into the
   Claudovka MCP server (or an Ark-generated state machine in this repo's
   `ark/` codebase). Keep the hook as a thin trigger that calls
   `pipeline.on_subagent_stop`. Cuts hook tokens, makes flow testable,
   removes prompt drift.
2. **Generate role/agent/hook prompts from a single Ark spec.** This repo
   already has `ark/specs/meta/` and `ark/tools/codegen/` — emit the agent
   markdown, hook prompts, and PDSL diagrams from one source. The team's
   commit history shows movement in this direction (`team-pipeline-*`
   directives, `ark-orchestrator` crate).
3. **Strict adventure state — append-only event log + materialized view.**
   Replace scattered field updates with `adventure.events.jsonl`; rebuild
   manifest/evaluations/TC tables from events. Crash-recovery becomes
   deterministic.
4. **Lite adventure profile for ≤3 tasks.** Skip permission analysis, skip
   custom roles, skip evaluations. Drive selection from
   `.agent/config.md` thresholds.
5. **Promote PDSL or replace with `.ark`.** Either wire PDSL into runtime
   validation (validate `manifest.md` against an `entity Adventure` block
   on every `reinit`), or migrate the spec to Ark and delete the JS DSL.
6. **Unify `agent-memory/` writeback rules.** The researcher should be
   allowed to update role memory (the design currently forbids this);
   alternatively, drop role memory and centralize in `knowledge/` keyed by
   role.
7. **Reconcile command naming.** Resolve `/task create` vs `/task-create`
   in `commands/task.md` and `CLAUDE.md`; update `.claude/settings.json`
   examples in docs.
8. **Add an active-version pin.** A `team-pipeline.toml` or
   `.claude-plugin/active.json` declaring which `0.14.x` cache subdir the
   project uses.
9. **Replace `turns * 1500` token estimate with a real counter via MCP**
   so cost/variance numbers in evaluations are trustworthy.
10. **Automated end-to-end smoke test.** A scripted `task-init -> create
    task -> advance through all stages` run as part of CI would catch
    "Unknown skill" regressions quickly.

## Strengths to Preserve

- **Markdown-first state.** Tasks, designs, plans, manifests, knowledge,
  even hooks live in markdown. Diff-friendly, version-controllable, no
  database. This is the right substrate for an agent pipeline.
- **Append-only `adventure.log`.** Single chronological audit trail per
  adventure, with rules forbidding agents from reading it back. Excellent
  for debugging and metrics.
- **Explicit per-agent `tools` / `disallowedTools`.** Capability scoping by
  role is a clean security model and matches Claude Code's subagent model.
- **"Full authority, zero autonomy" lead principle.** Lead proposes,
  user approves. Avoids runaway automation.
- **Schema-driven `reinit`.** Lets the plugin evolve without breaking
  initialized projects; deep-merges only missing fields.
- **Target conditions with proof methods.** Forces every requirement to
  carry a runnable proof; great for verifiability.
- **Custom per-adventure roles.** Trims default role prompts down to the
  adventure's actual tech stack — reduces token cost per agent spawn.
