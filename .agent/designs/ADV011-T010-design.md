# ADV011-T010 Downstream Adventure Plan — Design

## Approach

The T010 deliverable `research/downstream-adventure-plan.md` is a structured
roadmap: 3–6 H2 adventure sketches plus a single `## Ordering Constraint`
H2 that pins the mandatory serial chain. The core four (ADV-DU, ADV-BC,
ADV-CC, ADV-OP) are always present; the optional two (ADV-CE, ADV-UI) are
admitted only when upstream artefacts (T005 pruning catalog, T009
validation coverage matrix) explicitly demand them.

The design below specifies the exact schema so the implementer
(core-synthesist, sonnet) can produce the file deterministically and so
TC-017 and TC-018 grep-level autotests pass on first run.

## Target Files

- `.agent/adventures/ADV-011/research/downstream-adventure-plan.md` — NEW.
  Structured markdown, H2 per adventure, H3 per required field, one
  `## Ordering Constraint` H2, optional `## Excluded (not scheduled)` H2.

## H2 Adventure Section Schema

### Heading form

Each adventure section MUST begin with an H2 of exact form:

```
## ADV-<CODE> <Human Title>
```

where `<CODE>` ∈ {`DU`, `BC`, `CC`, `OP`, `CE`, `UI`}. Only these six
codes are admissible. The heading matches `^## ADV-` (TC-017 counter).

### Required four fields (H3 subsections)

Within each H2 section, these four H3 subsections appear in this fixed
order:

1. `### Concept` — one paragraph stating what the adventure accomplishes
   in terms of the three core roles (descriptor / builder / controller)
   and which unified design it realises.
2. `### Scope` — bullet list naming directories, modules, stdlib files,
   or artefact classes modified. Must include either
   "No new capabilities." or an enumerated list of allowed new
   capabilities. 3–8 bullets recommended.
3. `### Depends on` — comma-separated list of upstream ADV-XX ids from
   this plan, or the literal `none`. Must match the dependency
   consistency rules below.
4. `### Est. task count` — integer or short range (e.g. `8–12`) with a
   one-line rationale. Must respect the ≤20 tasks / adventure ceiling
   from the overarching design-downstream-adventure-plan.md.

Optional H3 subsections (`### Notes`, `### TCs implied`) are permitted
after the four required ones but carry no scoring weight.

### Dependency consistency rules

Each admitted adventure's `### Depends on` field must satisfy:

| Adventure | Depends on |
|-----------|------------|
| ADV-DU    | none |
| ADV-BC    | ADV-DU |
| ADV-CC    | ADV-DU, ADV-BC |
| ADV-OP    | ADV-DU, ADV-BC, ADV-CC |
| ADV-CE    | ADV-CC (if admitted) |
| ADV-UI    | none (sibling package; scheduled after ADV-OP per ordering) |

Any deviation must be justified in a `### Notes` subsection under the
offending adventure.

## Serial-Ordering Constraint

A dedicated H2 section `## Ordering Constraint` MUST contain, on one
physical line, the canonical sentence:

```
The four mandatory adventures are strictly serial: ADV-DU → ADV-BC → ADV-CC → ADV-OP.
```

This sentence exists solely to satisfy **TC-018**:
`grep -qE "ADV-DU.*ADV-BC.*ADV-CC.*ADV-OP" downstream-adventure-plan.md`.
The four ids appear left-to-right on one line with any separators; using
the Unicode arrow `→` matches the wording used by the overarching
design and the wave-E plan.

A second line in the same section states the optional-adventure
ordering rule:

```
ADV-CE and ADV-UI, if admitted, are scheduled after ADV-OP in any order.
```

The `## Ordering Constraint` heading does NOT start with `ADV-` and
therefore does NOT inflate the TC-017 H2 counter.

## 3-vs-6 Count Decision Rules

The final count of H2 `## ADV-` sections is determined by the following
admission matrix, in priority order:

### Floor = 4 (mandatory core)

ADV-DU, ADV-BC, ADV-CC, ADV-OP are ALWAYS present. They are the
realisation adventures for the three unified designs plus the
out-of-scope parking step required by the pruning catalog. Count
cannot go below 4.

### ADV-CE admission rule

Admit ADV-CE iff at least one of:

- `research/validation-coverage.md` contains a row with verdict
  `DEFERRED-TO: ADV-CE`.
- `research/pruning-catalog.md` contains a row with disposition
  `OUT-OF-SCOPE → ADV-CE`.

Otherwise ADV-CE is excluded. Rationale: validation coverage evidence
that some ADV-001..008 TC is intentionally parked for future code
evolution work, or pruning catalog evidence that a Hermes / evolution
artefact is relocated rather than dropped, creates a concrete
downstream anchor. If all Hermes artefacts carry `DROP` disposition
and no TC defers to ADV-CE, the optimizer work is speculative and
should not be scheduled from this adventure.

### ADV-UI admission rule

Admit ADV-UI iff at least one of:

- `research/validation-coverage.md` contains a row with verdict
  `DEFERRED-TO: ADV-UI`.
