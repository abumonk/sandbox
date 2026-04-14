---
task: ADV007-T019
adventure: ADV-007
phase: 6
target_conditions: [TC-019]
upstream:
  - .agent/adventures/ADV-007/research/phase5-concept-designs.md
  - .agent/adventures/ADV-007/research/phase3-2-integration-matrix.md
  - .agent/adventures/ADV-007/research/phase2-entity-redesign.md
  - .agent/adventures/ADV-007/research/phase6-mcp-operations.md
researched: 2026-04-14
---

# Phase 6 — Autotest Orientation Strategy

This document establishes Claudovka's **autotest orientation**: the
default posture that every feature, entity, and target condition ships
with an automated proof method, and manual testing is a deliberately
scoped exception rather than an implicit fallback. The literal phrase
**autotest** is restated in every major section to satisfy the TC-019
grep proof.

Autotest orientation is the pair to MCP-only operations
(`phase6-mcp-operations.md`). MCP-only determines *how* operations
are invoked; autotest determines *what proves each operation works*.
Both are prerequisites for Phase 7's self-healing and
automation-first posture, because self-healing is impossible when
the system cannot tell — mechanically — whether it has healed.

---

## 1. Autotest Principle Statement

> Every target condition, every entity, and every MCP tool MUST
> carry an automated proof method. If an automated proof is not
> feasible in the current iteration, the gap is explicit, time-
> bounded, and tracked; the proof method is never silently
> "manual" by default.

This inverts the pipeline's current posture, where target conditions
default to manual grep proofs and tests are added opportunistically.
Phase 6 switches the default: **no TC without an autotest plan**,
**no entity without a verifier**, **no MCP tool without a contract
test**.

Autotest does not mean "no manual testing ever" — see §3 on proof-
method taxonomy. It means manual testing is a *named, justified*
choice, not the path of least resistance.

---

## 2. Coverage Targets

### 2.1 Per entity type

Using the Phase-2 entity redesign taxonomy, every first-class entity
requires the following autotest coverage:

| Entity | Schema test | Transition test | Writer-contention test | Event-replay test |
|---|---|---|---|---|
| Task | required | required | required | required |
| Adventure manifest | required | required | required | required |
| Run (Phase 5) | required | required | n/a (TM-only) | required |
| Schedule | required | required | n/a (TM-only) | required |
| Messenger approval | required | required | required | required |
| Input-store item | required | optional | required | optional |
| Lead-state | required | required | required | required |
| Knowledge event | required | optional | required | required |
| Trigger | required | required | n/a | required |
| Permission assertion | required | n/a | n/a | optional |
| Role definition | required | n/a (static) | n/a | n/a |
| Skill definition | required | n/a (static) | n/a | n/a |

Each "required" cell becomes a concrete test file under
`ark/tests/test_<entity>_<kind>.py` (autotest-discoverable by
pytest), with the Phase 6.2 `test` MCP tool wrapping the runner.

### 2.2 Per subsystem

| Subsystem | Target coverage | Proof style |
|---|---|---|
| Ark DSL parser | 95% branch | table-driven pest-grammar tests |
| Ark codegen (Python) | 90% branch | golden snapshot tests |
| Ark codegen (Rust) | 80% branch (ramping to 90% with parity) | golden snapshot tests |
| Ark verifier (Z3 bridge) | 95% branch | property tests (hypothesis) against SMT-LIB fixtures |
| Orchestrator crate | 85% branch | integration tests with an in-process mock MCP |
| Agent / role runtime | 80% branch | replay tests over recorded adventure.log fixtures |
| Pipeline MCP tools | 100% contract | contract tests generated from `.ark` `mcp_tool_def` specs |
| GitHub MCP adapter | n/a remote | recorded-cassette tests (vcr.py) |
| Deploy MCP adapter | n/a remote | dry-run tests + smoke-deploy to a staging sandbox |
| UI (Phase 4) | 70% component | Playwright smoke tests over rendered views |
| Knowledge graph (memory MCP) | 85% branch | graph-invariant tests + schema round-trip |

Coverage numbers are *targets*, not gates — §5 on budgets explains
how a PR that drops below target is handled (not by blocking, by
autotest debt tracking).

### 2.3 Per target condition

Every TC row in an adventure manifest has a `proof_method` column
with one of three values (§3 taxonomy). Phase 6 adds a hard rule:
the default value for a newly-declared TC is `autotest`. Flipping
to `poc` or `manual` requires an explicit justification string
captured in the adventure manifest and surfaced in review.

