---
task_id: ADV007-T011
adventure_id: ADV-007
target_conditions: [TC-009]
generated: 2026-04-14
scope: Effectiveness review of the 7 active pipeline roles plus the 5 adventure-lifecycle roles invoked across ADV-001 through ADV-006
sources:
  - .agent/roles/{lead,messenger,planner,coder,code-reviewer,researcher,qa-tester}.md
  - .agent/config.md (active_roles, stage_assignments)
  - .agent/adventures/ADV-001..ADV-006/adventure.log
  - .agent/adventures/ADV-007/research/pipeline-management-review.md (T009 retrospective)
  - C:/Users/borod/.claude/plugins/cache/.../team-pipeline/0.11.0/{roles/templates,agents}/ (source templates)
---

# Role Effectiveness Review (Phase 3.1)

## 1. Scope and Method

This review evaluates the **7 declared active roles** in `.agent/config.md`
(`lead`, `messenger`, `planner`, `coder`, `code-reviewer`, `researcher`, `qa-tester`)
and the **5 adventure-lifecycle agents** that actually performed work across
ADV-001 through ADV-006 (`adventure-planner`, `adventure-preparer`,
`adventure-task-reviewer`, `adventure-reviewer`, `knowledge-extractor`,
plus one alias: `implementer` is the role-name used in adventure spawn logs
where `coder` is the declared role).

Method: read every role definition in `.agent/roles/`; cross-reference against
all `spawn:` events in adventure logs (262 events across six adventures);
correlate observed problems with the T009 retrospective (`pipeline-management-review.md`).

### Spawn frequency across ADV-001..ADV-006

| Role spawned                  | Count | Declared in active_roles? |
|-------------------------------|------:|---------------------------|
| implementer                   |    92 | yes (as `coder`, name mismatch) |
| adventure-task-reviewer       |    13 | no  (not declared)        |
| researcher                    |    12 | yes                       |
| planner                       |     6 | yes                       |
| adventure-reviewer            |     6 | no  (not declared)        |
| adventure-planner             |     6 | no  (not declared)        |
| knowledge-extractor           |     4 | no  (not declared)        |
| code-reviewer                 |     0 | yes                       |
| qa-tester                     |     0 | yes                       |
| messenger                     |     0 | yes                       |
| lead (as spawnable subagent)  |     0 | yes (orchestrator only)   |

Headline finding: **3 of 7 declared roles (qa-tester, code-reviewer, messenger)
have never been spawned in any adventure**, while 5 lifecycle roles that drive
every adventure are not in `active_roles` at all. The declared-vs-actual gap
is the single largest issue.

## 2. Per-Role Inventory

### 2.1 Active roles declared in config.md

