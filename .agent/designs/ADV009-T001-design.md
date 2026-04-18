# ADV009-T001 — Design test strategy for ADV-009 console v2

## Approach

Produce a single deliverable: `.agent/adventures/ADV-009/tests/test-strategy.md`.
This document is the contract that later implementation tasks (T005..T012,
T015..T021) must satisfy. It pins:

1. The framework (stdlib `unittest`) and the three test files.
2. A TC-to-test-function mapping table that covers **every** TC whose
   `proof_method` is `autotest` in the adventure manifest.
3. The full `python -m unittest discover` command.
4. A `data-testid` appendix enumerating every hook id referenced by the
   adventure-level designs.

The authoring pass does **not** create any `.py` files or modify `server.py`
or `index.html`. It is purely documentation; T003/T004/T005+ implement against
it.

## Target Files

- `.agent/adventures/ADV-009/tests/test-strategy.md` (new) — the contract.

No other files are touched. The three referenced `test_*.py` files are
declared here but are written by later tasks (T003, T004, T010, T012,
T016/T018). The design-test-strategy.md document under
`adventures/ADV-009/designs/` is the source and must not be modified.

## TC coverage (source: manifest.md autotest rows)

Every `autotest` TC below must appear in the strategy's mapping table. Drawn
from `.agent/adventures/ADV-009/manifest.md` lines 116-176:

**test_server.py** (Tier 1 — backend, stdlib HTTP in-process):
- TC-025 → `TestKnowledgePayload`
- TC-026 → `TestSummary`
- TC-027 → `TestDocumentsEndpoint.test_types`
- TC-028 → `TestDocumentsEndpoint.test_waves`
- TC-029 → `TestNextAction.test_review`
- TC-030 → `TestStdlibOnly`
- TC-034 → `TestStrategyDoc.test_tc_mapping`
- TC-035 → `TestStrategyDoc.test_framework`

**test_ui_layout.py** (Tier 2 — static HTML structure via `html.parser`):
- TC-001 → `TestAuditPresence`
- TC-002 → `TestAuditVerdicts`
- TC-003 → `TestAuditCoverage`
- TC-004 → `TestTabBar.test_four_tabs`
- TC-005 → `TestTabBar.test_no_legacy_tabs`
- TC-006 → `TestHeader`
- TC-008 → `TestTasksTab.test_buckets`
- TC-009 → `TestTasksTab.test_card_shape`
- TC-013 → `TestDocumentsTab.test_chips`
- TC-018 → `TestOverview.test_progress_bar`
- TC-022 → `TestDecisions.test_three_cards`
- TC-031 → `TestVisualSystem.test_classes`
- TC-032 → `TestVisualSystem.test_no_external`
- TC-033 → `TestVisualSystem.test_card_usage`

**test_ui_smoke.py** (Tier 2 interaction-adjacent / Tier 3 optional
Playwright; all TCs also have a static fallback assertion per
design-test-strategy.md §Approach):
- TC-010 → `TestTaskDetail.test_structured`
- TC-011 → `TestTaskDetail.test_disclosure`
- TC-014 → `TestDocuments.test_chip_filter`
- TC-015 → `TestDocuments.test_design_header`
- TC-016 → `TestDocuments.test_plan_waves`
- TC-017 → `TestDocuments.test_review_strip`
- TC-020 → `TestOverview.test_next_action`
- TC-024 → `TestDecisions.test_state_post`

**Additional autotest TCs from the addendum** (graph/Ark work; these live
in extra `test_*.py` files declared in-spec but also covered by the same
discover command):
- TC-036 → implicit: `python -m unittest discover -s
  .agent/adventures/ADV-009/tests -p "test_*.py"` exits 0.
- TC-039 → poc-adjacent autotest via `ark/ark.py parse`
- TC-040, TC-041 → `test_ir.py::TestSpecShapes`
- TC-042, TC-043, TC-044 → `test_ir.py::TestRoundTrip`
- TC-046, TC-052, TC-053, TC-054, TC-058, TC-059, TC-060, TC-061 →
  `test_graph_endpoint.py`
