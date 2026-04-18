---
task_id: ADV010-T015
adventure_id: ADV-010
status: PASSED
timestamp: 2026-04-18T00:01:00Z
build_result: N/A
test_result: N/A
---

# Review: ADV010-T015

## Summary
| Field | Value |
|-------|-------|
| Task | ADV010-T015 |
| Title | Test fixtures |
| Status | PASSED |
| Timestamp | 2026-04-18T00:01:00Z |

## Build Result
- Command: `` (none configured)
- Result: N/A

## Test Result
- Command: `` (none configured)
- Result: N/A — fixtures are data files, verified by inspection and math

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | All event JSON files validate or fail-validate as documented | Yes | 4 valid JSONs (happy_opus, happy_sonnet, replay, post_tool_use) parse correctly; missing_tokens omits `tokens_in` and `adventure_id`/`session_id` to trigger PayloadError; bad_model uses `unknown-model-xyz`; malformed.txt is non-JSON. All match documented intent. |
| 2 | Every metrics fixture has a known-good frontmatter-totals pair computable by hand | Yes | single_row: 1.6950=(85000+28000)/1000*0.015. multi_model: 1.7775 verified. with_tildes: 0.9180 verified. tampered: intentionally wrong (design intent). empty: all zeros. All match hand-computation. |

## Target Conditions
No target conditions assigned to this task (`target_conditions: []`).

## Issues Found
No issues found.

## Recommendations
- replay.json is confirmed byte-identical to happy_opus.json (diff exits 0) — idempotency test TC-CC-3 will work correctly.
- with_estimates.md correctly sets Est.Tokens=45000, Est.Cost=$0.6750 (=45000/1000*0.015) for Variance computation.
- tampered.md's intentionally wrong frontmatter (agent_runs: 99, total_cost: 9.9999) is a valid test of frontmatter-healing; a comment or design note would help readers quickly identify it as intentionally wrong, but this is minor.
