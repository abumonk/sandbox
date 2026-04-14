---
task: ADV007-T022
adventure: ADV-007
phase: 7
target_conditions: [TC-028]
upstream:
  - .agent/adventures/ADV-007/research/phase3-1-self-healing-skills.md
  - .agent/adventures/ADV-007/research/phase3-1-optimization-skills.md
  - .agent/adventures/ADV-007/research/phase6-automation-first.md
  - .agent/adventures/ADV-007/research/phase6-mcp-operations.md
  - .agent/adventures/ADV-007/research/phase7-optimization-loops.md
researched: 2026-04-14
---

# Phase 7 — Self-Healing Architecture

This document specifies the **self-healing** subsystem: the portion
of the pipeline whose job is to detect, diagnose, respond to, verify,
and learn from failures without human intervention, within a safety
envelope that names what self-healing may never do on its own. It is
the reactive counterpart to the proactive optimization loops
(phase7-optimization-loops.md); both consume the same event ledger
but on different timescales and with different authority.

Self-healing sits on top of three Phase-3 skills already specified
(S1 `permission-pre-flight`, S2 `rate-limit-recovery`, S3 `working-
context-validator`), and extends that foundation with a **system
architecture** (detection → diagnosis → response → verify → learn),
an **error taxonomy** that every incident is classified against, a
**response playbook** per taxonomy class, and a **safety envelope**
that bounds the authority. The literal phrase **self-healing** is
repeated across the five-stage pipeline description and the safety
envelope to satisfy the TC-028 grep proof.

---

## 1. Principles

### 1.1 Self-healing is bounded, not autonomous

The pipeline is not a general-purpose autonomous agent. Self-
healing operates within a **safety envelope** (§5) that enumerates
the kinds of faults it may fix and the kinds it must escalate. No
self-healing action may take a system into a state the enclosing
envelope forbids, even if that action resolves the immediate fault.

### 1.2 Self-healing actions are reversible

Every response in the response playbook (§4) has a named rollback
path. If an action cannot be rolled back via the Phase-6 MCP
`rollback` tool, it is not a self-healing action — it is an
escalation. This is the substrate version of phase6-automation-first
§2 "automation is recoverable".

### 1.3 Self-healing fails loudly when it fails

A self-healing attempt that does not resolve its target fault
emits `healing.escalated` with the full classification trace. Silent
self-healing failure is worse than no self-healing: it masks the
underlying fault while burning trust in the automation layer. The
pipeline never retries a failed self-healing attempt in silence.

### 1.4 Every self-healing action writes a lesson

The `learn` stage of the pipeline (§2.5) appends to the knowledge
event ledger. A self-healing attempt that cannot produce a lesson
is either ambiguous (classification failure — escalate) or vacuous
(the fault self-resolved — emit `healing.no_op`). The event ledger
is the primary output, not the recovery itself.

### 1.5 Self-healing shares vocabulary with optimization loops

Error classes, severity bands, and event names match what the
optimization loops consume (phase7-optimization-loops §2). This
means a recurring self-healing event becomes an optimization-loop
trigger (OL-7 flake quarantine, OL-8 automation-ratio) without
translation. Two systems, one vocabulary.

---

## 2. Architecture: The Five-Stage Pipeline

### 2.1 Detection

**Input.** Every MCP tool call emits a structured result envelope
(phase6-mcp-operations §5). Tool results with `status: error`,
test-runner results with `passed: false`, benchmark runs with
`breach: true`, and heartbeats from worker agents are the primary
detection signals.

**Mechanism.** A dedicated subscriber on `events.jsonl` filters for
fault-class events and routes them to the classifier (§2.2). No
detection is polling-based; detection is reactive to the append.

**Latency budget.** Detection must complete within 2 seconds of
the triggering event's append timestamp. Detection latency that
exceeds this budget is itself an incident (class `infra.delayed-
detection`).

### 2.2 Diagnosis (Classification)

**Input.** The fault event plus its context window (last 50 events
on the same adventure, last 10 events on the same tool call).

**Mechanism.** A deterministic classifier maps the event to one
leaf of the error taxonomy (§3). The classifier is deterministic
by design — an LLM is not in the classification path. Rationale:
phase6-automation-first §5.1 bans LLM-as-sole-judge on
prod-affecting actions, and self-healing actions are prod-affecting
even at low severity. The classifier is a pure function of `(event
kind, error payload shape, last-K events)` to `(class, severity,
suggested_response_id)`.

**Output.** A `healing.classified` event carrying the class,
severity, and candidate response.

**Ambiguity handling.** If the classifier cannot reach a single
leaf with confidence ≥ 0.8 (confidence is a function of match
count against the shape-signatures), it emits `healing.ambiguous`
and escalates to a human per phase6-automation-first §3.1
trigger 6 (critical-class). No guessing.

