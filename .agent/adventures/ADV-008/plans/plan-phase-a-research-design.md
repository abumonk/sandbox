# Phase A — Research & Design

## Designs Covered
- adr-001-shape-grammar-as-external-consumer
- design-shape-grammar-package (kickoff)

## Tasks

### ShapeML upstream research
- **ID**: ADV008-T01
- **Description**: Read the upstream ShapeML repo (`https://github.com/stefalie/shapeml`) and produce `.agent/adventures/ADV-008/research/shapeml-architecture.md` (≥6 H2 sections covering: architecture, grammar surface, runtime, compiler pipeline, file format, key abstractions). Note explicitly which features map directly to existing Ark constructs and which would force an Ark extension (so we know what to verify in T02).
- **Files**: `.agent/adventures/ADV-008/research/shapeml-architecture.md`
- **Acceptance Criteria**:
  - File exists with ≥6 `## ` headings.
  - Each ShapeML core abstraction (Shape, Rule, Module, Operation, Scope) has a "maps to Ark as ..." paragraph.
  - At least one explicit "would require Ark extension" callout if any.
- **Target Conditions**: TC-15
- **Depends On**: []
- **Evaluation**:
  - Access requirements: WebSearch, WebFetch (github.com/stefalie/shapeml), Write (research/)
  - Skill set: research, technical writing, C++ literacy
  - Estimated duration: 25min
  - Estimated tokens: 45000

### Test strategy for ADV-008
- **ID**: ADV008-T02
- **Description**: Design automated tests covering all target conditions with `proof_method: autotest`. Create `.agent/adventures/ADV-008/tests/test-strategy.md`. Define test files (one per concern: ir, verifier, evaluator, semantic, integrations, examples), pytest commands, and a TC-ID → test-function table. Mandatory test design task.
- **Files**: `.agent/adventures/ADV-008/tests/test-strategy.md`
- **Acceptance Criteria**:
  - Every TC with `proof_method: autotest` has at least one named test function.
  - Every test file in `shape_grammar/tests/` listed in design has a planned function set.
  - Pytest invocation commands documented per file.
- **Target Conditions**: TC-16, TC-22 (test design itself), and indirectly all autotest TCs
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read (designs/, schemas/), Write (tests/test-strategy.md)
  - Skill set: pytest, test design
  - Estimated duration: 20min
  - Estimated tokens: 30000

### Ark-as-host feasibility study
- **ID**: ADV008-T03
- **Description**: Read Ark's parser, verifier, codegen, stdlib, and existing islands (`code_graph.ark`, `agent_system.ark`, `evolution_skills.ark`). Verify that every shape-grammar entity in the schemas can be expressed in vanilla Ark syntax. Produce `.agent/adventures/ADV-008/research/ark-as-host-feasibility.md` documenting: per-entity feasibility, any inexpressible constructs, recommended workarounds (verbosity is acceptable). This is the **gate** for proceeding to Phase B.
- **Files**: `.agent/adventures/ADV-008/research/ark-as-host-feasibility.md`
- **Acceptance Criteria**:
  - Every entity in `schemas/entities.md` has a feasibility verdict (EXPRESSIBLE / NEEDS_WORKAROUND / BLOCKED).
  - Zero BLOCKED entities (if any: stop, escalate to user — do not patch Ark).
  - Workaround patterns documented for any NEEDS_WORKAROUND.
- **Target Conditions**: TC-18, TC-10 (informs)
- **Depends On**: [ADV008-T01, ADV008-T02]
- **Evaluation**:
  - Access requirements: Read (R:/Sandbox/ark/**), Write (research/)
  - Skill set: Ark DSL, Z3, Python parser internals
  - Estimated duration: 30min
  - Estimated tokens: 50000
