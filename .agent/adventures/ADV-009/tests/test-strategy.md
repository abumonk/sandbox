# Test Strategy — ADV-009 Console v2

## Framework

All tests use Python's built-in **`unittest`** module (Python 3, stdlib
only). Zero third-party imports are required to run the test suite.
Playwright is optional: Tier-3 test files guard their import with a
try/except and skip cleanly when Playwright is not installed.

## Files

### Core files (required by acceptance criteria)

| File | Tier | Description |
|------|------|-------------|
| `test_server.py` | Tier 1 — backend in-process | Tests the `server.py` HTTP handlers directly via `ThreadingHTTPServer` on a random port or by calling handler helpers. Covers all backend TCs (TC-025..TC-030, TC-034, TC-035). |
| `test_ui_layout.py` | Tier 2 — static HTML structure | Fetches `index.html` and parses it with stdlib `html.parser`. Asserts tabs, CSS classes, `data-testid` attributes, and chip bar presence without running JS. Covers structural TCs. |
| `test_ui_smoke.py` | Tier 2/3 — interaction | Exercises live client-side behaviour. Uses Playwright if importable; otherwise asserts against static markup as a Tier-2 fallback so autotest coverage is preserved. |

### Addendum extension files (participate in discover)

| File | Tier | Description |
|------|------|-------------|
| `test_ir.py` | Tier 1 — IR / Ark spec | Tests the Ark spec parse and IR extractor for `adventure_pipeline/`. Covers TC-039..TC-045. |
| `test_graph_endpoint.py` | Tier 1 — graph backend | Tests the `/api/adventures/{id}/graph` and `depends_on` POST endpoints. Covers TC-046, TC-052..TC-054, TC-058..TC-061. |
| `test_pipeline_tab.py` | Tier 2/3 — pipeline UI | Tests the Pipeline tab markup, cytoscape CDN tag, colour mapping, drag affordances, and rollback. Covers TC-047..TC-051, TC-055, TC-056. |

## Run Command

Execute from the repository root:

```
python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"
```

Tier-3 (Playwright) tests reside in `test_ui_smoke.py` and
`test_pipeline_tab.py` alongside Tier-2 tests. They skip themselves
automatically when `from playwright.sync_api import sync_playwright` fails,
so this single command covers all tiers.

## TC → Test Function Mapping

