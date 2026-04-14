---
task_id: ADV007-T009
adventure_id: ADV-007
generated: 2026-04-14
scope: ADV-001 through ADV-006 retrospective on pipeline management
sources:
  - .agent/adventures/ADV-001..ADV-006/manifest.md
  - .agent/adventures/ADV-001..ADV-006/adventure.log
  - .agent/adventures/ADV-001..ADV-006/metrics.md
  - .agent/adventures/ADV-002,005,006/adventure-report.md
  - .agent/knowledge/{patterns,issues,decisions}.md
---

# Pipeline Management Review (ADV-001 to ADV-006)

## 1. Summary of Six Completed Adventures

| ID  | Title                                        | Tasks | TCs | TC Pass | Iterations | Est. Cost | Tracked Cost | Tracked Runs |
|-----|----------------------------------------------|------:|----:|--------:|-----------:|----------:|-------------:|-------------:|
| 001 | Expressif Expression/Predicate System        | 32    | 30  | 30/30   | 0 (true)*  | $11.72    | not aggregated | 17/32 (53%) |
| 002 | CodeGraphContext Knowledge Graph             | 17    | 28  | 28/28   | 0          | not in manifest | ~$1.50 | 7/17 (41%) |
| 003 | Game-Studios Studio Hierarchy                | 14    | 0** | n/a     | 0          | not in report | not aggregated | partial |
| 004 | Hermes Self-Evolution                        | 19    | 46  | 46/46   | 0          | $6.63     | not aggregated | partial |
| 005 | Hermes Autonomous Agent Runtime              | 21    | 44  | 44/44   | 0          | not in manifest | ~$7.40 | 18/21 (86%) |
| 006 | Snip Visual Communication Layer              | 19    | 37  | 37/37   | 0          | $7.27     | ~$3.07       | 12/19 (63%) |

\* ADV-001 had a transient FAILED state caused by a reviewer searching the wrong directory; root cause was tooling not implementation, recovered without rework.
\** ADV-003's manifest.md does not populate the Target Conditions table; the report claims 100% pass and zero rework but TC count is unrecorded in frontmatter.

Aggregate: 122 tasks, 185 target conditions, **0 implementation rework iterations across all six adventures**. The dominant story is design-first success; the dominant failures are *bookkeeping* rather than execution.

## 2. Managing Fails (by severity)

### High severity

1. **Reviewer searched wrong working directory (ADV-001)** — `adventure-task-reviewer` operated from `R:/Sandbox/` instead of `R:/Sandbox/ark/`, marked 9 tasks FAILED ("test files missing") in a single batch, then a second pass corrected with note "Previous review incorrectly searched R:/Sandbox/ root instead of ark/ subdirectory." This wasted a full reviewer pass and could have triggered spurious rework. Pipeline lacks a working-directory contract for reviewers when tasks live in a sub-tree.

2. **Bash permission denial blocked verification (ADV-001)** — Implementer agents were repeatedly unable to run `pytest`/`cargo`. At least four log entries record "tests not runnable — Bash permission denied" or "code review passed" as substitute. Tasks were nonetheless marked `done`/`completed`. The pipeline accepted unverified completions because the implementer had no fallback path and the reviewer did not re-run the proof commands.

### Medium severity

3. **Manifest task-list never populated (ADV-002)** — `tasks: []` in the frontmatter. Adventure report flags this as preventing automated prerequisite checks. Task discovery had to fall back to filesystem scan.

4. **Manifest TC table empty (ADV-003)** — Target Conditions section in the manifest is absent from frontmatter. Adventure-reviewer log notes "0 target conditions in frontmatter" yet still produced a passing report. Acceptance signal degenerates to "all task reviews PASSED" without TC traceability.

5. **Metrics rows missing systematically** — Recurring across every adventure with quantified gap:
   - ADV-001: 14 implementer rows for 32 tasks (~44%); the rest unrecorded.
   - ADV-002: 7/17 tracked (41%).
   - ADV-005: 18/21 tracked (86%, best).
   - ADV-006: 12/19 tracked (63%).
   Aggregate frontmatter (`total_tokens_in`, `total_cost`, etc.) is **zero in every metrics.md inspected**. No agent ever updates the totals row.

