# Validation Against ADV-001..008 Target Conditions — Design

## Overview

Cross-checks the three unified designs against every target condition from
ADV-001..008 to prove that the unification loses no capability. The deliverable
is a coverage matrix: every TC from source adventures mapped to the unified
design and module that satisfies it (or to a pruning-catalog row that
explicitly retires it).

## Target Files

- `.agent/adventures/ADV-011/research/validation-coverage.md` — matrix. NEW.
- `.agent/adventures/ADV-011/research/validation-report.md` — narrative summary
  of coverage (green/amber counts, any gaps). NEW.

## Approach

1. Extract every TC from ADV-001..008 manifests (tabular; the tool is `grep` +
   manual transcription into the matrix).
2. For each TC, assign one of:
   - `COVERED-BY: <unified-design> §<section>` — the capability survives.
   - `RETIRED-BY: pruning-catalog row <n>` — the capability is intentionally
     dropped; cite the catalog row.
   - `DEFERRED-TO: ADV-NN` — the capability moves to a named downstream
     adventure (must appear in the downstream plan).
3. Completeness check: no TC has a blank verdict.
4. Assertion: `COVERED + RETIRED + DEFERRED = total_TCs_source`.
5. Any TC that was `COVERED` must name a concrete section in the unified
   design — not just "builder". A grep-based autotest enforces the section
   marker.

## Dependencies

- `design-unified-descriptor.md`
- `design-unified-builder.md`
- `design-unified-controller.md`
- `design-pruning-catalog.md`
- `design-downstream-adventure-plan.md`

## Target Conditions

- Every TC from ADV-001..008 manifests appears in the matrix.
- Every row has a non-blank verdict.
- Every `COVERED-BY` row cites a section anchor that exists in the referenced
  design file.
- The report totals match the TC counts from the source manifests (assertion
  testable by grep + arithmetic).