| Role | Model | Purpose | Current Output | Observed Problems | Recommendation |
|------|-------|---------|----------------|-------------------|----------------|
| **lead** | sonnet | Pipeline orchestrator: SubagentStop / SessionStart hook agent. Proposes transitions, runs git ops, manages roadmap, injects rules and memory, owns metrics writes. | Proposals to user; updates to lead-state.md; metrics rows; git proposals; roadmap updates. | Massive role definition (~570 lines, ~16 distinct duty sections). Six of these duties (Step2Step Management, Roadmap Maintenance, Adventure Management, MCP Integration, Hook Evaluation, Rules Injection) are conditional features that bloat every spawn. Also: lead is the only writer of metrics totals frontmatter, but per T009 those totals are 0 in every metrics.md inspected — duty exists in spec, never executed. | **Refactor (split)**: extract orchestrator-only duties into includable sub-skills (`skills/lead-roadmap.md`, `skills/lead-step2step.md`, `skills/lead-adventure.md`). Have the lead conditionally load skills based on context (only load roadmap skill when `.agent/roadmap.md` exists, etc.). Cuts prompt size ~60% on routine SubagentStops. Priority: **HIGH**. |
| **messenger** | haiku | Question lifecycle manager: present pending questions, collect answers, apply timeouts. | Updates to `.agent/questions/{pending,ready,archive}.md`. | **Zero spawns across 6 adventures, 122 tasks.** Either no agent has ever asked a question, or the lead never proposes invoking messenger when one exists. The role is well-scoped (~110 lines) but appears to be dead code. The T009 retrospective also notes that all six adventures completed with 0 review iterations, meaning agents either had enough context up front or made unilateral decisions instead of asking. | **Audit before retiring**: search for any `status: blocked_on_question` ever set; if zero, retire messenger and the question subsystem from `active_roles` (keep the files for future use). If any agent did set blocked_on_question, the lead is failing to invoke messenger — fix the lead. Priority: **MEDIUM**. |
| **planner** | opus | Pre-task design: read task, explore code, write `.agent/designs/{task-id}-design.md`, fill task design section, set status: ready. | Design document; updated task frontmatter; questions when stuck. | Used heavily as `planner` per-task in ADV-001 (6 spawns) but **largely supplanted by `adventure-planner`** in ADV-002..ADV-006 where designs are produced once at the adventure level. The role is sound but its niche is shrinking. Some design docs (ADV-005 T001) are produced by the implementer instead, with no ADR for who owns design at the task level. | **Clarify scope**: explicitly state planner handles only one-off / non-adventure tasks, and design responsibility for adventure tasks lies with adventure-planner (with task-level refinements done by the implementer). Add a stage_assignments entry distinguishing `planning_adventure` vs `planning_oneoff`. Priority: **MEDIUM**. |
| **coder** | sonnet | Implement task per design; run lint/build/test; set status: ready. | Source changes; test runs; updated task log. | Spawned 92 times as `implementer` (name drift). Two recurring failures: (1) marks status: ready/done after Bash permission denial when tests cannot run (T009 anti-pattern #1, observed 4+ times in ADV-001); (2) modifies files outside the task's `files` list without logging the addition (rule exists at line 44 of role; not enforced). | **Add a verification gate**: replace the Bash-failure -> "completed pending manual run" path with `status: blocked_on_question` (ask lead for permission) or `status: blocked` with a reason. Also: rename the spawn role to `coder` everywhere or add `implementer` as a documented alias. Priority: **HIGH**. |
| **code-reviewer** | opus | Run lint/build/test; check ACs; emit structured review report between markers. | Review report; task status passed/failed. | **Zero spawns across 6 adventures.** Replaced in practice by `adventure-task-reviewer`, which has a different output contract (markdown file in `reviews/`, not REVIEW-START/END markers) and a different failure mode (it produced 9 spurious FAILEDs in ADV-001 from a cwd error — a problem the code-reviewer role does not have because it specifies "Read all files listed in the task's `files` frontmatter" — explicit absolute paths, no cwd dependence). | **Reconcile with adventure-task-reviewer**: either retire code-reviewer (and document adventure-task-reviewer as the canonical reviewer) or merge adventure-task-reviewer's adventure-aware features back into code-reviewer and retire the adventure variant. Priority: **HIGH** (the divergence caused a real production incident). |
| **researcher** | opus | Post-completion learning extraction; updates patterns/issues/decisions; for adventure tasks also updates evaluation variance and adventure metrics. | Knowledge-base appends; adventure manifest evaluation rows; adventure.log + metrics rows. | Spawned 12 times across adventures with reliable behavior. Memory section is well-developed. The role is implicitly **two roles fused**: per-task knowledge extraction and per-adventure metrics aggregation. The latter is invoked per-task but only meaningful for the *last* task of an adventure (and only the `knowledge-extractor` actually batches across adventures). Also: this very role definition lacks the `disallowedTools: [Task]` line that all other non-orchestrator roles carry — minor permission hygiene issue. | **Split into `task-researcher` + `adventure-knowledge-extractor`** (the latter already exists as a separate spawn — formalize). Add `disallowedTools: [Task]`. Priority: **LOW**. |
| **qa-tester** | sonnet | Coverage-focused review: write missing tests, run full suite, check coverage thresholds. | New test files; coverage report; task status passed/failed. | **Zero spawns across 6 adventures.** Stage assignment for `reviewing` is `code-reviewer` (singular), with no fan-out to qa-tester. The role is well-specified but never selected. T009 weak-spot row 8 ("review depth varies") is partly a consequence: when code-reviewer collapses to "Implementation complete: PASS" there is no second-opinion qa-tester to catch coverage gaps. | **Wire into the pipeline**: change `stage_assignments.reviewing` to a list `[code-reviewer, qa-tester]` so both run in parallel, OR add a `coverage_gate` hook that triggers qa-tester only when `coverage_threshold` is configured. Without one of these, retire qa-tester. Priority: **HIGH**. |

### 2.2 Adventure-lifecycle roles (used heavily, NOT in active_roles)

| Role | Model | Purpose | Current Output | Observed Problems | Recommendation |
|------|-------|---------|----------------|-------------------|----------------|
| **adventure-planner** | opus | One-shot adventure decomposition: produce manifest, designs, plans, task list, custom roles, evaluations table. | `manifest.md`, `designs/*.md`, `plans/*.md`, `tasks/*.md`, optionally `roles/*.md`. | Single most expensive run in the pipeline (~$1.70 average). Generates "custom roles" inconsistently — ADV-001 generated 3 roles (coder, qa-tester, planner) that duplicate the global ones; ADV-007 generated planner + researcher only. No clear contract for when to override vs reuse. Manifest population is unreliable: ADV-002 shipped with `tasks: []`, ADV-003 with no TC table (T009 medium-severity #3 and #4). | **Add a manifest-validation gate** (refuse to complete with empty `tasks` or empty TC table). **Define an override policy** ("only emit `.agent/adventures/{id}/roles/{role}.md` if the global role needs an adventure-specific override"). Priority: **HIGH**. |
| **adventure-preparer** | opus | Per-task setup: branch creation, context injection, environment validation. | Updated task frontmatter (status: ready), git branch, prepared env. | Used in ADV-005, ADV-006. Permission pre-flight (T009 weak-spot row 2) is the obvious place for it — but it does not currently run permission validation. | **Expand scope** to include permission pre-flight: emit a permission manifest enumerating shells the implementer will need, fail loudly if missing. Priority: **HIGH**. |
| **adventure-task-reviewer** | opus | Per-task review with adventure context (TC traceability, manifest update). | `reviews/{task-id}-review.md`; updated task status; manifest TC row update. | Caused the ADV-001 false-FAILED batch (9 tasks) by running from wrong cwd (T009 high-severity #1). Output format diverges from `code-reviewer` — there is no machine-readable START/END marker, just a markdown file. Some reviews collapse to "Implementation complete: PASS" with no per-AC verdict (T009 low-severity #8). | **Adopt a working-directory contract** (read `project_root` from `.agent/config.md` or adventure manifest before searching for files). **Standardize output** with the same REVIEW-START/REVIEW-END marker as `code-reviewer` to enable parsing. **Limit batch size to 3** (T009 anti-pattern #5). Priority: **HIGH**. |
| **adventure-reviewer** | opus | End-of-adventure review: TC verification, evaluation variance, completion verdict, generate adventure-report.md. | `adventure-report.md`; updated manifest state; reconciled metrics summary. | Performed reliably across all adventures. Did NOT, however, populate aggregate `total_tokens_in` / `total_cost` frontmatter in `metrics.md` (T009 medium-severity #5; six-for-six). Should be the natural place to compute and write totals. | **Add metrics-aggregation duty**: on adventure completion, compute totals from per-row data and write back to `metrics.md` frontmatter. Priority: **MEDIUM**. |
| **knowledge-extractor** | sonnet | Cross-adventure knowledge synthesis: takes one or more adventure reports, extracts patterns/issues/decisions, updates `.agent/knowledge/*`. | Appended knowledge entries; cross-adventure pattern notes. | Was observed batching ADV-001+ADV-002+ADV-003 in a single spawn. T009 anti-pattern #8 flags this as a single point of failure (collapsed provenance). Otherwise reliable. | **Limit batch to 1 adventure per spawn** OR add a per-adventure checkpoint inside the run. Priority: **LOW**. |

## 3. Gap Analysis

### 3.1 Declared but unused (dead roles)
- `messenger` — 0 spawns. Question subsystem appears to be dead code; either unused infrastructure or invocation is broken.
- `qa-tester` — 0 spawns. Pipeline review is single-track; coverage-gated invocation does not exist.
- `code-reviewer` — 0 spawns inside adventures. Replaced by `adventure-task-reviewer` without an explicit deprecation.

### 3.2 Used but undeclared (shadow roles)
- `adventure-planner`, `adventure-preparer`, `adventure-task-reviewer`, `adventure-reviewer`, `knowledge-extractor` — all spawn frequently, none appear in `active_roles`. The list is silently incomplete and any tooling that reads `active_roles` to know what to load (memory, hooks, rules) is missing 5 of the 12 active roles.

### 3.3 Name drift
- Role file `coder.md` is spawned everywhere as `implementer`. Searching for "coder" in adventure logs returns zero results; searching for "implementer" returns 92. Anyone reading role definitions to understand pipeline behavior must know the alias mapping.

### 3.4 Responsibility overlap (redundancy)
- **planner vs adventure-planner**: both produce design documents. Boundary is implicit (per-task vs per-adventure) and inconsistently honoured.
- **code-reviewer vs adventure-task-reviewer**: both run lint/build/test and check ACs. Output formats differ; only the latter understands TCs.
- **researcher vs adventure-reviewer vs knowledge-extractor**: all three update manifest fields and/or knowledge base. Boundaries: researcher = per-task; adventure-reviewer = per-adventure verdict; knowledge-extractor = cross-adventure patterns. The boundaries are real but undocumented.

### 3.5 Missing roles (not in inventory but warranted by T009 findings)
- **permission-broker** — pre-spawn check that the implementer/reviewer has the Bash permissions it will need (T009 weak-spot row 2; high-severity #2).
- **metrics-aggregator** — fold into adventure-reviewer per recommendation above; or stand alone.
- **regression-ticketer** — when a reviewer notices a pre-existing failure (e.g. ADV-006 vehicle_physics.ark parse fail), no role currently owns ticketing it; the issue is logged in a review report and forgotten (T009 low-severity #9).
- **working-directory enforcer** — could be a hook rather than a role, but the gap is real.

### 3.6 Bloated roles
- `lead` at ~570 lines, ~16 conditional duty sections, single largest prompt in the pipeline. Per-spawn cost is not the issue (the lead is short-running); prompt-clarity-of-purpose is. Recommend splitting into orchestrator-core + includable skills.

## 4. Improvement Recommendations (Prioritized)

### Priority 1 — High-leverage fixes for known production incidents

1. **Reconcile `code-reviewer` and `adventure-task-reviewer`** into a single canonical reviewer role. Adopt the `adventure-task-reviewer` adventure-awareness, but use the `code-reviewer` REVIEW-START/END marker contract and the `code-reviewer` rule "Read all files listed in the task's `files` frontmatter" (which would have prevented the ADV-001 cwd incident). Update `stage_assignments.reviewing`. **Closes**: T009 high-severity #1, weak-spot row 1.
2. **Add a verification gate to `coder`**: when Bash is denied and tests cannot run, set `status: blocked` (not `ready`/`done`). This stops the silent-bypass pattern that landed unverified code in ADV-001. **Closes**: T009 high-severity #2, anti-pattern #1.
3. **Wire `qa-tester` into the pipeline OR retire it**. Either change `stage_assignments.reviewing` to `[code-reviewer, qa-tester]` (both run; coverage gate decides if qa-tester PASS is required) or remove from `active_roles`. The current state — declared but never spawned — is the worst option. **Closes**: T009 weak-spot row 8 (review depth).
4. **Document `adventure-*` and `knowledge-extractor` in `active_roles`**, with adventure-lifecycle stage assignments. The current omission means rules/hooks/memory tooling silently misses 5 of 12 active roles.
5. **Add manifest-validation gate to `adventure-planner`**: refuse to complete with `tasks: []` or empty TC table. **Closes**: T009 medium-severity #3 and #4.

### Priority 2 — Reduce role bloat and name drift

6. **Split the `lead` role** into an orchestrator core (~150 lines) plus 4-6 includable skill files (`lead-skill-roadmap.md`, `lead-skill-step2step.md`, `lead-skill-adventure.md`, `lead-skill-git.md`, `lead-skill-hooks.md`, `lead-skill-mcp.md`). The lead loads only the skills relevant to the current trigger context.
7. **Reconcile name `coder` vs `implementer`**: pick one and update the other location. Recommend renaming `coder.md` to `implementer.md` since 92 spawn sites already use that name and only 1 config entry uses `coder`.
8. **Clarify `planner` vs `adventure-planner` boundary**: add `stage_assignments` entries `planning_adventure: adventure-planner` and `planning_oneoff: planner`, or add a header in each role that names the other and the boundary.

### Priority 3 — Close systematic bookkeeping gaps via role duties

9. **Expand `adventure-preparer` to do permission pre-flight**: emit a manifest of required Bash shells; fail before spawning the implementer if any are missing. **Closes**: T009 weak-spot row 2.
10. **Extend `adventure-reviewer` to aggregate metrics**: on adventure completion compute and write totals back to `metrics.md` frontmatter. **Closes**: T009 medium-severity #5, anti-pattern #3.
11. **Limit `adventure-task-reviewer` to 3 tasks per spawn** to limit blast radius from environmental errors. **Closes**: T009 anti-pattern #5.
12. **Limit `knowledge-extractor` to 1 adventure per spawn** (or add per-adventure checkpoints). **Closes**: T009 anti-pattern #8.

### Priority 4 — Hygiene

13. **Add `disallowedTools: [Task]`** to the `researcher` role for parity with other non-orchestrator roles.
14. **Audit `messenger` invocation path**: confirm zero `blocked_on_question` ever set across 6 adventures; if confirmed, retire messenger and the questions/ subsystem from `active_roles` (keep files for future use). If any agent did ask a question and the lead failed to invoke messenger, fix the lead's question-detection logic.
15. **Add a `regression-ticketer` micro-role or hook** so that pre-existing failures spotted during review are surfaced as new tasks rather than lost in review reports.

## 5. Effort and Sequencing Note

Items 1, 2, 3, 4, 5 (P1) are the highest-value cluster — they each address a real production incident or bookkeeping gap and most are role-definition edits plus one config edit. Estimated effort: ~1 implementer-day total.

Items 6 (lead split) and 7 (rename) are larger touches but still bounded; lead split is best done as its own ADV given the file-count change.

Items 9-12 are the natural payload for the upcoming Phase 3.1 "self-healing skills" task (T010) and the deferred profiling work, since they all involve the lifecycle agents that own bookkeeping.

## 6. Cross-Reference with T009 and Knowledge Base

| T009 finding | Role recommendation here |
|---|---|
| High #1 — reviewer wrong cwd | P1.1 (canonical reviewer with explicit `files` reads) |
| High #2 — Bash permission block | P1.2 (coder verification gate); P3.9 (preparer permission pre-flight) |
| Medium #3 — empty `tasks: []` | P1.5 (adventure-planner manifest gate) |
| Medium #4 — empty TC table | P1.5 (same) |
| Medium #5 — metrics rows missing | P3.10 (adventure-reviewer aggregation) |
| Medium #6 — timestamp placeholders | not directly addressed by role changes; needs shared util (out of scope here) |
| Low #7 — status vocabulary drift | partly addressed by canonical reviewer (P1.1); fully needs schema enforcement |
| Low #8 — review depth varies | P1.3 (wire qa-tester) + P1.1 (canonical contract) |
| Low #9 — pre-existing failure carried over | P4.15 (regression-ticketer) |
| Anti-pattern #5 — large review batches | P3.11 (limit reviewer batch to 3) |
| Anti-pattern #8 — knowledge-extractor batching | P3.12 (limit extractor batch to 1) |

Every high- and medium-severity finding from T009 maps to at least one P1 or P3 role recommendation here. Low-severity items #6 (timestamps) requires a shared helper rather than a role change and is therefore out of scope for this review.

End of report.