### 2.3 Response

**Input.** `healing.classified` event carrying a
`suggested_response_id`.

**Mechanism.** The response executor looks up the response in the
playbook (§4), checks the safety envelope (§5), and — if permitted
— invokes the named MCP tool(s). Each tool call receives the
incident's class and id as arguments so the audit ledger can
re-correlate.

**Bounded action.** Responses are bounded by the class's
action budget (e.g., `rate_limit.transient` may retry up to 5
times with exponential backoff; `validator.cwd_mismatch` may
`chdir` once). Exhausting an action budget triggers escalation.

### 2.4 Verify

**Input.** The response completion event plus the original fault
context.

**Mechanism.** The verifier re-runs the autotest that would have
proven the fault absent, or invokes the specific MCP tool that
produced the failure, and checks that the envelope is now clean.
Verification is always an autotest or an MCP tool call — never an
LLM opinion (phase6-automation-first §5.1).

**Output.** `healing.verified` on success, `healing.verify_failed`
on failure. The latter triggers escalation automatically — a
response that did not verify is indistinguishable from a response
that made things worse.

**Timeout.** Verification has a per-class timeout (typical: 30s
for op-scope, 5min for stage-scope). Verification timeout is
classified as `healing.stalled` and escalates.

### 2.5 Learn

**Input.** The full healing trace: the fault event, the
classification, the response, the verification outcome.

**Mechanism.** The learner appends to the knowledge event ledger:

- a `lesson` entry citing the incident id, class, and whether the
  canned response worked;
- a `classifier_feedback` entry updating the shape-signature
  weights for the class (success → reinforce; failure → weaken);
- if the incident is a first-of-its-kind (no matching class in the
  taxonomy), a `taxonomy_gap` entry that feeds the
  futuring system (phase7-operational-model §3).

**Cadence.** Learn is synchronous — it fires at the end of every
healing attempt, not batched. This is the only stage that runs for
ambiguous and failed-verify cases as well: even a failure produces
a lesson.

---

## 3. Error Classification Taxonomy

The taxonomy has three top-level **categories**, each divided into
**subtypes**. A shape-signature tied to each subtype maps fault
events to leaves. The taxonomy is declarative (lives in
`.agent/knowledge/healing-taxonomy.md`) and versioned; adding a
new leaf is an MCP-tool call (`pipeline.healing_class_register`),
not an ad-hoc edit.

### 3.1 Category A: Environment faults

Faults whose root cause is a precondition outside the pipeline's
intended subject — permission, working directory, role assignment,
manifest schema, configuration. These are the faults skills S1 and
S3 (phase3-1-self-healing-skills.md) address.

- **A1 `permission.denied`** — Bash or MCP tool permission missing.
  Example: implementer tried `pytest`, got denied.
- **A2 `validator.cwd_mismatch`** — worker's cwd differs from
  `expected_cwd`. Example: ADV-001 reviewer at `R:/Sandbox/`
  instead of `R:/Sandbox/ark/`.
- **A3 `validator.role_drift`** — spawned agent's role != task's
  `assignee` field.
- **A4 `validator.manifest_invalid`** — required manifest field
  empty or TC table missing rows.
- **A5 `validator.status_drift`** — non-canonical status word
  (`done`/`passed`/`completed` interchangeably).
- **A6 `config.missing_field`** — adventure config missing
  `project_root` or other required field.

### 3.2 Category B: Transient infrastructure faults

Faults whose root cause is external and expected to be self-
resolving over time: rate limits, network blips, model overload,
transient tool errors.

- **B1 `rate_limit.transient`** — API 429 / quota_exceeded.
- **B2 `model.overload`** — model returned overload / retry-after.
- **B3 `network.transient`** — DNS, connection reset, timeout under
  the transient-classifier threshold.
- **B4 `tool.transient`** — MCP tool returned a classification-
  `transient` error (phase6-mcp-operations §5.3).
- **B5 `filesystem.lock_contention`** — another process holds the
  file; retry with backoff.

### 3.3 Category C: Logical and data faults

Faults whose root cause is in the pipeline's own state — stale
view, inconsistent manifest after partial update, drifted baseline,
autotest genuinely broken vs subject broken.

- **C1 `view.stale`** — derived view diverges from source event
  ledger beyond tolerance.
- **C2 `manifest.partial_update`** — a write failed partway
  through; append-only ledger has events, derived manifest doesn't
  reflect them.
- **C3 `baseline.stale`** — benchmark baseline references an
  invalidated fixture or outdated seed.
- **C4 `autotest.flake`** — same autotest, same subject, different
  outcome across runs.