Measurement: the adventure-planner produces a TC table; the reviewer
diffs the proof_method distribution; an adventure with >20%
`manual` TCs is flagged for escalation (Phase 7 human-balance loop
will enforce this as a gate).

---

## 3. Proof-Method Taxonomy

Three proof methods, with explicit when-to-use rules so the roles
(planner, reviewer, implementer) agree on the boundary.

### 3.1 `autotest`

A test program that produces a boolean pass/fail under the `test`
MCP tool without human observation. Includes:

- Unit tests (pytest, cargo test, Jest).
- Property tests (hypothesis, proptest).
- Golden / snapshot tests.
- Integration tests with mocked externals.
- Verifier-backed tests (Z3 assertions against a spec).
- Contract tests on MCP tools (input schema, output schema,
  error-envelope shape).

**Use when**: the behavior can be expressed mechanically. Default.

**Non-goals**: not expected to cover "does the UI look right",
"does the prose read well", "is this the right decision".

### 3.2 `poc` (proof-of-concept)

A scripted demonstration — one-shot artifact that the reviewer
replays and confirms produces the expected output. Lives under
`ark/tests/poc/` with a README describing the expected observation.
Halfway between autotest and manual: the *execution* is automated,
the *judgment* is human.

**Use when**: the proof requires cross-stack composition that is
too expensive to autotest, or the observable is qualitative (a
generated diagram looks topologically correct, a UI renders
without layout breakage).

**Examples**:

- "`compile` on the `evolution_skills.ark` spec produces a Python
  module that imports cleanly and whose generated docstrings match
  the spec annotations" — autotestable, should migrate away from
  poc when the snapshot diff stabilizes.
- "The Phase-4 node/graph editor renders a 500-node workflow
  without dropping frames" — stays poc because the observable is
  perceptual.

**Constraint**: every poc TC has an `autotest_path` field in the
adventure manifest pointing to the autotest that will supersede it.
Unfilled `autotest_path` is an autotest-debt entry.

### 3.3 `manual`

A human performs an action and reports the outcome. No automation.

