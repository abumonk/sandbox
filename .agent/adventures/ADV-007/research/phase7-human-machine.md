---
task: ADV007-T022
adventure: ADV-007
phase: 7
target_conditions: [TC-029]
upstream:
  - .agent/adventures/ADV-007/research/phase6-automation-first.md
  - .agent/adventures/ADV-007/research/phase5-concept-designs.md
  - .agent/adventures/ADV-007/research/phase7-optimization-loops.md
  - .agent/adventures/ADV-007/research/phase7-self-healing.md
researched: 2026-04-14
---

# Phase 7 — Human-Machine Balance Model

This document specifies how Claudovka divides work between automated
agents and human operators during steady-state operation. It extends
the **automation-first** principle established in T019 (phase 6) into
a concrete escalation matrix, a handoff protocol, a context-package
schema for humans, and an attention-budget model that bounds how much
human cognitive load the system is permitted to consume per day.

The target condition TC-029 is satisfied by the explicit
**escalation matrix** (section 3) and the **attention budget**
(section 5). Both are mechanized: the escalation matrix is a Rust
enum with associated predicates, and the attention budget is a signed
counter maintained by the orchestrator.

---

## 1. Operating Premise: Automation-First, Human-Exception

The baseline posture is that every decision point in the pipeline is
handled by an agent. Humans are invoked only when the orchestrator
raises an `EscalationEvent`, and each such event is typed, logged,
and budgeted. This inverts the conventional "human-in-the-loop"
framing: humans are **on-call for named exceptions**, not gatekeepers
of routine work.

Three consequences follow:

1. The system owes humans a **context package** rich enough that the
   handoff does not cost a full re-investigation. If we cannot
   construct such a package, the escalation is premature.
2. The system owes humans a **budget** — a bound on interruptions
   per day. If the budget is exhausted, the orchestrator must either
   defer non-urgent escalations or self-throttle the work that
   generates them.
3. The system owes humans a **return path** — a way to replay the
   human's decision as a rule so the same escalation does not recur.
   This is the mechanism by which the automation-first boundary
   advances over time.

---

## 2. Roles in the Balance

Claudovka recognizes four human roles with distinct escalation
contracts. Each role has an SLA, a channel, and a context-package
template.

| Role          | SLA        | Channel          | Typical Triggers                    |
|---------------|------------|------------------|-------------------------------------|
| Operator      | 15 min     | Live terminal    | Auto-fix failed, data loss risk     |
| Reviewer      | 4 hours    | PR / queue       | Policy-gate reject, novel diff      |
| Architect     | 1 day      | Weekly queue     | New decision class, constraint drift|
| Owner         | On demand  | Dashboard        | Budget/cost breach, strategic pivot |

The point of naming four roles is that the orchestrator can route
escalations without guessing. An auto-fix loop that has exhausted its
retry budget pages the **operator** — not the architect — because the
question is "unblock now", not "redesign". A novel change to the
Z3 invariant set pages the **architect**, not the operator, because
the question is "is this a legal move in our semantics", which has
no runtime-urgency component.

---

## 3. Escalation Matrix (TC-029)

The escalation matrix is the enumeration of concrete conditions under
which an agent is required to stop and hand off. Each row is a typed
event in the orchestrator with a predicate, a target role, and a
budget cost. Agents are forbidden from escalating outside this matrix;
an un-typed escalation is itself a bug reported to the architect.

```rust
pub enum EscalationEvent {
    AutoFixExhausted { task: TaskId, attempts: u8 },       // -> Operator
    VerifyInvariantDrift { spec: SpecId, delta: Diff },    // -> Architect
    PolicyGateReject { pr: PrId, rule: PolicyId },         // -> Reviewer
    NovelSemanticChange { spec: SpecId, kind: NoveltyKind },// -> Architect
    BudgetBreach { dim: Dim, over_pct: f32 },              // -> Owner
    DataLossRisk { artifact: Path, reason: String },       // -> Operator
    ConstraintConflict { rules: Vec<RuleId> },             // -> Architect
    HumanRequestedReview { pr: PrId, asker: AgentId },     // -> Reviewer
}
```

Mapping rules — tied directly to automation-first:

- **AutoFixExhausted** fires only after the self-healing loop
  (phase7-self-healing.md §4) has consumed its retry budget. The
  operator's job is narrow: unblock and, if the fix generalizes, ask
  the architect to file a new skill.
- **VerifyInvariantDrift** fires when the Z3 verifier reports a
  previously-passing invariant now failing and the change set touches
  the spec's declared invariants. This is the one class we refuse to
  auto-accept even if tests pass, because the guarantee itself moved.
- **PolicyGateReject** is the one routine human touch — a reviewer
  signs off on a policy exception or confirms the rejection stands.
  The reviewer's decision is fed back as a rule update candidate.
- **NovelSemanticChange** — detected by diffing AST shapes against a
  registered set of known shape classes. A new shape class requires
  architect review before the skill set is allowed to pattern-match
  on it.
- **BudgetBreach** — token, cost, wall-clock, or error-rate budget
  exceeded for the adventure. Owner decides stop/continue/rescope.
- **DataLossRisk** — an agent proposes an operation that deletes or
  overwrites state outside the sandbox boundary. Always operator.
- **ConstraintConflict** — two skills disagree on a gate. Never
  auto-resolved by vote; architect adjudicates the conflict as a
  semantic issue and publishes a tie-break rule.
- **HumanRequestedReview** — the "escape valve". Any agent may
  request a reviewer if its confidence drops below a threshold, even
  when no other row fires. Overused requests trigger a meta-alert to
  the architect: the agent's calibration may be off.

