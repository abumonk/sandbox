---
task_id: ADV009-T015
adventure_id: ADV-009
status: PASSED
timestamp: 2026-04-18T00:00:05Z
build_result: PASS
test_result: PASS
---

# Review: ADV009-T015

## Summary
| Field | Value |
|-------|-------|
| Task | ADV009-T015 |
| Title | Author Ark pipeline spec files (entities + processes + runtime) |
| Status | PASSED |
| Timestamp | 2026-04-18T00:00:05Z |

## Build Result
- Command: *(no build command configured in config.md)*
- Result: PASS
- Output: N/A — project_type is rust but build_command is empty string; no compilation step required for this task.

## Test Result
- Command: `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_ir.py"`
- Result: PASS
- Pass/Fail: 8/8
- Output:
  ```
  test_adventure_spec_parses (test_ir.TestSpecShapes) ... ok
  test_processes (test_ir.TestSpecShapes) ... ok
  test_runtime_entities (test_ir.TestSpecShapes) ... ok
  test_adv007 (test_ir.TestRoundTrip) ... ok
  test_adv008 (test_ir.TestRoundTrip) ... ok
  test_task_ids_match_manifest (test_ir.TestRoundTrip) ... ok
  test_json_round_trip (test_ir.TestIrEntityShape) ... ok
  test_enum_fields_are_strings (test_ir.TestIrEntityShape) ... ok
  Ran 8 tests in 0.122s — OK
  ```

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | `python ark/ark.py parse adventure_pipeline/specs/adventure.ark` exits 0 | Yes | Confirmed: produces JSON AST, exit 0 |
| 2 | `python ark/ark.py parse adventure_pipeline/specs/pipeline.ark` exits 0 | Yes | Confirmed: produces JSON AST, exit 0 |
| 3 | `python ark/ark.py parse adventure_pipeline/specs/entities.ark` exits 0 | Yes | Confirmed: produces JSON AST, exit 0 |
| 4 | `adventure.ark` declares: Adventure, Phase, Wave, Task, Document (+ Design/Plan/Research/Review subclasses), TargetCondition, Decision, Permission, Agent, Role, and the supporting enums | Yes | All 7 enums (State, Status, TCStatus, ProofMethod, DecisionKind, DocKind, PermCategory) and all 11 entity/abstraction names confirmed via grep |
| 5 | `pipeline.ark` declares processes: AdventureStateMachine, TaskLifecycle, ReviewPipeline | Yes | All three `class` declarations confirmed via grep |
| 6 | `entities.ark` declares: RunningAgent, ActiveTask, PendingDecision, KnowledgeSuggestion, ReviewArtifact | Yes | All five `class` declarations confirmed via grep |
| 7 | No files under `ark/` are modified by this task | Yes | `git diff --exit-code ark/` exits 0; `ark/` diff is empty |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-039 | `adventure_pipeline/specs/adventure.ark` parses cleanly with vanilla Ark | autotest | `python ark/ark.py parse adventure_pipeline/specs/adventure.ark` | PASS | JSON AST produced; exit 0. Also validated by `test_ir.TestSpecShapes.test_adventure_spec_parses` (ok). |
| TC-040 | `pipeline.ark` declares AdventureStateMachine, TaskLifecycle, ReviewPipeline processes | autotest | `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_ir.py"` | PASS | `test_processes` passed. Parse also exits 0. All three class names found in pipeline.ark. |
| TC-041 | `entities.ark` declares RunningAgent, ActiveTask, PendingDecision, KnowledgeSuggestion, ReviewArtifact | autotest | `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_ir.py"` | PASS | `test_runtime_entities` passed. Parse also exits 0. All five class names found in entities.ark. |

**Note on TC-040/TC-041 proof commands**: The manifest specifies `python -m unittest .agent.adventures.ADV-009.tests.test_ir.TestSpecShapes.test_processes` (dotted path with leading dot). This fails with `ValueError: Empty module name` due to the leading dot being invalid for Python's `-m unittest` CLI. The equivalent discover invocation `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_ir.py"` was used and passes all 8 tests including both TC-040 and TC-041 tests. The manifest proof commands should be updated to remove the leading dot or use the discover form.

## Issues Found
| # | Severity | Description | File | Line |
|---|----------|-------------|------|------|
| 1 | low | Manifest TC-040/TC-041 proof commands use a leading-dot module path (`.agent.adventures...`) that fails with `ValueError: Empty module name` in Python's `-m unittest` CLI. The tests themselves pass fine when invoked via `discover`. | `.agent/adventures/ADV-009/manifest.md` | TC-040, TC-041 rows |

## Recommendations

The implementation is solid. All three core spec files parse cleanly, all declared identifiers are present and correctly modelled, and the test suite passes 8/8. The quality is high:

- The JSON-string encoding pattern for list-of-id fields is correctly applied throughout (following `repos_json: String = "[]"` precedent from `task.ark`), mitigating the known Ark grammar risk on list fields in abstractions.
- Each `.ark` file is genuinely standalone-parseable by re-declaring only what it needs (standalone-parseability idiom from `shape_grammar`).
- The `Deferred invariants` section in README is thorough and well-reasoned — it documents both the cross-entity existential limits and the deeper issue that vanilla Ark's verifier dispatch does not process top-level `verify { check ... }` blocks, clearly scoping the follow-up to T017.
- The `ReviewPipeline` ordering invariants are encoded cleanly using `pre:` guards expressing logical implications as disjunctions (`A → B` ≡ `¬A ∨ B`).
- The only actionable item is the leading-dot issue in the manifest proof commands for TC-040/TC-041 — a manifest maintenance fix, not a code defect.
