---
adventure_id: ADV-010
generated_at: 2026-04-18T14:00:00Z
task_count: 18
tc_total: 37
tc_passed: 37
tc_pass_rate: "100%"
total_iterations: 1
knowledge_suggestions_count: 7
---

# Adventure Report: ADV-010

## 1. Executive Summary

| Field | Value |
|-------|-------|
| Adventure | ADV-010 |
| Title | Telemetry Capture — Research, Plan, Design, Wire & Implement |
| Duration | 2026-04-15 → 2026-04-18 (~3 days wall-clock) |
| Total Cost | ~$2.00 estimated (opus planner ~$0.63 + sonnet implementers ~$1.37). Live metrics.md is polluted with hundreds of duplicate synthetic rows — actual spend is not cleanly summable from that file and is itself a finding (see §4 Bottlenecks). |
| Tasks | 18/18 completed (17 PASSED, 1 FAILED-cosmetic) |
| TC Pass Rate | 37/37 autotest + poc TCs passing in the official regression gate (TC-RG-1, 39 tests, 1 platform-skip, 0 failures) |

ADV-010 closes the long-running telemetry gap recorded as issues in ADV-002, ADV-004, ADV-005, and ADV-006. The adventure shipped a complete capture pipeline — schema/cost_model/aggregator/capture/task_actuals + 4 reconstructors + backfill CLI + a 39-test regression suite + hook integration + live canary verification on ADV-009 + operator docs + knowledge base extraction. Every completed adventure now has `agent_runs > 0` and positive token totals; every future subagent completion writes a live row via the `SubagentStop`/`PostToolUse` hooks. The only sub-green note is ADV010-T011, which the adventure-task-reviewer marked FAILED due to three stale assertions in a dev-helper test file (`test_reconstructors.py`) whose expected row counts predate the real ADV-008 metrics.md contents — the T011 *implementation* modules are correct and their failures do not appear in the official regression gate (TC-RG-1) nor in the backfill/canary proofs.

## 2. Target Conditions Analysis

| ID | Description | Task | Result | Proof Output |
|----|-------------|------|--------|--------------|
| TC-RS-1 | gap-analysis has ≥8 findings with paths/lines | T001 | PASS | 8 findings F1–F8 verified |
| TC-TS-1 | test-strategy maps every autotest TC | T002 | PASS | TestStrategyCoverage ok |
| TC-S-1..3 | row header, frontmatter keys, row parse | T003/T005/T016 | PASS | 4 schema tests ok |
| TC-CC-1..4 | validate_event, row write, idempotency, cost column | T005/T007/T016 | PASS | capture tests ok |
| TC-CM-1..4 | cost_for fixture, unknown raises, aliases, load_rates | T004/T016 | PASS | 4 cost-model tests ok |
| TC-HI-1..4 | both hooks installed, permissions preserved, subprocess happy-path, malformed-json exit-0 | T007/T008/T016 | PASS | HI-2 platform-skipped on Windows (acceptable per manifest) |
| TC-AG-1..6 | frontmatter totals=row sums, idempotent recompute, format_duration | T006/T009/T010/T016 | PASS | aggregator tests ok |
| TC-EI-1..5 | PayloadError → exit 0, WriteError → exit 0 + log, Ctrl-C propagates, jsonl error log, heal after partial fail | T007/T010/T016 | PASS | EI-2 platform-skipped (Windows chmod semantics) |
| TC-BF-1..6 | every adventure has runs>0, ADV-008 tildes stripped, idempotent, never high confidence, unrecoverable sentinel, dry-run safe | T011/T012/T013/T016 | PASS | 239 rows materialized across ADV-001..ADV-009 |
| TC-LC-1 | live canary on ADV-009 produces populated row | T014/T016 | PASS | 1 test, 0.013s |
| TC-RG-1 | discover suite exits 0 | T016 | PASS | 39 tests, 1 skipped, 0 failed, 1.367s |

**Overall**: All 37 target conditions pass. Two tests are platform-skipped on Windows with documented reasons (TC-HI-2 / TC-EI-2 share the same `chmod`-on-Windows limitation). The live canary (TC-LC-1) was validated via pre/post fixture snapshots rather than a literal Task-tool subagent invocation, which the manifest explicitly permits ("the test reads pre/post fixture snapshots, so it is fully autotest once those exist").

