---
task_id: ADV007-T010
adventure_id: ADV-007
generated: 2026-04-14
category: profiling
upstream: research/pipeline-management-review.md
target_condition: TC-008
---

# Phase 3.1 — Profiling Skill Specifications

These three skills address the **bookkeeping failure class** that dominated ADV-001..ADV-006: 38+ missing per-task metrics rows, six-of-six adventures with `total_tokens_in: 0` aggregate frontmatter, placeholder `00:00:00Z` timestamps, and estimate/actual variance that could only be guessed (apparent `-58%` for ADV-006 was largely under-tracking, not under-spending). Every finding cited below is grounded in T009's `pipeline-management-review.md`.

The skills are designed as **drop-in capabilities** that any role (planner, implementer, reviewer, researcher, knowledge-extractor) can invoke without changing its core procedure. They are reusable across the 122 historical tasks and the upcoming ADV-007 backlog.

---

## Skill P1 — `metrics-row-emitter`

### Purpose
Guarantee that every spawned agent appends exactly one well-formed metrics row to `.agent/adventures/{adventure_id}/metrics.md` before declaring `complete`. Closes the most persistent bookkeeping gap: ADV-001 captured 14 of 32 implementer rows (44%), ADV-002 7 of 17 (41%), ADV-006 12 of 19 (63%). Aggregate cost reports today are back-derived and necessarily lossy.

### Triggers
- Agent reaches its terminal step (`step N/N`) and is about to log `complete:`.
- Agent is interrupted (timeout, error, manual stop) — the skill still flushes a row with `result: incomplete` and best-effort token counts.
- Pre-flight check at agent spawn: if a row for `(agent, task_id)` already exists, the skill blocks duplicate spawning unless `--rerun` is set.

### Inputs
- `agent` (string): role name (planner, implementer, reviewer, researcher, knowledge-extractor, adventure-planner, adventure-reviewer).
- `task_id` (string or `-`): task identifier or `-` for adventure-level work.
- `model` (string): opus, sonnet, haiku.
- `tokens_in`, `tokens_out` (int): from runtime usage counters.
- `duration` (string): wall-clock from spawn to terminal step, formatted `Nmin` or `Hh Mmin`.
- `turns` (int): conversation turns the agent used.
- `result` (enum): `complete | partial | failed | incomplete`.

### Outputs
- One appended row in `metrics.md` matching the table schema.
- A returned dict with the same fields, so the caller can chain into the aggregator (P2).

### Procedure
1. Read `metrics.md` frontmatter to get `adventure_id` and validate it matches the agent's working adventure.
2. Scan the existing rows; if a row with same `(agent, task_id, model)` exists with `result != incomplete`, abort with `duplicate_row` unless `--rerun` flag set.
3. Compose the row using the documented column order: `| agent | task | model | tokens_in | tokens_out | duration | turns | result |`.
4. Append (do not rewrite) to preserve append-only audit semantics.
5. Return the dict for chaining.

### Success metrics
- Coverage: `(rows_in_metrics_md) / (distinct (agent,task) spawns in adventure.log) >= 0.95` per adventure. Today's coverage range is 41–86%.
- Zero duplicate `(agent, task_id, model)` rows except those marked `--rerun`.
- Zero malformed rows (column count mismatch, missing fields).

### Failure modes
- **Token counters unavailable**: write the row with `tokens_in=0, tokens_out=0, result=partial` and a sibling note in adventure.log: `"metrics row written without token data — runtime usage unavailable"`. Never silently skip the row.
- **metrics.md missing**: bootstrap with the standard frontmatter and table header from the adventure manifest template; log `"metrics.md bootstrapped"`.
- **adventure_id mismatch**: hard fail; this would corrupt cross-adventure accounting.

### Integration points
- **planner / researcher / implementer / reviewer**: each ends its terminal step with `metrics-row-emitter(...)` instead of an ad-hoc `printf`. Removes the human-edited row variance noted across ADV-001..006.
- **adventure-planner / adventure-reviewer**: same call, with `task: -`.
- **lead** (orchestrator): can verify post-spawn that the row exists; if missing after a 60s grace, log `"metrics-row missing for {agent}/{task} — emit fallback"` and emit an `incomplete` row on the agent's behalf so the budget aggregator (P2) does not silently lose the run.