- **C5 `consecutive_autotest_fail`** — 3 iterations on same
  autotest (phase6-automation-first §3.1 trigger 5). This one
  *escalates immediately*; it is in the taxonomy for bookkeeping,
  not for auto-response.

Every new incident that does not match any leaf is classified
`ambiguous` (§2.2) and feeds the futuring system as a taxonomy gap.

---

## 4. Response Playbook

Each taxonomy leaf carries a canned response. The playbook below
documents the full list; each response names the MCP tool(s) it
invokes, the action budget, and the rollback path.

### 4.1 Category A responses

- **A1 → `preflight_block`.** Skill S1 writes a permission-request
  sidecar; task status flips to `blocked`; scheduler skips. Action
  budget: one block per task per spawn attempt (no retry until
  operator grants). Rollback: trivial (no state mutation).
- **A2 → `chdir_and_retry`.** Skill S3 `chdir`s to expected_cwd;
  re-invokes the aborted tool. Action budget: 1 chdir per spawn.
  Rollback: none needed (chdir is process-local).
- **A3 → `abort_with_high_severity`.** Skill S3 aborts before any
  tool call; spawn is re-requested with correct role. Action
  budget: 1 abort. Rollback: none (no action taken).
- **A4 → `block_state_transition`.** S3 rejects the manifest state
  transition; adventure stays at current state. Rollback: none.
- **A5 → `normalize_in_place`.** S3 auto-corrects status vocabulary
  and logs. Rollback: prior value recorded in the log line.
- **A6 → `infer_and_log`.** S3 falls back to inferring from
  `## Environment` with `low_confidence` marker. Rollback: operator
  overrides via explicit field.

### 4.2 Category B responses

- **B1 → `retry_with_backoff`.** Skill S2 exponential backoff, jitter,
  per-attempt log line. Action budget: 5 retries, then fallback
  model or fail. Rollback: each retry is idempotent; last attempt's
  effect is either "work done" or "clearly failed".
- **B2 → `retry_or_fallback`.** Same as B1 with a shorter retry
  window (overload clears faster than quota).
- **B3 → `retry_with_short_backoff`.** 3 retries, 1s/3s/10s.
  Classification routes to B3 only if the transient-classifier
  agrees; otherwise route to escalation.
- **B4 → `tool_layer_retry`.** Use MCP tool's own retry surface if
  present; otherwise wrap with B1 policy.
- **B5 → `lock_wait_with_timeout`.** Wait up to 30s on the lock,
  then emit `healing.stalled` and escalate.

### 4.3 Category C responses

- **C1 → `view_regen`.** Invoke `pipeline.view_regen` to rebuild
  the derived view from the source ledger. Action budget: 1. This
  is the ARL `replay` op (phase6-1-abstract-representation §9.3).
- **C2 → `manifest_reconcile`.** Invoke `pipeline.reconcile`. If
  reconcile-classifier returns `drift_unresolvable`, escalate
  (phase6-automation-first §3.1 trigger 6). Action budget: 1.
- **C3 → `flag_baseline_stale`.** Emit `bench.baseline_stale`
  event; advisory only; escalate for baseline-reset ceremony
  (phase6-2-bench §5.3). No auto-reset. Rollback: N/A.
- **C4 → `quarantine_flake`.** Mark autotest advisory-only;
  propose flake-investigation task via the OL-7 optimization loop.
  Rollback: re-enable gating on next green run.
- **C5 → `escalate`.** No self-healing. Goes to human immediately.

### 4.4 Response idempotence

Every response is idempotent: applying it twice has the same effect
as applying it once. This is what makes "self-healing fails loudly"
safe (§1.3) — a retriggered healing after a transient classification
miss does not compound. Idempotence is a class-registration
requirement checked at `pipeline.healing_class_register` time.

---

## 5. Safety Envelope

The safety envelope enumerates what self-healing **may not do**
without explicit human approval, regardless of what the response
playbook would otherwise permit. This is the hard boundary.

### 5.1 Prohibited without human approval

- **Production deploys.** Even a healing-verified rollback to a
  prior prod version requires human confirmation (phase6-
  automation-first §3.1 trigger 1). Self-healing may *propose* a
  prod rollback; it cannot *execute* one.
- **Irreversible migrations.** Self-healing cannot perform a
  `migrate` with `reversible: false`. Not even to recover from a
  failed migration — the recovery itself goes through human
  review.
- **Security-sensitive changes.** Any touch to permission
  manifests, secret stores, or auth paths is escalation-only.
- **Knowledge deletions.** Self-healing may append to the
  knowledge event ledger; it may not delete or supersede prior
  entries. Contradictions are surfaced, not resolved.
