---
task_id: ADV007-T010
adventure_id: ADV-007
generated: 2026-04-14
category: self-healing
upstream: research/pipeline-management-review.md
target_condition: TC-008
---

# Phase 3.1 — Self-Healing Skill Specifications

These three skills target the **failure recovery gaps** in T009: the bash-permission denial class that bypassed verification gates 4+ times in ADV-001 (high-severity #2, anti-pattern #1), the working-directory error that produced 9 simultaneous false-FAILED verdicts in ADV-001 (high-severity #1, anti-pattern #5), the absent rate-limit handling (zero incidents, but zero documented recovery either — a latent risk for larger runs), and the silent role-assignment drift (weak spot #7) that lets a task land with the wrong agent type without surfacing the mismatch.

The pattern across these failures is the same: an **environmental precondition was wrong** (permission, cwd, role, throughput cap), and the pipeline had no mechanism to detect/recover, so the failure leaked downstream as a false signal (task marked done, batch marked failed, work assigned to wrong role).

---

## Skill S1 — `permission-pre-flight`

### Purpose
Before a worker agent is spawned, verify it has every permission it will actually need. Block the spawn or downgrade it gracefully if not. Eliminates the ADV-001 failure class where an implementer wrote code, hit `Bash permission denied` on `pytest`, and marked the task `done` with a note "tests not runnable — pending manual test run". This silently bypasses the verification gate; the correct behavior is to leave the task `blocked` and surface the missing permission.

### Triggers
- Lead is about to spawn a child agent.
- Task file's `evaluation.access_requirements` field is updated (re-validate).
- A worker agent encounters a permission denial mid-execution (re-check whether the planner missed it).
- Manual operator command `permission-pre-flight {task_id}`.

### Inputs
- `task_id` (string): identifies the task.
- `permission_manifest` (dict): from the task file's `evaluation.access_requirements` (e.g. `[Read, Write, Bash:pytest, Bash:cargo]`). Per the T009 roadmap recommendation, planners must emit this explicitly; today only general access types appear.
- `agent_capabilities` (dict): the candidate agent's currently-granted permissions.
- `proof_commands` (list): from the manifest TC table — the literal shell commands that will be executed to verify acceptance criteria.

### Outputs
- A verdict: `{ok: bool, missing: [perm], suggestions: [str]}`.
- If `ok: false`, a structured `permission_request` written to a sidecar file `.agent/adventures/{adventure_id}/permission-requests/{task_id}.md` for the operator to grant.
- An adventure.log entry: `"pre-flight: T0xx requires Bash:pytest, currently denied — task held in blocked"`.

### Procedure
1. Parse `permission_manifest` and union with the parsed proof_commands (`Bash:pytest` is required if any proof_command begins with `pytest`).
2. Compare against `agent_capabilities`.
3. If any required permission is missing, write the permission_request, set the task status to `blocked` (per the status enum proposed in T009 recommendation #4), and emit the log line.
4. If all permissions are present, return `ok: true` and let the spawn proceed.
5. If a worker agent later encounters an unexpected denial, re-run pre-flight in retroactive mode and update the task's `access_requirements` so the planner's calibration improves.

### Success metrics
- Zero tasks marked `done`/`completed` after a permission denial in the run log. (Baseline: 4+ in ADV-001.)
- Permission-request files closed (granted) within operator SLA before re-spawn.
- Planner's `access_requirements` accuracy improves over adventures (measured by the rate of retroactive updates from the worker-side path, which should trend toward zero).

### Failure modes
- **Planner emits incomplete permission_manifest** (the historical case): pre-flight catches what it can from proof_commands; the worker-side retroactive path catches the rest. Each retroactive catch becomes a calibration data point.
- **Operator never grants**: task remains `blocked`; the wave scheduler (O2) deprioritizes it and continues with siblings; the adventure can still close partial if the blocked task is non-critical (operator decision).
- **Granted permission is not actually present at runtime** (sandbox lying): worker emits `incomplete` via P1, log entry surfaces the discrepancy, operator escalation.

### Integration points
- **lead**: must run pre-flight before every spawn; this is the gate.
- **adventure-planner**: per the T009 roadmap recommendation #3, must emit a permission manifest as part of step 8/9 ("permission analysis"). ADV-007's own manifest already does this in primitive form ("4 passes, 33 requests, 0 gaps").
- **planner** (per-task): fills `evaluation.access_requirements` based on the test-strategy file (T001 of every adventure) and the proof_command list.
- **implementer / reviewer / researcher**: when they hit an unexpected denial, they invoke pre-flight in retroactive mode rather than silently working around it.
- **profiling P1**: the `result: blocked` outcome is a first-class result code that does not pollute success metrics.

---

## Skill S2 — `rate-limit-recovery`

### Purpose
Handle 429 / quota-exhaustion responses gracefully. T009 records **zero rate-limit incidents across all six adventures** but also notes that the pipeline has no documented handling — meaning the first incident in a larger run will hit a stack with no recovery path. This skill is forward-looking insurance, designed before the failure happens.

### Triggers
- Any worker agent receives a 429 / "rate_limit_error" / "quota_exceeded" / model-overload response from the API.
- Lead receives a failed spawn with a rate-limit-related error.
- Pre-flight monitor detects sustained latency growth or rising error rate (early warning).

### Inputs
- `error_payload` (dict): the raw API error.
- `agent` (string), `task_id` (string), `model` (string): which run hit it.
- `retry_policy` (dict): `{max_retries: 5, base_delay_s: 30, max_delay_s: 600, jitter: 0.2}`.
- `model_fallback_chain` (list): e.g. `[opus -> sonnet -> haiku]` for capability-tolerant tasks; empty list (no fallback) for tasks marked `model_critical: true`.

### Outputs
- A retry decision: `{action: retry|fallback|defer|fail, delay_s: int, fallback_model: str|null}`.
- An adventure.log entry: `"rate-limit: {agent}/{task} hit 429 on {model}; action=retry delay=120s attempt=2/5"`.
- On `fail`: a permission-request-style file `.agent/adventures/{adventure_id}/rate-limit-incidents/{task_id}.md` for operator decision (raise quota, change strategy, etc.).

### Procedure
1. Parse the error payload. If not actually rate-limit-class, hand off to the generic error handler (out of scope).
2. Increment the per-task retry counter; if > `max_retries`, return `fail`.
3. Compute exponential backoff with jitter: `min(max_delay_s, base_delay_s * 2^attempt) * (1 + uniform(-jitter, jitter))`.
4. If `retry_attempts < max_retries`: return `retry` with computed delay.
5. If retries exhausted but `model_fallback_chain` is non-empty: select next model, return `fallback`. (Z3 acyclicity pattern from Effective approach #6 ensures the chain terminates.)
6. If both retry and fallback exhausted: return `fail` and write the incident file.
7. In all cases, also signal the scheduler (O2) to reduce `concurrency_cap` by 1 for the next 10 minutes (rate-limit dampening).

### Success metrics
- Time-to-recovery from a single 429 < 5 minutes for >90% of incidents.
- Zero incidents that escalate to `fail` without operator visibility (i.e. an incident file is always written when fail occurs).
- Adventure wall-clock impact of rate-limits stays <10% even at 5+ incidents per adventure.

### Failure modes
- **Sustained API outage**: retry policy exhausts, fallback chain exhausts, incident file generated, operator escalation. The skill does not pretend to recover from outages; it bounds the impact and surfaces them.
- **Fallback model lacks capability** (e.g. opus-only reasoning): the task fails the reviewer pass on quality grounds; reviewer flags `quality regression suspected — model fallback occurred`; operator decides whether to re-run on opus once quota is back. Pairs cleanly with profiling P1's `partial` result code.
- **Concurrent rate-limit dampening across many agents**: each agent contributes at most -1 to the cap; floor at 1; never deadlock.

### Integration points
- **all worker roles**: invoke S2 instead of crashing on 429.
- **lead**: monitors the dampening signal from S2 and applies it to subsequent spawns.
- **optimization O2 (parallel-fanout-scheduler)**: receives the dampened cap and replans within wave.
- **profiling P1**: rate-limit-recovered runs still emit a row, possibly with `partial` result if a fallback occurred.
- **knowledge-extractor**: incidents become a calibration signal — sustained 429s in one model class suggest tier-up or schedule-shift.

---

## Skill S3 — `working-context-validator`

### Purpose
Verify environmental preconditions before a worker agent does any real work: working directory, role/agent-type assignment, manifest validity, status-vocabulary compliance. Catches the ADV-001 reviewer-cwd disaster (9 false-FAILED verdicts in one batch because `R:/Sandbox/` was searched instead of `R:/Sandbox/ark/`), the ADV-002 / ADV-003 manifest-empty-fields issues (`tasks: []`, missing TC table) that should have blocked at concept→planning, the silent role-assignment drift between ADV-004 and ADV-007 (same kind of work assigned to different roles in different adventures), and the status vocabulary drift (`done`/`passed`/`completed`/`ready` used interchangeably).

### Triggers
- Worker agent's first action after spawn: validate before reading the task file.
- Manifest schema event: state transition `concept -> planning` or `planning -> review`.
- Periodic heartbeat: every 10 minutes during an `active` adventure.
- Manual `working-context-validator {adventure_id}` for audit.

### Inputs
- `agent` (string), `task_id` (string).
- `expected_cwd` (path): from adventure config's `project_root` field — this is the new field T009 recommends adding (recommendation #2).
- `expected_role` (string): the role declared in the task file's `assignee` field; validator checks the spawning agent's role matches.
- `manifest_schema` (dict): required-non-empty fields list (e.g. `tasks`, target-conditions table rows >0).
- `status_enum` (list): canonical `[pending, in_progress, blocked, review, passed, failed]` per T009 recommendation #4.

### Outputs
- A verdict: `{ok: bool, violations: [{type, detail, severity}]}`.
- If `ok: false` and severity any `high`, abort the worker before any tool call; surface the violation to the lead.
- If `ok: true` but violations exist at `low` severity (e.g. status vocabulary uses non-canonical word), auto-correct in place and log: `"validator: T0xx status normalized 'done' -> 'passed'"`.

### Procedure
1. Check current cwd against `expected_cwd`; if mismatch, `chdir` to expected and log. (Eliminates the ADV-001 reviewer cwd disaster.)
2. Check the spawned agent's actual role against `expected_role` from the task file; if mismatch, abort with high severity. (Closes weak spot #7 silent drift.)
3. Validate the manifest against `manifest_schema`: if any required field is empty, severity is `high` for state transitions out of `concept`, `medium` thereafter.
4. Scan the task file's `status` field and `## Log` entries for non-canonical status words; auto-normalize and log.
5. Cross-check the task file's `target_conditions` references against the manifest TC table; missing references are `medium` severity.
6. If any high-severity violation: write a `validator-incident` sidecar and abort.

### Success metrics
- Zero false-FAILED batches from cwd errors (baseline: 1 batch of 9 in ADV-001).
- Zero adventures advancing past `concept` with empty `tasks` or empty TC table (baseline: 2 of 6).
- Zero status-vocabulary drift entries reaching the adventure-reviewer (baseline: caught by review in ADV-005, missed elsewhere).
- Role-assignment drift: zero silent drift incidents (baseline: at least 1 documented in T009 ADV-004 vs ADV-007 comparison).

### Failure modes
- **expected_cwd field absent from adventure config** (legacy adventures): validator falls back to inferring from the manifest's `## Environment` section (`Workspace: R:\Sandbox\ark`); logs as `low_confidence`. New adventures must populate the field per T009 recommendation #2.
- **Auto-correction surprises operator**: every auto-correction emits a log line; the operator can disable auto-correct via `--strict` mode in which case low-severity becomes high.
- **Manifest schema is itself wrong**: the validator's schema is the source of truth; if the schema is wrong, fix the schema (and any prior auto-corrections become technical debt to revisit).

### Integration points
- **lead**: invokes validator immediately after spawn, before any agent procedure begins.
- **adventure-planner**: must populate `project_root` and `tasks` and TC table; validator at `concept -> planning` blocks if not.
- **all worker roles**: receive a clean, validated context — no need for each role to defensively check.
- **profiling P1**: the auto-corrected status field is what gets recorded, so metrics stay clean.
- **adventure-reviewer**: validator's heartbeat catches in-flight drift before the final review pass would have to handle it.

---

## Skill cross-cutting notes

### Order of adoption
S3 first (it gates the worker before it does any harm), S1 second (it gates the spawn before the worker is even created), S2 third (it is forward-looking insurance for a failure class not yet observed).

In failure-likelihood terms: S1 addresses 4+ historical incidents, S3 addresses 1 batch (9 task-incidents) plus 2 manifest-validity incidents plus diffuse status-drift, S2 addresses 0 historical incidents but is cheap to deploy and unbounded in worst-case impact.

### Anti-patterns cancelled
- Anti-pattern #1 (mark task done after permission block): S1 enforces `blocked` status; P1's `incomplete` result keeps it visible.
- Anti-pattern #2 (reviewer skipping proof execution): S1 verifies the reviewer has the permissions for proof_commands before allowing the review spawn.
- Anti-pattern #5 (single-shot batch reviews of many tasks): S3 catches cwd errors before the batch starts; the existing recommendation #8 (smaller batches) is independent insurance.
- Anti-pattern #6 (empty manifest fields treated as benign): S3 enforces non-empty fields at state transitions.
- Anti-pattern #7 (mixing status vocabulary): S3 auto-normalizes.

### Effective approaches reinforced
- Effective approach #1 (design-first zero-rework): S1+S3 protect the design contract by ensuring its preconditions hold.
- Effective approach #6 (Z3 ordinal pattern): S2's model fallback chain reuses the acyclicity recipe.

### Integration with existing roles (concrete edits)
- **lead orchestrator**: composite gate — `S3.validate -> S1.preflight -> spawn`. Any failure aborts cleanly.
- **adventure-planner.md**: step 8/9 ("permission analysis") expands to emit the explicit permission_manifest S1 requires. Step 4/9 ("created schemas") includes the manifest_schema S3 will check against.
- **all worker roles**: gain implicit guarantee that their context is valid; can drop ad-hoc `if` checks that crept in during ADV-001..006.
- **profiling P1**: rate-limit-recovered runs still emit P1 rows with the fallback model recorded; permission-blocked tasks emit `result: blocked` rows.

### Out of scope
- Recovery from systemic API outages (S2 surfaces them, does not pretend to recover).
- Schema-evolution of the manifest itself (S3 validates against the current schema; schema migrations are a separate adventure-planner concern).
- Per-tool sandboxing or capability scoping inside an agent (responsibility of the runtime, not the orchestrator).
- Recovery from corrupted workspace state (e.g. partial writes mid-tool-call) — handled by the runtime's tool-call atomicity, not the pipeline layer.

### Estimated leverage
S1 alone: prevents the entire ADV-001 verification-bypass class — historically 4+ tasks per affected adventure passing review with no executed proof_command. Quality leverage is enormous (false-positive completion rate goes to zero).
S3 alone: prevents the ADV-001 reviewer-cwd disaster (9 false FAILED verdicts in one batch) and the ADV-002/003 manifest-validity incidents.
S2 alone: zero observed leverage today, bounded worst-case insurance.

Combined, the three skills convert the pipeline from "0 implementation rework, but tolerates significant silent failure" to "0 implementation rework, with silent-failure mode actively closed." This complements the optimization family (which amplifies leverage) and the profiling family (which makes leverage measurable).
