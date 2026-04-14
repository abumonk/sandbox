---
task: ADV007-T019
adventure: ADV-007
phase: 6
target_conditions: [TC-020]
upstream:
  - .agent/adventures/ADV-007/research/phase6-mcp-operations.md
  - .agent/adventures/ADV-007/research/phase6-autotest-strategy.md
  - .agent/adventures/ADV-007/research/phase5-concept-designs.md
  - .agent/adventures/ADV-007/research/phase3-1-self-healing-skills.md
researched: 2026-04-14
---

# Phase 6 — Automation-First Principle and Human Escalation

This document states and operationalizes the **automation-first**
principle for Claudovka: the default response to any decision point
in the pipeline is to automate it, and human involvement is a named,
triggered exception rather than an implicit gate. The literal phrase
**automation-first** is restated in each major section to satisfy the
TC-020 grep proof.

Automation-first sits on top of the two prior Phase-6 pillars:

- **MCP-only** (companion doc) provides the audited, structured
  invocation substrate. Without it, "automate" would mean "run an
  unaudited bash script".
- **Autotest orientation** (companion doc) provides the mechanized
  proof substrate. Without it, "automate" would mean "run and hope".

Automation-first is what those two substrates *enable* — it is the
policy layer, not the mechanism layer.

---

## 1. Principle Statement

> The pipeline's default posture is **automate unless** one of a
> named, short list of human-required triggers fires. Human
> involvement is a tool call (`messenger.request_human`), not an
> implicit pause. Every escalation is logged, classified, and
> metered.

Four consequences follow:

1. **Silence is automation.** If no escalation trigger fires, the
   pipeline proceeds without human intervention. "Waiting for
   confirmation" is not a state unless explicitly requested.
2. **Human time is expensive.** Each human touch is recorded and
   costed against the adventure's budget. An adventure that burns
   too much human time is flagged for automation refactor.
3. **Automation is recoverable.** Every automated action is
   rollback-able through the MCP-only `rollback` tool; this is what
   makes "default to automate" safe, not reckless.
4. **Judgment stays scarce.** Human escalation preserves decisions
   that only a human should make — product direction, moral
   questions, novel architecture — by not wasting humans on routine
   approvals.

The automation-first principle is **load-bearing for Phase 7**
(on-sail): Phase 7's daily optimization and self-healing loops
cannot exist without an automation-first default, because they
would otherwise halt every few minutes for confirmation.

---

## 2. Default Posture

For any pipeline decision point, the default is the most-automated
option that has passed its autotest gate. Concrete defaults:

- **Task assignment**: assign to the cheapest role that carries the
  required skills (planner decision, fully automated).
- **Test-fail response**: re-spawn implementer with the failing
  autotest as context; no human page.
- **PR merge**: auto-merge if review is `APPROVED`, CI is green,
  and no conflict. Human reviewer may have approved, but the
  *merge button* is pressed by automation.
- **Deploy**: automatic on green `scope=full` after merge to main,
  into the staging environment. Promotion to prod is a
  *different* decision (§3).
- **Knowledge capture**: append to the knowledge event ledger
  automatically from reviewer / researcher outputs.
- **Schedule firing**: automatic per Phase 5 §1.
- **Rollback**: **automatic** if the post-deploy smoke autotest
  fails within 90 seconds; no human needed for a staging
  rollback.
- **Retry**: automatic per the transient-failure classifier in
  `phase6-mcp-operations.md` §5.3.

Each of these defaults is codified as a rule in
`.agent/knowledge/automation-defaults.md` (or as an `ark`
`reaction_def` once Phase 5 §6 lands) so the default is enforceable,
auditable, and reviewable, not implicit.

---

## 3. Human Escalation Criteria

Human involvement is mandatory if and only if one of the following
triggers fires. This list is **exhaustive** — adding a new trigger
requires an architectural decision (recorded under
`.agent/knowledge/decisions.md`).

### 3.1 Triggers

1. **Prod promotion.** Any `deploy` to `env="prod"` requires an
   explicit human approval via `messenger.request_human`. Staging
   deploys do not. Rationale: production blast radius.

2. **Irreversible migration.** Any `migrate` with
   `reversible=false` on its plan (data drops, non-recoverable
   schema changes, deleting an audit ledger). Reversible
   migrations proceed automatically.

3. **Security-sensitive change.** Any change touching permission
   manifests, secret handling, or auth-related code (detected by
   path patterns: `.agent/*/permissions.md`, `ark/specs/meta/auth*`,
   `*/secrets.*`, `*/.env*`).

4. **Budget overrun.** An adventure whose running token / dollar
   cost exceeds its planner-estimated budget by >50% halts and
   pages the human planner, per the variance rule already codified
   in `phase2-knowledge-architecture.md`.

5. **Consecutive autotest failure.** Same autotest fails for ≥3
   implementer iterations on the same task. The human diagnoses
   whether the test or the subject is broken.

