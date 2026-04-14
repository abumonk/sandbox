---
task_id: ADV008-T15
adventure_id: ADV-008
status: PASSED
timestamp: 2026-04-14T15:30:15Z
build_result: N/A
test_result: N/A
---

# Review: ADV008-T15

## Summary
| Field | Value |
|-------|-------|
| Task | ADV008-T15 |
| Title | Four example grammars |
| Status | PASSED |
| Timestamp | 2026-04-14T15:30:15Z |

## Build Result
- Command: N/A (no build command configured in `.agent/config.md`)
- Result: N/A

## Test Result
- Command: N/A (no test command configured in `.agent/config.md`)
- Result: N/A

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | All 4 files exist | Yes | `l_system.ark`, `cga_tower.ark`, `semantic_facade.ark`, `code_graph_viz.ark` all present in `shape_grammar/examples/` |
| 2 | `for f in shape_grammar/examples/*.ark; do python ark/ark.py verify "$f"; done` all exit 0 | Yes | Verified individually: l_system 1/1, cga_tower 4/4, semantic_facade 1/1, code_graph_viz 5/5 invariants — all exit 0 |
| 3 | `python -m shape_grammar.tools.ir <each>` succeeds on each | Yes | IR tool exits 0 on all four files; returns populated JSON with entities, fields, invariants |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-17 | Four example grammars exist and parse + verify under vanilla Ark | poc | `for f in shape_grammar/examples/l_system.ark shape_grammar/examples/cga_tower.ark shape_grammar/examples/semantic_facade.ark shape_grammar/examples/code_graph_viz.ark; do python ark/ark.py verify "$f" \|\| exit 1; done` | PASS | All four verified successfully (1/1, 4/4, 1/1, 5/5 invariants); exit 0 |

## Issues Found
No issues found.

## Recommendations
Implementation is clean and consistent. A few optional quality observations:

- The `semantic_labels` and `rules` fields in the IR output are empty lists for all four files. The grammars declare grammar *structure* (classes for rules, operations, terminals) but no concrete rule or label *instances*. This is by design — the evaluator instantiates rules at runtime — but downstream consumers (e.g. TC-20 example-driven tests) should be aware the IR does not populate those lists from these island files.
- `code_graph_viz.ark` is the richest file (14 classes, 5/5 invariants). It accurately reflects a prototypical grammar for node/edge visualization and correctly notes it does not ingest live code-graph data, which is an appropriate scope boundary.
- The four files share identical scaffolding (`Shape`, `Rule`, `Operation` abstractions) but each customises the operation set to match its grammar's needs. This is good pattern adherence — no copy-paste bloat, and each file is self-contained.
- `l_system.ark` correctly bounds `max_depth` to [1..8], tighter than the other grammars, which appropriately reflects the simplicity of a single self-recursing rule.
