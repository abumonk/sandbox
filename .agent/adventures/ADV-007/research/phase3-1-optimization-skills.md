---
task_id: ADV007-T010
adventure_id: ADV-007
generated: 2026-04-14
category: optimization
upstream: research/pipeline-management-review.md
target_condition: TC-008
---

# Phase 3.1 — Optimization Skill Specifications

These three skills target the **leverage opportunities** identified across ADV-001..ADV-006: the design-first / test-strategy-first pattern that produced 0 implementation rework over 122 tasks (Effective approach #1, #2 in T009), the parallel-spawning pattern observed in ADV-001 and ADV-005 (Effective approach #9), and the reflexive-self-validation pattern (Effective approach #3) that turned every domain into its own integration test. The skills push these from *occasional emergent behaviors* into *first-class repeatable capabilities*.

Unlike profiling (which is rescue work for known gaps), optimization is **leverage amplification**: each skill takes a pattern that works and exposes its preconditions explicitly so it triggers more reliably and earlier.

---

## Skill O1 — `estimate-from-history`

### Purpose
Replace planner intuition with empirical per-task estimates derived from completed adventures' metrics rows. T009 showed that planner estimates over-provision implementer time consistently — ADV-006 reviewer recommended baselining implementer tasks at ~9 min / ~$0.26 vs the planner's ~15-25 min / ~$0.45+ default. The conservative estimate is "safe" but encourages over-allocation of review windows and inflates apparent variance.

### Triggers
- Adventure-planner is composing the manifest evaluations table.
- Planner is creating a single new task file.
- Lead operator runs `estimate-from-history --task {task_template}` for sanity checks.
- Triggered automatically when knowledge-extractor finishes an adventure and detects |variance| > 30% on aggregated tasks.

### Inputs
- `task_descriptor` (dict): `{role, model, primary_skill_tags, expected_loc, complexity_tier}`. The complexity tier is a planner-supplied 1-5 ordinal.
- `history_corpus` (path): default `.agent/adventures/*/metrics.md`.
- `min_samples` (int, default 5): require at least this many comparable historical rows; otherwise return planner's prior estimate with a `low_confidence` flag.
- `weight_recency` (bool, default true): exponentially decay older runs.

### Outputs
- A dict: `{tokens_in_p50, tokens_in_p90, tokens_out_p50, tokens_out_p90, duration_p50, duration_p90, cost_p50, cost_p90, sample_size, confidence}`.
- A justification string suitable for inserting into the manifest as a comment, e.g. `"derived from 14 implementer/sonnet/parser tasks across ADV-001..006 (median 17min/$0.18, p90 32min/$0.41)"`.

### Procedure
1. Filter `history_corpus` rows to those matching `(role, model)` and tagged with at least one shared `primary_skill_tag`.
2. Apply complexity-tier multiplier (planner-calibrated, starts at 1.0 across all tiers and learns over adventures).
3. If sample size < `min_samples`, fall back to the planner's prior with `confidence: low`.
4. Compute p50/p90 percentiles for tokens_in, tokens_out, duration, cost.
5. Apply recency weight if enabled (half-life ~30 days).
6. Return the dict and justification string.

### Success metrics
- |variance| (actual vs estimate) shrinks adventure over adventure. Target: <25% for >70% of tasks by ADV-010.
- Sample size grows monotonically; new task tags get retired into the corpus.
- Planner produces no more `not in manifest` cost cells of the kind ADV-002 and ADV-005 carry.

### Failure modes
- **Cold start** (no history matches): emit planner's prior with `confidence: low`. P1+P2 from profiling-skills.md guarantee history accumulates.
- **Outlier-heavy corpus** (one adventure's runaway tasks dominate): p90 absorbs them; p50 stays robust. Operator can pass `--exclude-adventures` if needed.
- **Skill-tag drift** (planner invents new tags every adventure): handled by also matching on `role` alone with a wider variance band.

### Integration points
- **adventure-planner**: replaces the current heuristic in step 6/9 ("evaluations done") with a deterministic pull from history.
- **planner** (per-task): when creating a single new task, consults this skill for the `evaluation` block in the task frontmatter.
- **knowledge-extractor**: at adventure completion, computes per-task variances using P1+P2's data; large variances (>50%) are written into knowledge/issues.md as calibration entries (per the existing researcher procedure).
- **reviewer**: not directly consumed, but a task whose actual run exceeds `cost_p90` warrants a flag in the review report.

---

## Skill O2 — `parallel-fanout-scheduler`

### Purpose
Make the parallel-spawning pattern observed in ADV-001 (overlapping `spawn:` entries at near-identical timestamps for distinct task IDs) and ADV-005 (~7.5h wall time on 21 tasks) deterministic and dependency-aware. Today's parallelism is opportunistic — the lead notices independent tasks and fans out by hand. The scheduler makes it a contract.

### Triggers
- Adventure state transitions `review -> active` (initial fanout decision).
- A task transitions `in_progress -> passed`, freeing dependents (replanning trigger).
- A spawned agent reports `failed` or `blocked` (rebalancing trigger).
- Manual `--replan` from the operator.

### Inputs
- `manifest` (path): `.agent/adventures/{adventure_id}/manifest.md`.
- `task_files` (glob): `.agent/adventures/{adventure_id}/tasks/*.md`.
- `concurrency_cap` (int, default 4): maximum simultaneous spawned agents. Calibrated against rate-limit headroom (zero recorded incidents in ADV-001..006, so 4 is safe; could rise).
- `cost_budget` (float, optional): if set, scheduler prefers cheaper tasks first when at the cap.
- `priority_weights` (dict): user-supplied bias (e.g. `{depth_first: 0.7, breadth_first: 0.3}`).

### Outputs
- A wave plan: ordered list of spawn batches `[[task_a, task_b], [task_c], [task_d, task_e, task_f]]`.
- A Gantt-style annotation written to `adventure.log`: `"scheduler: wave 1 = [T001,T004], wave 2 after T001 = [T002,T005,T010], ..."`.
- A returned dict with critical-path estimate (using O1's p50 durations) and parallel speedup vs serial.

### Procedure
1. Build a dependency DAG from each task's `depends_on` field.
2. Verify acyclicity (apply the Z3 ordinal pattern reused across ADV-003/005/006 — Effective approach #6).
3. Topological sort, partitioning into waves where each wave's tasks have all dependencies in earlier waves.
4. Within each wave, sort by O1's `duration_p50` descending (longest-first to maximize wave parallelism without ragged tails).
5. Apply `concurrency_cap` by splitting oversized waves.
6. Compute critical path duration using p50 estimates from O1; report parallel speedup.
7. Emit wave plan and annotate adventure.log.

### Success metrics
- Wall-clock reduction vs serial spawning. ADV-005 already showed ~7.5h on 21 tasks (likely ~3.5x speedup); target >3x speedup at concurrency_cap=4 for adventures with >15 tasks.
- Zero scheduling-induced rework (i.e. no task spawned before a dependency completed).
- Zero rate-limit incidents (preserves the ADV-001..006 perfect record).

### Failure modes
- **Hidden dependency** (task A reads a file B writes, but no `depends_on`): scheduler trusts the manifest; the resulting failure surfaces in the implementer's reviewer pass and the operator updates the manifest. Recommend pairing with a dependency-inference linter (out-of-scope here, candidate ADV-008 task).
- **Concurrency_cap too high triggers rate-limit**: pairs with self-healing S2 (`rate-limit-recovery`) which automatically reduces the cap and replans.
- **All tasks serial** (no parallelism possible): scheduler degrades gracefully to serial and logs `"scheduler: critical path = serial, no fanout possible"`.

### Integration points
- **lead**: invokes this skill at `review -> active` transition instead of spawning the first task by hand.
- **adventure-planner**: optionally previews the wave plan during planning so the manifest carries an estimated wall-clock alongside the estimated cost.
- **all worker roles**: unchanged; they receive their task as before.
- **knowledge-extractor**: at adventure completion, compares planned waves vs observed waves and feeds discrepancies back as a calibration signal for `priority_weights`.

---

## Skill O3 — `context-pruner`

### Purpose
Reduce per-agent token-in by automatically pruning the read-set passed to a spawned agent down to what the task actually needs. Per-task averages from T009: implementer ~20K tokens in, planner ~30K, adventure-planner ~85K, adventure-reviewer ~45-120K. The adventure-reviewer cluster is the largest single line item per run; even a 30% prune translates directly into cost reduction at scale.

The pattern is already reinforced organically — agents spawn with task file, design, plan, and one upstream artifact. But there is no guard against the gradual creep where a researcher reads "all six manifests + all six logs + all six metrics + all six reports" (T009 input was exactly this, ~120K tokens in) when a curated subset would have sufficed.

### Triggers
- Lead is composing the spawn message for a child agent.
- Adventure-reviewer is preparing its read-set.
- Knowledge-extractor is preparing its read-set across multiple adventures.
- Manual `context-pruner --task {task_id} --dry-run` for operator inspection.

### Inputs
- `task_id` (string): identifies the consumer.
- `proposed_read_set` (list of paths): what the operator or default procedure intends to pass.
- `task_descriptor` (dict): same fields as O1, used to look up historical "minimal sufficient set".
- `mode` (enum): `aggressive | conservative` (default conservative). Aggressive removes anything outside p90 of historical reads; conservative removes only files no task of this type has ever read.

### Outputs
- A pruned read-set (subset of input).
- A justification list: `[{path, decision: kept|dropped, reason}]`.
- An estimated tokens-saved figure using cached file sizes.

### Procedure
1. Look up historical "files actually opened" from past tasks of the same role+skill_tags. (Requires a small `accessed-files` tracking enhancement to P1; see cross-cutting notes.)
2. For each path in `proposed_read_set`, classify:
   - `core`: opened in >70% of comparable historical tasks → keep.
   - `auxiliary`: opened in 30-70% → keep in conservative mode, drop in aggressive.
   - `rare`: opened in <30% → drop.
3. Always preserve the task file, design, plan, and immediate upstream artifact even if rare (these are the "design-first" foundations responsible for 0-rework outcomes).
4. Return pruned set, justification, estimated savings.

### Success metrics
- Average tokens_in per role drops by >20% with no increase in rework rate (rework rate baseline is 0 — must remain 0).
- Adventure-reviewer tokens_in drops from 45-120K range toward 30-80K.
- Operator override rate (`--no-prune`) <10% — high override rate signals the pruner is too aggressive.

### Failure modes
- **Pruner drops a file the task actually needs**: agent fails the task and the operator re-spawns with `--no-prune`; the failed-prune entry is added to the historical "must-keep" set for that role+skill pair. One-time cost per skill drift.
- **Cold start** (no historical access data): defaults to passthrough with a `low_confidence` log line. As P1+the access-tracking enhancement accumulate data, pruning gradually engages.
- **Aggressive mode on novel task**: explicit safeguard — aggressive mode disabled when sample size <10.

### Integration points
- **lead**: wraps every spawn in `context-pruner` before composing the spawn message.
- **planner / researcher / implementer / reviewer**: unchanged; they receive a smaller read-set transparently.
- **adventure-reviewer / knowledge-extractor**: highest leverage. Knowledge-extractor batching across adventures (anti-pattern #8 in T009) becomes safer when the per-adventure context is pruned.
- **profiling P1**: extension required — P1 should also record `accessed_files: [...]` per row so the pruner has training data.

---

## Skill cross-cutting notes

### Required data plumbing
O1 needs P1+P2 to produce reliable history.
O2 needs O1's p50 durations to optimize wave packing.
O3 needs an extension to P1 to record per-run accessed files.
**Order of adoption**: profiling skills first, then O1, then O2 and O3 in either order.

### Effective approaches reinforced
- Effective approach #1 (design-first zero-rework): O1 quantifies its payoff so it stays funded.
- Effective approach #2 (test strategy as T001): O3 always preserves the test-strategy file in the read-set.
- Effective approach #6 (Z3 ordinal pattern): O2 reuses it for DAG acyclicity.
- Effective approach #9 (parallel implementer spawning): O2 makes it the default rather than the exception.

### Anti-patterns mitigated
- Anti-pattern #5 (single-shot batch reviews of many tasks): O2 caps wave size, limiting blast radius.
- Anti-pattern #8 (knowledge-extractor batching across adventures collapsing provenance): O3 makes per-adventure context lean enough that batching is unnecessary.

### Integration with existing roles (concrete edits)
- **lead orchestrator**: add invocation of O3 before every spawn; invoke O2 at `review -> active`.
- **adventure-planner.md**: in step 6/9 (evaluations) consult O1 instead of using priors; optionally preview O2 wave plan in step 5/9 (plans).
- **planner.md** (per-task): consult O1 when filling the `evaluation` frontmatter block.
- **knowledge-extractor.md**: variance computations (currently sometimes "n/a") become deterministic.

### Out of scope
- Speculative parallelism across siblings of unfinished branches (could interact poorly with self-healing retries; defer to ADV-008+).
- Cache-based reuse of completed task outputs across adventures (separate skill family — knowledge layer, not pipeline layer).
- Per-tool token shaping inside an agent (responsibility of the agent's procedure, not the orchestrator's spawn).

### Estimated leverage
Combining O1+O2+O3 on a 20-task adventure with planner defaults:
- O1: shrinks "safe" estimates ~30-40% on average, freeing budget for additional tasks rather than reducing total spend (operator policy choice).
- O2: ~3x wall-clock speedup at concurrency_cap=4 (extrapolated from ADV-005's organic ~3.5x).
- O3: ~20-30% tokens_in reduction across the adventure, weighted heavily toward adventure-reviewer.
Compound effect on a $13.20-budget adventure (ADV-007 scale): ~$3-4 token savings, ~10h wall-clock savings — assuming the leverage stacks linearly, which it approximately does because the three target distinct dimensions (calibration, scheduling, context).