| TC | Test Class.Method | File |
|----|-------------------|------|
| TC-001 | `TestAuditPresence` | `test_ui_layout.py` |
| TC-002 | `TestAuditVerdicts` | `test_ui_layout.py` |
| TC-003 | `TestAuditCoverage` | `test_ui_layout.py` |
| TC-004 | `TestTabBar.test_four_tabs` | `test_ui_layout.py` |
| TC-005 | `TestTabBar.test_no_legacy_tabs` | `test_ui_layout.py` |
| TC-006 | `TestHeader` | `test_ui_layout.py` |
| TC-008 | `TestTasksTab.test_buckets` | `test_ui_layout.py` |
| TC-009 | `TestTasksTab.test_card_shape` | `test_ui_layout.py` |
| TC-010 | `TestTaskDetail.test_structured` | `test_ui_smoke.py` |
| TC-011 | `TestTaskDetail.test_disclosure` | `test_ui_smoke.py` |
| TC-013 | `TestDocumentsTab.test_chips` | `test_ui_layout.py` |
| TC-014 | `TestDocuments.test_chip_filter` | `test_ui_smoke.py` |
| TC-015 | `TestDocuments.test_design_header` | `test_ui_smoke.py` |
| TC-016 | `TestDocuments.test_plan_waves` | `test_ui_smoke.py` |
| TC-017 | `TestDocuments.test_review_strip` | `test_ui_smoke.py` |
| TC-018 | `TestOverview.test_progress_bar` | `test_ui_layout.py` |
| TC-020 | `TestOverview.test_next_action` | `test_ui_smoke.py` |
| TC-022 | `TestDecisions.test_three_cards` | `test_ui_layout.py` |
| TC-024 | `TestDecisions.test_state_post` | `test_ui_smoke.py` |
| TC-025 | `TestKnowledgePayload` | `test_server.py` |
| TC-026 | `TestSummary` | `test_server.py` |
| TC-027 | `TestDocumentsEndpoint.test_types` | `test_server.py` |
| TC-028 | `TestDocumentsEndpoint.test_waves` | `test_server.py` |
| TC-029 | `TestNextAction.test_review` | `test_server.py` |
| TC-030 | `TestStdlibOnly` | `test_server.py` |
| TC-031 | `TestVisualSystem.test_classes` | `test_ui_layout.py` |
| TC-032 | `TestVisualSystem.test_no_external` | `test_ui_layout.py` |
| TC-033 | `TestVisualSystem.test_card_usage` | `test_ui_layout.py` |
| TC-034 | `TestStrategyDoc.test_tc_mapping` | `test_server.py` |
| TC-035 | `TestStrategyDoc.test_framework` | `test_server.py` |
| TC-036 | _(full discover run exits 0 — integration gate, not a named function)_ | N/A |
| TC-039 | `TestSpecShapes.test_adventure_ark` | `test_ir.py` |
| TC-040 | `TestSpecShapes.test_processes` | `test_ir.py` |
| TC-041 | `TestSpecShapes.test_runtime_entities` | `test_ir.py` |
| TC-042 | `TestRoundTrip.test_adv007` | `test_ir.py` |
| TC-043 | `TestRoundTrip.test_adv008` | `test_ir.py` |
| TC-044 | `TestRoundTrip.test_task_ids_match_manifest` | `test_ir.py` |
| TC-046 | `TestGraphShape` | `test_graph_endpoint.py` |
| TC-047 | `TestCdn` | `test_pipeline_tab.py` |
| TC-048 | `TestTabOrder` | `test_pipeline_tab.py` |
| TC-049 | `TestStatusColours` | `test_pipeline_tab.py` |
| TC-050 | `TestNoWebsocket` | `test_pipeline_tab.py` |
| TC-051 | `TestTooltipsFromBackend` | `test_pipeline_tab.py` |
| TC-052 | `TestDependsOn.test_happy` | `test_graph_endpoint.py` |
| TC-053 | `TestDependsOn.test_self_cycle` | `test_graph_endpoint.py` |
| TC-054 | `TestDependsOn.test_cycle` | `test_graph_endpoint.py` |
| TC-055 | `TestDragOneShot` | `test_pipeline_tab.py` |
| TC-056 | `TestRollback` | `test_pipeline_tab.py` |
| TC-058 | `TestImport` | `test_graph_endpoint.py` |
| TC-059 | `TestGraphShape.test_schema` | `test_graph_endpoint.py` |
| TC-060 | `TestStdlibOnly` | `test_graph_endpoint.py` |
| TC-061 | `TestCycleFree` | `test_graph_endpoint.py` |

**Notes:**

- TC-036 is the meta-TC asserting the full `discover` command exits 0; it
  is not a named test function but is satisfied by the entire suite passing.
- TC-007, TC-012, TC-019, TC-021, TC-023, TC-037, TC-038, TC-045, TC-057
  have `proof_method: poc` or `proof_method: manual` and are excluded from
  this mapping (no autotest function required).

## Tiering Notes

Following `design-test-strategy.md §Approach`:

**Tier 1 — Backend in-process** (`test_server.py`, `test_ir.py`,
`test_graph_endpoint.py`): Start `ThreadingHTTPServer` on a random port
inside `setUpClass`; call endpoints over localhost HTTP. Fixture: a
synthetic `ADV-TEST/` tree placed in a temp directory. Covers TC-025..TC-030,
TC-034..TC-035, TC-039..TC-044, TC-046, TC-052..TC-054, TC-058..TC-061.

