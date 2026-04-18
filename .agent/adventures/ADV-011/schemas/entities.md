# Entities — ADV-011

This adventure is research/design; the "entities" here are the structured
rows of the deliverable documents, not runtime types.

## ConceptInventoryRow
- concept: string (non-empty)
- source_adventure: enum (ADV-001 | ADV-002 | ADV-003 | ADV-004 | ADV-005 | ADV-006 | ADV-007 | ADV-008 | ADV-010)
- source_artefact: string (manifest section, stdlib file, or design doc)
- description: string (≤ 200 chars)

## ConceptMappingRow
- concept: string
- source_adventure: one or many source adventures
- bucket: enum (descriptor | builder | controller | out-of-scope)
- canonical_name: string (post-dedup name)
- notes: string (optional)

## DeduplicationMatrixRow
- concept: string (canonical label)
- sources: list of (adventure_id, local_name)
- canonical_form: string (signature / struct name / pass id)
- assigned_bucket: enum (descriptor | builder | controller)
- unification_action: string
- Relations: every `sources[i].adventure_id` must match a row in
  `concept-mapping.md` with the same concept.

## PruningCatalogRow
- concept: string
- source_adventure: ADV-id
- justification: string (≥ 40 chars)
- disposition: enum (`OUT-OF-SCOPE → ADV-NN` | `DROP`)
- owner_risk: string

## ValidationCoverageRow
- tc_id: string (e.g. "ADV-003 TC-005")
- source_description: string
- verdict: enum (COVERED-BY | RETIRED-BY | DEFERRED-TO)
- target: string (design-doc + section anchor, pruning catalog row, or
  downstream ADV-NN)

## DownstreamAdventureSketch
- adv_id: string (e.g. "ADV-DU")
- title: string
- concept: paragraph
- scope: bullet list
- depends_on: list of ADV-ids
- est_task_count: integer
