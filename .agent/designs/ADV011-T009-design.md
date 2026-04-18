# ADV011-T009 — Validate unified designs against ADV-001..008 TCs — Design

## Approach

Produce two research deliverables that together prove the unified descriptor /
builder / controller designs lose no capability from the eight source
adventures:

1. `research/validation-coverage.md` — a single flat matrix, one row per TC
   harvested from ADV-001..008, each row carrying exactly one of three
   verdicts: `COVERED-BY | RETIRED-BY | DEFERRED-TO` with a concrete
   traceability citation.
2. `research/validation-report.md` — a narrative summary of the matrix: total
   TC count, per-verdict breakdown, per-source-adventure breakdown, open gaps,
   and the closure arithmetic equation that T011's Python unittest will
   enforce (TC-016).

The design is deliberately paperwork-heavy: the value is traceability, not
invention. The implementing agent harvests rows mechanically with `grep`,
assigns verdicts by reading the unified delta designs and the pruning
catalog, and writes the two deliverables without introducing any new claim
that is not already present in those upstream artefacts.

## Target Files

- `.agent/adventures/ADV-011/research/validation-coverage.md` — NEW. The flat
  coverage matrix. One row per source TC. No blank verdicts (TC-015).
- `.agent/adventures/ADV-011/research/validation-report.md` — NEW. Narrative
  summary with counts, per-verdict and per-adventure breakdowns, open-gaps
  section, and the arithmetic invariant line that T011's
  `test_coverage_arithmetic.py` parses (TC-016).

## TC Harvesting — grep procedure

The eight source adventures do not all store their TCs in the same file.
Empirical survey:

| Source adventure | TC location | Expected TC count | Harvest regex |
|------------------|-------------|-------------------|---------------|
| ADV-001 | `.agent/adventures/ADV-001/manifest.md` § Target Conditions | 30 | `^\| TC-\d+ \|` |
| ADV-002 | `.agent/adventures/ADV-002/tests/test-strategy.md` (manifest table is empty) | 28 | `^\| TC-\d+ \|` |
| ADV-003 | `.agent/adventures/ADV-003/tests/test-strategy.md` (manifest table is empty) | 35 | `^\| TC-\d+ \|` |
| ADV-004 | `.agent/adventures/ADV-004/manifest.md` § Target Conditions | 46 | `^\| TC-\d+ \|` |
| ADV-005 | `.agent/adventures/ADV-005/manifest.md` § Target Conditions | 44 | `^\| TC-\d+ \|` |
| ADV-006 | `.agent/adventures/ADV-006/manifest.md` § Target Conditions | 37 | `^\| TC-\d+ \|` |
| ADV-007 | `.agent/adventures/ADV-007/manifest.md` § Target Conditions | 34 | `^\| TC-\d+ \|` |
| ADV-008 | `.agent/adventures/ADV-008/manifest.md` § Target Conditions | 24 | `^\| TC-\d+ \|` |
| **Total** | | **278** | |

Concrete grep commands (to be run by the implementing agent; reproduce the
exact per-adventure counts above before transcribing rows):

```bash
# Per-adventure TC extraction
for f in \
  .agent/adventures/ADV-001/manifest.md \
  .agent/adventures/ADV-002/tests/test-strategy.md \
  .agent/adventures/ADV-003/tests/test-strategy.md \
  .agent/adventures/ADV-004/manifest.md \
  .agent/adventures/ADV-005/manifest.md \
  .agent/adventures/ADV-006/manifest.md \
  .agent/adventures/ADV-007/manifest.md \
  .agent/adventures/ADV-008/manifest.md; do
  printf '%s  ' "$f"
  grep -cE '^\| TC-[0-9]+ \|' "$f"
done

# Full row extraction (TC-id + description) for transcription
grep -E '^\| TC-[0-9]+ \|' <source-file> | awk -F'\|' '{print $2 "|" $3}'
```

If a source TC table is ever moved between `manifest.md` and
`tests/test-strategy.md`, the implementing agent MUST re-run the count
commands and update this table before transcribing rows. The Python
unittest in T011 reads the per-adventure expected counts from this design
document's inline table (or, for robustness, re-grep at test time — see
"Coverage arithmetic invariant" below).

## Row schema for validation-coverage.md

Column order is fixed; T011's unittest depends on it.

```
| tc_id | source_adventure | source_description | verdict | citation |
```

Field rules:

- `tc_id` — string, format `TC-NNN`. Not unique across adventures (ADV-001
  TC-005 and ADV-003 TC-005 are different TCs), so the row is keyed by the
  pair `(source_adventure, tc_id)`. To keep the row unambiguous, the
  `tc_id` cell carries the prefix: `ADV-001 TC-005`.
- `source_adventure` — one of `ADV-001..ADV-008`.
- `source_description` — the original TC Description column, trimmed to one
  line, pipes escaped as `\|`.
- `verdict` — exactly one of the three enum values below. No blanks. No
  other values.
- `citation` — a single string whose syntax depends on the verdict (see
  "Citation syntax by verdict" below). Must never be empty.

