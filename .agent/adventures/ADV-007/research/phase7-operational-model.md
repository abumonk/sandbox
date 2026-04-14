---
task: ADV007-T022
adventure: ADV-007
phase: 7
target_conditions: [TC-030]
upstream:
  - .agent/adventures/ADV-007/research/phase5-concept-designs.md
  - .agent/adventures/ADV-007/research/phase6-automation-first.md
  - .agent/adventures/ADV-007/research/phase7-optimization-loops.md
  - .agent/adventures/ADV-007/research/phase7-self-healing.md
  - .agent/adventures/ADV-007/research/phase7-human-machine.md
researched: 2026-04-14
---

# Phase 7 — Operational Model: Futuring System

This document specifies Claudovka's **futuring** subsystem: the
proactive, horizon-scanning capability that identifies improvements
to the system itself *before* they are required by a failing test,
an escalated incident, or a user request. It is the forward-looking
counterpart to the reactive optimization loops (phase7-optimization-
loops.md) and the reactive self-healing architecture (phase7-self-
healing.md).

Target condition TC-030 is satisfied by the explicit **futuring
cadence** (section 3), the **signal taxonomy** (section 4), the
**proactive backlog schema** (section 6), and the integration
contract with the recommendations stack from T018 (section 7).

---

## 1. Why Futuring Exists

A system that only reacts to failures asymptotically approaches its
current baseline — it cannot reach a better baseline except by
accident. A system that only reacts to user requests moves at the
pace of the user's imagination, which is bounded by what the user
already believes is possible. Futuring is the deliberate discipline
of *looking ahead*: surveying weak signals, extrapolating trends,
and queuing improvements whose value will be realized in weeks or
months, not hours.

Three concrete outcomes define success:

1. **A ranked proactive backlog** — always populated, always fresh,
   always readable by both agents and humans.
2. **A measurable hit rate** — of the proactive items acted on, what
   fraction prevented a later incident, unlocked a later feature, or
   reduced a later cost? The rate must be tracked so the subsystem
   itself is subject to optimization.
3. **A bounded footprint** — futuring is a background activity. It
   must not dominate the token or attention budget; its own cost is
   budgeted and reported.

Futuring is *not* speculative architecture astronomy. Every item it
produces carries a concrete "what would we do on Monday" next step.

---

## 2. Subsystem Overview

The futuring subsystem has four stages, each implemented as a skill
in the Role-Skill library, each independently schedulable:

```
   [ Horizon Scanner ]  -->  signals.jsonl
           |
           v
   [ Signal Synthesizer ] --> hypotheses.jsonl
           |
           v
   [ Hypothesis Evaluator ] --> backlog.yaml  (proactive-backlog)
           |
           v
   [ Proposal Router ] --> recommendations stack (T018)
```

Each stage writes a typed artifact consumed by the next. The
artifacts are ordinary files under `.agent/futuring/` so they can be
versioned, diffed, and reviewed. No stage has hidden state.

---

## 3. Horizon Scanning: Cadence and Outputs (TC-030)

The scanner runs on three fixed cadences, each with a distinct
horizon and a distinct output budget.

| Cadence | Horizon  | Token budget | Primary outputs                        |
|---------|----------|--------------|----------------------------------------|
| Daily   | 1-3 days | 8k           | tactical signals, drift flags          |
| Weekly  | 2-6 wk   | 40k          | hypotheses, candidate backlog entries  |
| Monthly | 1-2 qtr  | 120k         | strategic briefs, roadmap adjustments  |

The daily run is cheap and narrow: it diffs yesterday's metrics
snapshot against the trailing 28-day band and flags metrics that
crossed a control limit. The weekly run is the main generative
step: it synthesizes the week's signals into hypotheses and scores
them. The monthly run steps back further and asks whether the
adventure portfolio itself is aimed at the right problems.

Each run produces a dated artifact with a fixed schema. The weekly
`hypotheses.jsonl` file is the canonical entry point for the rest
of the pipeline; other artifacts feed into it.