- `research/pruning-catalog.md` contains at least one row with
  disposition `OUT-OF-SCOPE → ADV-UI` for a UI-adjacent artefact
  (candidates: `screenshot_manager`, `visual_search` advanced modes,
  `html_previewer` advanced modes, Electron / Pillow surfaces from
  ADV-006).

Otherwise ADV-UI is excluded.

### Ceiling = 6

The plan MUST NOT introduce adventures outside {DU, BC, CC, OP, CE, UI}.
If T009 emits a `DEFERRED-TO: ADV-XX` id that is not one of these six,
the implementer escalates to the lead agent and logs a planning gap;
they do NOT silently invent a seventh adventure.

### Concrete outcomes

- Both optionals excluded → count = 4.
- One optional admitted → count = 5.
- Both optionals admitted → count = 6.

All three outcomes satisfy TC-017 (`3 ≤ count ≤ 6`). The lower bound 3
is inherited from the overarching design; in practice the floor-of-4
rule always yields at least 4.

## Excluded Adventures Subsection

If either ADV-CE or ADV-UI is excluded, the plan ends with:

```
## Excluded (not scheduled)

- **ADV-CE Code Evolution** — <one-line rationale citing the
  validation-coverage row(s) or pruning-catalog row(s) that justify
  exclusion; e.g., "no DEFERRED-TO: ADV-CE in validation-coverage.md
  and all Hermes rows in pruning-catalog.md carry DROP disposition">.
- **ADV-UI UI Sibling** — <same pattern>.
```

The `## Excluded (not scheduled)` H2 does NOT start with `ADV-` and is
invisible to the TC-017 counter.

## Implementation Steps

1. Read `.agent/adventures/ADV-011/designs/design-downstream-adventure-plan.md`
   (seed list).
2. Read `.agent/adventures/ADV-011/research/validation-coverage.md`
   (produced by T009) and collect the set of distinct `DEFERRED-TO:
   ADV-XX` ids appearing in verdict cells.
3. Read `.agent/adventures/ADV-011/research/pruning-catalog.md`
   (produced by T005) and collect all `OUT-OF-SCOPE → ADV-XX`
   dispositions and all `DROP` rows for Hermes / UI artefacts.
4. Apply the admission rules above to decide whether ADV-CE and/or
   ADV-UI are admitted.
5. Write the 4 mandatory H2 sections in order: ADV-DU, ADV-BC, ADV-CC,
   ADV-OP. Each with the four H3 fields populated by refining the seed
   bullets from the overarching design. Cite COVERED-BY anchors from
   the validation matrix where relevant in `### Notes`.
6. If admitted, write ADV-CE and/or ADV-UI H2 sections after ADV-OP in
   that order.
7. Write the `## Ordering Constraint` H2 with the canonical sentence
   and the optional-ordering rule.
8. If either optional was excluded, write the
   `## Excluded (not scheduled)` subsection with rationales.
9. Self-check with the two TC grep commands before marking the task
   done.

## Testing Strategy

Two autotests, codified in the adventure manifest:

- **TC-017**: `c=$(grep -cE "^## ADV-" research/downstream-adventure-plan.md); [ "$c" -ge 3 ] && [ "$c" -le 6 ]`.
- **TC-018**: `grep -qE "ADV-DU.*ADV-BC.*ADV-CC.*ADV-OP" research/downstream-adventure-plan.md`.

Additional non-scored self-checks the implementer should run before
committing:

- Exactly one `## Ordering Constraint` H2 exists.
- Each `## ADV-XX …` section is followed by four H3 subsections in
  order: `### Concept`, `### Scope`, `### Depends on`,
  `### Est. task count`.
- Every `DEFERRED-TO: ADV-XX` id harvested from
  `validation-coverage.md` has a matching H2 section in the plan
  (no dangling deferrals).

## Risks

- **R1: T009 matrix not yet available when T010 runs.** Mitigation:
  T010 depends_on T009; the task runner should not dispatch T010
  until T009 is in `review` or `done`. If T009 is incomplete, T010
  blocks and logs `blocked: T009 not done` rather than guessing the
  DEFERRED-TO set.
- **R2: Writer silently introduces a seventh adventure.** Mitigation:
  admission allowlist {DU, BC, CC, OP, CE, UI} is enforced by design;
  any other id must escalate. No grep-level autotest catches this, so
  a human review gate exists at adventure review stage.
- **R3: Serial-ordering sentence uses em-dash or wrong separator and
  TC-018 regex still passes but semantic intent drifts.** Mitigation:
  the canonical sentence is fixed verbatim in this design. The regex
  is deliberately lax (any characters between ids) so the writer has
  some typographic freedom, but the design pins the wording.
- **R4: Optional-adventure rationale is vague ("might need UI later").**
  Mitigation: admission rules are strictly tied to T005 / T009
  artefact rows; rationale lines must cite the specific row by number
  or verdict, not speculative need.

## Out of Scope

- Writing task-level decomposition for each downstream adventure.
- Recomputing token / cost budgets (the envelope is stated once in the
  overarching design and cited, not re-derived).
- Scheduling calendar dates. The plan is a dependency DAG, not a Gantt
  chart.
