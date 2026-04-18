# Plan — Wave A: Measurement Sources

## Designs Covered

- research/telemetry-gap-analysis.md (research deliverable)
- designs/design-test-strategy.md (test design task)
- designs/design-capture-contract.md (§event payload)
- schemas/event_payload.md

Wave A establishes the signal inventory and the test-strategy
artifact. No code ships here; the output is research + test plan
+ schema contract that the later waves lean on.

## Tasks

### Telemetry gap analysis (research)

- **ID**: ADV010-T001
- **Description**: Produce
  `research/telemetry-gap-analysis.md` enumerating every concrete
  reason telemetry is not captured today, with file paths + line
  numbers + current-vs-expected per finding. Already drafted by the
  planner; the implementer verifies every cited line number against
  the live repo and amends any drift.
- **Files**:
  - `.agent/adventures/ADV-010/research/telemetry-gap-analysis.md`
    (verify + amend)
- **Acceptance Criteria**:
  - At least 8 numbered findings (F1..F8+).
  - Every finding has a file path and line range, verified to match
    current repo state.
  - "Derived requirements" section lists the modules under
    `.agent/telemetry/` with one-line purpose each.
- **Target Conditions**: TC-RS-1
- **Depends On**: none
- **Evaluation**:
  - Access requirements: Read (entire `.agent/`), Write (research/)
  - Skill set: technical writing, filesystem forensics
  - Estimated duration: 20min
  - Estimated tokens: 35000

### Test strategy document (mandatory test design task)

- **ID**: ADV010-T002
- **Description**: Author `tests/test-strategy.md` mapping every
  autotest TC to a named `unittest` function in a specific file.
  Record the CI one-liner. Already drafted; implementer verifies
  it covers every TC with `Proof Method: autotest` from the final
  manifest and adds any missing rows.
- **Files**:
  - `.agent/adventures/ADV-010/tests/test-strategy.md` (verify +
    amend)
- **Acceptance Criteria**:
  - Every autotest TC from the manifest appears in the TC-to-
    function mapping table.
  - The CI one-liner is present and is a `python -m unittest
    discover ...` command.
  - File lists one test file per design area (8 files expected).
- **Target Conditions**: TC-TS-1, TC-RG-1
- **Depends On**: none
- **Evaluation**:
  - Access requirements: Read (designs/, schemas/), Write (tests/)
  - Skill set: unittest, test-to-requirement mapping
  - Estimated duration: 15min
  - Estimated tokens: 25000

### Event payload schema contract

- **ID**: ADV010-T003
- **Description**: Verify and finalise
  `schemas/event_payload.md` and `schemas/row_schema.md` against the
  actual shape of Claude Code hook payloads. If the live hook uses
  different field names than those drafted, update the alias table
  in `design-hook-integration.md` to match.
- **Files**:
  - `.agent/adventures/ADV-010/schemas/event_payload.md`
  - `.agent/adventures/ADV-010/schemas/row_schema.md`
  - `.agent/adventures/ADV-010/schemas/processes.md`
  - `.agent/adventures/ADV-010/designs/design-hook-integration.md`
    (alias table only; do not edit other sections)
- **Acceptance Criteria**:
  - `event_payload.md` lists every required field with type +
    constraint.
  - `row_schema.md` declares all 12 columns in order with type.
  - `processes.md` documents the 3 workflows (live capture, backfill,
    task actuals).
- **Target Conditions**: TC-S-1, TC-S-2, TC-S-3
- **Depends On**: ADV010-T001
- **Evaluation**:
  - Access requirements: Read, Write (schemas/)
  - Skill set: schema design, dataclass typing
  - Estimated duration: 15min
  - Estimated tokens: 20000
