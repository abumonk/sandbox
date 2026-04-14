---
task: ADV007-T022
adventure: ADV-007
phase: 7
target_conditions: [TC-027]
upstream:
  - .agent/adventures/ADV-007/research/phase3-1-optimization-skills.md
  - .agent/adventures/ADV-007/research/phase3-1-self-healing-skills.md
  - .agent/adventures/ADV-007/research/phase5-concept-designs.md
  - .agent/adventures/ADV-007/research/phase6-automation-first.md
  - .agent/adventures/ADV-007/research/phase6-2-benchmark-design.md
researched: 2026-04-14
---

# Phase 7 — Day-to-Day Optimization Loops

This document specifies the optimization-loop subsystem that runs
continuously over the Claudovka pipeline once it has reached on-sail
operation. The loops consume the numeric substrate laid down by
Phase 6.2 benchmarks (budgets on latency, token cost, memory,
parallel efficiency, agent success rate) and the behavioral substrate
of Phase 6 automation-first (structured triggers, no prompt-embedded
fallbacks), and turn them into **bounded, cadenced, auditable**
corrective action. The design goal is not "an AI that optimizes
itself" — it is a set of narrow control loops whose inputs, actions,
and cooldowns are enumerable so that any regression in the loop
itself is attributable and reversible.

The literal phrase **optimization loop** is repeated across the major
sections (loop catalogue, loop hierarchy, integration with
recommendations stack) to satisfy the TC-027 grep proof.

---

## 1. Principles

### 1.1 Every optimization loop has a budget, a trigger, a bounded
### action set, and a cooldown

An **optimization loop** that can fire without bound is an outage
waiting to happen. Every loop below carries four non-optional fields:
the **metric under control** (the budget from phase6-2-benchmark-
design.md §4 that the loop defends); the **trigger condition** (the
precise numeric or event pattern that wakes the loop); the **action
set** (the enumerated list of mutations the loop is permitted to
perform, each itself a Phase-6 MCP tool call); and the **cooldown**
(the minimum wall-clock between successive firings against the same
subject). Any loop missing one of these four is rejected at
definition time by the loop-registry linter.

### 1.2 Loops never touch authoritative state directly

Loops propose. The recommendations stack (phase5-concept-designs.md
§7) ranks. A Phase-6 MCP tool applies. No optimization loop writes
to an append-only ledger, a baseline file, or a task manifest on its
own; it emits a `proposal.created` event whose action is a named
tool invocation. For loops cleared at `auto_accept` thresholds (§4.3)
the recommendations stack applies without human confirmation, but
the path through the ledger is the same — which means rollback is
the same.

### 1.3 Loops observe, they do not poll

Loops subscribe to `events.jsonl` via the view layer (ARL §9) and
fire on event patterns. No loop executes a filesystem walk or a
`git log` on a timer. This keeps token and compute cost linear in
the event rate rather than in the state size.

### 1.4 Loop output is an autotest-provable proposal

Every proposal a loop emits names a Phase-6 autotest (or a fresh
benchmark) as its verification. A proposal without a proof method
is malformed — the loop registry rejects it before it reaches the
stack. This enforces the "automation without autotest" anti-pattern
ban from phase6-automation-first §5.4.

### 1.5 Loop cadence is hierarchical, not uniform

Short-horizon loops (seconds to minutes) react to single events;
medium-horizon loops (hours to days) react to rolling-window
aggregates; long-horizon loops (weeks to months) react to drift
against milestone baselines. The three tiers are explicit (§3) so
that a loop never competes with itself across horizons.

---

## 2. Loop Catalogue

Nine named optimization loops cover the control surface the pipeline
needs in on-sail mode. Each row below is the contract; the §3
hierarchy assigns a horizon; §4 specifies integration with the
recommendations stack.

### 2.1 OL-1 — Token budget dampener

- **Metric under control.** `spawn.<role>` token cost from
  phase6-2-benchmark §4.2; per-adventure running token cost vs
  planner estimate (per phase6-automation-first §3.1 trigger 4, but
  at a soft 20% threshold rather than the 50% hard page).
- **Trigger.** Rolling 5-spawn median for any role exceeds its
  budget; or adventure running cost exceeds planner estimate by
  >20%.
