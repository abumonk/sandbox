---
task_id: ADV010-T011
adventure_id: ADV-010
status: FAILED
timestamp: 2026-04-18T12:05:00Z
build_result: N/A
test_result: FAIL
---

# Review: ADV010-T011

## Summary
| Field | Value |
|-------|-------|
| Task | ADV010-T011 |
| Title | Backfill tool — reconstructors |
| Status | FAILED |
| Timestamp | 2026-04-18T12:05:00Z |

## Build Result
- Command: _(none configured in config.md)_
- Result: N/A

## Test Result
- Command: `python -m pytest .agent/adventures/ADV-010/tests/test_reconstructors.py -v`
- Result: FAIL
- Pass/Fail: 28 passed, 3 failed
- Output:
  - FAILED `TestExistingRowsParse::test_expected_row_count` — got 21, expected 34–36
  - FAILED `TestExistingRowsParse::test_duration_conversion_4min` — no row with duration_s=240
  - FAILED `TestExistingRowsParse::test_duration_conversion_95s` — no row with duration_s=95
- Note: TC-BF-2 and TC-BF-5 (`test_backfill.py`) both PASS via pytest.

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | `existing_rows.parse(ADV-008/metrics.md)` returns 34 candidates with tildes stripped and integer tokens | No | Returns 21 — the real ADV-008/metrics.md has 21 rows, not 34. No tildes present in fixture; strip logic is correct but untested with tilde data. Implementer log claims 35, but actual count is 21. |
| 2 | `log_parser.parse(ADV-008/adventure.log)` returns ≥19 spawn events | Yes | Passes `test_at_least_19_spawn_events` |
| 3 | `git_windows.for_adventure("ADV-008")` returns per-task windows | Yes | Returns candidates; all pass git_windows tests |
| 4 | Each reconstructor has at least one fixture-based unit test | Yes | 31 tests across 4 reconstructors, using real ADV-008 data as fixtures |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-BF-2 | ADV-008 backfill preserves row numerics, strips tildes | autotest | `python -m pytest .agent/adventures/ADV-010/tests/test_backfill.py::TestAdv008RowsPreservedTildesStripped` | PASS | 1 passed |
| TC-BF-5 | Unreconstructable task → row with result=unrecoverable | autotest | `python -m pytest .agent/adventures/ADV-010/tests/test_backfill.py::TestUnreconstructableRowEmitted` | PASS | 1 passed |

## Issues Found
| # | Severity | Description | File | Line |
|---|----------|-------------|------|------|
| 1 | high | AC-1 unmet: `existing_rows.parse(ADV-008/metrics.md)` returns 21 candidates, not 34. Implementer log incorrectly states 35. The real metrics.md has exactly 21 rows and no duration strings (durations are already integer seconds). | `.agent/adventures/ADV-010/tests/test_reconstructors.py` | 67 |
| 2 | medium | Test `test_duration_conversion_4min` and `test_duration_conversion_95s` fail because no ADV-008 row has a string duration like "4min"/"95s" — the fixture has integer-second durations only. The duration-string parsing logic in `existing_rows.py` is correct but not validated by live fixture data. Tests need a synthetic fixture row with string durations. | `.agent/adventures/ADV-010/tests/test_reconstructors.py` | 91–99 |
| 3 | low | `backfill.py` uses deprecated `datetime.utcnow()` (DeprecationWarning on every run). | `.agent/telemetry/tools/backfill.py` | 636 |

## Recommendations
1. **Fix AC-1 (blocker):** Correct the expected row count in `test_expected_row_count` to match the actual ADV-008/metrics.md row count (21), or add the missing 13 rows to metrics.md if the AC count of 34 was intentional.
2. **Fix duration-string tests:** Add a synthetic fixture file with rows containing "4min" and "95s" duration strings to properly exercise `_parse_duration`. The underlying implementation is correct — only the test fixture is wrong.
3. **Minor:** Replace `datetime.utcnow()` in `backfill.py:636` with `datetime.now(timezone.utc)` to silence the deprecation warning.