Outputs must be **actionable, not descriptive**. A signal of the
form "token usage is trending up" is rejected; the required form is
"token usage is trending up at 4%/week, extrapolates to exceed the
adventure budget by day 58; earliest mitigation is caching the spec
index (T018 §4) — draft task attached."

---

## 4. Signal Taxonomy

Five signal classes, each with its own collector, its own storage,
and its own decay rule. Keeping them typed means the synthesizer
can reason about them uniformly.

1. **Metric signals** — deviations from control limits in the
   optimization-loop metrics (phase7-optimization-loops.md §3).
   Collected automatically. Decay: 7 days unless promoted.
2. **Escalation signals** — patterns in
   `human-decisions.jsonl` (phase7-human-machine.md §6) that
   suggest automatable categories. Decay: 30 days.
3. **External signals** — changes in upstream dependencies
   (language versions, MCP protocol revisions, model releases,
   library deprecations). Collected via WebSearch on a weekly
   cadence with a whitelist of sources. Decay: 90 days.
4. **Internal-knowledge signals** — new entries in
   `.agent/knowledge/{patterns,issues,decisions}.md` that recur
   across adventures. Collected by the researcher role as a
   byproduct of its normal work. Decay: 60 days.
5. **User-intent signals** — themes that repeat across user
   requests even when no single request was a feature ask.
   Decay: 30 days.

Each signal is stored as a single JSON line with a stable
`signal_id`, a `class`, a `collected_at`, a `source_ref`
(file/line/URL), a `strength` score in [0,1], and a
one-sentence `summary`. The schema is fixed so downstream stages
can be purely data-driven.

---

## 5. Signal Synthesis: From Signals to Hypotheses

The synthesizer's job is to cluster signals into **hypotheses**:
statements of the form "if we did X, outcome Y would likely occur
within horizon Z, at cost C." Every hypothesis must cite at least
two signals (single-signal hypotheses are filed as low-priority
"hunches" and given their own channel so they are not lost but do
not clog the backlog).

The synthesizer is itself a Role-Skill composition:

- **Clustering skill** — groups signals by concept-graph proximity
  using the ontology from phase5-concept-designs.md §3.
- **Hypothesis-drafting skill** — for each cluster, drafts the
  if/then/horizon/cost statement with an evidence list.
- **Critique skill** — applies a checklist (falsifiability, unique
  action, bounded cost, non-duplication against existing backlog)
  and rejects drafts that fail any check.

Hypothesis records carry a `confidence` (how sure are we the claim
is true), a `value` (estimated benefit if acted on), and a `cost`
(estimated work to validate/implement). The scoring function that
turns these into a priority is identical to the one used by the
recommendations stack (T018 §7), so proactive and reactive items
compete on a single scale.

---

## 6. Proactive Backlog Schema

The proactive backlog is a YAML file at
`.agent/futuring/backlog.yaml`. Each entry has:

```yaml
- id: fut-0042
  title: Pre-warm Z3 solver pool for verify-heavy adventures
  created: 2026-04-11
  horizon: 2-4 weeks
  signals: [sig-2024, sig-2031, sig-2033]
  hypothesis: |
    Verification wall-clock is dominated by solver startup on
    cold adventures. Keeping a warm pool across the adventure
    would cut phase-wall-clock by an estimated 18%.
  confidence: 0.7
  estimated_value: 0.6        # normalized, see T018 §7
  estimated_cost: 0.3
  priority_score: 0.14        # value * confidence - cost * 0.3
  next_action: |
    Prototype a one-solver pool in ark_verify.py and measure on
    ADV-005 replay.
  status: candidate            # candidate | accepted | rejected | done
  owner: none                  # filled on acceptance
  last_reviewed: 2026-04-14
```

Invariants on the backlog:

- Maximum 50 active entries. When full, the lowest-priority
  candidate is archived (not deleted — archived to
  `backlog-archive/YYYY-QN.yaml` for rule-extraction mining).
