# Plan — Wave E: Tests, Docs, Regression

## Designs Covered

- designs/design-test-strategy.md (mandatory test implementation task)

The autotest harness that certifies every other design doc. Also
the small amount of documentation surface that future adventures
need so they don't design the same mechanism twice.

## Tasks

### Test fixtures

- **ID**: ADV010-T015
- **Description**: Author all test fixtures under
  `tests/fixtures/`: 7 event JSON files (happy_opus, happy_sonnet,
  missing_tokens, bad_model, replay, post_tool_use,
  malformed.txt); 5 metrics.md files; 2 manifest files.
- **Files**:
  - `.agent/adventures/ADV-010/tests/fixtures/events/*.json` (7 files)
  - `.agent/adventures/ADV-010/tests/fixtures/events/malformed.txt`
  - `.agent/adventures/ADV-010/tests/fixtures/metrics/*.md` (5 files)
  - `.agent/adventures/ADV-010/tests/fixtures/manifests/*.md` (2 files)
- **Acceptance Criteria**:
  - All event JSON files validate or fail-validate as documented
    (self-check: running `schema.validate_event` on each produces
    the expected outcome).
  - Every metrics fixture has a known-good frontmatter-totals pair
    computable by hand.
- **Target Conditions**: (fixtures support multiple TCs; no direct TC)
- **Depends On**: ADV010-T005
- **Evaluation**:
  - Access requirements: Write (tests/fixtures/)
  - Skill set: realistic fixture crafting
  - Estimated duration: 20min
  - Estimated tokens: 30000

### Implement automated tests (mandatory test implementation task)

- **ID**: ADV010-T016
- **Description**: Implement every test file from
  `tests/test-strategy.md`:
  `test_schema.py`, `test_cost_model.py`, `test_capture.py`,
  `test_aggregator.py`, `test_task_actuals.py`,
  `test_error_isolation.py`, `test_backfill.py`,
  `test_live_canary.py`, `test_regression.py`, plus `conftest.py`
  and `__init__.py`. Each TC with `Proof Method: autotest` must
  have a named test function that asserts it and passes. Run
  the full discover command and confirm exit 0.
- **Files**:
  - `.agent/adventures/ADV-010/tests/__init__.py` (new)
  - `.agent/adventures/ADV-010/tests/conftest.py` (new)
  - `.agent/adventures/ADV-010/tests/test_schema.py` (new)
  - `.agent/adventures/ADV-010/tests/test_cost_model.py` (new)
  - `.agent/adventures/ADV-010/tests/test_capture.py` (new)
  - `.agent/adventures/ADV-010/tests/test_aggregator.py` (new)
  - `.agent/adventures/ADV-010/tests/test_task_actuals.py` (new)
  - `.agent/adventures/ADV-010/tests/test_error_isolation.py` (new)
  - `.agent/adventures/ADV-010/tests/test_backfill.py` (new)
  - `.agent/adventures/ADV-010/tests/test_live_canary.py` (new;
    canary test is skipped if fixture snapshots absent — becomes
    active after T014)
  - `.agent/adventures/ADV-010/tests/test_regression.py` (new)
- **Acceptance Criteria**:
  - `python -m unittest discover -s .agent/adventures/ADV-010/tests
    -v` exits 0 (after T014 canary fixtures exist; before then the
    canary test `skipUnless`es on fixture presence).
  - Every TC ID appears as either a test method name or a
    `self.assertIn(TC-..., ...)` comment in at least one test file.
  - `test_regression.py` subprocess-invokes discover and asserts 0.
- **Target Conditions**: TC-S-1, TC-S-2, TC-S-3, TC-CC-1, TC-CC-2,
  TC-CC-3, TC-CC-4, TC-CM-1, TC-CM-2, TC-CM-3, TC-CM-4, TC-HI-1,
  TC-HI-2, TC-HI-3, TC-HI-4, TC-AG-1, TC-AG-2, TC-AG-3, TC-AG-4,
  TC-AG-5, TC-AG-6, TC-EI-1, TC-EI-2, TC-EI-3, TC-EI-4, TC-EI-5,
  TC-BF-1, TC-BF-2, TC-BF-3, TC-BF-4, TC-BF-5, TC-BF-6, TC-RG-1,
  TC-TS-1
- **Depends On**: ADV010-T002, ADV010-T007, ADV010-T009, ADV010-T010,
  ADV010-T012, ADV010-T015
- **Evaluation**:
  - Access requirements: Read, Write (tests/), Bash (python
    -m unittest, subprocess)
  - Skill set: unittest, subprocess-driven tests, temp directories
  - Estimated duration: 30min
  - Estimated tokens: 90000
  - **NOTE**: At 90K tokens + 30min, this sits right at threshold.
    If during implementation the test surface grows beyond
    projection, split into T016a (test_schema + test_cost_model +
    test_capture + test_aggregator) and T016b (remaining files).
    Checkpoint at 3 green files.

### Operator documentation

- **ID**: ADV010-T017
- **Description**: Author a short operator doc at
  `.agent/telemetry/README.md` covering: layout, how the hook is
  wired, how to run backfill, how to read
  `capture-errors.log`, how to add a new cost rate. ≤ 200 lines.
- **Files**:
  - `.agent/telemetry/README.md` (new)
- **Acceptance Criteria**:
  - Covers the 5 topics above as `## Sections`.
  - Contains the discover one-liner.
  - Contains the backfill one-liner.
- **Target Conditions**: (doc-only; no TC)
- **Depends On**: ADV010-T016
- **Evaluation**:
  - Access requirements: Read (.agent/telemetry/), Write
  - Skill set: technical writing
  - Estimated duration: 10min
  - Estimated tokens: 15000

### Knowledge base extraction

- **ID**: ADV010-T018
- **Description**: After all prior tasks pass, append to
  `.agent/knowledge/patterns.md`, `decisions.md`, `issues.md` the
  distilled lessons from ADV-010: the row-schema pattern, the
  stdlib-only YAML-subset parser decision, the reconstruct-vs-fake
  decision, the exit-0-on-failure pattern, the
  backup-before-rename reversibility guard.
- **Files**:
  - `.agent/knowledge/patterns.md` (append)
  - `.agent/knowledge/decisions.md` (append)
  - `.agent/knowledge/issues.md` (append — close out the
    "Incomplete metrics tracking" and "Metrics Frontmatter
    Aggregation Gap" issues with "fixed in ADV-010")
- **Acceptance Criteria**:
  - ≥ 1 new entry per knowledge file, each attributed to ADV-010.
  - Existing entries preserved verbatim.
- **Target Conditions**: (process; no TC)
- **Depends On**: ADV010-T014, ADV010-T016
- **Evaluation**:
  - Access requirements: Read, Write (.agent/knowledge/)
  - Skill set: technical writing
  - Estimated duration: 10min
  - Estimated tokens: 15000
