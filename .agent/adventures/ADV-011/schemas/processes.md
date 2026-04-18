# Processes — ADV-011

## HarvestProcess
1. For each adventure in ADV-001..008 + ADV-010: read manifest `## Concept`
   and `## Target Conditions` columns.
2. For each stdlib `.ark` file under `ark/dsl/stdlib/`: extract item kinds and
   struct/enum names.
3. Append one row per raw concept to `research/concept-inventory.md`.
Error paths: missing manifest file (abort with clear error), empty concept
section (log warning and continue).

## ClassifyProcess
1. Consume `concept-inventory.md`.
2. For each row, apply the bucket decision rule from
   `design-concept-mapping.md`.
3. Write one row per concept into `research/concept-mapping.md`.
Error paths: ambiguous bucket (escalate — the design says every concept
resolves to one bucket; a true ambiguity is a design bug).

## DeduplicateProcess
1. Read `concept-mapping.md`.
2. Group rows by semantic equivalence using the seed signals in
   `design-deduplication-matrix.md` (Z3 ordinals, dual grammar, telemetry,
   PASS_OPAQUE, reflexive dogfooding, Skill).
3. Emit `research/deduplication-matrix.md` with one row per duplicated
   concept.
4. For any multi-source concept not in the matrix, append an entry under
   `## Not Duplicates` with a justification.

## PruneProcess
1. Read the `bucket = out-of-scope` rows of the mapping.
2. For each, write a catalog row with `disposition` set to either
   `OUT-OF-SCOPE → ADV-NN` (and name the downstream adventure) or `DROP` (with
   a ≥ 40-char justification).
3. Cross-check: every `OUT-OF-SCOPE → ADV-NN` disposition has a matching
   entry in the downstream plan.

## UnifyProcess
1. Consume all three inputs (mapping, dedup, prune).
2. For each bucket, produce the unified design (descriptor, builder,
   controller) citing source adventures and dedup/prune rows.
3. Each design explicitly references the concepts from its bucket.

## ValidateProcess
1. Read every source TC from ADV-001..008.
2. Assign each TC a verdict: COVERED-BY / RETIRED-BY / DEFERRED-TO.
3. Produce `research/validation-coverage.md` and
   `research/validation-report.md`.
4. Assert `covered + retired + deferred = total`.

## DownstreamPlanProcess
1. Derive downstream adventures from unified designs + pruning catalog.
2. Emit `research/downstream-adventure-plan.md` with 3–6 sketches.
3. Ensure every `OUT-OF-SCOPE → ADV-NN` disposition in the pruning catalog
   references an adventure listed here.