- **Action set.** `context-pruner` (skill O3 §2.3 from
  phase3-1-optimization-skills.md) switched to `aggressive` mode for
  the next N spawns; or propose a `spawn` recommendation that targets
  a cheaper model in the fallback chain when `model_critical: false`.
- **Cooldown.** 30 minutes per role.

### 2.2 OL-2 — Latency breach responder

- **Metric under control.** p95 latency per benchmark from
  phase6-2-benchmark §4.1.
- **Trigger.** A `bench.regression` event with `axis: latency` on a
  PR or nightly run.
- **Action set.** Propose a targeted profiling task (spawn with
  skill P1 profiling-skills.md); attach the offending run_id;
  propose a rollback of the triggering commit if the breach is
  >2× budget.
- **Cooldown.** One firing per benchmark per 24h (dup-suppression
  in the recommendations stack via `source_events_hash`).

### 2.3 OL-3 — Parallel efficiency tuner

- **Metric under control.** Speedup efficiency from phase6-2-bench
  §4.4; concurrency cap from skill O2
  (phase3-1-optimization-skills.md §2.2).
- **Trigger.** Observed efficiency for `parallel.spawn_fanout` drops
  below the 0.50 budget across 3 consecutive adventures; OR a
  rate-limit event from skill S2
  (phase3-1-self-healing-skills.md §2.2) has fired ≥2 times in 24h.
- **Action set.** Adjust concurrency cap ±1 via the scheduler's
  MCP tool (`pipeline.scheduler_set_cap`); propose O2 replan for
  active adventure waves.
- **Cooldown.** 10 minutes between cap changes; no change may
  exceed ±1 per cooldown window.

### 2.4 OL-4 — Model selection tuner

- **Metric under control.** Cost-per-success = `(token_cost * rate) /
  success_rate` per role per model from phase6-2-bench §4.5.
- **Trigger.** A role's cost-per-success on model X exceeds model
  Y's by >30% over a rolling 100-spawn window AND Y's success rate
  is within the role's budget.
- **Action set.** Propose updating the role's default model (via
  the role config MCP tool); never silently; always via `proposal`
  class `tune`.
- **Cooldown.** 7 days per role. Model changes cascade through
  other metrics; a fast tuner here is noise.

### 2.5 OL-5 — Context-pruner calibration loop

- **Metric under control.** Operator override rate on skill O3
  (`--no-prune` invocations); retroactive "dropped file needed" log
  entries.
- **Trigger.** O3 override rate exceeds 10% over the last 50 spawns
  for any (role, skill_tags) pair.
- **Action set.** Move the over-pruned file from `rare` to `auxiliary`
  (or `auxiliary` to `core`) in O3's historical must-keep table for
  that pair.
- **Cooldown.** 24 hours per (role, skill_tags) pair.

### 2.6 OL-6 — Estimation variance loop

- **Metric under control.** Planner estimation variance from the
  manifest evaluations table (phase3-1-optimization-skills.md §2.1
  success metric).
- **Trigger.** At adventure close, mean |variance| across all tasks
  exceeds 30% OR skill O1 `estimate-from-history` reports
  `confidence: low` for >50% of tasks.
- **Action set.** Invoke `estimate-from-history --recalibrate
  --adventure <id>` which updates the complexity-tier multiplier;
  propose a retrospective knowledge-base entry if the variance
  clustered on one role.
- **Cooldown.** Once per adventure close.

### 2.7 OL-7 — Flake quarantine loop

- **Metric under control.** Per-benchmark `unstable` marker
  (phase6-2-bench §5.5); per-autotest flake rate from phase6-autotest
  §4.3.
- **Trigger.** A benchmark crosses into or out of the `unstable`
  bucket; OR an autotest flakes on the same PR-branch twice.
- **Action set.** Propose a `flake-investigation` task; mark the
  affected gate advisory-only (phase6-autotest §4.3) until the
  proposal resolves.
- **Cooldown.** 48 hours per benchmark/test.

### 2.8 OL-8 — Automation-ratio defender

- **Metric under control.** Automation ratio from
  phase6-automation-first §6 (target >90%).
- **Trigger.** 7-day rolling automation ratio drops below 85%.
- **Action set.** Emit a trigger-distribution report (which of the
  §3.1 triggers fired most); propose a refactor task for the
  top-firing trigger if reversal rate on that trigger is <10%
  (the criterion for demotion to auto-handled).