**Tier 2 — Static HTML structure** (`test_ui_layout.py`, parts of
`test_pipeline_tab.py`): Fetch the static `index.html` from disk (no server
required) and parse with stdlib `html.parser`. Assert presence of specific
tags, CSS class names, and `data-testid` attributes. Covers structural TCs:
TC-001..TC-006, TC-008..TC-009, TC-013, TC-018, TC-022, TC-031..TC-033,
TC-047..TC-050.

**Tier 3 — Headless browser smoke** (portions of `test_ui_smoke.py` and
`test_pipeline_tab.py`): Uses Playwright `sync_api`. Guarded with:

```python
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
```

Every Tier-3 test class is decorated with
`@unittest.skipUnless(PLAYWRIGHT_AVAILABLE, "playwright not installed")`.

When Playwright is unavailable, TC-008, TC-011, TC-013, TC-014, TC-020,
TC-024 remain covered: each has a complementary Tier-2 static-HTML
assertion in `test_ui_layout.py` that verifies the same contract against
the markup, so autotest coverage is never lost — only weakened from
live-interaction to static-structure proof.

## Appendix A — data-testid Contract

The following `data-testid` attribute values are the contract between the
test suite and the UI implementation. Every attribute listed here must be
present in the corresponding element in `index.html`. Implementations that
rename or omit these ids will break the Tier-2/3 test suite.

### Core console hooks (from `design-test-strategy.md §Data-testid hooks`)

| Hook ID | Element | Used by TC(s) |
|---------|---------|---------------|
| `tab-overview` | Overview tab button | TC-004, TC-005 |
| `tab-tasks` | Tasks tab button | TC-004, TC-005 |
| `tab-documents` | Documents tab button | TC-004, TC-005 |
| `tab-decisions` | Decisions tab button | TC-004, TC-005 |
| `tc-progress-bar` | TC completion `<progress>` or `<div>` element | TC-006, TC-018 |
| `tc-progress-label` | Text label beside the progress bar | TC-006, TC-018 |
| `next-action-card` | Container div for the next-action card | TC-020 |
| `next-action-button` | Primary action button inside the next-action card | TC-020 |
| `chip-filter-all` | "All" chip button in Documents tab | TC-013, TC-014 |
| `chip-filter-designs` | "Designs" chip button | TC-013, TC-014 |
| `chip-filter-plans` | "Plans" chip button | TC-013, TC-014 |
| `chip-filter-research` | "Research" chip button | TC-013, TC-014 |
| `chip-filter-reviews` | "Reviews" chip button | TC-013, TC-014 |
| `task-card-{id}` | Task card root element (e.g. `task-card-ADV009-T001`) | TC-008, TC-009 |
| `task-card-status-{id}` | Status pill inside a task card | TC-009 |
| `doc-list-item-{filename}` | Document list row (e.g. `doc-list-item-design-test-strategy.md`) | TC-013 |
| `decisions-card-state-transitions` | State-transitions decisions card | TC-022, TC-024 |
| `decisions-card-permissions` | Permissions decisions card | TC-022 |
| `decisions-card-knowledge` | Knowledge suggestions decisions card | TC-022 |
| `show-details-{context}` | Disclosure toggle (e.g. `show-details-task`, `show-details-overview`) | TC-011 |

### Pipeline tab hooks (from `design-pipeline-graph-view.md`)

| Hook ID | Element | Used by TC(s) |
|---------|---------|---------------|
| `tab-pipeline` | Pipeline tab button | TC-048 |
| `pipeline-canvas` | Cytoscape graph mount point (`<div id="pipeline-canvas">`) | TC-047, TC-049 |

### Graph edit affordance hooks (from `design-graph-edit-affordances.md`)

| Hook ID | Element | Used by TC(s) |
|---------|---------|---------------|
| `context-menu` | Right-click context menu container | TC-055, TC-056 |
| `toast` | Toast notification element for rollback feedback | TC-056 |
