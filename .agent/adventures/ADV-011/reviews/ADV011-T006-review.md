---
task_id: ADV011-T006
adventure_id: ADV-011
status: PASSED
timestamp: 2026-04-15T00:04:30Z
build_result: N/A
test_result: N/A
---

# Review: ADV011-T006

## Summary
| Field | Value |
|-------|-------|
| Task | ADV011-T006 |
| Title | Unified descriptor design (+ delta report) |
| Status | PASSED |
| Timestamp | 2026-04-15T00:04:30Z |

## Build Result
- Command: `` (no build command configured in `.agent/config.md`)
- Result: N/A
- Output: `build_command` is empty string in config.md. This task is a research-only artefact — no compiled code is produced.

## Test Result
- Command: `` (no test command configured in `.agent/config.md`)
- Result: N/A
- Output: `test_command` is empty string in config.md. Target condition proof commands (TC-009, TC-010) are run directly as shell/grep checks per the manifest.

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | File `.agent/adventures/ADV-011/research/descriptor-delta.md` exists | Yes | File confirmed present; 509 lines |
| 2 | Verdict table has exactly 9 data rows with six columns (`file`, `verdict`, `target`, `rationale`, `concept_refs`, `dedup_refs`) | Yes | Header row `| file | verdict | target | rationale | concept_refs | dedup_refs |` confirmed; 9 data rows confirmed by counting non-header/separator pipe rows in the Verdict Table section |
| 3 | Every `verdict` value is one of the five allowed values and covers all 9 basenames | Yes | Verdicts extracted: 3x MOVE-TO-PRIMITIVES, 1x KEEP-RENAMED (code_graph), 1x MERGE-INTO, 4x KEEP-RENAMED (studio/evolution/agent/visual). All within the required allowlist. TC-009 passes. |
| 4 | Every row from `concept-mapping.md` with `bucket = descriptor` is cited in section 5a | Yes | 114 descriptor rows in concept-mapping.md; section 5a contains 114 data rows (1 header + 114 data). Every canonical_name from the descriptor bucket is present. |
| 5 | Every row from `deduplication-matrix.md` with `assigned_bucket = descriptor` is cited in section 5b | Yes | Two dedup rows carry `descriptor` bucket: `dual_grammar_parity` and `skill_definitions`. Both are cited in section 5b with `dedup_row_id`, `duplicate_forms`, `canonical_form`, and `resolution` columns. |
| 6 | Section 5c contains the literal strings `ADV-008` and `host-language` so TC-010's grep passes | Yes | TC-010 grep confirms both strings present. Section 5c also includes `feasibility` (from "feasibility study"). |
| 7 | Document contains five H2 sections: Verdict Table, Target Two-Level Stdlib Layout, Grammar Authoring Contract, AST Family Spec, Citations | Yes | All five H2 headings confirmed in exact required order. |
| 8 | Grammar Authoring Contract declares Lark primary / Pest secondary with a grammar-parity autotest | Yes | Rule 1 declares "Lark-primary / Pest-secondary"; Rule 4 specifies `tests/test_grammar_parity.py` with full implementation description. |
| 9 | AST Family Spec names a single `Item` variant enum with ~40 variants grouped by domain | Yes | 39 active variants (within design's "~40" target) across 7 groups: Base (10), Primitives (2), Studio (6), Evolution (7), Agent (8), Visual (6 after 2 dropped), code-graph (0 new — folded under Struct/Enum). |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-009 | `research/descriptor-delta.md` exists with a verdict row per stdlib file | autotest | `test -f .agent/adventures/ADV-011/research/descriptor-delta.md && for f in types expression predicate code_graph code_graph_queries studio evolution agent visual; do grep -q "$f.ark" ... || exit 1; done` | PASS | All 9 basenames (`types.ark`, `expression.ark`, `predicate.ark`, `code_graph.ark`, `code_graph_queries.ark`, `studio.ark`, `evolution.ark`, `agent.ark`, `visual.ark`) found in file |
| TC-010 | Descriptor delta cites the host-language contract from ADV-008 | autotest | `grep -qE "ADV-008\|host-language\|feasibility" .agent/adventures/ADV-011/research/descriptor-delta.md` | PASS | Section 5c contains "ADV-008", "host-language", and "feasibility" — grep exits 0 |

## Issues Found

No issues found.

## Recommendations

The implementation is thorough and well-structured. A few optional observations for quality:

1. **Concept citation count reconciliation** — Section 5a contains 114 data rows matching the 114 descriptor-bucket rows in `concept-mapping.md`. The count match is tight and correct; no rows are omitted or duplicated.

2. **`Feedback` variant in visual group** — The AST spec includes `Feedback` as a visual domain variant (from `Item::Feedback`) but the concept-mapping does not list `Item::Feedback` explicitly (only `Item::RenderConfig`, `Item::Diagram`, etc. through `Item::VisualSearch`). The verdict table row 9 rationale mentions `Item::Feedback` — this is consistent with the visual.ark content and the design, but the concept-mapping's absence of `Item::Feedback` as a named row is a pre-existing upstream gap from T003, not a T006 deficiency.

3. **`code_graph_queries.ark` dedup_refs cell** — The cell cites `dual_grammar_parity` as the dedup row reference. Technically the dedup-matrix row does not specifically name `code_graph_queries.ark` — it covers all grammar parity across all adventures. The citation is defensible given that code_graph_queries grammar rules are subsumed by the parity contract, but the linkage is indirect. No action required; it's the best available reference.

4. **`enum_SearchMode` retained note** — Section 5a correctly notes that `enum_SearchMode` is retained in `domain/visual.ark` for VisualReview filter semantics even though `struct_SearchQuery` is dropped. This is a careful judgment call consistent with the pruning catalog.

Overall, the delta report is a high-quality planning artefact: the decision tree is applied correctly and consistently, all citations are complete, both TC-009 and TC-010 pass cleanly, and the Grammar Authoring Contract and AST Family Spec sections are detailed enough to guide a downstream implementation adventure without ambiguity.