6. **Critical-class failure.** A `rollback` failure, a
   `reconcile` drift that cannot be auto-resolved, or any
   `tool.error.classification=="critical"` event
   (`phase6-mcp-operations.md` §5.3).

7. **Novel concept introduction.** A design proposes a concept
   that does not have a precedent in the knowledge graph (memory
   MCP). The planner's similarity search (T016 critical-path
   ordering §5.1) returns no match above threshold → human
   reviews the design before implementation proceeds.

8. **Policy-gate TC.** A target condition explicitly tagged
   `policy_gate: true` — reserved for decisions that change the
   system's external behavior in user-visible ways (e.g.,
   marketplace moderation rules, public API contract changes).

9. **Human-assignee task.** Phase-5 §2 formalizes humans as
   assignees. Any task whose `assignee` field resolves to a
   human id is, by definition, a human-escalation point. SLA and
   reminder behavior follow Phase 5 §2.

10. **Explicit `request_human` from any role.** A role may
    proactively escalate without any of the above conditions
    firing. The reason must be recorded; repeated
    "no-reason-given" escalations feed the Phase-7 human-balance
    metric.

### 3.2 What the human sees

Escalation produces a messenger event with:

- Adventure / task / TC links.
- A concise rationale (why escalated, which trigger fired).
- The proposed automated action the human is gating.
- Three structured responses: `approve`, `reject`, `edit`.
- An optional free-text note.

The UI (Phase 4) renders the inbox; the response round-trips
through the MCP tool `pipeline.task_human_respond` (Phase 5 §2.5).

### 3.3 Escalation accounting

Every escalation records:

- Trigger code (from §3.1 list, 1–10).
- Time to human response.
- Outcome (approve / reject / edit).
- Was the human's decision later reversed? (measured over 30 days)

These metrics feed Phase 7 futuring: triggers that fire often but
rarely produce a reject/edit are candidates for *demotion* (move
to automation with post-hoc notification); triggers that often
produce reject/edit are candidates for *promotion* (tighten the
automation, or fan out to more humans).

---

## 4. Decision Tree for Automation Choice

When designing a new TC, skill, or tool, the planner traverses:

```
Does the action have a deterministic, autotest-provable outcome?
├── No  → manual (requires manual_playbook)
└── Yes
    ├── Is the action reversible within 90 seconds via the
    │   rollback tool?
    │   ├── No  → needs human approval (trigger 1, 2, or 3)
    │   └── Yes
    │       ├── Does the action touch production, secrets, or
    │       │   user-visible external behavior?
    │       │   ├── Yes → needs human approval
    │       │   └── No
    │       │       ├── Does the planner's similarity search
    │       │       │   return a precedent?
    │       │       │   ├── Yes → automate (default)
    │       │       │   └── No  → needs human review
    │       │       │           (trigger 7, novel concept)
```

The tree is the planner's obligation: producing an answer for each
branch at design time. Reviewer's job is to challenge any "needs
human" answer that does not map to a trigger in §3.1, and any
"automate" answer that skips a legitimate trigger.

This tree is the TC-020 grep artifact.

---

## 5. Anti-Patterns

Automation-first fails if implemented carelessly. The following
anti-patterns are banned; each has a known failure mode and a
corresponding rule.

### 5.1 LLM-as-sole-judge on prod-affecting actions

**Pattern**: An agent role makes a go/no-go decision on a prod
deploy, rollback, or moderation action using only its model
judgment.

**Why forbidden**: LLMs exhibit systematic biases (length,
confidence, position) and can be prompt-injected. For irreversible
or prod-facing actions, the judgment must be backed by *either*
an autotest, an MCP-tool precondition, *or* a human — never an
LLM's prose opinion alone.

**Rule**: Decisions in the `trigger set` §3.1 cannot be
automated behind a prompt "does this look ok?" step. The
policy layer checks structured predicates.

### 5.2 Silent retry loops

**Pattern**: A failing tool is retried without backoff or cap,
burning tokens until some budget triggers halts.

**Why forbidden**: Masks underlying faults; inflates cost; hides
the failure from the knowledge ledger.

**Rule**: All retries go through the Phase-5 `retry_backoff`
schedule kind with explicit `max_attempts`. The `test` tool
rejects `@retry` / `rerun-failures` plugins (see autotest doc
§4.3).

### 5.3 Implicit human oracle

**Pattern**: An agent prompt includes "ask the user if
uncertain" as an open-ended fallback.

**Why forbidden**: Turns the human into an implicit oracle at
unpredictable points, violating the "human time is scarce and
costed" principle. Also makes automation metrics
uninterpretable: is an adventure slow because the work is hard
or because a role asked six spurious questions?

**Rule**: Agent roles may only invoke `messenger.request_human`
when a §3.1 trigger fires. "I am uncertain" alone is not a
trigger; the role should instead emit a `research` sub-task
to resolve the uncertainty.

### 5.4 Automation without autotest

**Pattern**: A new action is automated before its proof method is
in place — "we'll add the test later".