Example rows:

```
| ADV-001 TC-001 | ADV-001 | .ark files can declare expression Name { in, out, chain } items producing Item::Expression | COVERED-BY | descriptor-delta.md#expression-and-predicate-items |
| ADV-006 TC-022 | ADV-006 | Visual surface mouse hit-test returns region within 50ms | RETIRED-BY | pruning-catalog.md row 4 |
| ADV-007 TC-030 | ADV-007 | MCP query surface returns impact set for entity across spec+code | DEFERRED-TO | ADV-OP |
```

### Citation syntax by verdict

| Verdict | Required citation form | Grep check | Example |
|---------|------------------------|------------|---------|
| `COVERED-BY` | `<delta-file>#<section-anchor>` where `<delta-file>` is one of `descriptor-delta.md`, `builder-delta.md`, `controller-delta.md` (all in `research/`) and `<section-anchor>` is a GitHub-style slug of an H2/H3 heading that MUST exist in that file | `grep -qE "^#+ " research/<delta-file>` with the slug resolving to a present heading | `descriptor-delta.md#expression-and-predicate-items` |
| `RETIRED-BY` | `pruning-catalog.md row <n>` where `<n>` is the 1-based row number in the pruning catalog matrix | `[ $n -le $(grep -cE "^\|.*\|.*\|.*\|OUT-OF-SCOPE\|DROP" research/pruning-catalog.md) ]` | `pruning-catalog.md row 4` |
| `DEFERRED-TO` | `<adv-id>` where `<adv-id>` is a downstream adventure id declared in `research/downstream-adventure-plan.md` (one of `ADV-DU`, `ADV-BC`, `ADV-CC`, `ADV-OP`, and optionally `ADV-CE`, `ADV-UI`) | `grep -qE "^## <adv-id>" research/downstream-adventure-plan.md` | `ADV-OP` |

Ordering constraint: `COVERED-BY` citations point into delta docs that
already exist (produced by T006/T007/T008). `RETIRED-BY` citations point
into `pruning-catalog.md` which exists after T005. `DEFERRED-TO` citations
point into `downstream-adventure-plan.md` which is produced by T010 —
because this task (T009) precedes T010, `DEFERRED-TO` citations are written
with the canonical downstream IDs (`ADV-DU | ADV-BC | ADV-CC | ADV-OP |
ADV-CE | ADV-UI`) as specified in `design-downstream-adventure-plan.md`.
T010 is then required to honour whatever `DEFERRED-TO` targets this task
introduced; if T009 uses an ID that T010 does not materialise, T011's test
will fail (see "Coverage arithmetic invariant").

## Structure of validation-report.md

Fixed section layout; T011's unittest parses specific headings and table
shapes.

```markdown
# Validation Report — ADV-001..008 → ADV-011 Unified Designs

## Summary
- Total source TCs: <total>
- COVERED-BY: <n_covered>
- RETIRED-BY: <n_retired>
- DEFERRED-TO: <n_deferred>
- Invariant: covered + retired + deferred = total  →  <n_covered> + <n_retired> + <n_deferred> = <total>   [PASS|FAIL]

## Per-verdict breakdown
| verdict | count | % of total |
|---------|-------|------------|
| COVERED-BY | ... | ... |
| RETIRED-BY | ... | ... |
| DEFERRED-TO | ... | ... |

## Per-source-adventure breakdown
| source_adventure | total_TCs | COVERED-BY | RETIRED-BY | DEFERRED-TO |
|------------------|-----------|------------|------------|-------------|
| ADV-001 | 30 | ... | ... | ... |
| ADV-002 | 28 | ... | ... | ... |
| ADV-003 | 35 | ... | ... | ... |
| ADV-004 | 46 | ... | ... | ... |
| ADV-005 | 44 | ... | ... | ... |
| ADV-006 | 37 | ... | ... | ... |
| ADV-007 | 34 | ... | ... | ... |
| ADV-008 | 24 | ... | ... | ... |
| **Total** | **278** | | | |

## Per-downstream-adventure deferral breakdown
| downstream_adv | count | TCs |
|----------------|-------|-----|
| ADV-DU | ... | list of `ADV-NNN TC-NNN` |
| ADV-BC | ... | ... |
| ADV-CC | ... | ... |
| ADV-OP | ... | ... |
| ADV-CE | ... | ... |
| ADV-UI | ... | ... |

## Open gaps
Bullet list. Each bullet names a TC (`ADV-NNN TC-NNN`) for which the verdict
is suspicious (e.g., `COVERED-BY` citing a section anchor whose heading is
weakly related, or `DEFERRED-TO` where the downstream adventure has not
been sized). If this section is empty, it MUST contain the single line
"None." so a grep for `## Open gaps` + next-section delta is deterministic.

