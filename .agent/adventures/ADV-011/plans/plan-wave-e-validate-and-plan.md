# Plan — Wave E: Validate + Downstream Plan + Test Implementation

## Designs Covered
- design-validation-against-tcs
- design-downstream-adventure-plan
- design-test-strategy (implementation half)

## Tasks

### ADV011-T009 — Validate unified designs against ADV-001..008 TCs
- **ID**: ADV011-T009
- **Description**: Extract every TC from ADV-001..008 manifests (via grep). Produce `research/validation-coverage.md` with one row per TC assigning `COVERED-BY | RETIRED-BY | DEFERRED-TO` per `design-validation-against-tcs.md`. Each `COVERED-BY` cites a section anchor in one of the unified designs. Each `RETIRED-BY` cites a pruning-catalog row. Each `DEFERRED-TO` cites a downstream adventure id (will be resolved by T010 producing the plan). Also produce `research/validation-report.md` summarising counts and any open gaps.
- **Files**:
  - `.agent/adventures/ADV-011/research/validation-coverage.md` (NEW)
  - `.agent/adventures/ADV-011/research/validation-report.md` (NEW)
- **Acceptance Criteria**:
  - Both files exist.
  - Row count in coverage matrix equals total TCs across ADV-001..008.
  - No blank verdicts.
- **Target Conditions**: TC-015, TC-016
- **Depends On**: ADV011-T006, ADV011-T007, ADV011-T008
- **Evaluation**:
  - Access requirements: Read every ADV-001..008 manifest, Read designs/research, Write research/
  - Skill set: traceability, cross-document arithmetic
  - Estimated duration: 25min
  - Estimated tokens: 75000
  - Estimated model: sonnet

### ADV011-T010 — Downstream adventure plan
- **ID**: ADV011-T010
- **Description**: Produce `research/downstream-adventure-plan.md` with 3–6 downstream adventures per `design-downstream-adventure-plan.md`. Seed list (ADV-DU, ADV-BC, ADV-CC, ADV-OP, optional ADV-CE and ADV-UI). Each adventure sketch has Concept / Scope / Depends on / Est. task count. Document the serial-ordering constraint `ADV-DU → ADV-BC → ADV-CC → ADV-OP`.
- **Files**:
  - `.agent/adventures/ADV-011/research/downstream-adventure-plan.md` (NEW)
- **Acceptance Criteria**:
  - File exists.
  - 3–6 H2 adventure sections.
  - Every section has the four required fields.
  - Serial ordering constraint stated explicitly.
- **Target Conditions**: TC-017, TC-018
- **Depends On**: ADV011-T006, ADV011-T007, ADV011-T008, ADV011-T005, ADV011-T009
- **Evaluation**:
  - Access requirements: Read research/**, Write research/
  - Skill set: adventure planning, sequencing
  - Estimated duration: 20min
  - Estimated tokens: 40000
  - Estimated model: sonnet

### ADV011-T011 — Implement automated tests for all deliverables
- **ID**: ADV011-T011
- **Description**: Implement every test named in `tests/test-strategy.md`: (a) `tests/run-all.sh` aggregator that runs every shell proof-command; (b) `tests/test_coverage_arithmetic.py` asserting `covered + retired + deferred = total` in validation matrix; (c) `tests/test_mapping_completeness.py` asserting every concept in inventory is in mapping. Run the full suite and verify exit 0. Each test carries a docstring naming the TCs it validates.
- **Files**:
  - `.agent/adventures/ADV-011/tests/run-all.sh` (NEW)
  - `.agent/adventures/ADV-011/tests/test_coverage_arithmetic.py` (NEW)
  - `.agent/adventures/ADV-011/tests/test_mapping_completeness.py` (NEW)
  - `.agent/adventures/ADV-011/tests/__init__.py` (NEW, empty marker)
- **Acceptance Criteria**:
  - `bash .agent/adventures/ADV-011/tests/run-all.sh` exits 0.
  - `python -m unittest discover -s .agent/adventures/ADV-011/tests -v` exits 0.
- **Target Conditions**: TC-019, TC-020
- **Depends On**: ADV011-T001, ADV011-T002, ADV011-T003, ADV011-T004, ADV011-T005, ADV011-T006, ADV011-T007, ADV011-T008, ADV011-T009, ADV011-T010
- **Evaluation**:
  - Access requirements: Read all deliverables, Write tests/, Bash (bash + python -m unittest + grep + test)
  - Skill set: shell scripting, stdlib unittest, file existence asserts
  - Estimated duration: 20min
  - Estimated tokens: 45000
  - Estimated model: sonnet

### ADV011-T012 — Final validation report
- **ID**: ADV011-T012
- **Description**: Produce `research/final-validation-report.md` summarising the adventure outcome: count of concepts classified, dedup rows, prune rows, downstream adventures, and TC coverage numbers. Confirm run-all.sh passes. Confirm manifest state is ready to flip to `review`.
- **Files**:
  - `.agent/adventures/ADV-011/research/final-validation-report.md` (NEW)
- **Acceptance Criteria**:
  - File exists.
  - Cites counts from every artefact.
  - Confirms run-all.sh exits 0 (copy-paste of actual output).
- **Target Conditions**: TC-021
- **Depends On**: ADV011-T011
- **Evaluation**:
  - Access requirements: Read research/**, tests/**, Bash (rerun run-all.sh once)
  - Skill set: summary writing
  - Estimated duration: 10min
  - Estimated tokens: 20000
  - Estimated model: sonnet
