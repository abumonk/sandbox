# Deduplication Matrix — Design

## Overview

Identifies concepts that appear under different names across ADV-001..008 and
ADV-010, and collapses each set to a single canonical form. The deliverable is
a matrix document with one row per duplicated concept showing every source
adventure and the agreed canonical form.

## Target Files

- `.agent/adventures/ADV-011/research/deduplication-matrix.md` — matrix +
  rationale. NEW.

## Approach

Seed the matrix with the six explicit duplications identified in the concept
notes (see below). For each row, the matrix records:

- `concept` — canonical concept label
- `sources` — list of `(adventure_id, local_name)` pairs
- `canonical_form` — single agreed name + brief shape (e.g. function signature,
  Z3 pass id, schema struct name)
- `assigned_bucket` — one of descriptor/builder/controller (imported from the
  mapping)
- `unification_action` — what happens in the downstream work (e.g. "promote to
  stdlib primitive", "hoist into shared verifier plugin", "collapse two Z3
  functions into one")

Seed rows (planner may discover more during harvest):

1. **DAG acyclicity via Z3 ordinals** — ADV-003 (studio escalation) + ADV-006
   (visual_review cycles). Canonical form: single `verify.dag_acyclicity(node_kind,
   edge_kind)` plugin in the builder.
2. **Dual Lark+Pest grammar maintenance** — ADV-001..006, ADV-008 (as a pattern
   rather than a spec). Canonical form: a single grammar authoring contract in
   the descriptor (one source of truth, both targets generated or hand-mirrored
   with a parity test).
3. **Telemetry / metrics capture** — ADV-001, 002, 005, 006 (listed as
   *unsolved* in each), solved in ADV-010. Canonical form: ADV-010's
   `capture.py` + cost model + aggregator in the controller.
4. **PASS_OPAQUE Z3 pattern** — introduced in ADV-002, reused in ADV-003, 004,
   006, 008. Canonical form: single `verify.opaque_primitive(name, kind)`
   registrar in the builder.
5. **Reflexive dogfooding** — ADV-002 (self-indexing), ADV-004
   (evolution_skills.ark), ADV-005 (hermes_skills.ark), ADV-008 (sibling
   package). Canonical form: a recurring *technique* documented in the
   controller unified design (validation-by-consumption). Not a duplicated
   entity; duplicated *practice*.
6. **Skill definitions** — ADV-003 (studio roles' skills), ADV-004
   (`evolution_target` over skills), ADV-005 (`skill_manager`,
   `skill_generation`). Canonical form: single `Skill` struct in the descriptor
   + single `skill_manager` runtime in the controller.

Additional likely rows (planner discovers during harvest):

7. **Role / agent terminology** — ADV-003 `role`, ADV-005 `agent` + `persona` —
   reconcile or keep both with explicit mapping.
8. **Event / hook terminology** — ADV-003 `hook`, ADV-010 `SubagentStop` hook.
9. **Review cycle** — ADV-006 `visual_review` vs ADV-004 human-in-loop PR gate.

Completeness check: every concept with multiple sources in
`concept-mapping.md` must appear in this matrix, either as its own row or
justified-as-distinct in a trailing `## Not Duplicates` section.

## Dependencies

- `design-concept-mapping.md` (consumer of its mapping output).

## Target Conditions

- Matrix contains at least the 6 seed duplications plus every multi-source
  concept from the mapping.
- Every row has a non-empty `canonical_form` and `unification_action`.
- Every multi-source concept from `concept-mapping.md` is accounted for (either
  in the matrix or in `## Not Duplicates`).