- Each entry has a `last_reviewed` date; an entry not touched in 30
  days is auto-downgraded one priority tier.
- A `candidate` that reaches priority > 0.5 is auto-promoted into
  a draft adventure plan and routed to the owner role for
  acceptance.

---

## 7. Integration with the Recommendations Stack (T018)

The recommendations stack from T018 §7 is the system's single
queue of things the orchestrator *might* do next. Futuring is one
of its input channels — it does not replace or compete with the
stack, it feeds it.

Input channels (restating for context, and adding futuring):

1. **Reactive** — failing tests, escalations, budget breaches.
2. **User-request** — explicit user asks.
3. **Rule-extraction** — patterns mined from
   `human-decisions.jsonl` (phase7-human-machine.md §6).
4. **Futuring** — this subsystem, proactive entries from the
   backlog above. *New in this design.*

Channel-specific behavior:

- Futuring items enter the stack at their computed priority_score
  but with a channel tag `source=futuring`. The stack's consumer
  policies can weight channels differently: the default is that
  reactive outranks futuring at equal score, and user-request
  outranks both, but a futuring item with high confidence and
  low cost can still preempt a low-priority reactive item.
- Futuring items carry their full context package (hypothesis,
  signals, next_action) so they do not need a separate fetch.
- When a futuring item is consumed, its outcome (did acting on it
  produce the predicted Y within horizon Z?) is written back to
  `.agent/futuring/outcomes.jsonl`. This closes the loop and
  feeds the hit-rate metric in section 1.

The integration point is deliberately narrow: futuring writes to
the stack, reads nothing from it directly. This keeps the
subsystem testable in isolation and prevents feedback loops where
a proposal about the recommender biases the recommender's output.

---

## 8. Inputs Summary

Consolidated list of inputs the futuring subsystem consumes:

| Input                                       | Frequency    | Used by             |
|---------------------------------------------|--------------|---------------------|
| optimization-loop metrics snapshot          | daily        | Metric signals      |
| human-decisions.jsonl                       | weekly       | Escalation signals  |
| external whitelist (WebSearch)              | weekly       | External signals    |
| .agent/knowledge/*.md                       | weekly       | Internal signals    |
| user-conversation transcript summaries      | weekly       | User-intent signals |
| concept-graph (phase5 §3)                   | on-demand    | Clustering          |
| recommendations-stack scoring config (T018) | on-demand    | Scoring             |

All inputs are files or structured queries — none are memories or
implicit state. This means the subsystem is fully reproducible: re-
running a past week should, modulo external-signal drift, produce a
comparable backlog.

---

## 9. Metrics for Futuring Itself

Because futuring is a system we paid for, we measure it:

- **Hit rate** — of accepted futuring items, fraction that, within
  horizon, produced the predicted outcome. Target: >= 40%.
- **Lead time** — for incidents that *were* presaged by a signal,
  median days between signal-collected and incident-occurred.
  Target: >= 7 days (signal is earlier than incident at least a week).
- **Noise rate** — candidates rejected by the critique skill or
  aged out unreviewed. Target: <= 30% (too low suggests the
  scanner is under-fishing; too high suggests it is over-fishing).
- **Subsystem cost** — tokens, wall-clock, and LLM calls per week.
  Budgeted at <= 5% of the adventure's total operating cost.

These metrics are themselves reviewed monthly and produce meta-
hypotheses — the subsystem optimizes itself through the same loop
that optimizes everything else.

---

## 10. Target Condition Compliance

- **TC-030 — futuring system, cadence, backlog, and integration**:
  satisfied by sections 3 (cadence table with daily/weekly/monthly
  horizons and budgets), 4 (five-class signal taxonomy), 6
  (proactive backlog YAML schema with invariants), and 7
  (integration contract with the recommendations stack from T018,
  naming the new `futuring` channel and its outcome-feedback loop).
  Section 9 makes the subsystem auditable by publishing metrics
  for itself.