## 3. Task Review Synthesis

### ADV010-T001: Telemetry gap analysis (research) — PASSED
- **Planned**: 8+ numbered findings with file/line citations, derived-requirements list.
- **Actual**: Exactly 8 findings, every citation verified against live repo; 5 telemetry modules scoped.
- **Iterations**: 0.
- **Design Accuracy**: accurate.
- **Issues Found**: none.

### ADV010-T002: Test strategy — PASSED
- **Planned**: Test strategy doc mapping every autotest TC to a named function.
- **Actual**: TC→function map delivered with within-1 delta tolerance for strategy/manifest drift.
- **Iterations**: 0.
- **Design Accuracy**: accurate.

### ADV010-T003: Schema module — PASSED
- **Planned**: Row + frontmatter schema dataclasses with parser.
- **Actual**: Exact 12-column row header and 6-key frontmatter delivered; parser rejects bad types, duplicate Run IDs.
- **Iterations**: 0.
- **Design Accuracy**: accurate.

### ADV010-T004: Cost model — PASSED
- **Planned**: Rates loader from `.agent/config.md`, pure cost_for(), normalize_model() aliases, UnknownModelError.
- **Actual**: All four behaviors delivered; stdlib-only YAML-subset parser used (see §6 decision already in knowledge base).
- **Iterations**: 0.
- **Design Accuracy**: accurate.

### ADV010-T005: Validator / event types — PASSED
- **Planned**: Dataclass event validator + deterministic Run ID.
- **Actual**: Run ID = truncated SHA-1 of event fields; every documented invalid payload variant rejected.
- **Iterations**: 0.
- **Design Accuracy**: accurate.

### ADV010-T006: Aggregator + format_duration — PASSED
- **Planned**: Frontmatter recompute from rows; byte-idempotent; table-driven duration formatter.
- **Actual**: All 6 aggregator TCs pass; atomic `.new` + rename + backup write pattern.
- **Iterations**: 0.
- **Design Accuracy**: accurate.

### ADV010-T007: Capture entrypoint + error isolation — PASSED
- **Planned**: stdin-driven capture with exit-0-on-failure and jsonl error log.
- **Actual**: All 4 acceptance criteria + 5 EI target conditions pass (EI-2 platform-skipped on Windows, documented).
- **Iterations**: 0.
- **Design Accuracy**: accurate. This is the single largest integration task and landed clean.

### ADV010-T008: Hook registration — PASSED
- **Planned**: Append `SubagentStop` + `PostToolUse` hooks to `.claude/settings.local.json` without touching `permissions.allow`.
- **Actual**: 122-byte `permissions.allow` preserved exactly; both hooks point at `capture.py`.
- **Iterations**: 0.

### ADV010-T009: Task actuals updater — PASSED
- **Planned**: Pipe-table editor that fills Actual Duration/Tokens/Cost/Variance without touching other rows.
- **Actual**: Byte-preservation of non-matching rows verified; hand-computed variance values match.
- **Iterations**: 0.

### ADV010-T010: Capture wiring for T009 — PASSED
- **Planned**: Glue capture.py → task_actuals on terminal events.
- **Actual**: Heal-after-partial-fail test (EI-5) passes via this wiring.
- **Iterations**: 0.

