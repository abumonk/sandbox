# Pruning Catalog — Design

## Overview

Produces the explicit catalog of everything introduced in ADV-001..008 that is
*not* part of the Ark core (descriptor/builder/controller). Each row carries a
justification and a disposition: `OUT-OF-SCOPE → future adventure N` or `DROP`.

## Target Files

- `.agent/adventures/ADV-011/research/pruning-catalog.md` — pruning table +
  justifications. NEW.

## Approach

Drive the catalog from the `bucket = out-of-scope` rows of
`concept-mapping.md`. For each row, record:

- `concept` — name
- `source_adventure` — ADV-id and artefact
- `justification` — why it is outside the three core roles
- `disposition` — `OUT-OF-SCOPE → ADV-NN` (with a working adventure title) OR
  `DROP` (with rationale why nothing downstream needs it)
- `owner_risk` — what breaks if we prune without replacement (e.g. "ADV-006 loses
  its Pillow annotator — but no core consumer depends on it")

Seed entries from the concept notes (planner may add/revise during harvest):

| concept | source | justification | disposition |
|---------|--------|---------------|-------------|
| Darwinian optimizer mode | ADV-004 | NotImplementedError stub; speculative; not required by gateway/skill-manager | DROP (replace with explicit `// phase-4 code-evolution` note in unified controller) |
| screenshot_manager, visual_search, html_previewer | ADV-006 | Electron/Pillow/Ollama UI-adjacent; no builder or controller dependency | OUT-OF-SCOPE → future `ark-ui` adventure |
| Phase 1-7 ecosystem research artefacts | ADV-007 | Planning about Claudovka ecosystem, not Ark core | DROP (already completed; archived; no forward reference) |
| 10-phase master roadmap | ADV-007 | Planning artefact; prescriptive for adventure sequencing only | DROP |
| shape_grammar/ package contents | ADV-008 | Specific ShapeML content; sibling-package pattern is core, content is not | OUT-OF-SCOPE → stays in sibling package (not pruned from repo; pruned from unified core design) |
| Darwinian git-organism evolver | ADV-004 | Future phase; not core | OUT-OF-SCOPE → future `ark-code-evolution` adventure |
| MCP server research catalog (14 servers) | ADV-007 | External tool planning; not Ark core | DROP |

The catalog must make explicit:

- Any row that **also** appears in the deduplication matrix: if its canonical
  form is core, the concept is *not* pruned — it is unified. The pruning
  catalog only contains rows that are *not* going to be unified into the core.
- Any row that requires a named future adventure: the future adventure must
  appear in the downstream plan (`design-downstream-adventure-plan.md`).

## Dependencies

- `design-concept-mapping.md`
- `design-deduplication-matrix.md`

## Target Conditions

- Every `bucket = out-of-scope` concept in the mapping has exactly one row in
  the catalog.
- Every `OUT-OF-SCOPE → ADV-NN` disposition references an adventure listed in
  the downstream plan.
- Every `DROP` disposition names a non-empty rationale (string must be ≥ 40
  chars — tests will grep).
