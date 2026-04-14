# Plan: Pipeline Tab — Graph View + Edit Affordances (Wave E — addendum)

New wave inserted **before Wave C** (testing). Depends on Wave D (Ark
spec + IR extractor) and is adjacent to Wave B (frontend rewrite) but
touches `index.html` in a disjoint section. The final sequencing becomes:

- Wave A (T001–T004) — unchanged
- Wave B (T005–T011) — unchanged
- Wave D (T015–T017) — Ark spec + IR (new)
- Wave E (T018–T020) — Pipeline tab + endpoints (new)
- Wave C (T012–T014) + T021 — testing + polish (T021 is a new graph-tests task)

## Designs Covered

- design-pipeline-graph-view
- design-graph-edit-affordances
- design-graph-backend-endpoints

## Tasks

### Add `/graph` + `depends_on` backend endpoints
- **ID**: ADV009-T018
- **Description**: Extend `server.py` with:
  1. `GET /api/adventures/{id}/graph` — imports
     `adventure_pipeline.tools.ir.extract_ir`, serves the node/edge/
     explanations payload specified in design-pipeline-graph-view.
  2. `POST /api/adventures/{id}/tasks/{task_id}/depends_on` — detailed in
     design-graph-edit-affordances; uses a shared `_cycle_free` helper.
  Stdlib only. No changes to the T003/T004 endpoints. Follow existing
  `server.py` patterns for route dispatch, frontmatter rewrite, and error
  responses.
- **Files**: `.agent/adventure-console/server.py`
- **Acceptance Criteria**:
  - `curl localhost:{port}/api/adventures/ADV-007/graph` returns 200 with
    a payload containing `nodes`, `edges`, `explanations`.
  - Valid `depends_on` POST returns 200 with the merged list; file on
    disk updated correctly.
  - Self-cycle POST returns 400; cycle-creating POST returns 400.
  - `python -m unittest` run stays green.
  - No third-party imports added.
- **Target Conditions**: TC-046, TC-052, TC-053, TC-054, TC-058, TC-059, TC-060, TC-061
- **Depends On**: [ADV009-T016, ADV009-T003, ADV009-T004]
- **Evaluation**:
  - Access requirements: Read, Edit, Bash (python -m unittest, curl via python)
  - Skill set: Python stdlib HTTP, regex, graph algorithms
  - Estimated duration: 28 min
  - Estimated tokens: 85000

### Implement Pipeline tab rendering (cytoscape + polling)
- **ID**: ADV009-T019
- **Description**: Add the Pipeline tab to the v2 console: insert the
  fifth `<button>` in the tab bar, add a dispatcher case, author
  `renderPipeline(adv)`, load cytoscape (and dagre-layout if adopted) via
  CDN `<script>` tags, mount the graph on `<div id="pipeline-canvas">`,
  poll `/api/adventures/{id}/graph` every 5 s (default; overridable via
  `?poll=N`), apply status-colour mapping per design, render tooltips
  from the backend `explanations` map, and a small fixed legend.
- **Files**: `.agent/adventure-console/index.html`
- **Acceptance Criteria**:
  - Pipeline appears as the 4th top-level tab (between Documents and
    Decisions) — total of 5 tabs.
  - cytoscape loaded from a CDN URL; no local copy, no bundler.
  - Graph renders adventure, phase, task, document, tc, decision nodes
    with the correct status colours for ADV-007 sample data.
  - Polling uses `setTimeout`; no WebSocket / EventSource anywhere.
  - Tooltips come from `explanations[id]` (no hardcoded strings).
- **Target Conditions**: TC-047, TC-048, TC-049, TC-050, TC-051
- **Depends On**: [ADV009-T006, ADV009-T018]
- **Evaluation**:
  - Access requirements: Read, Edit
  - Skill set: Vanilla JS, cytoscape.js API, DOM
  - Estimated duration: 30 min
  - Estimated tokens: 95000

### Add graph edit affordances (drag, click, right-click menu)
- **ID**: ADV009-T020
- **Description**: Wire interactive editing onto the Pipeline tab:
  click state-transition edges → POST state; drag task→task → POST
  `depends_on` with optimistic edge placement + rollback on 4xx;
  right-click → DOM context menu with the item set from
  design-graph-edit-affordances (open doc, approve design, approve
  permissions, apply knowledge suggestion, open task detail). Toasts for
  errors. 500 ms double-submit guard.
- **Files**: `.agent/adventure-console/index.html`
- **Acceptance Criteria**:
  - Drag gesture fires exactly one POST per completed gesture.
  - On 4xx, the optimistic edge is removed and a `.toast` shows the
    server's error message.
  - Context menu items route only to existing endpoints + the new
    `depends_on` POST; no other new routes introduced here.
  - State-transition click posts to `/api/adventures/{id}/state` with the
    same payload as the v1 Decisions tab.
- **Target Conditions**: TC-055, TC-056, TC-057
- **Depends On**: [ADV009-T019]
- **Evaluation**:
  - Access requirements: Read, Edit
  - Skill set: Vanilla JS, cytoscape event API, DOM menu
  - Estimated duration: 28 min
  - Estimated tokens: 85000

### Implement automated tests for Pipeline tab and IR extractor
- **ID**: ADV009-T021
- **Description**: Extend the ADV-009 test suite with:
  - `tests/test_ir.py` — IR round-trip on ADV-007 + ADV-008, entity
    shape, enum serialization, orphan-id detection.
  - `tests/test_graph_endpoint.py` — `/graph` payload schema test,
    node/edge cardinality smoke tests, `depends_on` POST round-trip
    including 400 cases (self-cycle, cycle-creating, unknown task).
  - `tests/test_pipeline_tab.py` — static inspection of `index.html`:
    cytoscape CDN present, 5-tab tab bar, no WebSocket/EventSource usage,
    no hardcoded tooltip strings (via a pattern check).
  All use stdlib `unittest`. Full discover must exit 0.
- **Files**:
  - `.agent/adventures/ADV-009/tests/test_ir.py`
  - `.agent/adventures/ADV-009/tests/test_graph_endpoint.py`
  - `.agent/adventures/ADV-009/tests/test_pipeline_tab.py`
- **Acceptance Criteria**:
  - `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"` exits 0.
  - Every autotest TC from TC-039..TC-061 has a matching `test_` function.
  - Tests use stdlib only.
- **Target Conditions**: TC-039, TC-040, TC-041, TC-042, TC-043, TC-044,
  TC-046, TC-047, TC-048, TC-049, TC-050, TC-051, TC-052, TC-053,
  TC-054, TC-055, TC-056, TC-058, TC-059, TC-060, TC-061
- **Depends On**: [ADV009-T001, ADV009-T015, ADV009-T016, ADV009-T018,
  ADV009-T019, ADV009-T020]
- **Evaluation**:
  - Access requirements: Read, Write, Bash (python -m unittest, python server.py)
  - Skill set: Python unittest, HTTP client, HTMLParser, graph test authoring
  - Estimated duration: 30 min
  - Estimated tokens: 100000