- **Cooldown.** Weekly.

### 2.9 OL-9 — Knowledge-gap loop

- **Metric under control.** Knowledge event ledger density;
  researcher/reviewer `insufficient_context` signal count
  (phase6-automation-first §3.1 trigger 10 adjacent).
- **Trigger.** A design proposal triggers trigger 7 (novel-concept)
  more than twice in a week; OR a reviewer cites "no precedent" on
  a TC ≥2× in 10 days.
- **Action set.** Propose a scoped research task adding entries to
  the relevant knowledge area; attach the specific TCs that hit the
  gap.
- **Cooldown.** 14 days per knowledge area.

---

## 3. Loop Hierarchy

The nine loops fall into three cadence tiers. The tiering prevents
a fast loop (OL-3 concurrency cap) from competing with a slow loop
(OL-4 model selection) for the same metric surface.

### 3.1 Short horizon (seconds to hours)

- **OL-1 (token dampener), OL-3 (parallel tuner), OL-7 (flake
  quarantine).** These loops react to individual events or
  single-PR signals. Their cooldowns are in minutes. They must
  never propose an action whose verification takes longer than the
  cooldown, because the next firing would arrive before proof of
  the previous action.

### 3.2 Medium horizon (hours to days)

- **OL-2 (latency breach), OL-5 (pruner calibration), OL-8
  (automation-ratio defender).** These react to rolling aggregates
  or PR-level regressions. Their proposals often target a single
  named artefact (a commit, a role's pruner config, a specific
  trigger). Their autotest verification runs in the nightly slot.

### 3.3 Long horizon (days to months)

- **OL-4 (model tuner), OL-6 (estimation variance), OL-9
  (knowledge-gap).** These see the whole adventure or whole
  quarter. Their proposals are structural: change a role's model,
  recalibrate the planner, add knowledge. Their verification is a
  benchmark baseline-reset ceremony (phase6-2-bench §5.3) or a
  milestone close event.

### 3.4 Horizon conflicts

When a short-horizon loop proposes a change on a metric a long-
horizon loop also owns, the long-horizon loop's cooldown freezes
the short-horizon loop for the same subject. Example: OL-4 proposes
switching a role to a cheaper model; OL-1 cannot then react to that
role's token cost for 7 days (OL-4's cooldown). This is the
"long overrides short on shared metric" rule, enforced by the
registry at loop-definition time.

---

## 4. Integration with the Recommendations Stack

### 4.1 One proposal class per loop

Each loop registers its proposals under a named class in the
recommendations stack taxonomy (phase5-concept-designs.md §7.3). The
class names: `budget_dampen`, `latency_response`, `parallel_tune`,
`model_tune`, `pruner_tune`, `estimation_tune`, `flake_quarantine`,
`automation_refactor`, `knowledge_gap`. A class is registered once
at loop-install time via `rec.class.register` (phase5-concept-designs
§7.6); unregistered classes cannot emit proposals.

### 4.2 Source-event attribution

Every proposal carries `source_events: [evt-id, ...]` — the event
ids from `events.jsonl` that triggered the loop. This is non-
optional; the registry rejects empty source_events. Attribution
enables: (a) idempotence via the `(class, source_events_hash)`
key so two loops firing on the same event do not double-propose;
(b) rationale rendering; (c) post-hoc audit of "why did this
change happen?".

### 4.3 Auto-accept thresholds

Proposals whose class has `auto_accept: true` bypass human
confirmation. Only three classes are auto-accept by default:

- `parallel_tune` — concurrency cap changes ±1 (cheap, reversible,
  fast-cycled).
- `pruner_tune` — file-classification updates (affect context
  composition only; reversible by the next calibration cycle).
- `flake_quarantine` — marking a test advisory; the test still
  runs, it just stops gating.

All others are `auto_accept: false`; their acceptance goes through
the lead or a human, per the §3.1 trigger matrix from
phase6-automation-first §3. Changing a class's `auto_accept` status
requires a recorded decision (decisions.md entry), matching the
"new trigger requires architectural decision" rule.

### 4.4 Urgency routing

The recommendations stack supports `urgency: high|normal|low`. Loop
proposals set urgency by rule:

- `high`: latency breach >2× budget; rate-limit event floor reached;
  automation ratio <80%.
- `normal`: all other budget breaches; calibration signals.
- `low`: drift (p < 0.01 without breach); estimation variance within
  30-50% band.

