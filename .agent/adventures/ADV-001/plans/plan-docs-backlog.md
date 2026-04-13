# Plan: Documentation & Backlog Integration

## Designs Covered
- 01_dsl_surface (user-facing documentation)
- All others (backlog entries so auto-tick knows the work is tracked)

## Tasks

### Extend DSL_SPEC.md with Expression & Predicate subsystem
- **ID**: ADV001-T031
- **Description**: Append a new section "Expression and Predicate subsystem" to
  `R:/Sandbox/ark/docs/DSL_SPEC.md` documenting: the `expression` and `predicate` top-level
  items, the `|>` pipe operator and its precedence, parameter reference classes (`@var`,
  `[a.b]`, `#items[0]`, `{nested}`), examples from stdlib, and the opaque-primitive rule
  for verification. Include one worked example showing the full pipeline (parse → verify →
  codegen).
- **Files**:
  - `R:/Sandbox/ark/docs/DSL_SPEC.md`
- **Acceptance Criteria**:
  - New section present, at least 60 lines
  - Headline examples (`x |> clamp(0, 30)`, `name |> starts-with("Nik")`) included
  - Cites the stdlib files `dsl/stdlib/expression.ark` and `dsl/stdlib/predicate.ark`
- **Target Conditions**: TC-029
- **Depends On**: [ADV001-T011, ADV001-T020]
- **Evaluation**:
  - Access requirements: Edit DSL_SPEC.md
  - Skill set: technical writing, Ark DSL
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Register work in specs/meta/backlog.ark
- **ID**: ADV001-T032
- **Description**: Add a task entry to `R:/Sandbox/ark/specs/meta/backlog.ark` referencing
  this adventure (status: done once all upstream tasks complete). Follow the existing
  backlog entry format; set priority to match current priority tier.
- **Files**:
  - `R:/Sandbox/ark/specs/meta/backlog.ark`
- **Acceptance Criteria**:
  - New task entry parses (`python ark.py verify specs/meta/backlog.ark` green)
  - Increments `total_count`
- **Target Conditions**: TC-030
- **Depends On**: [ADV001-T029]
- **Evaluation**:
  - Access requirements: Read+Edit backlog.ark, Bash
  - Skill set: Ark DSL, backlog conventions
  - Estimated duration: 10min
  - Estimated tokens: 15000