## Methodology
Short paragraph — points at `design-validation-against-tcs.md` and this
task's design doc; names the grep commands used to harvest source TCs;
names the three delta docs + pruning catalog + downstream plan used to
assign verdicts.
```

## Coverage arithmetic invariant (enforced by T011)

Equation (MUST hold; T011 `test_coverage_arithmetic.py` enforces this):

```
covered + retired + deferred  ==  total_source_TCs
```

Where:
- `covered` = count of rows in `validation-coverage.md` with verdict
  `COVERED-BY`.
- `retired` = count of rows with verdict `RETIRED-BY`.
- `deferred` = count of rows with verdict `DEFERRED-TO`.
- `total_source_TCs` = sum over ADV-001..008 of
  `grep -cE '^\| TC-[0-9]+ \|' <source-file>` where `<source-file>` is
  resolved per the harvest table above.

T011 will implement `tests/test_coverage_arithmetic.py` as a stdlib
unittest with (at minimum) these assertions:

1. `test_total_equals_source_grep` — re-greps each source file at test
   time, sums the per-adventure counts, asserts `==` total row count in
   coverage matrix.
2. `test_no_blank_verdict` — every data row has a non-empty verdict cell
   matching `^(COVERED-BY|RETIRED-BY|DEFERRED-TO)$`.
3. `test_closure_sum` — covered + retired + deferred == total rows.
4. `test_every_covered_cites_existing_anchor` — for each `COVERED-BY` row,
   the slug in the citation resolves to an H2/H3 heading present in the
   named delta file.
5. `test_every_retired_row_exists_in_pruning_catalog` — the cited row
   number is within the pruning catalog's data-row range.
6. `test_every_deferred_id_in_downstream_plan` — the cited
   `ADV-XX` id appears as an H2 heading in
   `research/downstream-adventure-plan.md`.

(T011 is a separate task; this design ensures its test inputs are
well-formed by pinning the row schema above.)

## Implementation Steps (for the sonnet implementer, T009 assignee:
`core-synthesist`)

1. Run the per-adventure grep count commands in "TC Harvesting". Confirm
   the per-adventure totals match the table above (30+28+35+46+44+37+34+24
   = 278). If the environment produces different numbers, STOP and log
   the discrepancy in `validation-report.md § Open gaps` rather than
   silently rewriting the table.
2. For each source file, extract the raw TC rows with
   `grep -E '^\| TC-[0-9]+ \|' <source>` and transcribe `tc_id` +
   `source_description` into `validation-coverage.md` using the Row
   schema above. Prefix every `tc_id` with its source adventure id.
3. For every transcribed row, assign a verdict by reading:
   - `research/descriptor-delta.md`, `research/builder-delta.md`,
     `research/controller-delta.md` → candidates for `COVERED-BY`.
     Choose the nearest H2/H3 whose slug describes the capability.
   - `research/pruning-catalog.md` → candidates for `RETIRED-BY`. Cite
     the row number.
   - `research/concept-mapping.md` bucket `out-of-scope` and
     `design-downstream-adventure-plan.md` → candidates for
     `DEFERRED-TO`. Cite the downstream adventure id.
4. Fill the `citation` cell using the verdict-specific syntax. Never
   leave blank.
5. Compute the per-verdict and per-adventure counts; write
   `validation-report.md` per the fixed structure.
6. Self-check: manually run the six invariants listed above (counts
   balance; no blanks; all cited anchors exist). Fix before handoff.
7. Append to the task log and adventure.log.

## Testing Strategy

- TC-015 proof command: `test -f validation-coverage.md && ! grep -E '^\|.*TC-.*\| *\|' validation-coverage.md` — passes when no blank verdict rows exist.
- TC-016 proof command: `python -m unittest .agent.adventures.ADV-011.tests.test_coverage_arithmetic` — passes once T011 implements the test AND this task's outputs satisfy it.
- Local smoke (implementer-run, no CI): recount source TCs with the grep
  command block above; count matrix rows with
  `grep -cE '^\| ADV-00[1-8] TC-' validation-coverage.md`; confirm
  equality.

## Risks

- **Source TC tables may drift between `manifest.md` and
  `tests/test-strategy.md`.** Mitigation: the inline per-adventure
  location table in this design names the current source of truth;
  T011's test re-greps at run time so drift is caught.
- **`COVERED-BY` over-claim**: an implementer may cite a generic section
  anchor ("builder-delta.md#verify") for a specific capability. Mitigation:
  the citation MUST be an H2/H3 slug that is topically narrow; T011's
  `test_every_covered_cites_existing_anchor` enforces existence; the "open
  gaps" section of the report is expected to surface weak-cite rows for
  human review.
- **`DEFERRED-TO` forward reference**: T009 runs before T010, so the
  downstream adventure ids are taken from
  `design-downstream-adventure-plan.md`. If T010 later omits an ID that
  T009 used, T011 will fail — fix by amending T010's output, not T009's.
- **Pipe characters in TC descriptions** break the markdown table.
  Mitigation: transcribe with `\|` escapes; row count test is
  `^\| ADV-00[1-8] TC-` which ignores wrapped rows.
- **TC-id collision across adventures** (same `TC-005` number reused in
  multiple adventures): keyed by prefix `ADV-NNN TC-NNN` in the `tc_id`
  column; uniqueness is on the pair, not the bare `TC-NNN`.