6. **Timestamp placeholders (`00:00:00Z`)** — Adventure logs in ADV-001, ADV-003, ADV-004 contain identical placeholder timestamps for distinct events, making timeline reconstruction unreliable. ADV-001 has at least 9 entries timestamped `00:00:00Z` for adventure-task-reviewer activity that clearly happened sequentially.

### Low severity

7. **Task status vocabulary drift** — Across adventures implementer logs use `done`, `passed`, `completed`, `ready` interchangeably. ADV-005 review explicitly caught T014 logged as `status: done` instead of `status: passed`. There is no enforced enum.

8. **Review depth varies** — ADV-002 reviewer noted reviews T001-T007 listed per-AC verdicts while T008-T017 collapsed to "Implementation complete: PASS". Audit value of the latter is near zero.

9. **Pre-existing parse failure carried adventure-to-adventure** — `specs/game/vehicle_physics.ark` "unexpected character '.'" failure was noted in ADV-006 review; nothing in the pipeline forces a regression to be ticketed when discovered.

## 3. Weak Spots in the Pipeline

| Weak Spot | Manifestation | Manual Intervention Required |
|-----------|---------------|------------------------------|
| Working-directory contract | Reviewer in wrong cwd, false FAILED batch | Operator re-ran reviewer in correct cwd |
| Bash permissions for verification | Implementer can write code but cannot run `pytest`/`cargo` | Operator (or reviewer) had to run proofs out-of-band; many tasks landed without machine verification |
| Metrics aggregation | `total_*` fields stay at 0 forever | No one. Numbers are simply lost; cost reports are estimates back-derived from per-row data |
| Manifest population | `tasks: []`, missing TC tables | Adventure-reviewer or operator must reconstruct mapping by file scan |
| TC -> task -> review traceability | TC table not always present, reviews don't always cite TC IDs | Operator manually correlates TC to evidence |
| Timestamp discipline | Placeholder `00:00:00Z` entries | Cannot recover real timeline; operator estimates from filesystem mtimes |
| Permission/role boundary for `researcher` | T001 in ADV-004 was logged as implementer running test-strategy work; in ADV-007 the same kind of work is assigned to `researcher`. Role assignment is inconsistent across adventures | None — silent drift |
| Knowledge-extractor batching | One run handled ADV-001+ADV-002+ADV-003 (`spawn: ADV-001,ADV-002,ADV-003 extracting`) — efficient but collapses provenance; if it had failed mid-way, partial state would be hard to recover | Operator inspection |

## 4. Effective Approaches (Patterns Reinforced)

1. **Design-first zero-rework** is the single biggest pipeline win. Five of six adventures (ADV-002 through ADV-006) reached 0 rework across a combined 90 tasks and 155 TCs. The investment in 6-11 design documents, plans, and a test-strategy document per adventure (always T001) decisively pays off.

2. **Test strategy as T001** — Every adventure from ADV-002 onward begins with a test-strategy task that maps every TC to a specific test file/function. This is the contract that makes "implement and pass review on first try" feasible.

3. **Reflexive self-validation as the first real consumer** — ADV-002 (771 nodes / 3475 edges from indexing Ark itself), ADV-004 (reflexive evolution_skills.ark caught 2 bugs in evolution_verify.py), ADV-005 (ark_agent.ark uses agent items to describe itself), ADV-006 (visual_island.ark uses visual items). Acts as a free integration test.

4. **Dual-grammar parity in lockstep** — Adjacent tasks (T003 Lark, T004 Pest in ADV-005/006) keep the two runtimes in sync; never seen as a source of rework.

5. **Domain-isolated tool packages** — `tools/{domain}/` with separate `verify`/`codegen`/`runner`/etc. modules (ADV-003 studio, ADV-004 evolution, ADV-005 agent, ADV-006 visual). No coupling regressions reported.