---

## Skill P2 — `aggregate-budget`

### Purpose
Compute and write back the `total_tokens_in`, `total_tokens_out`, `total_duration`, `total_cost`, and `agent_runs` fields in `metrics.md` frontmatter. Today these fields are zero in **every metrics file across six adventures**. Without them, no adventure-level cost report is possible without back-derivation.

### Triggers
- Adventure-reviewer terminal step (post all task reviews, pre-report).
- Adventure state transition `active -> review` and `review -> archived`.
- Manual operator command `aggregate-budget {adventure_id}`.
- Daily cron / scheduler tick if the adventure is `active` and last aggregation > 24 h ago.

### Inputs
- `adventure_id` (string).
- `cost_table` (dict): per-model rate map sourced from `.agent/config.md` (currently opus, sonnet, haiku per-MTok rates).
- `mode` (enum): `incremental | full_recompute` (default incremental — read existing totals, add new rows since last aggregation; full_recompute scans all rows and overwrites).

### Outputs
- Updated frontmatter in `.agent/adventures/{adventure_id}/metrics.md` with the five total fields populated.
- A diff line appended to adventure.log: `"aggregator: tokens_in +X, tokens_out +Y, runs +Z, cost +$W"`.
- Return dict with the new totals plus delta from prior totals.

### Procedure
1. Parse the metrics.md table; reject malformed rows (skip, log to adventure.log with row index).
2. For each well-formed row, look up `model` in `cost_table` and compute row cost: `tokens_in/1e6 * input_rate + tokens_out/1e6 * output_rate`.
3. Sum tokens_in, tokens_out, durations (parse `Nmin`/`Hh Mmin` to seconds, then back to canonical), costs, and agent_runs.
4. In incremental mode, add to existing totals; in full mode, overwrite.
5. Rewrite frontmatter atomically (tmp file + rename) to avoid partial writes.
6. Append the delta line to adventure.log.

### Success metrics
- After running on any of ADV-001..006, the frontmatter no longer reads zero.
- Sum of per-row cost matches the overwritten total to within rounding error (<$0.01).
- Zero adventure.log entries reading `"aggregator: malformed row"` after a clean run.

### Failure modes
- **Unknown model in cost_table**: skip cost contribution for that row, count tokens, log `"unknown model {x} for row {i} — cost omitted"`. Never crash.
- **Concurrent write to metrics.md** (rare): atomic rename pattern protects against half-files; if the rename fails, retry once with backoff and surface as `failed` to the caller.
- **Missing duration units**: assume minutes if the field is bare integer; log a warning.

### Integration points
- Pairs with **P1**: P1 produces the rows, P2 consumes them.
- **adventure-reviewer**: aggregator must run before the report is written so the report can cite real numbers (current ADV-002, 005, 006 reports cite estimates and back-derived numbers).
- **knowledge-extractor**: variance computation against estimates becomes deterministic instead of "n/a" as in five of six historical adventures.
- **lead**: after `state -> active`, a daily aggregation gives an in-flight burn-down rather than a post-mortem-only signal.

---

## Skill P3 — `wallclock-stamp`

### Purpose
Eliminate the `00:00:00Z` placeholder timestamp class. ADV-001, ADV-003, ADV-004 each contain many distinct events stamped with this placeholder; ADV-001 alone has 9 sequential reviewer activities collapsed to the same timestamp, making timeline reconstruction unreliable for incident analysis. Every log line in `adventure.log` and every metrics.md row should carry a real timestamp at sub-second precision.

### Triggers
- Any agent prepares to append a line to `adventure.log`.
- Any agent prepares to write a `created`, `updated`, or `## Log` entry into a task file.
- Any agent prepares to emit a metrics row.

