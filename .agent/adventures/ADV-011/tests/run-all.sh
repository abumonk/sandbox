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
run_tc TC-004 'python -m unittest discover -s .agent/adventures/ADV-011/tests -p "test_mapping_completeness.py" -v'

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
run_tc TC-016 'python -m unittest discover -s .agent/adventures/ADV-011/tests -p "test_coverage_arithmetic.py" -v'

# --- TC-017 ----------------------------------------------------------------
run_tc TC-017 'test -f .agent/adventures/ADV-011/research/downstream-adventure-plan.md && c=$(grep -cE "^## ADV-" .agent/adventures/ADV-011/research/downstream-adventure-plan.md); [ "$c" -ge 3 ] && [ "$c" -le 6 ]'

# --- TC-018 ----------------------------------------------------------------
run_tc TC-018 'grep -qE "ADV-DU.*ADV-BC.*ADV-CC.*ADV-OP" .agent/adventures/ADV-011/research/downstream-adventure-plan.md'

# --- TC-019 ----------------------------------------------------------------
run_tc TC-019 'test -x .agent/adventures/ADV-011/tests/run-all.sh || test -f .agent/adventures/ADV-011/tests/run-all.sh'

# --- TC-020 ----------------------------------------------------------------
run_tc TC-020 'python -m unittest discover -s .agent/adventures/ADV-011/tests -v'

# --- TC-021 ----------------------------------------------------------------
run_tc TC-021 'test -f .agent/adventures/ADV-011/research/final-validation-report.md && for k in "inventory" "mapping" "dedup" "pruning" "descriptor" "builder" "controller" "validation" "downstream"; do grep -qi "$k" .agent/adventures/ADV-011/research/final-validation-report.md || exit 1; done'

exit "$FAIL"