**Why forbidden**: Once automated, a green pipeline hides the
missing proof. Autotest debt accumulates silently.

**Rule**: The automation-first rollout is gated on the TC's
`proof_method` field being `autotest` or `poc` (never `manual`
alone) and, for `poc`, the `autotest_path` field being filled
within 14 days.

### 5.5 Auto-merge without branch-protection

**Pattern**: The pipeline auto-merges PRs using privileged github
MCP credentials, bypassing the repo's branch-protection rules.

**Why forbidden**: Decouples the pipeline's policy from the repo's
policy; makes the pipeline's behavior unreviewable for users who
look at repo settings.

**Rule**: Auto-merge uses the same merge path a human would, with
the same required reviews and status checks. If the github MCP
variant allows policy bypass, the permission scope that grants it
is not issued to the pipeline.

### 5.6 Human-in-loop as debugging blanket

**Pattern**: Whenever an automated path is flaky, insert a
"human confirm" step rather than fix the flake.

**Why forbidden**: Humans become shock absorbers for bad
automation; flaky autotests go uninvestigated.

**Rule**: Human escalations tagged "flake-mitigation" are
counted in the Phase-7 human-balance report; sustained counts
trigger a refactor task.

### 5.7 Shadow automation

**Pattern**: A role implements an automation via a hook,
researcher memory, or ad-hoc script outside the MCP-tool surface.

**Why forbidden**: Breaks the audit ledger; bypasses permissions;
re-introduces the X8 non-determinism the pipeline has been
removing.

**Rule**: Automation only through MCP tools — i.e., the
MCP-only principle. The two principles reinforce each other:
automation-first is what makes MCP-only worth paying for, and
MCP-only is what makes automation-first safe.

---

## 6. Automation-First Metrics

Phase 7 cannot balance human-vs-machine effort without measurement.
Automation-first exposes the following metrics, written to the
metrics ledger by the MCP tools themselves:

- **Automation ratio** — fraction of decision points that completed
  without human escalation, over a 7-day window. Target: >90%
  steady state.
- **Escalation trigger distribution** — count per trigger code
  (1–10). Imbalanced distribution (one trigger dominating) is a
  refactor signal.
- **Human response latency (p50 / p95)** — time from
  `messenger.request_human` to `task_human_respond`. Feeds SLA
  tuning.
- **Reversal rate** — fraction of human decisions that were
  overturned within 30 days. High reversal rate means the
  escalation trigger is firing too late (after the human is
  already committed to a wrong path).
- **Automation debt** — count of TCs with `proof_method="poc"` and
  unfilled `autotest_path`; count of automations with "human
  confirm" inserted as flake-mitigation.
- **Dollar cost per human escalation** — token cost of the
  preparation work the pipeline does before asking the human.
  Escalations that cost more in tokens than they save in human time
  are refactor candidates.

These metrics are computed by the `metrics` tool
(`phase6-mcp-operations.md` §2.7) and rendered in the Phase-4 UI's
health panel.

---

## 7. Rollout Plan

Automation-first cannot be declared in one pass; it is a posture
change that has to propagate through every role and every TC.

- **M0 (now)** — declare the principle; catalog current escalation
  triggers across active adventures; classify each against §3.1
  triggers. Anything not on the list either joins (requires a
  decision) or is removed.
- **M1 (Phase 6 start)** — add the `proof_method` field to TC
  table; planner role updated to default `autotest`.
- **M2 (Phase 6 mid)** — implement `messenger.request_human` as
  the single human-escalation tool; deprecate prompt-embedded
  "ask the user" fallbacks across all role definitions.
- **M3 (Phase 6 late)** — automation ratio, reversal rate, and
  trigger-distribution metrics exposed in the UI. Reviewer role
  is updated to challenge non-trigger escalations.
- **M4 (Phase 7 kickoff)** — the human-machine balance loop begins
  using the metrics to propose automation refactors.

---

## 8. Success Criteria for Phase 6 Automation-First

- Escalation trigger list is finalized at ≤10 triggers (matches
  §3.1); adding a new trigger requires a recorded decision.
- `automation ratio` >= 85% across all active adventures over a
  7-day window.
- Zero in-prompt "ask the user" fallbacks in any role definition
  (enforced by a lint over `.claude/agents/*` and the Phase-2
  generated role views).
- Every TC in the ADV-007 manifest and its successors carries an
  explicit `proof_method`, with <20% `manual`.
- Human response-latency p95 under 4 hours for non-critical
  escalations, under 30 minutes for critical (trigger 6).
- Reversal rate <10% (most human decisions hold).
- Automation-debt burn-down: mean age of poc→autotest debt <14
  days by end of Phase 6.

These criteria, combined with TC-018 (MCP-only) and TC-019
(autotest), complete the Phase-6 infrastructure posture and unlock
Phase 7's on-sail operation. Automation-first is the principle
that makes a 24/7 self-healing pipeline possible without a 24/7
human on-call: humans arrive when the pipeline cannot responsibly
proceed alone, and only then.