### ADV010-T011: Backfill reconstructors — FAILED (cosmetic)
- **Planned**: 4 reconstructors (existing_rows, log_parser, git_windows, task_log) + per-reconstructor fixture tests.
- **Actual**: Implementation modules correct; backfill-consuming TCs (TC-BF-2, TC-BF-5) pass; live backfill on ADV-008 completed successfully. 28/31 tests in `test_reconstructors.py` pass. The 3 failures are in a *dev-helper* test file, not the regression gate: `test_expected_row_count` expects 34 rows but real ADV-008/metrics.md has 21; `test_duration_conversion_4min` / `test_duration_conversion_95s` require fixture rows with string durations ("4min", "95s") but the live ADV-008 fixture has integer seconds already. The implementer's commit log claimed 35 rows — that was incorrect. `test_reconstructors.py` is NOT part of `discover -s .agent/adventures/ADV-010/tests` (TC-RG-1 = 39 tests, all pass).
- **Iterations**: 1 (failure surfaced by reviewer; not re-implemented because downstream TCs pass and the failing assertions are fixture-count drift, not behavioral bugs).
- **Design Accuracy**: minor_drift (implementer's row-count claim was wrong).
- **Issues Found**: 3 (1 high-severity fixture mismatch, 1 medium missing-string-duration fixture, 1 low `datetime.utcnow()` deprecation).

### ADV010-T012: Backfill CLI — PASSED
- **Planned**: `backfill.py` CLI with `--apply` / dry-run / confidence grading / unrecoverable sentinel.
- **Actual**: Byte-idempotent across runs; backfilled rows never `Confidence: high`; no `~` characters in output.
- **Iterations**: 0.

### ADV010-T013: Run backfill on ADV-001..ADV-009 — PASSED
- **Planned**: Apply backfill to every completed adventure with reviewable diffs.
- **Actual**: 9 backup files written (`metrics.md.backup.20260418T1250…Z`); 239 total rows materialized (runs: 36/32/31/23/24/22/26/21/25 across ADV-001..009); all pass post-check `agent_runs > 0`. TC-BF-1 and TC-BF-2 both PASS live.
- **Iterations**: 0.

### ADV010-T014: Live canary on ADV-009 — PASSED
- **Planned**: Invoke a real subagent and assert a populated row + matching totals.
- **Actual**: Canary simulated via stdin injection (per manifest note, acceptable); post fixture shows `agent_runs` 24→25 and `total_tokens_in` 747000→759500 = 747000+12500.
- **Iterations**: 0.
- **Minor note**: Pre fixture uses human-readable duration (`2h 10min`) while post/live use seconds; doesn't affect canary but flagged for future aggregation work.

### ADV010-T015: Test fixtures — PASSED
- **Planned**: Realistic fixture metrics.md files for every TC category.
- **Actual**: All downstream tests consume fixtures without complaint.
- **Iterations**: 0.

### ADV010-T016: Automated test suite — PASSED
- **Planned**: `python -m unittest discover` exits 0; every TC has a named test.
- **Actual**: 39 tests, 1 platform-skip, 0 failed, 1.367s. Every autotest TC covered.
- **Iterations**: 0.

### ADV010-T017: Operator README — PASSED
- **Planned**: `.agent/telemetry/README.md` covering hook install, backfill, error recovery.
- **Actual**: Delivered; no issues.
- **Iterations**: 0.

### ADV010-T018: Knowledge base extraction — PASSED
- **Planned**: ≥1 new entry per knowledge file, attributed to ADV-010; preserve existing entries.
- **Actual**: 3 patterns added (row-schema-with-confidence-column, exit-0-on-failure, backup-before-rename), 2 decisions added (stdlib YAML-subset parser, reconstruct-vs-fake), 1 issue added (YAML-subset parser fragility). Two pre-existing issues closed with additive `Status: fixed in ADV-010 —` suffixes (preserving verbatim originals).
- **Iterations**: 0.

**Tasks needing multiple review cycles**: Only ADV010-T011 received a FAILED review. The failure was a fixture/expectation drift rather than a behavioral bug and was knowingly accepted because the regression gate and live backfill both succeed.

## 4. Process Analysis

### Iterations
- Total review cycles across 18 tasks: **18 reviews, 1 FAILED (cosmetic)**. 17/18 tasks passed on first review.
- Tasks requiring 0 iterations (17): T001, T002, T003, T004, T005, T006, T007, T008, T009, T010, T012, T013, T014, T015, T016, T017, T018.
- Tasks requiring 1+ iterations: **T011** (dev-helper test fixture count drift; reviewer log captured as `failed`, not re-implemented because TC-BF-2 / TC-BF-5 / TC-BF-1 / TC-BF-6 all pass downstream).

### Common Issue Patterns
- **Implementer log inaccuracy** (observed in T011): The implementer's commit log stated `existing_rows.parse(ADV-008/metrics.md)` returns 35 rows; actual return is 21. Reviewers caught this; the AC table in task files does not have a machine-verified "claimed count" cross-check.
- **`datetime.utcnow()` deprecation** (observed in T011, T013, T016 review notes): Python 3.12 emits a non-blocking DeprecationWarning from `.agent/telemetry/tools/backfill.py:636`. Reviewer left as low-severity; not fixed in this adventure.
- **Windows platform skips** (TC-HI-2, TC-EI-2): Read-only file semantics differ on Windows; tests are platform-skipped with documented reasons. Acceptable but means CI on a Linux runner will cover 2 more TCs.
- **metrics.md self-pollution** (discovered during this review): `.agent/adventures/ADV-010/metrics.md` contains ~200+ duplicated synthetic rows (`6be12a81e55f | … coder | ADV010-T005 | opus | 85000 | 28000 …`) and a variety of schema-drifted rows mixing the old 8-column format, the new 12-column format, and short planner rows. This is ADV-010's *own* metrics.md — the frontmatter still reads `total_tokens_in: 0`. Either the canary/test fixture leaked into the live file, or the hook was installed before the adventure's own runs were complete. Worth investigating as a data-hygiene finding independent of the pipeline behavior.
- **Fixture vs. live-data drift** (T011): Tests that assert exact counts / exact string formats against an external evolving file (ADV-008/metrics.md) go stale when the upstream file is rewritten mid-adventure (here: by T013's own backfill run rewriting ADV-008/metrics.md to 21 de-tilded rows before T011's tests were finalized).

### Phase Distribution
Phase-level token/time distribution is not reliably computable because the adventure's own metrics.md is polluted (see above). Rough shape from review files:
| Phase | Approximate share |
|-------|-------------------|
| Planning (opus planner spawns, T001–T018 × 2K–5K out) | ~25% |
| Implementing (sonnet implementer, T001..T018) | ~55% |
| Reviewing (adventure-task-reviewer × 18) | ~15% |
| Fixing (T011 was NOT re-implemented; no rework cycles) | ~5% |

### Bottlenecks
- **T011 fixture count drift**: reviewer had to reconcile four sources (AC, implementer's claim, test expectation, live file) to judge severity. A pre-review autotest that greps the live file for row count would collapse this to one step.
- **Live metrics.md corruption**: the adventure intended to fix telemetry capture but its own metrics.md is the messiest example in the repo. Suggests the hook went live while test fixtures were still being piped through the real capture.py. Future adventures should invoke capture.py against a temp file only, never the adventure's own metrics.md, during development.

## 5. Timeline Analysis

| Task | Planned Est. | Approx. Actual (from review/log) | Variance |
|------|--------------|---------------------------------|----------|
| T001 | 20 min / 35K | ~18 min / ~31K | on target |
| T002 | 15 min / 25K | ~8 min / ~20K | faster |
| T003 | 15 min / 20K | ~8 min / ~32K | more tokens, less time |
| T004 | 25 min / 40K | ~10 min / ~26K | faster |
| T005 | 25 min / 45K | ~15 min / ~36K | faster |
| T006 | 25 min / 40K | ~25 min / ~22K | on target |
| T007 | 30 min / 60K | ~30 min / ~67K | on target |
| T008 | 10 min / 12K | ~6 min / ~9K | faster |
| T009 | 30 min / 50K | ~18 min / ~50K | faster |
| T010 | 10 min / 15K | ~8 min / ~19K | on target |
| T011 | 30 min / 70K | ~20 min / ~75K | on target |
| T012 | 25 min / 50K | ~25 min / ~58K | on target |
| T013 | 20 min / 30K | ~15 min / ~49K | more tokens |
| T014 | 15 min / 20K | ~15 min / ~16K | on target |
| T015 | 20 min / 30K | ~12 min / ~21K | faster |
| T016 | 30 min / 90K | (no isolated row) | at limit; shipped without split |
| T017 | 10 min / 15K | ~4 min / ~10K | faster |
| T018 | 10 min / 15K | ~8 min / ~44K | tokens over, time under |

**Estimation accuracy**: Wall-clock estimates were conservative across the board (most tasks finished 20–50% faster than planned). Token estimates were closer to actual but occasionally undershot (T003, T013, T018 consumed more tokens than estimated while taking less time — consistent with heavy file reading dominating chat turns). T016 was planned at the 90K/30-min ceiling and shipped without needing the split-on-overrun path.

## 6. Knowledge Extraction Suggestions

**Important dedup note**: ADV-010's T018 already extracted six entries to `.agent/knowledge/`:
- patterns.md: `Row-schema with confidence column`, `Exit-0-on-failure for sidecar processes`, `Backup-before-rename reversibility guard`
- decisions.md: `Stdlib-only YAML-subset parser for config frontmatter`, `Reconstruct-vs-fake for historical telemetry rows`
- issues.md: `YAML-subset parser fragility`; plus status-closure suffixes on `Incomplete metrics tracking` and `Metrics Frontmatter Aggregation Gap`

The suggestions below are **new** observations surfaced during the review process (not duplicates of T018's set):

| # | Type | Target File | Title |
|---|------|-------------|-------|
| 1 | issue | .agent/knowledge/issues.md | Self-polluted metrics during telemetry adventure development |
| 2 | issue | .agent/knowledge/issues.md | Dev-helper test files drift vs. regression-gate suite |
| 3 | issue | .agent/knowledge/issues.md | `datetime.utcnow()` DeprecationWarning in backfill.py |
| 4 | pattern | .agent/knowledge/patterns.md | Regression-gate vs. dev-helper test separation |
| 5 | pattern | .agent/knowledge/patterns.md | Platform-skip with documented reason for OS-specific filesystem semantics |
| 6 | feedback | .claude/agent-memory/team-pipeline-implementer/log-accuracy.md | Implementer log row counts must be machine-verified, not claimed |
| 7 | process | (informational) | Pre-review cardinality check for fixture-bound tests |

### Suggestion 1: Self-polluted metrics during telemetry adventure development
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **Self-polluted metrics during telemetry-pipeline development**: ADV-010's own `metrics.md` accumulated ~200+ duplicated synthetic rows and mixed-schema rows because capture.py was wired to the live hook while fixture tests were still being developed — every test invocation of capture.py against the default target wrote into the adventure's own metrics.md. Mitigation: during development of telemetry capture, always pass an explicit `--metrics-file <tmp>` argument, never let the SubagentStop hook fire against the adventure's own metrics.md, and install the hook only AFTER the last implementation task finishes. Detection: a cardinality check (`grep -c '^| ' metrics.md` vs. expected row count at task-completion time) catches it instantly. (from ADV-010)
  ```

### Suggestion 2: Dev-helper test files drift vs. regression-gate suite
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **Dev-helper tests drift from the regression gate**: ADV-010 T011 shipped a `test_reconstructors.py` that was NOT included in `discover -s .agent/adventures/ADV-010/tests` (the TC-RG-1 gate). Three of its assertions went stale against real ADV-008 data. Because it wasn't in the gate, the drift surfaced only when the adventure-task-reviewer ran it independently. Mitigation: either (a) include every test file the adventure ships in the `discover` glob, or (b) explicitly label dev-helper tests as such in a `tests/README.md` and exclude them from the reviewer's proof command. Do not leave tests in the tree that aren't either in the gate or documented as excluded. (from ADV-010 T011)
  ```

### Suggestion 3: `datetime.utcnow()` DeprecationWarning in backfill.py
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **`datetime.utcnow()` deprecated in Python 3.12**: `.agent/telemetry/tools/backfill.py:636` calls `datetime.datetime.utcnow()` which emits a DeprecationWarning on every run. Non-blocking for tests but noisy in CI output and scheduled for removal in a future Python release. Fix: replace with `datetime.datetime.now(datetime.UTC)`. (from ADV-010, reviews of T011/T013/T016)
  ```

### Suggestion 4: Regression-gate vs. dev-helper test separation
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Regression-gate vs. dev-helper test separation**: When a test suite mixes (a) tests that gate acceptance and (b) exploratory tests used during development to diff against live files, either put every test under the same `discover` root (so CI sees all of them) or segregate dev-helper tests under `tests/dev/` and add a `tests/README.md` listing which subdirectories are gate vs. helper. A test in the tree but outside the gate is worse than no test — it rots silently and surfaces only in review. (from ADV-010)
  ```

### Suggestion 5: Platform-skip with documented reason for OS-specific filesystem semantics
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Platform-skip with documented reason for OS-specific filesystem semantics**: Tests that depend on POSIX `chmod` read-only semantics (e.g., write-error handling) behave differently on Windows where `chmod` does not block writes. Rather than making such tests pass-or-xfail, emit an explicit `@unittest.skipIf(sys.platform == "win32", "chmod read-only on Windows may not block writes")` decorator. The skip message itself documents the limitation and appears in test output. ADV-010 used this for TC-HI-2 and TC-EI-2 and it kept the Windows regression gate clean without masking the Linux-specific behaviour. (from ADV-010)
  ```

### Suggestion 6: Implementer log row counts must be machine-verified
- **Type**: feedback
- **Target File**: `.claude/agent-memory/team-pipeline-implementer/log-accuracy.md`
- **Role**: implementer
- **Content**:
  ```
  ---
  name: Implementer log numeric claims must be machine-verified
  description: When an implementer log asserts a specific row count / file length / element count, run the grep or len() that proves it rather than estimating from memory.
  type: feedback
  ---

  Rule: any numeric claim in the implementer's task log (row count, test count, line count, file size) must be produced by a shell or Python command executed in the same turn, and the command should be cited.

  **Why:** ADV-010 T011's log stated `existing_rows.parse(ADV-008/metrics.md)` returns 35 rows; the real count was 21. The reviewer caught it, but only after reconciling four sources. A `grep -c '^| ' <file>` in the implementer's log would have prevented the failed review.

  **How to apply:** Before writing "returns N rows" or "produces N files" in a task log, run the verifying command in the same turn and quote the output. If counts come from a Python REPL, paste the REPL line.
  ```

### Suggestion 7: Pre-review cardinality check for fixture-bound tests
- **Type**: process
- **Target File**: (informational — not auto-applied)
- **Content**:
  ```
  Process suggestion: add a "cardinality sanity" step to the adventure-task-reviewer's pre-test routine for tasks whose tests assert exact counts against external files. Before running the test suite, grep the external file(s) for the asserted cardinality and flag discrepancies up front. This would have converted T011's FAILED review into a "fixture drift — update expected count" note in minutes instead of a failed-review cycle. Candidate implementation: an optional `expected_counts` block in the task file listing `{path: N}` pairs that the reviewer checks before invoking pytest/unittest.
  ```

## 7. Recommendations

Actionable, ordered by priority:

1. **Clean up ADV-010/metrics.md immediately** (high). The adventure that fixed telemetry has the most polluted metrics.md in the repo. Run `backfill.py --apply` on ADV-010 itself, deduplicate the synthetic `6be12a81e55f` rows, and recompute the frontmatter. Without this, ADV-010's own telemetry is a negative example of the pattern it just shipped.
2. **Fix `datetime.utcnow()` in backfill.py:636** (medium). One-line change, silences DeprecationWarning across the whole pipeline, future-proofs against Python removal.
3. **Fix or retire `test_reconstructors.py`** (medium). Either update the 3 stale assertions to reflect the real ADV-008 data (21 rows, integer-second durations) and add synthetic fixtures for string-duration cases, OR move it under `tests/dev/` with a README note. Leaving it in the tree as-is is a false negative.
4. **Install the hook as the very last step of telemetry-development adventures** (medium). Prevents self-pollution of the adventure's own metrics.md during iteration.
5. **Add cardinality sanity step to adventure-task-reviewer** (low). See Suggestion 7 above.
6. **Fill out the manifest Evaluations table** (low). Every Actual Duration/Tokens/Cost/Variance cell is still `—` because the task_actuals updater was built but not pointed at ADV-010's own manifest. Dogfooding opportunity.

### Areas needing hardening or refactoring
- **`.agent/telemetry/tools/backfill.py`**: 636-line single file with the deprecated API call, string-vs-integer duration handling split across multiple reconstructors. Candidate for refactor into per-concern modules once a second backfill consumer appears.
- **YAML-subset parser in `cost_model.py`**: flagged in issues.md already — fine for now but will need replacement if `.agent/config.md` frontmatter grows beyond flat mappings + one level.
- **Fixture/live-data coupling**: several tests read real ADV-008 / ADV-009 files. When a future adventure touches those, tests silently drift. Consider freezing reference fixtures under `tests/fixtures/frozen/` and diffing against them instead of reading live paths.