### Inputs
- `precision` (enum): `second | millisecond` (default second for human readability, millisecond for high-rate parallel spawns).
- `tz` (enum): `utc | local` (default utc; local accepted only when paired with explicit offset, as ADV-007 already does with `+01:00`).
- `fallback_offset` (int seconds, default 1): if the system clock is unavailable or returns epoch-0, return `last_known_timestamp + fallback_offset` and tag the line with `?` suffix.

### Outputs
- An ISO-8601 string with offset, e.g. `2026-04-14T05:30:00+01:00` or `2026-04-14T05:30:00.123Z`.
- A monotonically non-decreasing sequence within the same agent invocation.

### Procedure
1. Read system clock.
2. If clock returns epoch-0 or fails, read the last timestamp in `adventure.log`, parse it, add `fallback_offset`, mark the value with `?`.
3. Apply timezone normalization (utc -> Z, local -> explicit offset).
4. Apply precision truncation/extension.
5. Cache the value in agent-local memory so the next call within the same step is guaranteed monotonic (add 1ms if needed).

### Success metrics
- Zero `00:00:00Z` lines in any new adventure.log after the skill is rolled out.
- Strictly monotonic per-agent timestamps within a single step.
- Cross-agent ordering correct to within clock skew (~1s acceptable).

### Failure modes
- **Clock returns garbage**: handled by `fallback_offset` path; the `?` suffix is a deliberate signal to operators that timeline near this entry is approximate.
- **Daylight-saving transitions** (local-tz mode): always emit explicit offset, never bare local time.

### Integration points
- Used by **every role's logging procedure** (planner, researcher, implementer, reviewer, knowledge-extractor, adventure-planner, adventure-reviewer, lead).
- Pairs with the upcoming **review-evidence-citation** convention proposed in T011: reviewer cites the timestamp range it inspected, only meaningful if timestamps are real.
- Pairs with **P2 (aggregate-budget)**: durations summed from real timestamps are accurate; durations summed from `00:00:00Z` cluster collapse to zero.

---

## Skill cross-cutting notes

### Order of adoption
P1 first (it produces the data), P3 second (it makes the data interpretable), P2 third (it consumes the data). Adopting P2 without P1 in place would produce confidently-wrong totals.

### Estimation accuracy enabling
Once P1+P2+P3 are in place, the **variance** column in the manifest evaluations table can be populated for every task, not just for the rare T013/T015 entries we see in ADV-007 today. The downstream effect is that planner cost estimates become tunable: ADV-006 reviewer recommended baselining implementer tasks at ~9 min / $0.26 instead of 15-25 min / $0.45+; that recommendation could not be made empirically before because tracked coverage averaged ~57% across the six adventures.

### Why three skills, not one mega-skill
Each can be adopted independently. P1 unblocks P2 unblocks accurate estimation. P3 is orthogonal and can be deployed even without P1/P2. Splitting also matches the observed agent-procedure granularity: agents already log per-step lines and emit per-run rows.

### Anti-pattern cancellation
- Cancels anti-pattern #3 (zero metrics aggregates by hand never): P2 makes "by hand" obsolete.
- Cancels anti-pattern #4 (timestamp placeholders): P3 forbids them at source.
- Mitigates anti-pattern #1 (mark task done after permission block): P1's `incomplete` result keeps the run on the books even when the bash gate fires.

### Integration with existing roles (concrete edits)
- **planner.md / researcher.md / implementer.md / reviewer.md / knowledge-extractor.md**: replace the existing `## Record Metrics` section with a single line: `Invoke P1 (metrics-row-emitter) at terminal step. P3 (wallclock-stamp) for every log line.`
- **adventure-planner.md / adventure-reviewer.md**: same plus `Invoke P2 (aggregate-budget) before emitting the adventure report.`
- **lead** (orchestrator): on receiving `complete` from a child agent, confirm P1 row exists; if absent after grace period, emit a fallback `incomplete` row.

### Out of scope
- Token estimation accuracy improvements (separate skill family — see optimization-skills.md, O1 `estimate-from-history`).
- Per-tool rate-limit accounting (covered in self-healing-skills.md, S2 `rate-limit-recovery`).
- Per-permission audit (covered in self-healing-skills.md, S1 `permission-pre-flight`).
