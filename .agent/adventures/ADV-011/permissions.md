---
adventure_id: ADV-011
status: approved
created: 2026-04-15T02:35:00Z
approved: 2026-04-15T02:55:00Z
passes_completed: 4
validation_gaps: 0
---

# Permission Requests — ADV-011: Ark Core Unification

## Summary

14 permission entries across 12 tasks, 2 custom agents (`core-synthesist`,
`descriptor-architect`) + default `researcher`. All 4 analysis passes complete.
0 validation gaps. **Read-mostly adventure**: no writes to `ark/` or
`shape_grammar/`; all writes are confined to
`.agent/adventures/ADV-011/**`. The only shell access required is for running
proof commands under `tests/`.

## Pass 1 — Codebase Tooling Scan

Discovered in-repo infrastructure:

- `.claude/settings.local.json` — 128+ entry `permissions.allow`; existing
  bash allow-list covers `test:*`, `grep:*`, `cat:*`, `ls:*`, `wc:*`, `head:*`,
  `tail:*`, `diff:*`, `python:*`, `python -m unittest:*`, `bash:*`, `cd:*`.
- `.agent/config.md` — adventure thresholds (max_task_tokens 100K,
  max_task_duration 30min) and cost rates.
- Python 3.12 runtime; stdlib `unittest` available (no pytest dependency for
  ADV-011).
- No `Makefile`, `Taskfile`, `justfile`, `package.json` at repo root matters
  for this adventure.
- Git: master branch, conventional commits; `git diff`, `git log` used
  optionally for evidence but not required by any TC.
- No `.env.example` required.

Shell commands agents will need (per Pass 1 + Pass 2):

- `test -f <path>` — existence checks for every deliverable TC.
- `grep -c '^## ' <file>` — section-count TCs.
- `grep -cE '<regex>' <file>` — bucket / keyword count TCs.
- `bash .agent/adventures/ADV-011/tests/run-all.sh` — aggregator (T011, T012).
- `python -m unittest discover -s .agent/adventures/ADV-011/tests -v` — unit
  tests (T011, T012).
- `wc -l`, `sort`, `diff` — support utilities.

No external network access required. No MCP tools required.

## Pass 2 — Plan-Driven Analysis

Per-task trace:

- T001 (harvest): Read `.agent/adventures/ADV-00{1..8}/manifest.md`,
  `ADV-010/manifest.md`, `ADV-010/designs/`, `ADV-010/schemas/`, optional
  `reviews/adventure-report.md`, `ark/dsl/stdlib/*.ark`,
  `ark/dsl/grammar/ark.pest`, `ark/tools/parser/ark_grammar.lark`,
  `ark/specs/root.ark`. Write `research/concept-inventory.md`.
- T002 (test-strategy): Read `designs/`, `schemas/`. Write
  `tests/test-strategy.md`.
- T003 (classify): Read `research/concept-inventory.md`, `designs/`. Write
  `research/concept-mapping.md`.
- T004 (dedup): Read mapping, `.agent/knowledge/patterns.md`,
  `.agent/knowledge/decisions.md`. Write `research/deduplication-matrix.md`.
- T005 (prune): Read mapping. Write `research/pruning-catalog.md`.
- T006 (descriptor-delta): Read mapping, dedup, prune, `ark/dsl/stdlib/*.ark`.
  Write `research/descriptor-delta.md`.
- T007 (builder-delta): Read mapping, dedup, prune,
  `ark/tools/verify/*.py`, `ark/tools/codegen/*.py`,
  `ark/tools/visualizer/*.py`. Write `research/builder-delta.md`.
- T008 (controller-delta): Read mapping, dedup, prune, `ark/tools/agent/*.py`,
  `ark/tools/evolution/*.py`, `ark/tools/visual/review_loop.py`,
  `.agent/telemetry/**`, `.agent/adventures/ADV-010/designs/**`,
  `.agent/adventures/ADV-010/schemas/**`. Write `research/controller-delta.md`.