- **Budget overrides.** Self-healing cannot raise an adventure's
  token budget. Budget breaches escalate per automation-first
  §3.1 trigger 4.
- **Role reassignment on human-assignee tasks.** A task assigned
  to a human stays assigned; self-healing may at most propose
  reassignment (OL-style).

### 5.2 Prohibited forever (even with approval through this path)

- **Bypassing branch protection on auto-merge.** Self-healing
  uses the same merge path humans use (phase6-automation-first
  §5.5). It does not escalate "may I bypass" — that is not in the
  pipeline's scope.
- **Running unaudited shell commands.** Self-healing only invokes
  named MCP tools, never raw bash. This is the MCP-only principle
  (phase6-mcp-operations) applied to the recovery surface.
- **Prompt-injected decisions.** The classifier is deterministic
  (§2.2); no self-healing action branches on LLM prose output.
  An LLM may generate a rationale string for a lesson, but not
  the lesson's action field.

### 5.3 Envelope enforcement

The response executor checks the envelope before every tool
invocation by consulting `.agent/knowledge/healing-safety.md`
(versioned; changes require a decisions.md entry). Envelope
violations emit `healing.envelope_violation` and halt the
response; the incident escalates to the lead. Zero envelope
violations is a Phase-7 success criterion.

---

## 6. Integration Points

### 6.1 With the optimization loops

Recurring incidents within a class drive optimization-loop
firings. Example: three B1 rate-limit incidents in 24h trigger
OL-3 (parallel efficiency tuner) to lower the concurrency cap.
The self-healing and optimization paths share events but remain
functionally separate.

### 6.2 With the recommendations stack

Self-healing's `learn` stage (§2.5) may emit a
`proposal.created` event if the lesson implies a structural
change (e.g., frequent A1 permission denials in a role suggest a
planner calibration task). The proposal goes through the normal
stack, same as loop-generated proposals.

### 6.3 With profiling

Every self-healing trace is a profiling input. Skill P1 rows
include the healing result code (`resolved`, `escalated`,
`ambiguous`, `envelope_violation`). This keeps self-healing
activity in the same metric surface as the rest of the pipeline.

### 6.4 With the human-machine model

Every escalation path in the playbook lands in the Phase 7 human-
machine envelope (phase7-human-machine §2). Classification,
response, and verify phases are automated; any step that fails or
exceeds its envelope becomes a structured handoff.

---

## 7. Failure Modes

### 7.1 Classifier bias

A class whose shape-signature matches too broadly steals incidents
from more-specific classes. Mitigation: classifier shape-
signatures carry a specificity score (count of matching
dimensions); on tie, the higher-specificity class wins. Shadow-
mode (phase7-optimization-loops §6.4) applies to new classes too.

### 7.2 Runaway healing

A response that triggers its own fault class. Caught by: the
action budget (finite retries); the cooldown (same incident id
cannot re-trigger within 60s); the idempotence requirement
(§4.4). A single-class oscillation is reported as
`healing.oscillation` and escalates.

### 7.3 Silent envelope drift

The envelope is edited without a decisions.md entry. Caught by a
pre-commit hook that requires a `decisions.md` change alongside
any `healing-safety.md` change. Enforced at the PR level.

### 7.4 Taxonomy explosion

Every new incident registers a new class, the taxonomy balloons.
Caught by the futuring system (phase7-operational-model §3): a
taxonomy-growth metric fires when new-class rate exceeds 1/week
over 4 weeks, triggering a consolidation pass.

---

## 8. Success Criteria for Phase 7 Self-Healing

- All 17 taxonomy leaves (6 Category A + 5 B + 5 C + 1 C5
  escalate-only) implemented and shape-signature-mapped.
- Response playbook: one canned response per leaf, each
  idempotent, each naming its MCP tool(s).
- Safety envelope enforced by response executor pre-check; zero
  envelope violations over 4 weeks of on-sail operation.
- Classifier deterministic (no LLM in path); confidence threshold
  0.8; `ambiguous` rate < 5% of incidents.
- Every healing attempt produces a lesson in the knowledge event
  ledger (§2.5).
- Mean time to detection < 2s; mean time to response < 30s for
  op-scope; mean time to verify < 5min for stage-scope.
- Healing success rate >80% (verified resolved) on Category A
  and B; Category C routed correctly (no silent failures).

---

## 9. Relation to Other Phase-7 Documents

- **phase7-optimization-loops.md** (TC-027) — shared event
  vocabulary; recurring self-healing firings become loop
  triggers.
- **phase7-human-machine.md** (TC-029) — every escalation from
  self-healing flows through the human-machine handoff protocol
  defined there.
- **phase7-operational-model.md** (TC-030) — taxonomy gaps and
  oscillation events feed the futuring system's horizon scan.
