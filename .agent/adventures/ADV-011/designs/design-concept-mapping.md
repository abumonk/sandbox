# Concept Mapping: ADV-001..008 → Core Ark Roles — Design

## Overview

This design specifies the deliverable that classifies every concept introduced
in ADV-001..008 into exactly one of four buckets: **descriptor**, **builder**,
**controller**, or **out-of-scope**. The output is a single markdown file under
`research/concept-mapping.md` containing a master table plus a rationale
paragraph per bucket.

The mapping is the first structural artefact of this adventure and is the basis
for downstream deduplication (design-deduplication-matrix), pruning
(design-pruning-catalog), and the three unified designs.

## Target Files

- `.agent/adventures/ADV-011/research/concept-mapping.md` — master table +
  per-bucket rationale. NEW.
- `.agent/adventures/ADV-011/research/concept-inventory.md` — raw per-adventure
  concept list (ADV-001..008 + ADV-010). NEW. This is the precursor feed for the
  mapping table.

## Approach

1. Harvest raw concepts per adventure by reading each manifest's
   `## Concept`, `## Target Conditions` (column `Description`), and stdlib
   artifact under `ark/dsl/stdlib/*.ark`. Record in `concept-inventory.md`.
2. Define the four buckets:
   - **Descriptor**: DSL surface — grammar rules, AST nodes, schema structs,
     parsers (Lark + Pest), stdlib `.ark` files, item kinds.
   - **Builder**: transformation layer — codegen modules, verifiers (Z3 passes,
     invariants, PASS_OPAQUE usage), visualisers, impact/diff tools.
   - **Controller**: runtime surface — gateway, skill-manager, scheduler,
     evaluator, self-evolution loop, telemetry capture (ADV-010), event
     contracts, execution backends, learning.
   - **Out-of-scope**: everything else (UI/Electron, ecosystem roadmap
     artefacts, sibling-package semantics, speculative optimisers, visual
     screenshot surfaces, etc.) — each row carries a one-line pointer to a
     future adventure or "DROP" tag.
3. For each concept in `concept-inventory.md`, produce a row in
   `concept-mapping.md` with columns:
   `concept | source_adventure | bucket | canonical_name | notes`.
4. Every row's `bucket` field must equal exactly one of
   `{descriptor, builder, controller, out-of-scope}`. No multi-bucket rows.
5. Completeness check: after mapping, count concepts per adventure in the
   mapping table vs the inventory; assert equal counts (an autotest enforces
   this).

## Dependencies

None — this is the foundational design. Downstream designs consume its output.

## Target Conditions

- Every concept in `concept-inventory.md` appears in exactly one row of
  `concept-mapping.md`.
- Every row carries a valid bucket tag from the fixed set.
- Every out-of-scope row carries either a future-adventure pointer or a `DROP`
  tag.
- The mapping covers ADV-001..008 + ADV-010 (ADV-007 ecosystem artefacts enter
  as a single `out-of-scope: ecosystem` row, not per concept).
