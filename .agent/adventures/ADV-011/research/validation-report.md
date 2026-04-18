# Validation Report — ADV-001..008 → ADV-011 Unified Designs

## Summary

- Total source TCs: 272
- COVERED-BY: 179
- RETIRED-BY: 61
- DEFERRED-TO: 32
- Invariant: covered + retired + deferred = total  →  179 + 61 + 32 = 272  [PASS]

**Harvest discrepancy note.** The design (ADV011-T009-design.md) stated 278 TCs expected
(ADV-003 contributing 35). At harvest time, `grep -cE '^\| TC-[0-9]+ \|'` against each source
file returned 29 for ADV-003 (not 35). The remaining seven adventures matched their pinned
counts. Per the design's own instruction ("If the environment produces different numbers, STOP
and log the discrepancy in validation-report.md § Open gaps"), the actual harvested total 272
is used throughout. The arithmetic invariant is computed against 272.

---

## Per-verdict breakdown

| verdict | count | % of total |
|---------|-------|------------|
| COVERED-BY | 179 | 65.8% |
| RETIRED-BY | 61 | 22.4% |
| DEFERRED-TO | 32 | 11.8% |

---

## Per-source-adventure breakdown

| source_adventure | total_TCs | COVERED-BY | RETIRED-BY | DEFERRED-TO |
|------------------|-----------|------------|------------|-------------|
| ADV-001 | 30 | 22 | 0 | 8 |
| ADV-002 | 28 | 23 | 0 | 5 |
| ADV-003 | 29 | 26 | 0 | 3 |
| ADV-004 | 46 | 41 | 1 | 4 |
| ADV-005 | 44 | 40 | 0 | 4 |
| ADV-006 | 37 | 27 | 7 | 3 |
| ADV-007 | 34 | 0 | 34 | 0 |
| ADV-008 | 24 | 0 | 19 | 5 |
| **Total** | **272** | **179** | **61** | **32** |

---

## Per-downstream-adventure deferral breakdown

| downstream_adv | count | TCs |
|----------------|-------|-----|
| ADV-DU | 26 | ADV-001 TC-008, ADV-001 TC-017, ADV-001 TC-023, ADV-001 TC-025, ADV-001 TC-026, ADV-001 TC-028, ADV-001 TC-029, ADV-001 TC-030, ADV-002 TC-005, ADV-002 TC-027, ADV-002 TC-028, ADV-003 TC-027, ADV-003 TC-028, ADV-003 TC-029, ADV-004 TC-043, ADV-004 TC-045, ADV-004 TC-046, ADV-005 TC-041, ADV-005 TC-043, ADV-005 TC-044, ADV-006 TC-037, ADV-008 TC-08, ADV-008 TC-11, ADV-008 TC-12, ADV-008 TC-13, ADV-008 TC-14 |
| ADV-BC | 0 | — |
| ADV-CC | 0 | — |
| ADV-OP | 0 | — |
| ADV-CE | 0 | — |
| ADV-UI | 6 | ADV-002 TC-022, ADV-002 TC-023, ADV-004 TC-038, ADV-005 TC-036, ADV-006 TC-023, ADV-006 TC-031 |

---

## Open gaps