6. **Z3 ordinal pattern reused across domains** — Same DAG-acyclicity recipe used in ADV-003 (studio escalation), ADV-005 (model fallback), ADV-006 (visual_review). Cross-adventure pattern reuse with no modification.

7. **Optional-dependency import guard** (ADV-006 Pillow, mermaid CLI) — keeps install footprint small without sacrificing functionality when deps are present.

8. **Dual-input AST helpers `_get(obj, field)`** (ADV-005, reused in ADV-006 visual_runner) — single helper handles dict-shape and dataclass-shape AST. Cuts an entire class of "shape mismatch" rework.

9. **Parallel implementer spawning** — ADV-001 logs show overlapping `spawn:` entries for distinct task IDs at near-identical timestamps. The pipeline can fan out implementers when dependencies allow; this drove ADV-005's full run into ~7.5 hours wall time.

## 5. Anti-Patterns to Avoid

1. **Marking tasks `done` after a permission block** — In ADV-001 the implementer wrote "tests not runnable — Bash permission denied; task file updated to completed pending manual test run". This silently bypasses the verification gate. The correct pipeline behavior is to leave the task in `blocked` and surface the missing permission to the lead.

2. **Reviewer skipping proof execution** — ADV-001 batch reviewer log: `step 2/5: ran build — skip (no build artifacts present)` and `step 3/5: ran tests — skip (test files missing)`. The reviewer concluded "all FAILED" without running the proof commands the manifest explicitly defined. Reviewer must execute the proof_command from the TC table, not infer pass/fail from filesystem state.

3. **Updating zero metrics aggregates by hand never** — Six adventures, six `total_tokens_in: 0` headers. Either the schema should be removed, or the last writer (or adventure-reviewer) must compute the sum. Choosing neither is the worst option.

4. **Timestamp placeholders** — `00:00:00Z` in logs makes incident analysis impossible. Always wall-clock; if unavailable, sequential offsets from spawn.

5. **Single-shot batch reviews of many tasks** — ADV-001's `spawn: ADV001-T024 through ADV001-T032 reviewing (9 tasks)` produced 9 simultaneous FAILED verdicts because of one cwd error. Smaller batches limit blast radius.

6. **Empty manifest fields treated as benign** — ADV-002 (`tasks: []`) and ADV-003 (no TC table) shipped without anyone blocking the adventure. The manifest schema should be validated at the `concept -> planning` transition.

7. **Mixing `status` vocabulary** (`done`/`passed`/`completed`/`ready`) — implementer agents pick whichever feels right; reviewers occasionally catch and complain. Define an enum.

8. **Knowledge-extractor batching across adventures** — collapses provenance and creates a single point of failure for three retros.

## 6. Token Economics

### Estimation accuracy

Only ADV-001, ADV-004, and ADV-006 carry both an estimate and a partially-tracked actual. Aggregate tracked spend severely under-runs the planner's estimates, but the tracked portion is itself incomplete:

| Adv | Estimated Cost | Tracked Cost | Tracked Coverage | Apparent Variance | Real Variance (est.) |
|-----|---------------:|-------------:|-----------------:|------------------:|---------------------:|
| 001 | $11.72         | none aggregated | 53% of tasks  | n/a               | likely -50% to -70%  |
| 002 | not in manifest | ~$1.50        | 41% of tasks  | n/a               | ~ -65% if extrapolated |
| 004 | $6.63          | not aggregated | partial      | n/a               | likely -40%          |
| 005 | not in manifest | ~$7.40        | 86% of tasks  | n/a               | close to estimate    |
| 006 | $7.27          | ~$3.07        | 63% of tasks  | -58% on tracked   | ~ -33% extrapolated  |

### Per-task observed averages (from tracked rows)

- Implementer (sonnet, typical task): ~20K tokens in, ~3K out, ~8 minutes wall, ~12 turns, ~$0.10-0.20 per task.
- Planner (opus, per-task design): ~30K tokens in, ~7K out, ~5 minutes, ~12 turns.
- Adventure-planner (opus, single shot): ~85K tokens in, ~28K out, ~30 minutes, ~40 turns. Largest individual run cost (~$1.70).
- Adventure-reviewer (opus): ~45-120K tokens in, ~8K out, ~10 minutes.
- Knowledge-extractor (sonnet): ~18K in, ~4K out, can batch across adventures.

