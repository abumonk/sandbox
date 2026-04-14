---
id: ADV-009
title: Adventure Console UI v2 — Simple, Reader-First Layout
state: active
created: 2026-04-14T21:36:55Z
updated: 2026-04-15T00:10:00Z
tasks: [ADV009-T001, ADV009-T002, ADV009-T003, ADV009-T004, ADV009-T005, ADV009-T006, ADV009-T007, ADV009-T008, ADV009-T009, ADV009-T010, ADV009-T011, ADV009-T012, ADV009-T013, ADV009-T014, ADV009-T015, ADV009-T016, ADV009-T017, ADV009-T018, ADV009-T019, ADV009-T020, ADV009-T021]
depends_on: []
---
## Concept

Plan, design, and implement a **simpler UI** for the Adventure Console
(`.agent/adventure-console/`) created in the previous session. The current UI is
functional but technical: 9 tabs, inline frontmatter, raw command columns,
log dumps. Goal: make it a **fast-reading control surface** that a human can
scan in seconds, not parse like a config file.

**Concrete requirements (from the prompt):**

1. **Custom layouts per document type.**
   - **Task**: status pill, depends-on chain, target-conditions checklist,
     description + acceptance criteria. No raw frontmatter, no log dump
     by default.
   - **Design**: rendered prose with a one-line "what this design decides"
     header pulled from the doc.
   - **Plan**: phases / waves as visual groups, not a wall of markdown.

2. **Combine four tabs into one `Documents` tab.**
   Designs + Plans + Research + Reviews collapse into a single tab with a
   **filter bar** (chips: All · Designs · Plans · Research · Reviews) and
   a single document list.

3. **Audit and simplify every element of the console.**
   - Remove technical noise (raw paths, log tails, frontmatter, command
     strings, file-system jargon) from default views.
   - Keep the *information density* of essentials (state, progress,
     blockers) but drop the bytes of clutter around them.
   - Anything technical stays accessible behind a "Show details" toggle —
     not on the default view.

**Final shape (proposed, to be refined in design phase):**

| Sidebar | Header | Tabs |
|---------|--------|------|
| Adventures with state badge + 1-line subtitle | Title · state pill · progress bar · primary action button | **Overview** · **Tasks** · **Documents** · **Decisions** |

- **Overview**: concept summary, target-conditions progress (visual bars,
  not a 9-column table), next action.
- **Tasks**: kanban-style or grouped-by-status list with custom task card
  layout. Click → detail panel with the simplified task layout.
- **Documents**: unified browser with type filter; each doc rendered with
  its custom layout.
- **Decisions** (replaces Permissions + Knowledge + state-transitions):
  the things a human needs to *act on* — pending approvals, knowledge
  suggestions awaiting curation, state transitions.

**Backend impact**: `server.py` already exposes the right primitives. The
adventure may add 1-2 endpoints (e.g. structured task summary, document
type tagging) but no schema changes.

**Success looks like**: open the console, glance at any adventure, and know
within 5 seconds what state it's in, what's blocking it, and what action is
expected of you — without reading any frontmatter or shell command.

---

## Addendum (2026-04-14T22:00:00Z) — Ark representation + live graph view

Two additional, scope-expanding requirements:

**4. Ark representation of adventures, pipelines, and entities.**
Mirror the ADV-008 pattern: a **sibling package** `R:/Sandbox/adventure_pipeline/`
(or `.agent/adventure-console/specs/` if we keep it inside the console
artifact) provides the Ark spec. **Ark itself is not modified.** Specs cover:
- `adventure.ark` — entities: Adventure, Phase, Wave, Task, State, Transition,
  Permission, Document (Design/Plan/Research/Review), Decision, TargetCondition,
  Agent, Role.
- `pipeline.ark` — processes: adventure-state machine (concept → planning →
  review → active → blocked/completed/cancelled), task lifecycle, review
  pipeline orchestration.
- `entities.ark` — runtime entities: RunningAgent, ActiveTask, PendingDecision,
  KnowledgeSuggestion, ReviewArtifact.
- Optional: verifier passes for state-transition validity, permission coverage,
  TC traceability — invoked through Ark's existing verifier (no Ark patches).
- IR extractor + Python adapter that lifts a live `.agent/adventures/ADV-NNN/`
  directory into a populated IR matching the spec.

