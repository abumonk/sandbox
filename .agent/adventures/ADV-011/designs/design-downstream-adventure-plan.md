# Downstream Adventure Plan — Design

## Overview

Produces the ordered list of downstream implementation adventures that realise
the unified design. Each downstream adventure gets a one-page sketch
(concept, scope, TCs implied, dependencies).

## Target Files

- `.agent/adventures/ADV-011/research/downstream-adventure-plan.md` —
  numbered adventure list with sketches. NEW.

## Approach

Starting from the three unified designs, produce 3–6 downstream adventures
plus any "out-of-scope parking" adventures required by the pruning catalog.

Seed list (planner may refine):

1. **ADV-DU Descriptor Unification**
   - Concept: collapse 9 stdlib files into the two-level primitives/domain
     layout; implement the single grammar authoring contract; keep Lark+Pest
     parity tests.
   - Scope: stdlib reorganisation, grammar consolidation, AST normalisation,
     parser refactor. Implementation. No new language features.
   - TCs implied: every `COVERED-BY: design-unified-descriptor` row in the
     validation matrix.
   - Depends on: none (merges into existing ark/).

2. **ADV-BC Builder Consolidation**
   - Concept: introduce `verify.Harness` with the four shared passes; port
     every domain verifier to the plugin interface; consolidate codegen into
     one pipeline with per-target emitters.
   - Scope: `tools/verify/` + `tools/codegen/` refactor; no new Z3 logic.
   - TCs implied: every `COVERED-BY: design-unified-builder` row.
   - Depends on: ADV-DU (needs unified AST).

3. **ADV-CC Controller Consolidation**
   - Concept: merge `tools/agent/*`, `tools/evolution/*`,
     `tools/visual/review_loop.py`, `.agent/telemetry/*` under one Controller
     spine with the named subsystems; wire the event bus; keep append-only
     jsonl for the event log.
   - Scope: controller runtime refactor; integrates ADV-010 telemetry; no new
     platform adapters.
   - TCs implied: every `COVERED-BY: design-unified-controller` row.
   - Depends on: ADV-DU + ADV-BC (needs unified descriptor+builder outputs).

4. **ADV-OP Out-of-Scope Parking**
   - Concept: archive / relocate everything in the pruning catalog with
     disposition `OUT-OF-SCOPE`. UI-adjacent (`screenshot_manager`,
     `visual_search`, `html_previewer` advanced modes) moves under a new
     `ark-ui/` sibling or gets deleted per row. Ecosystem artefacts from
     ADV-007 archived under a `_archive/` directory with a pointer file.
   - Scope: moves and deletions; no new capabilities.
   - TCs implied: every `RETIRED-BY: pruning-catalog` row has its source
     artefact actually moved or removed.
   - Depends on: ADV-DU/BC/CC (to ensure nothing surviving depends on pruned
     artefacts).

5. **ADV-CE Code Evolution (deferred)** — *optional; only if needed*
   - Concept: bring back the Darwinian optimizer mode that was pruned,
     properly implemented with git-organism + pytest guardrails.
   - Scope: optimizer plugin, guardrail integration, PR gate.
   - Depends on: ADV-CC.

6. **ADV-UI UI Sibling (deferred)** — *optional; only if required by future
   work*
   - Concept: the `ark-ui/` sibling package that houses the Electron/Pillow
     visual surfaces pruned here.
   - Depends on: none (sibling like shape_grammar/).

### Ordering constraint

`ADV-DU → ADV-BC → ADV-CC → ADV-OP` is strictly serial. ADV-CE and ADV-UI can
run after ADV-OP in any order.

### Budget envelope guidance

Each downstream adventure should target ≤20 tasks at sonnet rates (by analogy
with ADV-004/005). A rough budget envelope of $4–8 per downstream adventure is
realistic from ADV-001..008 actuals.

## Dependencies

- All three unified designs
- `design-pruning-catalog.md`
- `design-validation-against-tcs.md`

## Target Conditions

- The plan file exists with 3–6 numbered adventures at H2 (`## ADV-XX`) level.
- Every downstream adventure section lists at minimum: `Concept`, `Scope`,
  `Depends on`, `Est. task count`.
- The serial-ordering constraint is stated explicitly.