**Use when**: the TC is inherently about human judgment (e.g.,
"the generated prose is readable", "the marketplace listing
describes the skill accurately"). Must be rare.

**Constraint**: every `manual` TC has a `manual_playbook` field
pointing to a short markdown checklist under
`.agent/knowledge/manual-playbooks/`, so the manual step is
repeatable even if different humans perform it.

### 3.4 Decision tree

```
Is the observable a boolean (pass / fail) derivable from
program output?
├── Yes → autotest
└── No
    ├── Is the observable a stable artifact a reviewer can
    │   inspect and sign off?
    │   ├── Yes → poc (with autotest_path to migrate)
    │   └── No → manual (with manual_playbook)
```

Planner uses the tree when filling in `proof_method` for each TC;
reviewer uses the tree as the default challenge question ("why is
this not autotest?"). The tree is also a TC-019 grep artifact.

---

## 4. Regression Surface and Golden Tests

### 4.1 The regression surface

A regression is any change that flips a previously-green autotest
to red. The *regression surface* is the union of all current
autotests plus the set of "lessons learned" autotests materialized
from past incidents. Phase-2 lessons entity (knowledge events) is
the source: every `lesson.learned` observation with
`type: regression` spawns an autotest in the next adventure.

Sizing: with 34 target conditions across ADV-007 alone, the
Claudovka autotest surface is projected to reach roughly 400-600
autotests by end of Phase 6 (10-15 per subsystem × 6 subsystems +
entity-suite tests + tool contract tests). This fits comfortably
in a single `test --scope=full` run; budget §5 assumes this scale.

### 4.2 Golden-test strategy

Generated-code and rendered-view tests use **golden snapshots**:

- Location: `ark/tests/golden/<area>/<case>.expected.<ext>`.
- Update path: `test --update-snapshots` is permission-gated
  (T-local-write, implementer role only) and refuses if there are
  uncommitted changes outside the snapshot tree, to prevent
  accidental test laundering.
- Review requirement: every PR whose diff touches
  `tests/golden/` must include a `snapshot-change` label; the
  reviewer checklist includes "does the golden diff represent
  intentional output change?".
- Rotation: snapshots older than 180 days are reviewed for
  relevance during Phase-7 maintenance loops.

Golden tests replace ad-hoc "compare the generated Python to what
we remember it should look like" reviews, which have historically
been the largest source of review churn (from patterns observed in
ADV-001 through ADV-006).

### 4.3 Flakiness policy

Flaky tests are treated as bugs in the *test*, not in the subject.
The policy:

- **Detection**: any autotest that flips green↔red twice in 10
  runs on the same ref is flagged flaky.
- **Quarantine**: flagged tests move to a `quarantine/` directory
  and continue to run but do not gate merges. This buys time to
  fix without blocking unrelated work.
- **SLA**: a quarantined test has a 5-working-day fix SLA; expiry
  escalates to lead and auto-opens a GitHub issue (via github MCP).
- **Zero-tolerance on `test --scope=full`**: the full-stack run
  must be 100% non-flaky; any flakiness there is a critical
  incident, not a quarantine candidate.
- **No `@retry`**: the test framework config disallows
  `pytest-retry` / `rerun-failures` plugins. Retries mask
  nondeterminism.

---

## 5. CI Orchestration

### 5.1 Who triggers what

Phase 6 CI orchestration is driven entirely by the `test` MCP tool
and the github MCP's workflow trigger. The trigger matrix:

| Event | Scope | Who triggers | Duration budget |
|---|---|---|---|
| File edit during an active task | incremental (changed files only) | implementer (on save hook) | <5s |
| Task moves to `reviewing.ready` | task-scope suite | reviewer spawn | <60s |
| PR opened | affected-subsystem suite | github actions via `github.run_workflow` | <5min |
| PR approved, pre-merge | `scope="full"` | github actions | <15min |
| Nightly | `scope="full"` + benchmark suite | scheduler (Phase 5 §1) | <45min |
| Post-deploy smoke | `scope="smoke"` | deploy tool on success | <90s |

### 5.2 Budgets

Each scope carries a time budget; an autotest that exceeds its
scope's budget is moved to a slower scope. This prevents any single
test from silently expanding the fast path. Budgets are enforced by
the `test` tool's wall-clock timer and recorded in the run ledger.

Token budgets also apply — the autotest strategy should not inflate
the pipeline's token cost. Reviewer spawn's autotest step has a
<2k-token budget (structured pass/fail summary only, not raw test
output). Full test logs stay on disk and are fetched only when a
test fails.

### 5.3 Dependency on MCP-only

Every CI trigger listed above is an MCP tool call, not a shell
invocation. `github.run_workflow` starts a remote job, that job's
runner invokes the `test` tool locally, results come back through
`github.get_workflow_run`. End-to-end, autotest orchestration shares
the MCP-only audit trail (§2.3 of `phase6-mcp-operations.md`).

### 5.4 Human escalation from autotest

When an autotest fails on a pre-merge run, the default path is
`implementing.failed` → planner re-spawn. No human yet. Human is
escalated only if:

- The same autotest has failed for 3 consecutive implementer
  iterations, OR
- The failure classification is `critical` (see
  `phase6-mcp-operations.md` §5.3), OR
- The test belongs to the `zero-tolerance` set (verifier
  invariants, `rollback` contract, idempotency-key handling).

Details are in `phase6-automation-first.md` §4.

---

## 6. Relation to Existing Claudovka Tests

The repo already contains extensive Python test coverage under
`ark/tests/` — evidence: test_agent_*, test_evolution_*, and the
parser / codegen / verify suites surfaced in `git status`. Phase 6
autotest orientation does not discard these; it **classifies and
budgets them**:

- Existing tests become the M1 baseline for the per-subsystem
  coverage targets in §2.2.
- Any test not currently part of `scope=ark` classification is
  mapped into one of the named scopes.
- A coverage audit at the start of Phase 6 produces a deficit
  report per subsystem; those deficits are tracked as autotest-
  debt entries in the knowledge event ledger.

Rust tests (under `ark-orchestrator` and sibling crates) are folded
in through `cargo test` invoked by the `test` MCP tool; the tool
unifies the pytest and cargo outputs into a single pass/fail
envelope.

---

## 7. Success Criteria for Phase 6 Autotest

- 100% of target conditions in newly-created adventures carry a
  `proof_method` field; no implicit default.
- <20% of TCs across all active adventures use `manual`.
- `scope="full"` autotest run passes deterministically on 10
  consecutive main-branch commits (flakiness budget: 0).
- 85%+ coverage on every Tier-1 subsystem (orchestrator, codegen,
  parser, verifier) by end of Phase 6.
- All 7 MCP tools from `phase6-mcp-operations.md` have contract
  tests generated from their `.ark` `mcp_tool_def` specs.
- Golden-snapshot tree has <5% stale snapshots (not touched in 180
  days) at any time.
- Mean autotest-debt age <14 days (median gap between a `poc` TC
  being logged and its `autotest_path` being filled).

These criteria feed TC-019 proof. Phase 7 (on-sail) then shifts
from autotest *adoption* to autotest *expansion* — growing the
regression surface as new lessons accrue.