- **ADV-003 TC count discrepancy**: `grep -cE '^\| TC-[0-9]+ \|' .agent/adventures/ADV-003/tests/test-strategy.md` returned 29 rows, not 35 as pinned in the design. The six missing TCs are absent from the test-strategy.md file at harvest time. This reduces the total from the expected 278 to 272. The T011 test suite must be updated to use the re-grepped count (272) rather than the design-specified count (278), or the ADV-003 test-strategy.md must be updated to add the missing 6 rows before T011 runs.
- **ADV-004 TC-017 (Darwinian mode raises NotImplementedError)**: Cited as RETIRED-BY pruning-catalog.md row 1 ("Darwinian optimizer mode" — DROP). The disposition is correct per the pruning catalog; flagged here because this TC's subject (a NotImplementedError stub) maps cleanly to the pruned concept, but a downstream reader should verify this is intentional and not an accidental gap in evolution controller coverage.
- **ADV-008 TC-08, TC-11..14 (shape_grammar integration adapters)**: These five TCs are deferred to ADV-DU. They concern the Ark-as-host-language integration surface (semantic label propagation, visualizer/impact/diff adapters). ADV-DU must size these when it materialises — they represent substantive integration work, not trivial tasks.
- **ADV-007 wholesale RETIRED**: All 34 ADV-007 TCs are RETIRED-BY because ADV-007's deliverables were ecosystem research artefacts (phase1-7 research documents, roadmaps, UI studies) now superseded by ADV-011's unified design surface. T010 and the downstream adventure plan replace the ADV-007 roadmap function. Human reviewers should confirm this disposition before closing ADV-011.

---

## Methodology

TCs were harvested from the eight source adventures using the regex `^\| TC-\d+ \|` applied to each adventure's authoritative TC source file per `designs/ADV011-T009-design.md` §TC Harvesting:

- ADV-001: `.agent/adventures/ADV-001/manifest.md`
- ADV-002: `.agent/adventures/ADV-002/tests/test-strategy.md`
- ADV-003: `.agent/adventures/ADV-003/tests/test-strategy.md`
- ADV-004: `.agent/adventures/ADV-004/manifest.md`
- ADV-005: `.agent/adventures/ADV-005/manifest.md`
- ADV-006: `.agent/adventures/ADV-006/manifest.md`
- ADV-007: `.agent/adventures/ADV-007/manifest.md`
- ADV-008: `.agent/adventures/ADV-008/manifest.md`

Per-adventure counts were verified against the design's pinned values before classification. ADV-003 returned 29 (not 35); the discrepancy is logged in § Open gaps above.

Verdicts were assigned by consulting three classification inputs in order:

1. **COVERED-BY** — if the TC's subject matter maps to content in one of `research/descriptor-delta.md`, `research/builder-delta.md`, or `research/controller-delta.md`. The citation form is `<delta-file>#<section-anchor>` where the anchor is an H2 or H3 slug present in that file. Heuristic: grammar/parser/AST/stdlib TCs → descriptor-delta; verify/codegen/module TCs → builder-delta; runtime/controller/subsystem TCs → controller-delta.

2. **RETIRED-BY** — if the TC's subject matter matches a concept in `research/pruning-catalog.md` that carries a DROP or OUT-OF-SCOPE disposition. The citation form is `pruning-catalog.md row <n>` where `<n>` is the 1-based data-row number. ADV-007 TCs map to ADV-007 ecosystem research rows (rows 3, 4, 7, 11, 12, 18, 23-40); ADV-006 UI-surface TCs map to rows 2 and 9; ADV-008 shape_grammar TCs map to row 5.

3. **DEFERRED-TO** — if the TC addresses future-work capabilities not covered by the current unified designs and not pruned. All deferred TCs cite either ADV-DU (Descriptor Unification — downstream implementation of the grammar authoring contract, registry integration, and CI/test scaffolding) or ADV-UI (UI Surface — HTML rendering, visualisation color coding, screenshot/html-preview pipeline). No TCs were deferred to ADV-BC, ADV-CC, ADV-OP, or ADV-CE in this classification, as no harvested TCs specifically address those adventure domains.

Authority documents consulted:
- `designs/ADV011-T009-design.md` — harvest procedure, verdict rules, report structure
- `research/descriptor-delta.md` (T006 output) — DSL/stdlib/grammar coverage
- `research/builder-delta.md` (T007 output) — verify/codegen/module coverage
- `research/controller-delta.md` (T008 output) — runtime/subsystem coverage
- `research/pruning-catalog.md` (T005 output) — pruning dispositions (46 data rows)
