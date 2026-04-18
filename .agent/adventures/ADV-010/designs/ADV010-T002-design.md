# Test Strategy Document (ADV010-T002) - Design

## Approach

The test-strategy document (`tests/test-strategy.md`) has already been drafted by the adventure planner. It contains a CI one-liner, per-file coverage tables mapping 35 autotest TCs to named unittest functions across 9 test files, and a fixtures strategy section. The implementer's job is to **verify completeness** against the manifest's final TC list, ensure structural correctness, and amend any gaps.

## Target Files

- `.agent/adventures/ADV-010/tests/test-strategy.md` - The sole deliverable. Verify and amend the TC-to-function mapping table to ensure every autotest TC from the manifest is covered.

## Implementation Steps

1. **Read the manifest TC table** (`manifest.md` Target Conditions section). Extract every row where `Proof Method` = `autotest`. There should be exactly 35 such TCs (TC-TS-1, TC-S-1..TC-S-3, TC-CC-1..TC-CC-4, TC-CM-1..TC-CM-4, TC-HI-1..TC-HI-4, TC-AG-1..TC-AG-6, TC-EI-1..TC-EI-5, TC-BF-1..TC-BF-6, TC-LC-1, TC-RG-1).

2. **Cross-check against test-strategy.md**. For each autotest TC from step 1, confirm it appears in the per-file coverage tables with:
   - A specific test file name (column: Test file / header section).
   - A specific function name matching `test_<snake_case>` convention.
   - A brief assertion description.

3. **Verify test file count**. The acceptance criteria require 8 test files (one per design area). The current draft lists 9 test files including `test_regression.py`. Confirm these files cover all 7 design areas plus the regression suite:
   - `test_schema.py` (row_schema / event_payload)
   - `test_cost_model.py` (design-cost-model)
   - `test_capture.py` (design-capture-contract + design-hook-integration)
   - `test_aggregator.py` (design-aggregation-rules)
   - `test_task_actuals.py` (design-aggregation-rules, task-actuals subset)
   - `test_error_isolation.py` (design-error-isolation)
   - `test_backfill.py` (design-backfill-strategy)
   - `test_live_canary.py` (live canary from concept section 6)
   - `test_regression.py` (CI gate / discovery)

   Note: the acceptance criteria say "8 files expected" but the design lists 9 (task_actuals is split from aggregator). The implementer should count unique test files and confirm the acceptance criteria intent -- 8+ distinct test files is acceptable since test_regression.py serves as the CI gate and test_task_actuals.py is a legitimate split of aggregation concerns.

4. **Verify CI one-liner** is present and matches:
   ```
   python -m unittest discover -s .agent/adventures/ADV-010/tests -v
   ```

5. **Verify fixtures strategy section** documents the three fixture categories (events, metrics, manifests) with representative file names.

6. **Verify self-check clause** exists -- the document should note that `test_regression.py` will grep-count TC rows in `test-strategy.md` against manifest autotest TCs to catch drift.

7. **Amend any gaps**. If the manifest has a TC not present in test-strategy.md, add it to the correct per-file table with an appropriate function name and assertion description. If a test file is missing, add a new section header.

8. **Final verification**. Count TC rows across all per-file tables. Must equal 35 (the count of `Proof Method: autotest` rows in the manifest). Every TC ID must appear exactly once.

## Testing Strategy

This is itself the test design task -- its output is verified by:
- **TC-TS-1**: `test_regression.py` preamble grep-counts both the manifest autotest TCs and the test-strategy.md TC rows, asserting equality. This is the autotest proof.
- **TC-RG-1**: `test_regression.py::test_full_discover_exits_zero` re-invokes `unittest discover` via subprocess and asserts exit 0.

Manual verification during implementation: grep for each TC-XX-N in both `manifest.md` and `test-strategy.md` and confirm bidirectional coverage.

## Risks

- **TC count drift**: If tasks T003-T018 introduce or remove TCs during implementation, test-strategy.md must be updated. The self-check in test_regression.py mitigates this by failing CI if counts diverge.
- **"8 files expected" ambiguity**: The acceptance criteria say 8 files but the design has 9 test files (test_task_actuals.py split from test_aggregator.py). This is a design improvement, not a violation -- the implementer should confirm the intent is "at least one test file per design area" which is satisfied.
- **Function naming**: The strategy maps TC to function names that do not yet exist in code. If implementers of T016 choose different names, the strategy must be updated to match. The TC ID is the stable key, not the function name.
