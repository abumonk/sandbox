# Test Strategy — ADV-011 Ark Core Unification

## Scope

This is a research adventure. All target conditions (TC-001..TC-021 + TC-TS-1) are
proven by automated checks — `test -f` existence probes, `grep`-based content
assertions, and `python -m unittest` for argumentative arithmetic checks. The
`manual` proof method is **disallowed**; any TC that cannot be probed by a
deterministic shell or Python command is a design bug and must be redesigned.

The single CI entrypoint is `tests/run-all.sh`. It runs every proof command in
manifest numeric order, collects failures without short-circuiting, and exits 0
only when all checks pass. Python unittest is used for two argumentative
checks (TC-016, TC-004) that require parsing pipe-table files.

## Proof Method Policy

- **autotest**: shell one-liner using `test -f`, `grep`, `awk`, `bash -c`, or
  `python -m unittest`. Must be runnable unattended from repo root.
- **poc**: allowed only when a pure shell proof would require fragile pipe-table
  parsing or multi-step arithmetic. Each `poc` TC must have a justification
  entry in `## POC Justifications`.
- **manual**: DISALLOWED — any manual proof is a design bug.

## TC → Proof Command Mapping

| TC | Method | Produced By | Proof Command |
|----|--------|-------------|---------------|
| TC-001 | autotest | T001 | `test -f .agent/adventures/ADV-011/research/concept-inventory.md && for a in 001 002 003 004 005 006 007 008 010; do grep -q "ADV-$a" .agent/adventures/ADV-011/research/concept-inventory.md \|\| exit 1; done` |
| TC-002 | autotest | T001 | `grep -E "^\| concept \| source_adventure \| source_artefact \| description \|" .agent/adventures/ADV-011/research/concept-inventory.md` |
| TC-TS-1 | autotest | T002 | `test -f .agent/adventures/ADV-011/tests/test-strategy.md && [ $(grep -cE "^\| TC-" .agent/adventures/ADV-011/tests/test-strategy.md) -ge 20 ]` |
| TC-003 | autotest | T003 | `test -f .agent/adventures/ADV-011/research/concept-mapping.md && grep -q "## Per-Bucket Rationale" .agent/adventures/ADV-011/research/concept-mapping.md` |
| TC-004 | poc | T003 + T011 | `python -m unittest .agent.adventures.ADV-011.tests.test_mapping_completeness.TestMappingCompleteness.test_buckets_allowlist` |
| TC-005 | autotest | T004 | `test -f .agent/adventures/ADV-011/research/deduplication-matrix.md && for k in "Z3 ordinals" "Lark" "Pest" "telemetry" "PASS_OPAQUE" "dogfood" "Skill"; do grep -qi "$k" .agent/adventures/ADV-011/research/deduplication-matrix.md \|\| exit 1; done` |
| TC-006 | autotest | T004 | `grep -E "^\|.*\|.*\|.*\|.*\|.*\|" .agent/adventures/ADV-011/research/deduplication-matrix.md \| grep -vE "^\| *canonical_form \|" \| grep -vE "^\|-" \| awk -F'\\|' 'NF>=6 && $4 !~ /^ *$/ {c++} END {exit (c>=6)?0:1}'` |
| TC-007 | autotest | T005 | `test -f .agent/adventures/ADV-011/research/pruning-catalog.md && [ $(grep -cE "^\|.*\|" .agent/adventures/ADV-011/research/pruning-catalog.md) -ge 9 ]` |
| TC-008 | autotest | T005 | `! grep -E "^\|.*\|.*\|.*\|.*\|.*\|" .agent/adventures/ADV-011/research/pruning-catalog.md \| grep -vE "(OUT-OF-SCOPE|DROP\|disposition\|---)"` |
| TC-009 | autotest | T006 | `test -f .agent/adventures/ADV-011/research/descriptor-delta.md && for f in types expression predicate code_graph code_graph_queries studio evolution agent visual; do grep -q "$f.ark" .agent/adventures/ADV-011/research/descriptor-delta.md \|\| exit 1; done` |
| TC-010 | autotest | T006 | `grep -qE "ADV-008\|host-language\|feasibility" .agent/adventures/ADV-011/research/descriptor-delta.md` |
| TC-011 | autotest | T007 | `test -f .agent/adventures/ADV-011/research/builder-delta.md && for p in "dag_acyclicity" "opaque_primitive" "numeric_interval" "reference_exists"; do grep -q "$p" .agent/adventures/ADV-011/research/builder-delta.md \|\| exit 1; done` |
| TC-012 | autotest | T007 | `for m in ark_verify studio_verify evolution_verify agent_verify visual_verify graph_verify expression_smt ark_codegen studio_codegen evolution_codegen agent_codegen visual_codegen; do grep -q "$m" .agent/adventures/ADV-011/research/builder-delta.md \|\| exit 1; done` |
| TC-013 | autotest | T008 | `test -f .agent/adventures/ADV-011/research/controller-delta.md && grep -qE "ADV-010\|telemetry" .agent/adventures/ADV-011/research/controller-delta.md` |
| TC-014 | autotest | T008 | `for s in "gateway" "skill" "scheduler" "evaluator" "evolution" "telemetry" "review"; do grep -qi "$s" .agent/adventures/ADV-011/research/controller-delta.md \|\| exit 1; done` |
| TC-015 | autotest | T009 | `test -f .agent/adventures/ADV-011/research/validation-coverage.md && ! grep -E "^\|.*TC-.*\| *\|" .agent/adventures/ADV-011/research/validation-coverage.md` |
| TC-016 | autotest | T009 + T011 | `python -m unittest .agent.adventures.ADV-011.tests.test_coverage_arithmetic` |
| TC-017 | autotest | T010 | `test -f .agent/adventures/ADV-011/research/downstream-adventure-plan.md && c=$(grep -cE "^## ADV-" .agent/adventures/ADV-011/research/downstream-adventure-plan.md); [ "$c" -ge 3 ] && [ "$c" -le 6 ]` |
| TC-018 | autotest | T010 | `grep -qE "ADV-DU.*ADV-BC.*ADV-CC.*ADV-OP" .agent/adventures/ADV-011/research/downstream-adventure-plan.md` |
| TC-019 | autotest | T011 | `bash .agent/adventures/ADV-011/tests/run-all.sh` |
| TC-020 | autotest | T011 | `python -m unittest discover -s .agent/adventures/ADV-011/tests -v` |
| TC-021 | autotest | T012 | `test -f .agent/adventures/ADV-011/research/final-validation-report.md && for k in "inventory" "mapping" "dedup" "pruning" "descriptor" "builder" "controller" "validation" "downstream"; do grep -qi "$k" .agent/adventures/ADV-011/research/final-validation-report.md \|\| exit 1; done` |

