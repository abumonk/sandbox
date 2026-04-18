# Plan — Wave B: Classify + Deduplicate

## Designs Covered
- design-concept-mapping
- design-deduplication-matrix

## Tasks

### ADV011-T003 — Classify every concept into descriptor/builder/controller/out-of-scope
- **ID**: ADV011-T003
- **Description**: Consume `research/concept-inventory.md`. For each concept, apply the classification rules from `design-concept-mapping.md` and record a row in `research/concept-mapping.md`. Every row carries exactly one bucket tag. Any multi-source concept gets a single row listing all sources in `source_adventure`. Include a `## Per-Bucket Rationale` trailing section (4 paragraphs).
- **Files**:
  - `.agent/adventures/ADV-011/research/concept-mapping.md` (NEW)
- **Acceptance Criteria**:
  - File exists with master table + per-bucket rationale section.
  - Every inventory row is represented in the mapping (enforced by T011 test_mapping_completeness).
  - Every bucket tag comes from the fixed set of four.
- **Target Conditions**: TC-003, TC-004
- **Depends On**: ADV011-T001
- **Evaluation**:
  - Access requirements: Read `research/concept-inventory.md`, `designs/`, Write `research/`
  - Skill set: taxonomy design, systems classification, opinionated writing
  - Estimated duration: 25min
  - Estimated tokens: 55000
  - Estimated model: sonnet

### ADV011-T004 — Deduplication matrix with canonical forms
- **ID**: ADV011-T004
- **Description**: Produce `research/deduplication-matrix.md` per `design-deduplication-matrix.md`. Seed with the 6 identified duplications (Z3 ordinals, dual Lark+Pest, telemetry, PASS_OPAQUE, reflexive dogfooding, Skill definitions). Scan the mapping for additional multi-source concepts; either include them as matrix rows or justify as non-duplicates under `## Not Duplicates`. Each matrix row carries canonical_form, assigned_bucket, unification_action.
- **Files**:
  - `.agent/adventures/ADV-011/research/deduplication-matrix.md` (NEW)
- **Acceptance Criteria**:
  - File exists.
  - At least the 6 seed rows present (grep-verifiable).
  - Every row has non-empty canonical_form and unification_action.
- **Target Conditions**: TC-005, TC-006
- **Depends On**: ADV011-T003
- **Evaluation**:
  - Access requirements: Read `research/concept-mapping.md`, Write `research/`
  - Skill set: pattern recognition, cross-adventure synthesis
  - Estimated duration: 20min
  - Estimated tokens: 40000
  - Estimated model: sonnet
