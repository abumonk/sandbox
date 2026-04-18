# ADV-011 Final Validation Report

Produced by task ADV011-T012 (researcher). Date: 2026-04-15.

---

## Counts

One row per research artefact. Values are data-row counts (header and separator rows excluded).

| Artefact | Metric | Value |
|----------|--------|-------|
| `concept-inventory.md` | concepts harvested from ADV-001..008 + ADV-010 | 229 |
| `concept-mapping.md` | concepts classified (descriptor / builder / controller / out-of-scope) | 218 |
| `deduplication-matrix.md` | duplication rows with canonical_form | 8 |
| `pruning-catalog.md` | prune rows (OUT-OF-SCOPE or DROP disposition) | 46 |
| `descriptor-delta.md` | stdlib files with verdict | 9 / 9 |
| `builder-delta.md` | verify/codegen modules classified | 21 |
| `controller-delta.md` | unified subsystems named | 7 / 7 |
| `validation-coverage.md` | total source TCs / covered / retired / deferred | 272=179+61+32 |
| `downstream-adventure-plan.md` | downstream adventures planned | 6 |

---

## TC Coverage

Source of truth: `validation-coverage.md` (produced by T009).

- **Total source TCs (ADV-001..008):** 272
- **Covered by unified designs:** 179
- **Retired via pruning-catalog:** 61
- **Deferred to downstream adventures:** 32
- **Identity:** covered + retired + deferred = total (179+61+32=272) ✓

**Covered (179).** These TCs address concepts whose subject matter maps directly to content in one of the three delta files (`descriptor-delta.md`, `builder-delta.md`, or `controller-delta.md`); they are substantively addressed by ADV-011's unified design research.

**Retired (61).** These TCs target concepts in `pruning-catalog.md` that carry a DROP or OUT-OF-SCOPE disposition; the dominant source is ADV-007 (34 ecosystem research artefact TCs) and ADV-008 shape_grammar domain content (19 TCs), which are superseded by or deferred outside the ark-core unified design surface.

**Deferred (32).** These TCs address future-work capabilities not yet covered by the current unified designs and not pruned; 26 are deferred to ADV-DU (Descriptor Unification, covering grammar/parser/stdlib restructuring) and 6 to ADV-UI (UI Surface, covering HTML rendering and screenshot pipeline capabilities).

---

## Run-All Output

Command: `bash .agent/adventures/ADV-011/tests/run-all.sh`
Executed: 2026-04-15T04:08:00Z
Exit code: 0

```text
==> TC-001
    PASS TC-001
==> TC-002
| concept | source_adventure | source_artefact | description |
    PASS TC-002
==> TC-TS-1
    PASS TC-TS-1
==> TC-003
    PASS TC-003
==> TC-004
test_buckets_allowlist (test_mapping_completeness.TestMappingCompleteness.test_buckets_allowlist)
TC-004: every mapping row's bucket column is in the allowlist. ... ok
test_every_inventory_concept_is_mapped (test_mapping_completeness.TestMappingCompleteness.test_every_inventory_concept_is_mapped)
Cross-file: no concept from inventory is silently dropped. ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.042s

OK
    PASS TC-004
==> TC-005
    PASS TC-005
==> TC-006
    PASS TC-006
==> TC-007
    PASS TC-007
==> TC-008
    PASS TC-008
==> TC-009
    PASS TC-009
==> TC-010
    PASS TC-010
==> TC-011
    PASS TC-011
==> TC-012
    PASS TC-012
==> TC-013
    PASS TC-013
==> TC-014
    PASS TC-014
==> TC-015
    PASS TC-015
==> TC-016
test_arithmetic_holds (test_coverage_arithmetic.TestCoverageArithmetic.test_arithmetic_holds)
TC-016: covered + retired + deferred == total. ... ok
test_each_tc_has_exactly_one_verdict (test_coverage_arithmetic.TestCoverageArithmetic.test_each_tc_has_exactly_one_verdict)
Every TC row must match exactly one of the three verdicts. ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.001s

OK
    PASS TC-016
==> TC-017
    PASS TC-017
==> TC-018
    PASS TC-018
==> TC-019
    PASS TC-019
==> TC-020
test_arithmetic_holds (test_coverage_arithmetic.TestCoverageArithmetic.test_arithmetic_holds)
TC-016: covered + retired + deferred == total. ... ok
test_each_tc_has_exactly_one_verdict (test_coverage_arithmetic.TestCoverageArithmetic.test_each_tc_has_exactly_one_verdict)
Every TC row must match exactly one of the three verdicts. ... ok
test_buckets_allowlist (test_mapping_completeness.TestMappingCompleteness.test_buckets_allowlist)
TC-004: every mapping row's bucket column is in the allowlist. ... ok
test_every_inventory_concept_is_mapped (test_mapping_completeness.TestMappingCompleteness.test_every_inventory_concept_is_mapped)
Cross-file: no concept from inventory is silently dropped. ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.042s

OK
    PASS TC-020
==> TC-021
    PASS TC-021
Exit code: 0
```

---

## Ready-for-Review Statement

Tasks T001 through T011 are all complete: T001 produced `concept-inventory.md`, T002 produced the test strategy, T003 produced `concept-mapping.md`, T004 produced `deduplication-matrix.md`, T005 produced `pruning-catalog.md`, T006 produced `descriptor-delta.md`, T007 produced `builder-delta.md`, T008 produced `controller-delta.md`, T009 produced `validation-coverage.md`, T010 produced `downstream-adventure-plan.md`, and T011 produced the `run-all.sh` CI aggregator and Python unit tests. All 21 target conditions (TC-001 through TC-021, including TC-TS-1 and TC-020) pass with exit code 0 as confirmed by the `run-all.sh` output above. The arithmetic invariant `179+61+32=272` is verified by `test_coverage_arithmetic.py` (TC-016) and restated in this report. ADV-011 is ready to flip to `state: review`.
