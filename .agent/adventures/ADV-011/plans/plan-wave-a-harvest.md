# Plan — Wave A: Harvest + Test Strategy

## Designs Covered
- design-concept-mapping (inventory half)
- design-test-strategy (early test-strategy authoring)

## Tasks

### ADV011-T001 — Harvest ADV-001..008 + ADV-010 into concept inventory
- **ID**: ADV011-T001
- **Description**: Read each manifest under `.agent/adventures/ADV-00{1..8}/manifest.md` and `.agent/adventures/ADV-010/manifest.md`. Read each `reviews/adventure-report.md` when present. Read the corresponding stdlib `.ark` files under `ark/dsl/stdlib/`. Produce `research/concept-inventory.md` listing every concept (item kind, struct/enum, runtime module, research artefact) tagged with source adventure + source artefact. Table columns per `schemas/entities.md#ConceptInventoryRow`.
- **Files**: 
  - `.agent/adventures/ADV-011/research/concept-inventory.md` (NEW)
- **Acceptance Criteria**:
  - File exists and is non-empty.
  - Contains at least one row per adventure in ADV-001..008 + ADV-010.
  - Every row has all four columns populated.
- **Target Conditions**: TC-001, TC-002
- **Depends On**: none
- **Evaluation**:
  - Access requirements: Read `.agent/adventures/**`, Read `ark/dsl/stdlib/**`, Write `research/`
  - Skill set: reading source manifests, tabular writing, Ark DSL literacy
  - Estimated duration: 25min
  - Estimated tokens: 55000
  - Estimated model: sonnet

### ADV011-T002 — Design test strategy for Ark Core Unification
- **ID**: ADV011-T002
- **Description**: Design automated tests covering every target condition with `proof_method: autotest`. Produce `tests/test-strategy.md` with the TC → proof-command mapping. Specify the `run-all.sh` CI aggregator structure and the two `unittest` files (`test_coverage_arithmetic.py`, `test_mapping_completeness.py`). For each `poc` TC, document the justification inline.
- **Files**:
  - `.agent/adventures/ADV-011/tests/test-strategy.md` (NEW)
- **Acceptance Criteria**:
  - File exists.
  - Every TC in the manifest is listed with its proof-command string.
  - Every `poc` TC has a justification sentence.
- **Target Conditions**: TC-TS-1
- **Depends On**: none (test design runs in parallel with harvest)
- **Evaluation**:
  - Access requirements: Read `designs/`, `schemas/`, Write `tests/`
  - Skill set: test-to-requirement mapping, shell + stdlib unittest
  - Estimated duration: 15min
  - Estimated tokens: 22000
  - Estimated model: sonnet