## POC Justifications

### TC-004 — bucket allowlist

Method: poc

Justification: The check "every row's bucket ∈ {descriptor, builder,
controller, out-of-scope}" is argumentative over table cells. A pure
shell/grep proof would require parsing markdown pipe-tables, which is
fragile. Instead a python unittest (`test_buckets_allowlist` in
`test_mapping_completeness.py`) parses the file and asserts the allowlist.
This is `poc` because the proof command points at a named python test
function, not a one-liner shell command.

Proof Command: `python -m unittest .agent.adventures.ADV-011.tests.test_mapping_completeness.TestMappingCompleteness.test_buckets_allowlist`

## CI Aggregator (run-all.sh)

The skeleton below is produced as `tests/run-all.sh` by T011. Do NOT create this
file in T002 — this block is the specification for T011 to copy verbatim.

```bash
#!/usr/bin/env bash
# run-all.sh — ADV-011 CI aggregator.
# Produced by T011 from the skeleton in test-strategy.md.
# Runs every TC proof command in manifest order. Exit 0 only if all pass.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"

FAIL=0
run_tc() {
  local id="$1"; shift
  echo "==> $id"
  if bash -c "$*"; then
    echo "    PASS $id"
  else
    echo "    FAIL $id"
    FAIL=1
  fi
}

# --- TC-001 ----------------------------------------------------------------
run_tc TC-001 'test -f .agent/adventures/ADV-011/research/concept-inventory.md && for a in 001 002 003 004 005 006 007 008 010; do grep -q "ADV-$a" .agent/adventures/ADV-011/research/concept-inventory.md || exit 1; done'

# --- TC-002 ----------------------------------------------------------------
run_tc TC-002 'grep -E "^\| concept \| source_adventure \| source_artefact \| description \|" .agent/adventures/ADV-011/research/concept-inventory.md'

# --- TC-TS-1 ---------------------------------------------------------------
run_tc TC-TS-1 'test -f .agent/adventures/ADV-011/tests/test-strategy.md && [ $(grep -cE "^\| TC-" .agent/adventures/ADV-011/tests/test-strategy.md) -ge 20 ]'

# --- TC-003 ----------------------------------------------------------------
run_tc TC-003 'test -f .agent/adventures/ADV-011/research/concept-mapping.md && grep -q "## Per-Bucket Rationale" .agent/adventures/ADV-011/research/concept-mapping.md'

# --- TC-004 ----------------------------------------------------------------
run_tc TC-004 'python -m unittest .agent.adventures.ADV-011.tests.test_mapping_completeness.TestMappingCompleteness.test_buckets_allowlist'

# --- TC-005 ----------------------------------------------------------------
run_tc TC-005 'test -f .agent/adventures/ADV-011/research/deduplication-matrix.md && for k in "Z3 ordinals" "Lark" "Pest" "telemetry" "PASS_OPAQUE" "dogfood" "Skill"; do grep -qi "$k" .agent/adventures/ADV-011/research/deduplication-matrix.md || exit 1; done'

# --- TC-006 ----------------------------------------------------------------
run_tc TC-006 'grep -E "^\|.*\|.*\|.*\|.*\|.*\|" .agent/adventures/ADV-011/research/deduplication-matrix.md | grep -vE "^\| *canonical_form \|" | grep -vE "^\|-" | awk -F"|" '"'"'NF>=6 && $4 !~ /^ *$/ {c++} END {exit (c>=6)?0:1}'"'"''

# --- TC-007 ----------------------------------------------------------------
run_tc TC-007 'test -f .agent/adventures/ADV-011/research/pruning-catalog.md && [ $(grep -cE "^\|.*\|" .agent/adventures/ADV-011/research/pruning-catalog.md) -ge 9 ]'

# --- TC-008 ----------------------------------------------------------------
run_tc TC-008 '! grep -E "^\|.*\|.*\|.*\|.*\|.*\|" .agent/adventures/ADV-011/research/pruning-catalog.md | grep -vE "(OUT-OF-SCOPE|DROP|disposition|---)"'

# --- TC-009 ----------------------------------------------------------------
run_tc TC-009 'test -f .agent/adventures/ADV-011/research/descriptor-delta.md && for f in types expression predicate code_graph code_graph_queries studio evolution agent visual; do grep -q "$f.ark" .agent/adventures/ADV-011/research/descriptor-delta.md || exit 1; done'

# --- TC-010 ----------------------------------------------------------------
run_tc TC-010 'grep -qE "ADV-008|host-language|feasibility" .agent/adventures/ADV-011/research/descriptor-delta.md'

# --- TC-011 ----------------------------------------------------------------
run_tc TC-011 'test -f .agent/adventures/ADV-011/research/builder-delta.md && for p in "dag_acyclicity" "opaque_primitive" "numeric_interval" "reference_exists"; do grep -q "$p" .agent/adventures/ADV-011/research/builder-delta.md || exit 1; done'

# --- TC-012 ----------------------------------------------------------------
run_tc TC-012 'for m in ark_verify studio_verify evolution_verify agent_verify visual_verify graph_verify expression_smt ark_codegen studio_codegen evolution_codegen agent_codegen visual_codegen; do grep -q "$m" .agent/adventures/ADV-011/research/builder-delta.md || exit 1; done'

# --- TC-013 ----------------------------------------------------------------
run_tc TC-013 'test -f .agent/adventures/ADV-011/research/controller-delta.md && grep -qE "ADV-010|telemetry" .agent/adventures/ADV-011/research/controller-delta.md'

# --- TC-014 ----------------------------------------------------------------
run_tc TC-014 'for s in "gateway" "skill" "scheduler" "evaluator" "evolution" "telemetry" "review"; do grep -qi "$s" .agent/adventures/ADV-011/research/controller-delta.md || exit 1; done'

# --- TC-015 ----------------------------------------------------------------
run_tc TC-015 'test -f .agent/adventures/ADV-011/research/validation-coverage.md && ! grep -E "^\|.*TC-.*\| *\|" .agent/adventures/ADV-011/research/validation-coverage.md'

# --- TC-016 ----------------------------------------------------------------
run_tc TC-016 'python -m unittest .agent.adventures.ADV-011.tests.test_coverage_arithmetic'

# --- TC-017 ----------------------------------------------------------------
run_tc TC-017 'test -f .agent/adventures/ADV-011/research/downstream-adventure-plan.md && c=$(grep -cE "^## ADV-" .agent/adventures/ADV-011/research/downstream-adventure-plan.md); [ "$c" -ge 3 ] && [ "$c" -le 6 ]'

# --- TC-018 ----------------------------------------------------------------
run_tc TC-018 'grep -qE "ADV-DU.*ADV-BC.*ADV-CC.*ADV-OP" .agent/adventures/ADV-011/research/downstream-adventure-plan.md'

# --- TC-019 ----------------------------------------------------------------
run_tc TC-019 'bash .agent/adventures/ADV-011/tests/run-all.sh'

# --- TC-020 ----------------------------------------------------------------
run_tc TC-020 'python -m unittest discover -s .agent/adventures/ADV-011/tests -v'

# --- Python unittests -------------------------------------------------------
run_tc TC-016 'python -m unittest discover -s .agent/adventures/ADV-011/tests -p "test_coverage_arithmetic.py" -v'
run_tc TC-020 'python -m unittest discover -s .agent/adventures/ADV-011/tests -v'

# --- TC-021 ----------------------------------------------------------------
run_tc TC-021 'test -f .agent/adventures/ADV-011/research/final-validation-report.md && for k in "inventory" "mapping" "dedup" "pruning" "descriptor" "builder" "controller" "validation" "downstream"; do grep -qi "$k" .agent/adventures/ADV-011/research/final-validation-report.md || exit 1; done'

exit "$FAIL"
```