### Cost calibration recommendation

Per ADV-006 reviewer recommendation: future estimates should baseline implementer tasks at ~9 minutes / ~$0.26 rather than the planner's conservative defaults (often ~15-25 min / $0.45+). The conservative estimates are not harmful for budgeting but they do encourage operators to over-allocate review windows.

### Rate-limit incidents

**Zero recorded rate-limit / 429 incidents across all six adventures.** The bottleneck has consistently been *permissions* (Bash gate in ADV-001) and *bookkeeping* (metrics, timestamps), not API throttling. There are no recovery patterns for rate-limits because none have been needed; if rate-limits do appear in larger runs, the pipeline currently has no documented handling.

## 7. Cross-Reference with Knowledge Base

Every issue in `.agent/knowledge/issues.md` matches a finding above:

- "Task completion tracking gaps" = anti-pattern #1 (mark done after block) + manifest population weak spot.
- "Bash permission blocks verification" = high-severity #2 + weak spot row 2.
- "Incomplete metrics tracking" = medium-severity #5 + weak spot row 3.
- "Ported Spec Normalization" (ADV-003 T013) = an in-pipeline catch, not a fail; pipeline working as intended.
- "Metrics Frontmatter Aggregation Gap" = anti-pattern #3.
- "Log Timestamp Placeholders" = medium-severity #6 + anti-pattern #4.
- "Spec-verifier field naming contracts" (ADV-005) = also caught in-pipeline (low severity).

The knowledge base is accurate but **none of the high/medium-severity findings have been remediated in pipeline tooling.** They survive as known-issue notes that future implementers and reviewers must remember by hand.

## 8. Top Recommendations for ADV-007 Roadmap

Ordered by expected leverage:

1. **Add a `metrics-gate` to the reviewer**: refuse to mark a task PASSED unless `metrics.md` contains a row for the task ID. Closes the most persistent bookkeeping gap.
2. **Working-directory contract in adventure config**: explicit `project_root` field consumed by every spawned agent; reviewers chdir before searching.
3. **Permission pre-flight**: planner emits a permission manifest including the proof_command shells required; lead validates before spawning implementers. Eliminates ADV-001's `pytest blocked` class of incident.
4. **Status vocabulary enum** (`pending|in_progress|blocked|review|passed|failed`) enforced by task-file schema.
5. **Wall-clock timestamp helper** (a tiny shared utility) removes the `00:00:00Z` failure mode.
6. **Manifest validation gate** at `concept -> planning`: require non-empty `tasks` and a TC table.
7. **Aggregate metrics on adventure-reviewer completion**: compute and write totals back to frontmatter.
8. **Smaller review batches** (max 3 tasks per spawn) to limit blast radius from a single environmental error.

## Appendix A: Failure Frequency Table

| Failure Class                       | ADV-001 | ADV-002 | ADV-003 | ADV-004 | ADV-005 | ADV-006 | Total |
|-------------------------------------|--------:|--------:|--------:|--------:|--------:|--------:|------:|
| Bash permission block on tests       | 4+      | 0       | 0       | 0       | 0       | 0       | 4+    |
| Reviewer cwd error (false FAILED)    | 1 (9 tasks)| 0    | 0       | 0       | 0       | 0       | 1     |
| Metrics rows missing                 | ~18     | 10      | unknown | unknown | 3       | 7       | 38+   |
| Metrics aggregate frontmatter zero   | yes     | yes     | yes     | yes     | yes     | yes     | 6/6   |
| Timestamp placeholders               | many    | few     | many    | many    | few     | few     | 6/6   |
| Empty manifest tasks/TC table        | no      | tasks=[]| TC empty| no      | no      | no      | 2     |
| Implementation rework iterations     | 0       | 0       | 0       | 0       | 0       | 0       | 0     |
| Rate-limit / 429                     | 0       | 0       | 0       | 0       | 0       | 0       | 0     |

End of report.