- T009 (validate): Read every ADV-001..008 manifest + ADV-010 manifest,
  designs/, research/**. Write `research/validation-coverage.md`,
  `research/validation-report.md`.
- T010 (downstream plan): Read research/**. Write
  `research/downstream-adventure-plan.md`.
- T011 (test impl): Read every deliverable, Write `tests/run-all.sh`,
  `tests/test_coverage_arithmetic.py`, `tests/test_mapping_completeness.py`,
  `tests/__init__.py`. Bash to run tests.
- T012 (final report): Read research/**, tests/**. Bash rerun run-all.sh.
  Write `research/final-validation-report.md`.

## Pass 3 — Historical Pattern Match

From `.agent/knowledge/issues.md`:

- **Sub-agent Bash allowlist rejection** (from ADV-008): first sub-agent
  invocations hit allowlist rejections. Mitigation: request `bash:*`, `test:*`,
  `grep:*`, `python -m unittest:*`, `python:*` explicitly.
- **Metrics tracking recurrence**: ADV-010 solves it via hooks. ADV-011 relies
  on ADV-010's capture — no additional hook install needed; standard
  `metrics.md` row append is the terminal step for each task.
- **Log timestamp placeholders**: reviewers will check that each task uses an
  actual wall-clock timestamp, not round numbers.

From `.agent/knowledge/patterns.md`:

- **Test strategy before implementation**: T002 runs in wave A with T001 to
  guarantee this pattern.
- **Append-only jsonl for multi-writer state**: not triggered here because the
  controller event-log redesign is a downstream adventure, not this one.

## Pass 4 — Cross-Validation Matrix

| Task | Agent | Stage | Read | Write | Shell | MCP | External | Verified |
|------|-------|-------|------|-------|-------|-----|----------|----------|
| T001 | core-synthesist | impl | `.agent/adventures/ADV-00{1..8,10}/**`, `ark/dsl/stdlib/**`, `ark/dsl/grammar/**`, `ark/tools/parser/**`, `ark/specs/root.ark`, `.agent/knowledge/**` | `research/concept-inventory.md` | none | none | none | yes |
| T002 | researcher | impl | `designs/`, `schemas/` | `tests/test-strategy.md` | none | none | none | yes |
| T003 | core-synthesist | impl | `research/concept-inventory.md`, `designs/` | `research/concept-mapping.md` | none | none | none | yes |
| T004 | core-synthesist | impl | mapping, `.agent/knowledge/**` | `research/deduplication-matrix.md` | none | none | none | yes |
| T005 | core-synthesist | impl | mapping | `research/pruning-catalog.md` | none | none | none | yes |
| T006 | descriptor-architect | impl | mapping, dedup, prune, `ark/dsl/stdlib/**` | `research/descriptor-delta.md` | none | none | none | yes |
| T007 | core-synthesist | impl | mapping, dedup, prune, `ark/tools/verify/**`, `ark/tools/codegen/**`, `ark/tools/visualizer/**` | `research/builder-delta.md` | none | none | none | yes |
| T008 | core-synthesist | impl | mapping, dedup, prune, `ark/tools/agent/**`, `ark/tools/evolution/**`, `ark/tools/visual/review_loop.py`, `.agent/telemetry/**`, `.agent/adventures/ADV-010/**` | `research/controller-delta.md` | none | none | none | yes |
| T009 | core-synthesist | impl | every ADV-00{1..8,10}/manifest.md, designs/, research/** | `research/validation-coverage.md`, `research/validation-report.md` | none | none | none | yes |
| T010 | core-synthesist | impl | research/** | `research/downstream-adventure-plan.md` | none | none | none | yes |
| T011 | researcher | impl | every deliverable | `tests/**` | `bash`, `test`, `grep`, `python`, `python -m unittest` | none | none | yes |
| T012 | researcher | impl | research/**, tests/** | `research/final-validation-report.md` | `bash .agent/adventures/ADV-011/tests/run-all.sh` | none | none | yes |

Validation checks:

1. Every task has ≥1 permission entry per assigned agent role. ✓
2. Every shell command from Pass 1 that relates to a task's files is covered.
   ✓ (only T011 + T012 need shell; both listed.)
3. Every `proof_command` in TCs is covered by T011's bash/unittest allow-list.
   ✓
4. Every file in a task's `files` field has a matching read/write permission.
   ✓
5. Task dependencies: dependent tasks' agents have read access to
   predecessors' outputs via the research/** scope. ✓
6. Git operations: config's `git.mode: current-branch` — no branch-per-task
   operations required; commits happen at adventure close by lead. ✓

0 validation gaps.

## Requests

### Shell Access

| # | Agent | Stage | Command | Reason | Tasks |
|---|-------|-------|---------|--------|-------|
| 1 | researcher | impl | `test -f *`, `test -d *` | Deliverable existence TCs | T011, T012 |
| 2 | researcher | impl | `grep -c *`, `grep -cE *`, `grep -q *`, `grep -l *` | Section/row count TCs | T011, T012 |
| 3 | researcher | impl | `bash .agent/adventures/ADV-011/tests/run-all.sh` | Aggregated CI entrypoint | T011, T012 |
| 4 | researcher | impl | `python -m unittest discover -s .agent/adventures/ADV-011/tests -v` | stdlib unittest | T011, T012 |
| 5 | researcher | impl | `wc -l`, `sort`, `head`, `tail`, `cat`, `diff` | Support utilities for TC proofs | T011, T012 |

### File Access

| # | Agent | Stage | Scope | Mode | Reason | Tasks |
|---|-------|-------|-------|------|--------|-------|
| 6 | core-synthesist | impl | `.agent/adventures/ADV-00{1..8}/**`, `.agent/adventures/ADV-010/**` | read | Source manifests for harvest/classify/dedup/validate | T001, T003, T004, T008, T009 |
| 7 | core-synthesist | impl | `.agent/knowledge/**` | read | Pattern reuse, decisions | T001, T004 |
| 8 | descriptor-architect | impl | `ark/dsl/stdlib/**`, `ark/dsl/grammar/**`, `ark/tools/parser/**`, `ark/specs/root.ark` | read | Descriptor delta analysis | T006 |
| 9 | core-synthesist | impl | `ark/tools/verify/**`, `ark/tools/codegen/**`, `ark/tools/visualizer/**`, `ark/tools/agent/**`, `ark/tools/evolution/**`, `ark/tools/visual/review_loop.py`, `.agent/telemetry/**` | read | Builder/controller delta analysis | T007, T008 |
| 10 | any | impl | `.agent/adventures/ADV-011/**` | read/write | This adventure's workspace | all |
| 11 | researcher | impl | `.agent/adventures/ADV-011/tests/**` | write | Test implementation | T002, T011 |

### MCP Tools

None required.

### External Access

None required.

## Historical Notes

- ADV-007 was the closest analogue (research adventure producing documents);
  it used `poc` for most TCs. ADV-011 tightens this by using `autotest` for
  existence and content TCs, reserving `poc` only for coverage arithmetic.
- ADV-010 established `autotest`-by-default for every TC; we inherit that bar.
- Like ADV-008, this adventure has a hard invariant: **no writes to `ark/`**.
  Unlike ADV-008, this adventure also does not write to any sibling package —
  every artefact is confined to `.agent/adventures/ADV-011/`.

## Approval
- [ ] Approved by user
- [ ] Approved with modifications: {notes}
- [ ] Denied: {reason}