- TC-047, TC-048, TC-049, TC-050, TC-051, TC-055, TC-056 →
  `test_pipeline_tab.py`

The strategy doc notes these extra files (`test_ir.py`,
`test_graph_endpoint.py`, `test_pipeline_tab.py`) as additional test modules
that participate in the same discover run. The three files required by the
acceptance criterion ("test_server.py, test_ui_smoke.py, test_ui_layout.py")
remain the core declared set; the others are declared as addendum extensions.

## Implementation Steps

1. Read `.agent/adventures/ADV-009/manifest.md` TC table (already catalogued
   above) and `.agent/adventures/ADV-009/designs/design-test-strategy.md`.
2. Create `.agent/adventures/ADV-009/tests/` directory (if missing) and
   author `test-strategy.md` with these sections:
   - `# Test Strategy — ADV-009 Console v2` header.
   - `## Framework` — state stdlib `unittest`, Python 3, zero third-party.
   - `## Files` — declare `test_server.py`, `test_ui_smoke.py`,
     `test_ui_layout.py` (core) plus addendum-extension files
     (`test_ir.py`, `test_graph_endpoint.py`, `test_pipeline_tab.py`).
   - `## Run Command` — block-quote
     `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"`.
   - `## TC → Test Function Mapping` — one table row per autotest TC using
     the assignments above. Columns: `TC | Test Class.Method | File`.
   - `## Tiering Notes` — copy Tier 1/2/3 approach summary from
     design-test-strategy.md (attribution line, not a wholesale copy).
   - `## Appendix A — data-testid Contract` — enumerate every hook id from
     design-test-strategy.md §Data-testid hooks: `tab-overview`, `tab-tasks`,
     `tab-documents`, `tab-decisions`, `tc-progress-bar`, `tc-progress-label`,
     `next-action-card`, `next-action-button`, `chip-filter-{all,designs,
     plans,research,reviews}`, `task-card-{id}`, `task-card-status-{id}`,
     `doc-list-item-{filename}`, `decisions-card-{state-transitions,
     permissions,knowledge}`, `show-details-{context}`. Plus any ids
     referenced by addendum designs (`pipeline-tab`, `graph-canvas`,
     `node-{id}`, `edge-{from}-{to}` if specified by
     design-pipeline-graph-view.md / design-graph-edit-affordances.md —
     check those designs during authoring and include every id found).
3. Self-check: every TC marked `autotest` in manifest.md appears in the
   mapping table. Count should match a grep of
   `proof_method.*autotest`-equivalent rows (expected: 33 core + addendum).
4. Self-check: the three core test files are named exactly
   `test_server.py`, `test_ui_smoke.py`, `test_ui_layout.py`.
5. Self-check: the `data-testid` appendix lists every hook id named in
   design-test-strategy.md §Data-testid hooks plus any addendum additions.

## Testing Strategy

This task produces a documentation deliverable. Verification happens later:
- TC-034 (`TestStrategyDoc.test_tc_mapping`) will parse the strategy doc
  and assert every autotest TC is covered.
- TC-035 (`TestStrategyDoc.test_framework`) will assert the framework line
  says "unittest" and the three core test files are declared.

The planner does not execute tests. The coder (ADV009-T001 implementer)
only writes the markdown file.

## Risks

- **Drift between manifest and strategy doc**: if new autotest TCs are
  added post-authoring, the mapping table becomes stale. Mitigation: the
  acceptance criterion scopes "every autotest TC" to the manifest snapshot
  at authoring time; T003's TC-034 test is the enforcement point.
- **Addendum test files not in "declared three"**: the acceptance criterion
  names three files, but the addendum introduces `test_ir.py`,
  `test_graph_endpoint.py`, `test_pipeline_tab.py`. Mitigation: list the
  three as "core" and the others as "addendum extensions" — both get
  picked up by `discover -p "test_*.py"`, satisfying TC-036.
- **data-testid hooks in addendum designs not yet enumerated**: during
  authoring, also scan design-pipeline-graph-view.md and
  design-graph-edit-affordances.md for any `data-testid` references and
  include them in Appendix A.