**5. Visualization & editing of live pipeline entities via nodes/graphs/diagrams.**
A new tab — provisional name **Pipeline** — that renders the running adventure
as an interactive graph:
- **Show**: nodes for Adventure / Phases / Waves / Tasks / Documents /
  Decisions; edges for `depends_on`, `target_conditions ↔ tasks`, state
  transitions; live status colors (running / blocked / passed / failed).
- **Explain**: hover/click nodes for plain-language tooltips ("This task
  depends on T002 because the audit verdicts gate every frontend task"),
  matched against the Ark IR so explanations are spec-driven, not hardcoded.
- **Edit**: drag to wire `depends_on`; click to trigger state transitions;
  right-click for add-task / approve-design / open-doc actions. Edits route
  through existing API endpoints + 1-2 new ones (`POST .../tasks/{id}/depends_on`).

**Library decision (proposed, planner to ratify):** **cytoscape.js** loaded
via CDN — keeps the no-build-step constraint, supports editable graphs, has
a small footprint. Alternatives: vis-network (simpler), D3 (bare-metal).

**Updated tab structure (proposed):** Overview · Tasks · Documents ·
**Pipeline** · Decisions. Pipeline becomes the visual heart; the other tabs
remain text-first for fast reading.

**Success delta:** the user can not only *read* an adventure in 5 seconds
(original goal) but also *see* its full structure as a diagram and *act* on
it directly from the graph.

## Target Conditions
| ID | Description | Source | Design | Plan | Task(s) | Proof Method | Proof Command | Status |
|----|-------------|--------|--------|------|---------|--------------|---------------|--------|
| TC-001 | `research/audit.md` exists and enumerates >= 30 distinct UI elements | design-simplification-audit | design-simplification-audit | plan-audit-and-backend | ADV009-T002 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestAuditPresence` | pending |
| TC-002 | every audit row has a verdict in {keep, hide-behind-toggle, remove} | design-simplification-audit | design-simplification-audit | plan-audit-and-backend | ADV009-T002 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestAuditVerdicts` | pending |
| TC-003 | every current-tab dispatch branch has at least one audit row | design-simplification-audit | design-simplification-audit | plan-audit-and-backend | ADV009-T002 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestAuditCoverage` | pending |
| TC-004 | v2 index.html renders exactly four top-level tabs | design-information-architecture | design-information-architecture | plan-frontend-rewrite | ADV009-T006 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestTabBar.test_four_tabs` | pending |
| TC-005 | Log/Knowledge/Permissions/Designs/Plans/Research/Reviews do not appear as top-level tabs | design-information-architecture | design-information-architecture | plan-frontend-rewrite | ADV009-T006, ADV009-T011 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestTabBar.test_no_legacy_tabs` | pending |
| TC-006 | Header contains ID, title, state pill, TC progress indicator, primary action button | design-information-architecture | design-information-architecture | plan-frontend-rewrite | ADV009-T006 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestHeader` | pending |
| TC-007 | Sidebar rows show state badge + ID + title + one-line subtitle, no paths/counts | design-information-architecture | design-information-architecture | plan-frontend-rewrite | ADV009-T006 | poc | open browser, inspect sidebar markup | pending |
| TC-008 | Tasks tab groups tasks into status buckets; empty buckets hidden | design-task-card-layout | design-task-card-layout | plan-frontend-rewrite | ADV009-T008 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestTasksTab.test_buckets` | pending |
| TC-009 | Task card shows status/ID/title/depends/TCs but no file path or assignee by default | design-task-card-layout | design-task-card-layout | plan-frontend-rewrite | ADV009-T008 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestTasksTab.test_card_shape` | pending |
| TC-010 | Task detail renders Description + Acceptance Criteria as components, not markdown blob | design-task-card-layout | design-task-card-layout | plan-frontend-rewrite | ADV009-T008 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_smoke.TestTaskDetail.test_structured` | pending |
| TC-011 | Frontmatter/log/raw path hidden by default; visible after Show-details toggle | design-task-card-layout | design-task-card-layout | plan-frontend-rewrite | ADV009-T008 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_smoke.TestTaskDetail.test_disclosure` | pending |
| TC-012 | TC checklist row shows checkbox reflecting TC status | design-task-card-layout | design-task-card-layout | plan-frontend-rewrite | ADV009-T008 | poc | open ADV-007 task, verify checklist matches manifest TC status | pending |
| TC-013 | Documents tab shows chip filter bar with All/Designs/Plans/Research/Reviews | design-document-layouts | design-document-layouts | plan-frontend-rewrite | ADV009-T009 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestDocumentsTab.test_chips` | pending |
| TC-014 | Chip click filters list client-side without a network request | design-document-layouts | design-document-layouts | plan-frontend-rewrite | ADV009-T009 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_smoke.TestDocuments.test_chip_filter` | pending |
| TC-015 | Opening a design shows "What this design decides:" header | design-document-layouts | design-document-layouts | plan-frontend-rewrite | ADV009-T009 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_smoke.TestDocuments.test_design_header` | pending |
| TC-016 | Opening a plan with `## Wave N` renders waves as visual groups | design-document-layouts | design-document-layouts | plan-frontend-rewrite | ADV009-T009 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_smoke.TestDocuments.test_plan_waves` | pending |
| TC-017 | Opening a review shows PASSED/FAILED badge and summary strip | design-document-layouts | design-document-layouts | plan-frontend-rewrite | ADV009-T009 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_smoke.TestDocuments.test_review_strip` | pending |
| TC-018 | Overview renders a progress bar for TCs (not a table) | design-overview-tab | design-overview-tab | plan-frontend-rewrite | ADV009-T007 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestOverview.test_progress_bar` | pending |
| TC-019 | Overview lists up to 5 non-passing TCs above the Show-all disclosure | design-overview-tab | design-overview-tab | plan-frontend-rewrite | ADV009-T007 | poc | open ADV-007 overview, count blocker rows | pending |
| TC-020 | Overview renders a single next-action card matching adventure state | design-overview-tab | design-overview-tab | plan-frontend-rewrite | ADV009-T007 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_smoke.TestOverview.test_next_action` | pending |
| TC-021 | Full raw concept markdown is hidden until user clicks Show more | design-overview-tab | design-overview-tab | plan-frontend-rewrite | ADV009-T007 | poc | inspect Overview markup for `<details>` containing full concept | pending |
| TC-022 | Decisions tab renders three cards; empty cards hidden | design-decisions-tab | design-decisions-tab | plan-frontend-rewrite | ADV009-T010 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestDecisions.test_three_cards` | pending |
| TC-023 | Permissions card shows request counts; full doc hidden by default | design-decisions-tab | design-decisions-tab | plan-frontend-rewrite | ADV009-T010 | poc | open ADV-009 Decisions tab, verify counts + disclosure | pending |
| TC-024 | State-transition button from Decisions posts to /api/adventures/{id}/state | design-decisions-tab | design-decisions-tab | plan-frontend-rewrite | ADV009-T010 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_smoke.TestDecisions.test_state_post` | pending |
| TC-025 | Knowledge suggestions write same JSON payload as v1 (regression) | design-decisions-tab | design-decisions-tab | plan-frontend-rewrite | ADV009-T010 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_server.TestKnowledgePayload` | pending |
| TC-026 | GET /api/adventures/{id} includes summary block with all declared fields | design-backend-endpoints | design-backend-endpoints | plan-audit-and-backend | ADV009-T003 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_server.TestSummary` | pending |
| TC-027 | GET /api/adventures/{id}/documents returns unified list with correct type per entry | design-backend-endpoints | design-backend-endpoints | plan-audit-and-backend | ADV009-T004 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_server.TestDocumentsEndpoint.test_types` | pending |
| TC-028 | Plan with `## Wave 1` and `## Wave 2` reports waves: 2 | design-backend-endpoints | design-backend-endpoints | plan-audit-and-backend | ADV009-T004 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_server.TestDocumentsEndpoint.test_waves` | pending |
| TC-029 | next_action.kind == "approve_permissions" for state=review with unapproved permissions | design-backend-endpoints | design-backend-endpoints | plan-audit-and-backend | ADV009-T003 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_server.TestNextAction.test_review` | pending |
| TC-030 | server.py remains stdlib-only (no new third-party imports) | design-backend-endpoints | design-backend-endpoints | plan-audit-and-backend | ADV009-T003, ADV009-T004 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_server.TestStdlibOnly` | pending |
| TC-031 | .card/.pill/.progress/.chip-bar/.chip/.stack/.disclosure CSS rules exist | design-visual-system | design-visual-system | plan-frontend-rewrite | ADV009-T005 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestVisualSystem.test_classes` | pending |
| TC-032 | No new external CSS or font link added; marked.js remains sole external dep | design-visual-system | design-visual-system | plan-frontend-rewrite | ADV009-T005 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestVisualSystem.test_no_external` | pending |
| TC-033 | Every primary card uses .card class (no ad-hoc inline card styles) | design-visual-system | design-visual-system | plan-frontend-rewrite | ADV009-T007, ADV009-T010 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ui_layout.TestVisualSystem.test_card_usage` | pending |
| TC-034 | tests/test-strategy.md maps every autotest TC to a named test function | design-test-strategy | design-test-strategy | plan-audit-and-backend | ADV009-T001 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_server.TestStrategyDoc.test_tc_mapping` | pending |
| TC-035 | All declared test files use stdlib unittest | design-test-strategy | design-test-strategy | plan-audit-and-backend | ADV009-T001 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_server.TestStrategyDoc.test_framework` | pending |
| TC-036 | Full unittest discover command exits 0 | design-test-strategy | design-test-strategy | plan-testing-and-polish | ADV009-T012 | autotest | `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"` | pending |
| TC-037 | 5-second-glance manual verification passes on ADV-007 and ADV-008 | manifest/concept | — | plan-testing-and-polish | ADV009-T013 | manual | open console; verify 5s-glance-report.md | pending |
| TC-038 | README updated to reflect the four v2 tabs and new /documents endpoint | manifest/concept | — | plan-testing-and-polish | ADV009-T014 | manual | diff README.md; grep for v2 tab names | pending |
| TC-039 | `adventure_pipeline/specs/adventure.ark` parses cleanly with vanilla Ark | design-ark-pipeline-spec | design-ark-pipeline-spec | plan-ark-spec-and-ir | ADV009-T015 | autotest | `python ark/ark.py parse adventure_pipeline/specs/adventure.ark` | pending |
| TC-040 | `pipeline.ark` declares AdventureStateMachine, TaskLifecycle, ReviewPipeline processes | design-ark-pipeline-spec | design-ark-pipeline-spec | plan-ark-spec-and-ir | ADV009-T015 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ir.TestSpecShapes.test_processes` | pending |
| TC-041 | `entities.ark` declares RunningAgent, ActiveTask, PendingDecision, KnowledgeSuggestion, ReviewArtifact | design-ark-pipeline-spec | design-ark-pipeline-spec | plan-ark-spec-and-ir | ADV009-T015 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ir.TestSpecShapes.test_runtime_entities` | pending |
| TC-042 | IR extractor on ADV-007 returns populated tasks/documents/tcs/permissions | design-ark-pipeline-spec | design-ark-pipeline-spec | plan-ark-spec-and-ir | ADV009-T016 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ir.TestRoundTrip.test_adv007` | pending |
| TC-043 | IR extractor on ADV-008 returns populated tasks/documents/tcs/permissions | design-ark-pipeline-spec | design-ark-pipeline-spec | plan-ark-spec-and-ir | ADV009-T016 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ir.TestRoundTrip.test_adv008` | pending |
| TC-044 | Every Task.id emitted by the extractor matches manifest `tasks:` frontmatter list | design-ark-pipeline-spec | design-ark-pipeline-spec | plan-ark-spec-and-ir | ADV009-T016 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_ir.TestRoundTrip.test_task_ids_match_manifest` | pending |
| TC-045 | Verifier passes clean OR deferrals documented in adventure_pipeline/README.md; `ark/` untouched | design-ark-pipeline-spec | design-ark-pipeline-spec | plan-ark-spec-and-ir | ADV009-T017 | poc | `git diff --exit-code ark/ && python ark/ark.py verify adventure_pipeline/specs/verify/state_transitions.ark` | pending |
| TC-046 | `GET /api/adventures/{id}/graph` returns JSON with nodes[], edges[], explanations{} | design-graph-backend-endpoints | design-graph-backend-endpoints | plan-graph-view-and-editing | ADV009-T018 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_graph_endpoint.TestGraphShape` | pending |
| TC-047 | index.html loads cytoscape via a CDN `<script>` tag (no bundler, no local copy) | design-pipeline-graph-view | design-pipeline-graph-view | plan-graph-view-and-editing | ADV009-T019 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_pipeline_tab.TestCdn` | pending |
| TC-048 | Pipeline tab appears as 4th top-level tab, between Documents and Decisions (5 tabs total) | design-pipeline-graph-view | design-pipeline-graph-view | plan-graph-view-and-editing | ADV009-T019 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_pipeline_tab.TestTabOrder` | pending |
| TC-049 | Node status colours follow design mapping (task/tc/decision/document) | design-pipeline-graph-view | design-pipeline-graph-view | plan-graph-view-and-editing | ADV009-T019 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_pipeline_tab.TestStatusColours` | pending |
| TC-050 | Polling uses setTimeout; no WebSocket/EventSource in server.py or index.html | design-pipeline-graph-view | design-pipeline-graph-view | plan-graph-view-and-editing | ADV009-T019 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_pipeline_tab.TestNoWebsocket` | pending |
| TC-051 | Tooltip text comes from backend explanations map (no hardcoded tooltip strings in renderPipeline) | design-pipeline-graph-view | design-pipeline-graph-view | plan-graph-view-and-editing | ADV009-T019 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_pipeline_tab.TestTooltipsFromBackend` | pending |
| TC-052 | depends_on POST returns 200 with updated list on valid input | design-graph-edit-affordances | design-graph-edit-affordances | plan-graph-view-and-editing | ADV009-T018 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_graph_endpoint.TestDependsOn.test_happy` | pending |
| TC-053 | depends_on POST returns 400 on self-cycle | design-graph-edit-affordances | design-graph-edit-affordances | plan-graph-view-and-editing | ADV009-T018 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_graph_endpoint.TestDependsOn.test_self_cycle` | pending |
| TC-054 | depends_on POST returns 400 on cycle-creating input | design-graph-edit-affordances | design-graph-edit-affordances | plan-graph-view-and-editing | ADV009-T018 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_graph_endpoint.TestDependsOn.test_cycle` | pending |
| TC-055 | Drag-to-connect emits exactly one POST per gesture | design-graph-edit-affordances | design-graph-edit-affordances | plan-graph-view-and-editing | ADV009-T020 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_pipeline_tab.TestDragOneShot` | pending |
| TC-056 | 4xx response rolls visual edge back (no stale optimistic edge) | design-graph-edit-affordances | design-graph-edit-affordances | plan-graph-view-and-editing | ADV009-T020 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_pipeline_tab.TestRollback` | pending |
| TC-057 | Context menu items route only to existing endpoints + depends_on | design-graph-edit-affordances | design-graph-edit-affordances | plan-graph-view-and-editing | ADV009-T020 | poc | inspect index.html context-menu handlers; grep for non-allowlisted routes | pending |
| TC-058 | server.py imports adventure_pipeline.tools.ir and uses it from /graph handler | design-graph-backend-endpoints | design-graph-backend-endpoints | plan-graph-view-and-editing | ADV009-T018 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_graph_endpoint.TestImport` | pending |
| TC-059 | /graph payload passes schema smoke test (node.data.id/kind; edges/explanations shape) | design-graph-backend-endpoints | design-graph-backend-endpoints | plan-graph-view-and-editing | ADV009-T018 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_graph_endpoint.TestGraphShape.test_schema` | pending |
| TC-060 | server.py remains stdlib-only after graph endpoints land | design-graph-backend-endpoints | design-graph-backend-endpoints | plan-graph-view-and-editing | ADV009-T018 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_graph_endpoint.TestStdlibOnly` | pending |
| TC-061 | `_cycle_free` helper rejects direct self-cycles and transitive cycles | design-graph-backend-endpoints | design-graph-backend-endpoints | plan-graph-view-and-editing | ADV009-T018 | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_graph_endpoint.TestCycleFree` | pending |

## Evaluations
| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |
|------|---------------------|-----------|---------------|-------------|-----------|-----------------|---------------|-------------|----------|
| ADV009-T001 | Read, Write | test planning, markdown | 12 min | 18,000 | $0.054 | — | — | — | — |
| ADV009-T002 | Read, Write | UX analysis, markdown | 20 min | 30,000 | $0.090 | — | — | — | — |
| ADV009-T003 | Read, Edit, Bash | Python stdlib HTTP, JSON | 18 min | 45,000 | $0.135 | — | — | — | — |
| ADV009-T004 | Read, Edit, Bash | Python stdlib HTTP, regex | 20 min | 50,000 | $0.150 | — | — | — | — |
| ADV009-T005 | Read, Edit | CSS | 12 min | 18,000 | $0.054 | — | — | — | — |
| ADV009-T006 | Read, Edit | Vanilla JS, DOM, CSS | 25 min | 70,000 | $0.210 | — | — | — | — |
| ADV009-T007 | Read, Edit | Vanilla JS, DOM | 22 min | 55,000 | $0.165 | — | — | — | — |
| ADV009-T008 | Read, Edit | Vanilla JS, regex section parsing | 28 min | 85,000 | $0.255 | — | — | — | — |
| ADV009-T009 | Read, Edit | Vanilla JS, DOM, regex | 28 min | 90,000 | $0.270 | — | — | — | — |
| ADV009-T010 | Read, Edit | Vanilla JS, DOM | 22 min | 60,000 | $0.180 | — | — | — | — |
| ADV009-T011 | Read, Edit, Bash | JS refactoring | 15 min | 28,000 | $0.084 | — | — | — | — |
| ADV009-T012 | Read, Write, Bash | Python unittest, HTTP client, HTMLParser | 28 min | 95,000 | $0.285 | — | — | — | — |
| ADV009-T013 | Read, Write, Bash | manual UI verification | 12 min | 15,000 | $0.045 | — | — | — | — |
| ADV009-T014 | Read, Edit | markdown authoring | 8 min | 12,000 | $0.036 | — | — | — | — |
| ADV009-T015 | Read, Write | Ark DSL authoring, domain modelling | 25 min | 60,000 | $0.180 | — | — | — | — |
| ADV009-T016 | Read, Write, Bash | Python stdlib, regex, markdown parsing | 28 min | 85,000 | $0.255 | — | — | — | — |
| ADV009-T017 | Read, Write, Bash | Ark verifier, Z3 invariants | 18 min | 35,000 | $0.105 | — | — | — | — |
| ADV009-T018 | Read, Edit, Bash | Python stdlib HTTP, regex, graph algorithms | 28 min | 85,000 | $0.255 | — | — | — | — |
| ADV009-T019 | Read, Edit | Vanilla JS, cytoscape.js API, DOM | 30 min | 95,000 | $0.285 | — | — | — | — |
| ADV009-T020 | Read, Edit | Vanilla JS, cytoscape events, DOM menu | 28 min | 85,000 | $0.255 | — | — | — | — |
| ADV009-T021 | Read, Write, Bash | Python unittest, HTTP client, graph testing | 30 min | 100,000 | $0.300 | — | — | — | — |
| **Total** | — | — | **457 min** | **1,216,000** | **$3.648** | — | — | — | — |

**Thresholds**: `adventure.max_task_tokens = 100000`; `adventure.max_task_duration = 30min`.
All tasks (including T015-T021) are at or under both thresholds.
T019 and T021 sit at the duration ceiling — acceptable; no split needed,
but watch at execution time. Cost computed at
`adventure.token_cost_per_1k.opus = 0.015` (conservative; most tasks will
run on sonnet at $0.003/1k, cutting total cost to ~$0.73).

**Addendum impact**: +7 tasks, +23 TCs (TC-039..TC-061), +4 designs,
+2 plans, +1 sibling package (`adventure_pipeline/`). Adventure remains
wave-able: original Wave A/B/C intact; new Waves D (T015-T017) and E
(T018-T020) insert between B and C, with T021 joining the testing wave.

## Environment
- **Project**: Sandbox (Claudovka ecosystem)
- **Workspace**: R:\Sandbox
- **Repo**: https://github.com/abumonk/sandbox.git
- **Branch**: master
- **PC**: TTT
- **Platform**: Windows 11 Pro 10.0.26200
- **Runtime**: Node v24.12.0, Python 3.12
- **Shell**: bash
