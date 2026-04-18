# Plan — Wave D: Unified Designs (parallel)

## Designs Covered
- design-unified-descriptor
- design-unified-builder
- design-unified-controller

## Tasks

These three tasks can run in parallel once T003 (mapping) + T004 (dedup) +
T005 (pruning) are complete.

### ADV011-T006 — Unified descriptor design (+ delta report)
- **ID**: ADV011-T006
- **Description**: Produce `research/descriptor-delta.md` per section 4 of `design-unified-descriptor.md`. Classify every current `ark/dsl/stdlib/*.ark` file with a verdict from {KEEP-AS-IS, KEEP-RENAMED, MERGE-INTO, MOVE-TO-PRIMITIVES, RETIRE}. Cite every descriptor-bucket concept from the mapping. Cite every dedup row assigned to the descriptor. Include the target two-level stdlib layout, the grammar authoring contract, and the AST family spec. Note: the unified design doc itself already exists under `designs/` — this task produces only the delta report.
- **Files**:
  - `.agent/adventures/ADV-011/research/descriptor-delta.md` (NEW)
- **Acceptance Criteria**:
  - File exists.
  - Every file under `ark/dsl/stdlib/*.ark` has a verdict row.
  - Every descriptor-bucket dedup row is cited.
- **Target Conditions**: TC-009, TC-010
- **Depends On**: ADV011-T003, ADV011-T004, ADV011-T005
- **Evaluation**:
  - Access requirements: Read `research/**`, `ark/dsl/stdlib/**`, Write `research/`
  - Skill set: DSL architecture, grammar design, Ark literacy
  - Estimated duration: 25min
  - Estimated tokens: 60000
  - Estimated model: sonnet

### ADV011-T007 — Unified builder design (+ delta report)
- **ID**: ADV011-T007
- **Description**: Produce `research/builder-delta.md` per `design-unified-builder.md`. Classify every current `tools/verify/*`, `tools/codegen/*`, and `tools/visualizer/*` module with `KEEP | MERGE-INTO-HARNESS | RETIRE`. Specify the four canonical shared verify passes (`dag_acyclicity`, `opaque_primitive`, `numeric_interval`, `reference_exists`) and map each to the domain verifiers it replaces. Cite every builder-bucket dedup row.
- **Files**:
  - `.agent/adventures/ADV-011/research/builder-delta.md` (NEW)
- **Acceptance Criteria**:
  - File exists.
  - Every module under `ark/tools/verify/`, `ark/tools/codegen/` has a verdict row.
  - The four shared verify passes are each cited with at least one source domain verifier they replace.
- **Target Conditions**: TC-011, TC-012
- **Depends On**: ADV011-T003, ADV011-T004, ADV011-T005
- **Evaluation**:
  - Access requirements: Read `research/**`, `ark/tools/verify/**`, `ark/tools/codegen/**`, Write `research/`
  - Skill set: Z3 harness design, codegen pipeline architecture
  - Estimated duration: 25min
  - Estimated tokens: 60000
  - Estimated model: sonnet

### ADV011-T008 — Unified controller design (+ delta report)
- **ID**: ADV011-T008
- **Description**: Produce `research/controller-delta.md` per `design-unified-controller.md`. Classify every current `tools/agent/*`, `tools/evolution/*`, `tools/visual/review_loop.py`, and `.agent/telemetry/*` module with `KEEP | MERGE | RETIRE`. Specify the event bus with event kinds, the state model (persistent memory / metrics rows / adventure log), and the reflexive-dogfooding validation practice. Explicitly merge ADV-010's telemetry capture into the controller (not sibling).
- **Files**:
  - `.agent/adventures/ADV-011/research/controller-delta.md` (NEW)
- **Acceptance Criteria**:
  - File exists.
  - Every controller-adjacent module has a verdict row.
  - ADV-010 designs are cited for telemetry integration.
  - Every controller-bucket dedup row is cited.
- **Target Conditions**: TC-013, TC-014
- **Depends On**: ADV011-T003, ADV011-T004, ADV011-T005
- **Evaluation**:
  - Access requirements: Read `research/**`, `ark/tools/agent/**`, `ark/tools/evolution/**`, `.agent/telemetry/**`, `.agent/adventures/ADV-010/**`, Write `research/`
  - Skill set: runtime architecture, event systems, telemetry
  - Estimated duration: 25min
  - Estimated tokens: 60000
  - Estimated model: sonnet