Each row carries a budget cost (below). Agents may not fire an event
whose cost would exceed the remaining daily budget for its target
role without first being deferred or queued.

---

## 4. Handoff Protocol and Context Package

A handoff is only valid if the orchestrator attaches a **context
package** matching the role's template. Missing fields are a
handoff-rejected error; the agent must either populate them or
downgrade to a deferred queue entry.

Common envelope (all roles):

```yaml
escalation_id: esc-<ulid>
event: AutoFixExhausted
raised_at: 2026-04-14T09:12:33Z
raised_by: agent:self-healer@1.4
task_id: ADV007-T022
adventure_id: ADV-007
budget_cost: 1.0
deadline: 2026-04-14T09:27:33Z   # raised_at + role SLA
return_path: handoff-return-1a2b  # see section 6
```

Role-specific body templates:

- **Operator package**: last N lines of each failing log, the failing
  command and exit code, the inverse-operation (rollback) snippet,
  and the smallest test that reproduces. No prose rationale — the
  operator reads logs, not essays.
- **Reviewer package**: the PR link, the rule that triggered, the
  diff scoped to the offending hunks, similar past decisions with
  outcomes, and a pre-drafted "approve" and "reject" comment.
- **Architect package**: the spec diff, the invariant(s) whose
  proof changed, the concept-graph neighborhood (phase5-concept-
  designs §3), and a list of downstream consumers of the changed
  surface.
- **Owner package**: the budget dimension, the trajectory chart, the
  projected completion cost under three scopes (stop / continue /
  rescope), and a one-paragraph plain-English summary.

A context package is generated by the agent raising the escalation.
The agent is required to construct it locally before the escalation
is considered raised; the orchestrator will not page until the
package validates against its template. This prevents the
degenerate case where an agent "escalates" by dumping undifferentiated
state onto a human.

---

## 5. Attention Budget Model

The attention budget is a per-role, per-day scalar that quantifies
how much human cognition the system is permitted to consume.

```
Budget(role, day) = BaseCapacity(role) * HealthFactor(role, day)
```

Default base capacities (tunable per deployment):

| Role       | Base capacity (units/day) | Unit definition           |
|------------|---------------------------|---------------------------|
| Operator   | 8                         | 1 unit = 10-minute engage |
| Reviewer   | 12                        | 1 unit = 1 PR review      |
| Architect  | 3                         | 1 unit = 1 design decision|
| Owner      | 2                         | 1 unit = 1 strategic call |

`HealthFactor` starts at 1.0 and decreases under observed load:
failed escalations (the human rejected the package as inadequate),
late responses (past SLA), and stacking (two escalations for the same
root cause) all subtract. The factor is published back into the
orchestrator so that agents can **see** the remaining budget and
self-regulate.

Budget-aware agent behavior:

- If an agent is about to raise an escalation but the target role's
  remaining budget is < 1.0, the agent must:
  1. Attempt a lower-cost alternative (defer, downgrade, widen
     auto-retry window, or request a different role).
  2. If none exists and the event is non-urgent (not DataLossRisk,
     not BudgetBreach, not AutoFixExhausted on a blocking task),
     enqueue the escalation for the next day with a justification.
  3. If it is urgent, raise anyway but emit a **budget-overrun**
     signal that is itself surfaced to the owner.

This model makes human attention a first-class, measured resource
rather than a free variable. It is the dual of the token/cost budget
tracked elsewhere in the adventure framework.

---

## 6. Return Path: Converting Decisions into Rules

Every human decision made through an escalation has a **return path
id** in the envelope. When the human acts, the orchestrator captures:

- the decision (accept / reject / modify / defer)
- any free-text rationale (optional)
- the full context package as it was at decision time

These tuples land in `.agent/knowledge/human-decisions.jsonl`. A
weekly **rule-extraction** run (owned by the architect role) scans
the log for:

- Recurring (role, event-type, decision) triplets — candidates for a
  new automatic rule that short-circuits the escalation next time.
- Contradictory decisions on near-identical packages — candidates
  for architect attention because the system's current
  representation is not distinguishing them.
- High-budget-cost recurring events — candidates for investment in
  a dedicated skill or an MCP tool.

Rule extraction feeds the recommendations stack (T018 §7) as a
dedicated source channel. The goal is that the automation-first
boundary is always **advancing leftward**: each week, a category
that used to require a human is now handled by a rule, and new
categories take the freed budget.

---

## 7. Failure Modes and Counter-Designs

Four anti-patterns to watch, each with an explicit counter-design:

1. **Paging-storm after deploy.** Counter: escalations within 30
   minutes of a known deploy share a single envelope until the
   deploy stabilizes. Reviewer gets one batched package, not ten.
2. **Context-package bloat.** Counter: strict token ceilings per
   role template (operator: 2k, reviewer: 8k, architect: 16k,
   owner: 4k). Agents that violate are rejected and must re-package.
3. **Silent human override.** Counter: every decision must be typed
   (accept/reject/modify/defer); free-text-only decisions are
   rejected so the rule extractor has structured input.
4. **Budget gaming.** Counter: an agent cannot avoid raising an
   escalation by reclassifying — the event taxonomy is closed and
   the verifier checks that the chosen event matches the predicate.

---

## 8. Target Condition Compliance

- **TC-029 — escalation criteria with attention budget**: satisfied
  by sections 3 (typed matrix, concrete triggers tied to
  automation-first) and 5 (per-role, per-day budget with
  health-factor feedback and agent self-regulation). Both artifacts
  are mechanized in the orchestrator enum and the budget counter
  respectively; neither is narrative-only.