## Python Unittest Files

The two skeletons below are produced as `tests/test_coverage_arithmetic.py` and
`tests/test_mapping_completeness.py` by T011. Do NOT create these files in T002 —
these blocks are the specification for T011 to copy verbatim.

### test_coverage_arithmetic.py

```python
"""Validates TC-016 — validation-coverage arithmetic.

The validation-coverage.md file produced by T009 lists every source TC from
ADV-001..008 with a verdict column whose value is one of
COVERED-BY / RETIRED-BY / DEFERRED-TO. This unittest parses the file and
asserts the count identity.
"""

import pathlib
import re
import unittest

COVERAGE = pathlib.Path(
    ".agent/adventures/ADV-011/research/validation-coverage.md"
)

VERDICTS = ("COVERED-BY", "RETIRED-BY", "DEFERRED-TO")


class TestCoverageArithmetic(unittest.TestCase):
    """TC-016: covered + retired + deferred == total_source_TCs."""

    def setUp(self):
        self.assertTrue(
            COVERAGE.exists(),
            f"Missing {COVERAGE} — T009 must produce it before T011 runs.",
        )
        self.text = COVERAGE.read_text(encoding="utf-8")

    def _count_rows_by_verdict(self):
        counts = {v: 0 for v in VERDICTS}
        total = 0
        for line in self.text.splitlines():
            if not line.startswith("| TC-"):
                continue
            total += 1
            for v in VERDICTS:
                if v in line:
                    counts[v] += 1
                    break
        return total, counts

    def test_each_tc_has_exactly_one_verdict(self):
        """Every TC row must match exactly one of the three verdicts."""
        total, counts = self._count_rows_by_verdict()
        self.assertGreater(total, 0, "No TC rows found in validation-coverage.md")
        self.assertEqual(
            sum(counts.values()),
            total,
            f"Some rows have 0 or >1 verdicts. counts={counts}, total={total}",
        )

    def test_arithmetic_holds(self):
        """TC-016: covered + retired + deferred == total."""
        total, counts = self._count_rows_by_verdict()
        self.assertEqual(
            counts["COVERED-BY"] + counts["RETIRED-BY"] + counts["DEFERRED-TO"],
            total,
        )


if __name__ == "__main__":
    unittest.main()
```