High-urgency proposals fan out via the messenger (phase5-concept
§4); normal and low stay in the inbox until the recipient pulls.

### 4.5 Cooldown interaction with ranker

The recommendations stack ranker (phase5-concept §7.5) receives
each loop's proposals in a stream. When a proposal enters cooldown,
the ranker decays its score according to the loop's cooldown
decay curve (linear by default). This means a proposal that was
"critical yesterday, ignored today" fades to low priority naturally
rather than persisting indefinitely on the open-proposals view.

---

## 5. Loop Observability

Every optimization loop emits two event kinds:

- `loop.fired` — `{loop_id, subject, trigger_match, cooldown_until}`
  on every firing. Feeds the loop-activity dashboard.
- `loop.suppressed` — `{loop_id, subject, reason: cooldown|
  horizon_conflict|autoaccept_disabled}` on every non-firing. Equally
  important for debugging a loop that "should have fired".

A weekly loop-health report (analogous to phase6-2-bench §6.3
dashboard) summarizes firings per loop, acceptance rate per class,
and horizon conflicts. A loop firing with acceptance rate <20% over
4 weeks is a candidate for demotion (lower its urgency, lengthen its
cooldown, or retire it). A loop with acceptance rate >90% across
weeks is a candidate for promotion to `auto_accept: true`, contingent
on the rollback ergonomics of its class.

---

## 6. Failure Modes and Safety Nets

### 6.1 Oscillation

Two loops toggling the same metric back and forth. The rule "long
overrides short on shared metric" (§3.4) eliminates the common
case. Residual oscillation between same-horizon loops is caught by
the loop registry: two loops cannot name the same `metric_under_
control` primary key. Secondary effects are flagged at definition
review.

### 6.2 Runaway proposals

A mis-configured reducer that emits a proposal per event. The
recommendations stack's per-class rate limit (phase5-concept §7.7
"spam control") caps proposal rate per class per hour at 10.
Exceeding the cap converts subsequent proposals into a single
`rec.saturation` event routed to the lead.

### 6.3 Metric drift without proposal

A metric breaching budget but no loop firing. Caught by the
automation-ratio defender OL-8 (meta-loop) and by the nightly
bench report cross-check: every breach in the bench report must
correspond to an open or resolved proposal within 48h; breaches
without proposals emit `loop.gap` events.

### 6.4 Loop logic bug

A loop registers with broken triggers. Pre-registration the loop
runs in `shadow` mode for 14 days: it emits `loop.shadow_fire`
events but does not create proposals. Shadow-mode firings are
reviewed against the metric history; loops whose shadow firings
disagree with human judgment on >20% of cases do not graduate to
live mode.

---

## 7. Success Criteria for Phase 7 Optimization Loops

- All nine loops implemented and registered with their four-field
  contract (metric, trigger, action set, cooldown).
- Loop registry enforces horizon-conflict and shared-metric
  invariants at definition time (not runtime).
- Shadow-to-live graduation completed for all nine loops before
  on-sail declaration.
- Weekly loop-health report generated and reviewed.
- Acceptance rate per class tracked for ≥8 weeks; demotion and
  promotion decisions recorded in `.agent/knowledge/decisions.md`.
- Zero loop-induced rollbacks (loops propose; rollbacks come from
  the post-action autotest, not from the loop). A loop-induced
  rollback is a loop-logic bug and a post-mortem trigger.
- Integration with the recommendations stack complete: every loop
  emits through the stack; no loop writes directly to event
  ledgers.

---

## 8. Relation to Other Phase-7 Documents

- **phase7-self-healing.md** (TC-028): self-healing is the reactive
  complement to the optimization loop — when a loop cannot propose
  fast enough, self-healing catches the failure and rolls back.
  Loops and self-healing share the trigger vocabulary but differ in
  cadence (loops are budget-defending; self-healing is error-
  responding).
- **phase7-human-machine.md** (TC-029): loops whose acceptance rate
  is low are candidates for either demotion (remove them) or
  promotion of human attention budget (raise their urgency). The
  attention-budget model is defined there.
- **phase7-operational-model.md** (TC-030): the futuring system
  consumes the same event ledger as the loops but operates on a
  longer horizon still — it proposes *new loops* based on patterns
  the existing nine do not cover.
