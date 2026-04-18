# Test Strategy — Design

## Overview

This is a **research adventure**. Every target condition uses
`proof_method: autotest` where technically feasible; proofs consist of `test
-f` existence checks, `grep -c` section/content checks, and a small number of
`poc` checks where the proof is argumentative rather than mechanical (e.g.
coverage arithmetic).

The single CI entrypoint is a shell script
`.agent/adventures/ADV-011/tests/run-all.sh` that runs every TC proof command
in sequence and exits non-zero on any failure.

## Target Files

- `.agent/adventures/ADV-011/tests/test-strategy.md` — TC → proof command
  mapping table. NEW (produced by T002).
- `.agent/adventures/ADV-011/tests/run-all.sh` — aggregated CI entrypoint.
  NEW (produced by T011).
- `.agent/adventures/ADV-011/tests/test_coverage_arithmetic.py` — stdlib
  `unittest` check that `COVERED + RETIRED + DEFERRED = total_source_TCs` in
  `validation-coverage.md`. NEW.
- `.agent/adventures/ADV-011/tests/test_mapping_completeness.py` — stdlib
  `unittest` that every concept in `concept-inventory.md` is referenced in
  `concept-mapping.md`. NEW.

## TC → Proof-Command Mapping

For each TC listed in the manifest, the strategy names the proof command.
Canonical patterns:

- **Existence** — `test -f <path>`
- **Section count** — `[ $(grep -c '^## ' <file>) -ge N ]`
- **Bucket membership** — `grep -cE "bucket: (descriptor|builder|controller|out-of-scope)" <mapping>`
- **Dedup rows present** — `grep -q "Z3 ordinals" <dedup.md>` etc. for each
  seed row.
- **Coverage arithmetic** — unittest function reading the matrix file.

## Rule: no `manual` TCs

Every TC must be either `autotest` (shell or unittest) or `poc` with a
justification (coverage arithmetic, count-based). `manual` is disallowed.

## Target Conditions (for this design)

- `test-strategy.md` maps every TC to a concrete proof command string.
- `run-all.sh` exits 0 once all deliverables exist.
- The two unittest files exist and each contains at least one test function
  with a docstring naming the TCs it validates.