### test_mapping_completeness.py

```python
"""Validates TC-004 and cross-file completeness.

TC-004 (poc): every bucket value in concept-mapping.md is one of
  {descriptor, builder, controller, out-of-scope}.
Cross-file: every concept named in concept-inventory.md appears at least
  once in concept-mapping.md (no dropped concepts during classification).
"""

import pathlib
import re
import unittest

INVENTORY = pathlib.Path(
    ".agent/adventures/ADV-011/research/concept-inventory.md"
)
MAPPING = pathlib.Path(
    ".agent/adventures/ADV-011/research/concept-mapping.md"
)

ALLOWED_BUCKETS = {"descriptor", "builder", "controller", "out-of-scope"}


def _table_rows(text):
    """Yield cell-list for each pipe-table data row (skips header + ---)."""
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s-]+\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() in {"concept", "tc"}:
            continue  # header row
        yield cells


class TestMappingCompleteness(unittest.TestCase):
    def setUp(self):
        for f in (INVENTORY, MAPPING):
            self.assertTrue(
                f.exists(),
                f"Missing {f} — upstream task must produce it first.",
            )
        self.inventory_text = INVENTORY.read_text(encoding="utf-8")
        self.mapping_text = MAPPING.read_text(encoding="utf-8")

    def test_buckets_allowlist(self):
        """TC-004: every mapping row's bucket column is in the allowlist."""
        # Bucket column index must match schemas/entities.md#ConceptMappingRow.
        # Expected columns: concept | bucket | source_adventure | rationale
        bucket_idx = 1
        for cells in _table_rows(self.mapping_text):
            if len(cells) <= bucket_idx:
                continue
            bucket = cells[bucket_idx].lower()
            self.assertIn(
                bucket,
                ALLOWED_BUCKETS,
                f"Row has invalid bucket '{bucket}': {cells}",
            )

    def test_every_inventory_concept_is_mapped(self):
        """Cross-file: no concept from inventory is silently dropped."""
        inv_concepts = set()
        for cells in _table_rows(self.inventory_text):
            if cells:
                inv_concepts.add(cells[0].lower())
        missing = [
            c for c in inv_concepts if c and c.lower() not in self.mapping_text.lower()
        ]
        self.assertEqual(
            missing,
            [],
            f"Concepts in inventory missing from mapping: {missing[:5]} ...",
        )


if __name__ == "__main__":
    unittest.main()
```

## Invariants

- Every TC in the manifest appears exactly once in the master table above.
- Every proof command in the master table is copied verbatim from the manifest's
  `Proof Command` column (preserving all `\|` escapes, pipes, and quotes).
- `grep -cE "^\| TC-" tests/test-strategy.md` must return ≥ 22 (one per TC row).
- Every `poc` TC in the master table has a corresponding subsection in
  `## POC Justifications`. Currently: TC-004 only.
- The `run-all.sh` skeleton orders TCs in manifest numeric order with TC-TS-1
  placed between TC-002 and TC-003 (alphabetically in the manifest table).
- The `run-all.sh` skeleton uses `set -euo pipefail` with a `run_tc` wrapper
  so individual failures are collected rather than short-circuiting the full run.
- Both Python unittest skeletons assume cwd is the repo root; `run-all.sh` ensures
  this by resolving `$ROOT` from its own location before invoking python.
