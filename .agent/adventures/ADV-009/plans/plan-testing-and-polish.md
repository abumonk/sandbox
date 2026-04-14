# Plan: Testing and Polish (Wave C)

## Designs Covered
- design-test-strategy
- (regression coverage for all other designs)

## Tasks

### Implement automated tests for ADV-009
- **ID**: ADV009-T012
- **Description**: Implement the three test files declared in
  `tests/test-strategy.md`. Tier 1 (`test_server.py`) covers backend TCs
  (summary block, documents endpoint, next-action logic, stdlib-only).
  Tier 2 (`test_ui_layout.py`) parses `index.html` statically for tab
  structure, CSS class presence, and `data-testid` hooks. Tier 3
  (`test_ui_smoke.py`) uses Playwright if available; otherwise
  `unittest.skip`. Run the full discover command and verify exit 0.
- **Files**:
  - `.agent/adventures/ADV-009/tests/test_server.py`
  - `.agent/adventures/ADV-009/tests/test_ui_layout.py`
  - `.agent/adventures/ADV-009/tests/test_ui_smoke.py`
- **Acceptance Criteria**:
  - `python -m unittest discover -s .agent/adventures/ADV-009/tests -p
    "test_*.py"` exits 0.
  - Every autotest TC declared in test-strategy.md has a matching
    `test_` function name.
  - Tier 3 tests skip cleanly if Playwright is not installed (the run
    still exits 0).
  - Tests use only stdlib for Tier 1 and Tier 2.
- **Target Conditions**: TC-036, plus proof-runs for every TC whose
  `proof_method` is `autotest` (TC-004, TC-005, TC-008, TC-009, TC-010,
  TC-011, TC-013, TC-014, TC-015, TC-016, TC-017, TC-018, TC-020,
  TC-022, TC-024, TC-025, TC-026, TC-027, TC-028, TC-029, TC-030,
  TC-031, TC-032, TC-033).
- **Depends On**: [ADV009-T001, ADV009-T003, ADV009-T004, ADV009-T005,
  ADV009-T006, ADV009-T007, ADV009-T008, ADV009-T009, ADV009-T010,
  ADV009-T011]
- **Evaluation**:
  - Access requirements: Read, Write, Bash (python -m unittest, python
    server.py)
  - Skill set: Python unittest, HTTP client, HTMLParser, optional
    Playwright
  - Estimated duration: 28 min
  - Estimated tokens: 95000

### 5-second-glance manual verification
- **ID**: ADV009-T013
- **Description**: Using ADV-007 and ADV-008 (the most content-rich
  adventures in the tree), run the console and perform the 5-second
  glance test: open each tab and confirm (a) no raw paths visible,
  (b) no frontmatter visible by default, (c) no log tail visible by
  default, (d) the next-action card is meaningful. Record findings in
  `.agent/adventures/ADV-009/research/5s-glance-report.md`.
- **Files**: `.agent/adventures/ADV-009/research/5s-glance-report.md`
- **Acceptance Criteria**:
  - Report exists and covers both adventures.
  - Each of the four manual-check items has a ✓/✗ verdict per adventure.
  - Any ✗ becomes a follow-up issue (logged in the report, not blocking).
- **Target Conditions**: TC-037 (manual)
- **Depends On**: [ADV009-T012]
- **Evaluation**:
  - Access requirements: Read, Write, Bash (python .agent/adventure-console/server.py)
  - Skill set: Manual UI verification
  - Estimated duration: 12 min
  - Estimated tokens: 15000

### Update README for v2
- **ID**: ADV009-T014
- **Description**: Update `.agent/adventure-console/README.md` to reflect
  the four-tab v2 layout. Replace the v1 "Main pane — tabs per adventure"
  table with the Overview/Tasks/Documents/Decisions description. Add a
  brief note about the `summary` block and the new `/documents` endpoint.
  Keep the rest (run / how-to / safety) intact.
- **Files**: `.agent/adventure-console/README.md`
- **Acceptance Criteria**:
  - README mentions exactly the four v2 tabs and does not list the nine
    v1 tabs in the "What it does" section.
  - The endpoints table lists `/api/adventures/{id}/documents`.
  - Run command still "`python .agent/adventure-console/server.py`".
- **Target Conditions**: TC-038 (manual)
- **Depends On**: [ADV009-T011]
- **Evaluation**:
  - Access requirements: Read, Edit
  - Skill set: Markdown authoring
  - Estimated duration: 8 min
  - Estimated tokens: 12000
