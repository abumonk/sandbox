# Phase B — Spec Island

## Designs Covered
- design-shape-grammar-package (specs/)
- design-semantic-rendering (semantic entities)

## Tasks

### Author shape_grammar.ark spec island
- **ID**: ADV008-T04
- **Description**: Write `shape_grammar/specs/shape_grammar.ark` declaring the core entities (Shape, Rule, Operation abstraction, Scope, ShapeGrammar island) using **existing Ark syntax only** — no new keywords, no new AST nodes. Mirror the structure in `schemas/entities.md`. The island must parse with vanilla `ark parse` and verify with vanilla `ark verify`.
- **Files**: `shape_grammar/specs/shape_grammar.ark`
- **Acceptance Criteria**:
  - `python ark/ark.py parse shape_grammar/specs/shape_grammar.ark` exits 0.
  - `python ark/ark.py verify shape_grammar/specs/shape_grammar.ark` exits 0.
  - File contains `island ShapeGrammar { ... max_depth ... seed ... axiom ... }`.
  - File declares all 5 core entities from `schemas/entities.md`.
- **Target Conditions**: TC-01, TC-02
- **Depends On**: [ADV008-T03]
- **Evaluation**:
  - Access requirements: Read (ark/specs/, schemas/), Write (shape_grammar/specs/), Bash (`python ark/ark.py parse|verify`)
  - Skill set: Ark DSL authoring
  - Estimated duration: 25min
  - Estimated tokens: 40000

### Author operations.ark spec island
- **ID**: ADV008-T05
- **Description**: Write `shape_grammar/specs/operations.ark` declaring the 8 operation primitive classes (ExtrudeOp, SplitOp, CompOp, ScopeOp, IOp, TOp, ROp, SOp) as Ark `class` declarations subtyping a shared `Operation` abstraction. Each class declares the field set from `schemas/entities.md`.
- **Files**: `shape_grammar/specs/operations.ark`
- **Acceptance Criteria**:
  - `python ark/ark.py verify shape_grammar/specs/operations.ark` exits 0.
  - All 8 classes declared.
  - Each class has its field set from the schema.
- **Target Conditions**: TC-01, TC-02
- **Depends On**: [ADV008-T04]
- **Evaluation**:
  - Access requirements: Read (schemas/), Write (shape_grammar/specs/), Bash (`python ark/ark.py verify`)
  - Skill set: Ark DSL authoring
  - Estimated duration: 20min
  - Estimated tokens: 30000

### Author semantic.ark spec island
- **ID**: ADV008-T06
- **Description**: Write `shape_grammar/specs/semantic.ark` declaring `SemanticLabel` and `Provenance` classes per `schemas/entities.md`. Verifies under vanilla Ark.
- **Files**: `shape_grammar/specs/semantic.ark`
- **Acceptance Criteria**:
  - `python ark/ark.py verify shape_grammar/specs/semantic.ark` exits 0.
  - `SemanticLabel` and `Provenance` classes both present.
- **Target Conditions**: TC-01, TC-02
- **Depends On**: [ADV008-T04]
- **Evaluation**:
  - Access requirements: Read (schemas/), Write (shape_grammar/specs/), Bash (`python ark/ark.py verify`)
  - Skill set: Ark DSL authoring
  - Estimated duration: 15min
  - Estimated tokens: 22000
