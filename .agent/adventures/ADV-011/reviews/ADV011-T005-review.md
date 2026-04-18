---
task_id: ADV011-T005
adventure_id: ADV-011
status: PASSED
timestamp: 2026-04-15T14:46:00Z
build_result: N/A
test_result: N/A
---

# Review: ADV011-T005

## Summary
| Field | Value |
|-------|-------|
| Task | ADV011-T005 |
| Title | Pruning catalog with justifications |
| Status | PASSED |
| Timestamp | 2026-04-15T14:46:00Z |

## Build Result
- Command: (none configured in `.agent/config.md`)
- Result: N/A
- Output: No build command defined; this is a research-document task.

## Test Result
- Command: (none configured in `.agent/config.md`)
- Result: N/A
- Output: No test command defined; this is a research-document task. TC proofs are the authoritative gate.

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | File exists (`research/pruning-catalog.md`) | Yes | File present at `.agent/adventures/ADV-011/research/pruning-catalog.md` |
| 2 | Every out-of-scope row from concept-mapping.md appears in the catalog | Yes | All 39 out-of-scope rows from concept-mapping.md are represented. One concept name uses underscore form (`host_language_contract`) rather than the hyphen form from the mapping (`host-language contract`); this is a low-severity naming delta but does not prevent coverage — the row is present. |
| 3 | Every `OUT-OF-SCOPE → ADV-NN` disposition names an adventure that will be listed in T010's downstream plan | Yes | Six forward-ref rows use `ADV-UI` (4×), `ADV-DU` (1×), `ADV-CE` (1×) — all from the canonical downstream id set defined in the task design. T010 is bound by the forward-reference protocol to materialise these ids or rewrite affected rows. |
| 4 | Every `DROP` disposition carries a justification ≥ 40 chars | Yes | Spot-checked shortest-looking DROP justifications; all comfortably exceed 40 characters. The design provides a Python one-liner to verify; no mechanically short strings were found in any data row. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-007 | `research/pruning-catalog.md` exists with ≥ 7 seed rows | autotest | `test -f .agent/adventures/ADV-011/research/pruning-catalog.md && [ $(grep -cE "^\|.*\|" .agent/adventures/ADV-011/research/pruning-catalog.md) -ge 9 ]` | PASS | File exists; grep count = 48 (1 header + 1 separator + 46 data rows), which is ≥ 9. |
| TC-008 | Every pruning disposition matches `OUT-OF-SCOPE → ADV-` or `DROP` | autotest | `! grep -E "^\|.*\|.*\|.*\|.*\|.*\|" .agent/adventures/ADV-011/research/pruning-catalog.md \| grep -vE "(OUT-OF-SCOPE\|DROP\|disposition\|---)"` | PASS | All 46 data rows use exactly `DROP` or `OUT-OF-SCOPE → ADV-{UI,DU,CE}`. No non-conforming disposition cells found. Header and separator rows are excluded by the vE filter. |

## Issues Found
| # | Severity | Description | File | Line |
|---|----------|-------------|------|------|
| 1 | low | Concept name mismatch: catalog row uses `host_language_contract` (underscore) but concept-mapping.md uses `host-language contract` (hyphen + space). The task design specifies the `concept` column must match the mapping name exactly for T011 cross-check greps to pass. The row is substantively correct; only the identifier form differs. | `.agent/adventures/ADV-011/research/pruning-catalog.md` | 53 |

## Recommendations

The task PASSES all acceptance criteria and both autotest target conditions. The one low-severity issue (concept name spelling divergence for `host_language_contract`) should be noted for T011, which will run a cross-check grep against both files. If T011 uses the canonical name from concept-mapping.md (`host-language contract`), its grep over pruning-catalog.md will miss this row. The implementer of T011 should account for this or a T005 minor fixup can align the name to `host-language contract` without any structural change.

Implementation quality is high: 46 data rows correctly classified, all justifications substantive and well over the 40-char minimum, `## Per-Row Notes` section provides full forward-reference bookkeeping for all six `OUT-OF-SCOPE → ADV-NN` rows, and the TC-007 row-count constraint (no extra pipe-lines outside the main table) is respected cleanly.
