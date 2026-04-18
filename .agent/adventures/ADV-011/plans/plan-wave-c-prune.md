# Plan — Wave C: Prune

## Designs Covered
- design-pruning-catalog

## Tasks

### ADV011-T005 — Pruning catalog with justifications
- **ID**: ADV011-T005
- **Description**: Produce `research/pruning-catalog.md` per `design-pruning-catalog.md`. Drive from the `bucket = out-of-scope` rows of `concept-mapping.md`. Seed the catalog with the 7 candidates from the adventure brief (Darwinian stub, screenshot/visual_search/html_previewer, ecosystem artefacts, master roadmap, shape_grammar content, Darwinian git-organism, MCP server catalog). Every row carries `justification (≥ 40 chars)`, `disposition`, `owner_risk`. Disposition is one of `OUT-OF-SCOPE → ADV-NN` or `DROP` — no other values permitted.
- **Files**:
  - `.agent/adventures/ADV-011/research/pruning-catalog.md` (NEW)
- **Acceptance Criteria**:
  - File exists.
  - Every out-of-scope row from the mapping appears in the catalog.
  - Every `OUT-OF-SCOPE → ADV-NN` disposition names an adventure that will be listed in T010's downstream plan.
  - Every `DROP` disposition carries a justification ≥ 40 chars.
- **Target Conditions**: TC-007, TC-008
- **Depends On**: ADV011-T003 (needs mapping buckets)
- **Evaluation**:
  - Access requirements: Read `research/concept-mapping.md`, Write `research/`
  - Skill set: prioritisation, architectural judgment
  - Estimated duration: 15min
  - Estimated tokens: 30000
  - Estimated model: sonnet
