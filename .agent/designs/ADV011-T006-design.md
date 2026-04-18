# Unified Descriptor — Delta Report — Design

## Approach

Produce a single research artefact, `descriptor-delta.md`, that operationalises
section 4 of `designs/design-unified-descriptor.md`. The delta is a *planning*
artefact — it decides, per current stdlib file, what the unification adventure
(`ADV-Descriptor-Unification`) must do to reach the target two-level layout,
without actually moving any code. The report has five required sections:

1. **Verdict Table** — one row per `ark/dsl/stdlib/*.ark` file with one of five
   verdicts: `KEEP-AS-IS | KEEP-RENAMED | MERGE-INTO | MOVE-TO-PRIMITIVES |
   RETIRE`.
2. **Target Two-Level Stdlib Layout** — the `primitives/` + `domain/` tree
   copied from section 4 of the unified-descriptor design, annotated with the
   specific rows from the verdict table that populate each branch.
3. **Grammar Authoring Contract** — Lark-primary, Pest-secondary, a fixed
   six-section layout, one patch per domain addition, enforced by a parity
   autotest.
4. **AST Family Spec** — single `Item` variant enum rooted in `ark-dsl` (Rust)
   and `ark_parser.Ast` (Python), with the 40-variant seed list and the
   dual-input helper contract.
5. **Citations** — every descriptor-bucket concept row from
   `research/concept-mapping.md` and every descriptor-bucket row from
   `research/deduplication-matrix.md` is quoted with its row ID, plus an
   explicit citation of ADV-008's host-language contract (TC-010).

The report is *read-only* with respect to `ark/` — it neither moves files nor
edits grammars. It is a document that the downstream implementation adventure
will execute.

## Target Files

- `.agent/adventures/ADV-011/research/descriptor-delta.md` (NEW) — the single
  deliverable. Roughly 400–600 lines. Markdown with one top-level H1, five H2
  sections in the order above, and pipe-delimited tables in sections 1, 2, and
  5.

No other files are created or modified. No `ark/` sources are touched (adventure
constraint: "No grammar changes. No codegen changes. No file moves in `ark/`").

## Verdict Table — Column Schema

Section 1 of the deliverable is a markdown table with exactly these six columns,
in this order:

| column | type | meaning |
|--------|------|---------|
| `file` | string | Path relative to `ark/dsl/stdlib/`, e.g. `types.ark`. Must exactly match `basename $f` for every `$f` in `ark/dsl/stdlib/*.ark` — enforced by TC-009. |
| `verdict` | enum | One of the five values (see rules below). |
| `target` | string | Post-unification location/identity. Format depends on verdict: for `KEEP-AS-IS` → same path; for `KEEP-RENAMED` → `domain/<new>.ark`; for `MERGE-INTO` → `domain/<host>.ark#<section>`; for `MOVE-TO-PRIMITIVES` → `primitives/<bucket>.ark`; for `RETIRE` → `—` (dash). |
| `rationale` | prose (1 sentence) | Why this verdict, phrased as an observation about the file's content (not a command). |
| `concept_refs` | comma-separated row IDs | IDs of rows from `research/concept-mapping.md` whose `source_artefact` points at this file. At least one ref per row; blank is a lint failure. |
| `dedup_refs` | comma-separated row IDs | IDs of rows from `research/deduplication-matrix.md` with `assigned_bucket = descriptor` that mention this file (or `—` if none apply). |

### Verdict assignment rules

The five verdicts are exhaustive and mutually exclusive. The implementer MUST
apply this decision tree in order — first match wins:

1. **`MOVE-TO-PRIMITIVES`** — file contains *only* type-level items
   (`primitive`, `struct`, `enum`) and no domain-specific item kinds
   (`studio`, `role`, `agent`, `evolution_target`, `diagram`, etc.), AND the
   items are used by ≥ 2 other stdlib files or by the core grammar.
   *Example*: `types.ark` (7 primitives + 10 math structs + orchestration enums
   referenced from every other stdlib file). Target: `primitives/types.ark`.

2. **`RETIRE`** — file is listed as DROP in `research/pruning-catalog.md`
   OR its content is strictly superseded by another file (detected via dedup
   matrix row where `canonical_form` points to a different file). No target;
   the content is dropped or absorbed without renaming.
   *Example* (hypothetical): a placeholder stdlib file containing only TODO
   markers.

3. **`MERGE-INTO`** — file's entire item list is a proper subset of a larger
   domain's natural scope, AND a dedup matrix row exists that names both this
   file and its host with `canonical_form = <host>`. The host must be a
   different `*.ark` file, not a section of the same file. Target format:
   `domain/<host>.ark#<section>`.
   *Example*: `code_graph_queries.ark` (expression/predicate rules over the
   `code_graph.ark` schema) merges into `domain/code_graph.ark#queries`.

4. **`KEEP-RENAMED`** — file survives as a single-domain island but needs a
   different name to match the two-level layout (usually because the current
   name is grammar-level, not domain-level), OR the file is moving from the
   flat `stdlib/` root into `stdlib/domain/`. Target: `domain/<new>.ark`.
   *Example*: `studio.ark` at flat root becomes `domain/studio.ark` (same
   content, new path). The *rename* here is the path, not the basename.

5. **`KEEP-AS-IS`** — file survives in its current form *and* at its current
   path (or its current path is already the target path in the new layout).
   This verdict is reserved and may in practice apply to zero files, since
   every current file lives at `stdlib/<name>.ark` (flat) while the target
   layout is two-level. The verdict exists so the enum remains closed and
   exhaustive.

### Row count and coverage

The table must contain exactly nine rows, one per file returned by
`ls ark/dsl/stdlib/*.ark`:

1. `types.ark`
2. `predicate.ark`
3. `expression.ark`
4. `code_graph.ark`
5. `code_graph_queries.ark`
6. `studio.ark`
7. `evolution.ark`
8. `agent.ark`
9. `visual.ark`

TC-009 greps for each of `types`, `expression`, `predicate`, `code_graph`,
`code_graph_queries`, `studio`, `evolution`, `agent`, `visual` followed by
`.ark`. All nine basenames MUST appear in the `file` column.

### Seed guidance (non-binding — implementer applies the decision tree)

- `types.ark` → **MOVE-TO-PRIMITIVES** (`primitives/types.ark`).
- `predicate.ark` → **MOVE-TO-PRIMITIVES** (`primitives/predicate.ark` — boolean
  primitives reused by every domain's `check:` clauses).
- `expression.ark` → **MOVE-TO-PRIMITIVES** (`primitives/expression.ark` —
  numeric/text expression stdlib reused across domains).
- `code_graph.ark` → **KEEP-RENAMED** to `domain/code_graph.ark`.
- `code_graph_queries.ark` → **MERGE-INTO** `domain/code_graph.ark#queries`.
- `studio.ark`, `evolution.ark`, `agent.ark`, `visual.ark` → **KEEP-RENAMED** to
  `domain/<file>` (path promotion into the `domain/` subdirectory).

The implementer MUST confirm each of the above against the actual concept
mapping and dedup matrix and override where the rules require it.

## Target Two-Level Stdlib Layout

Section 2 reproduces the layout tree from section 4 of the unified-descriptor
design, annotated with verdict-table references:

```
ark/dsl/stdlib/
  primitives/          # type-only — auto-preluded into every consumer
    types.ark          ← row 1 (MOVE-TO-PRIMITIVES)
    predicate.ark      ← row 2 (MOVE-TO-PRIMITIVES)
    expression.ark     ← row 3 (MOVE-TO-PRIMITIVES)
  domain/              # one file per domain island, opt-in import
    code_graph.ark     ← row 4 (KEEP-RENAMED) + row 5 absorbed under #queries
    studio.ark         ← row 6 (KEEP-RENAMED)
    evolution.ark      ← row 7 (KEEP-RENAMED)
    agent.ark          ← row 8 (KEEP-RENAMED)
    visual.ark         ← row 9 (KEEP-RENAMED)
```

Rules captured under the tree:

- **`primitives/` invariant**: every file contains *only* `primitive`, `struct`,
  `enum` items — no domain kinds, no imports of `domain/*`. Enforced by a
  lint pass in the downstream adventure.
- **`domain/` invariant**: every file is an island; may import
  `stdlib.primitives.*` (auto-prelude) and may import other
  `stdlib.domain.*` siblings only via an explicit `import` statement.
- **Import path rewrite**: every current `import stdlib.types` becomes
  `import stdlib.primitives.types`; the auto-prelude will make the explicit
  form optional.

## Grammar Authoring Contract

Section 3 pins down the Lark-primary / Pest-secondary workflow that the
downstream implementation adventure will enforce. Content requirements:

1. **Primacy rule** — `ark/tools/parser/ark_grammar.lark` is the authoring
   grammar; `ark/dsl/grammar/ark.pest` is a *mirror* that must produce
   byte-identical JSON AST on every fixture. Rationale cited inline: ADV-001
   TC-005 already established Lark↔Pest byte-identity as a hard contract, and
   the Python parser is the reference implementation (see `ark.py parse`).
2. **Fixed six-section layout** — every grammar file ordered identically:
   (a) whitespace/comments, (b) top-level `file`/`import_stmt`/`item`, (c) four
   primitives (`@in`, `#process`, `@out`, `$data`), (d) base items (abstraction,
   class, instance, island, bridge, registry, verify, primitive, struct, enum),
   (e) domain items in alphabetical order, (f) shared terminals (IDENT,
   STRING, NUMBER, PIPE_FN_IDENT). The current `ark.pest` top-level already
   matches this shape (see file lines 17–59); the contract makes it mandatory
   rather than incidental.
3. **One-patch rule** — any domain addition or rename lands as a single commit
   that patches both grammars atomically, accompanied by a new fixture under
   `ark/dsl/stdlib/fixtures/` (or equivalent) that exercises the new rule.
   Replaces the current practice (ADV-003 split the work across T003/T004).
4. **Grammar-parity autotest** — `tests/test_grammar_parity.py` loads every
   `.ark` file under `ark/dsl/stdlib/` (and `specs/`), parses with both
   `ark_parser.py` and the Rust `dsl` crate, and asserts JSON AST equality.
   Runs in CI. Any grammar drift fails the build.
5. **Domain ordering** — domain item rules MUST appear in alphabetical order
   by item-kind keyword in both grammars (`agent_def`, `annotation_def`,
   `benchmark_gate_def`, …). Makes diffs reviewable and keeps the two files
   visually aligned.
6. **Cross-cutting rules** (pipe_expr, typed_field_list, dotted_path, numeric
   literal syntax) MUST live in the shared-terminals section so domain
   additions never redefine them.

The section ends with a one-paragraph note that these rules supersede the
ad-hoc practice visible across ADV-001..006 where each adventure introduced
its own grammar-extension approach.

## AST Family Spec

Section 4 specifies the unified AST. Content requirements:

1. **Single root** — `Item` is a variant enum (Rust `enum Item`, Python tagged
   union under `ark_parser.Ast.Item`). Every top-level declaration in a parsed
   `.ark` file is an `Item` variant.
2. **Variant seed list** — enumerate the current and target variants, grouped:
   - **base** (10): `Abstraction`, `Class`, `Instance`, `Island`, `Bridge`,
     `Registry`, `Verify`, `Primitive`, `Struct`, `Enum`.
   - **primitives** (2): `Expression`, `Predicate`.
   - **studio domain** (6): `Role`, `Studio`, `Command`, `Hook`, `Rule`,
     `Template`.
   - **evolution domain** (7): `EvolutionTarget`, `EvalDataset`,
     `FitnessFunction`, `Optimizer`, `BenchmarkGate`, `EvolutionRun`,
     `Constraint`.
   - **agent domain** (8): `Agent`, `Platform`, `Gateway`, `ExecutionBackend`,
     `Skill`, `LearningConfig`, `CronTask`, `ModelConfig`.
   - **visual domain** (6): `Diagram`, `Preview`, `Annotation`, `VisualReview`,
     `RenderConfig`, `Feedback` — note `Screenshot`, `VisualSearch` are
     dropped per `research/pruning-catalog.md` (cite row ID).
   - **code_graph domain** (1): `CodeGraphNode`/`CodeGraphEdge` folded under
     `Struct` + `Enum` variants with domain annotation; no new variant.
   Total: ~40 variants, down from 43 currently declared across the two
   grammars.
3. **Dual-input helper contract** — every variant exposes `from_lark(tree)`
   (Python) and `from_pest(pair)` (Rust) with a shared fixture-driven
   round-trip test. This preserves the "Dual-input AST helpers" pattern from
   ADV-005 and makes the parity autotest trivially implementable.
4. **Where it lives** — one Rust crate (`ark-dsl`, single `ast.rs` module,
   `pub enum Item`), one Python module (`ark_parser.Ast`). No per-domain crate
   split. Cross-references ADV-005's dual-parser work as the canonical
   pattern.
5. **Extensibility rule** — adding a new domain variant requires (a) a Lark
   rule, (b) a mirrored Pest rule, (c) a variant in `Item`, (d) a fixture,
   (e) a re-run of the grammar-parity autotest. All five in one patch —
   enforced by the one-patch rule above.

## Citation Contract (Concept + Dedup + ADV-008)

Section 5 of the deliverable is the citation manifest. It has three
sub-sections:

### 5a. Descriptor-bucket concepts

A markdown table with columns `concept_row_id | concept_name | resolved_in`
listing every row from `research/concept-mapping.md` whose `bucket =
descriptor`. The `resolved_in` column points at the section of
`design-unified-descriptor.md` or `descriptor-delta.md` that addresses it
(e.g. "§Grammar Authoring Contract rule 3"). Zero rows uncited is a
linter failure.

### 5b. Descriptor-bucket dedup rows

A markdown table with columns `dedup_row_id | duplicate_forms |
canonical_form | resolution` listing every row from
`research/deduplication-matrix.md` whose `assigned_bucket = descriptor`. The
`resolution` column names the specific rule or verdict in this document that
resolves the duplication (e.g. "verdict row 5: MERGE-INTO
`domain/code_graph.ark#queries`").

Acceptance criterion (task AC #3): zero descriptor-bucket dedup rows
uncited.

### 5c. Host-language contract citation (TC-010)

A prose paragraph, no table. MUST contain the literal strings `ADV-008` and
`host-language` so that TC-010's regex (`grep -qE
"ADV-008\|host-language\|feasibility"`) passes. The paragraph summarises the
contract from `design-unified-descriptor.md` section 6:

> The descriptor must remain expressive enough that a sibling package (e.g.,
> `shape_grammar/`) can consume the DSL without requiring new item kinds. The
> ADV-008 host-language feasibility study (T03) set the bar at 0 BLOCKED items
> and ≤2 NEEDS_WORKAROUND. Any domain addition proposed by this delta report
> MUST re-run that study before landing.

The paragraph ends with an explicit cross-reference to
`.agent/adventures/ADV-008/research/feasibility-study.md` (or the actual
filename — implementer confirms path at write time).

## Implementation Steps

The implementer (role: `descriptor-architect`, model: sonnet) executes in this
order:

1. **Load inputs**: read `design-unified-descriptor.md` (§4 for layout, §2 for
   grammar strategy, §3 for AST, §6 for host contract),
   `research/concept-mapping.md` (filter `bucket = descriptor`),
   `research/deduplication-matrix.md` (filter `assigned_bucket = descriptor`),
   `research/pruning-catalog.md` (check for descriptor-file DROP rows).
2. **Enumerate stdlib files**: `ls ark/dsl/stdlib/*.ark` → nine rows. Confirm
   the list matches the TC-009 grep pattern.
3. **Apply verdict decision tree** to each file in order, recording rationale
   and filling `concept_refs` / `dedup_refs` from the loaded inputs.
4. **Write section 2** (layout tree) with row-number annotations pulled from
   the completed verdict table.
5. **Write section 3** (grammar contract) — six rules plus the parity-autotest
   note. Quote actual rule names from `ark.pest`/`ark_grammar.lark` where
   helpful.
6. **Write section 4** (AST family) — list all ~40 variants grouped by domain;
   mark retired variants with their pruning-catalog row ID.
7. **Write section 5a/5b/5c** citations; verify each descriptor-bucket mapping
   row and each descriptor-bucket dedup row is cited exactly once.
8. **Self-lint**:
   - `grep -c "^| " descriptor-delta.md` in the verdict table → 9 data rows +
     1 header + 1 separator = 11 lines.
   - Run TC-009 and TC-010 grep commands locally; both must pass.
   - Confirm no uncited descriptor-bucket dedup row (AC #3).
9. **Update task**: append log line, flip `status: ready` on task, record
   metrics row.

## Testing Strategy

Two target conditions plus three task acceptance criteria:

- **TC-009** (autotest): `for f in types expression predicate code_graph
  code_graph_queries studio evolution agent visual; do grep -q "$f.ark"
  descriptor-delta.md; done` — every basename appears.
  *Verification*: the verdict table's `file` column contains every basename.
- **TC-010** (autotest): `grep -qE "ADV-008\|host-language\|feasibility"
  descriptor-delta.md` — host-language paragraph wording.
  *Verification*: section 5c contains both literal strings.
- **AC #1** ("File exists"): `test -f
  .agent/adventures/ADV-011/research/descriptor-delta.md`.
- **AC #2** ("Every file has a verdict row"): covered by TC-009 + verdict
  column non-empty on all 9 rows.
- **AC #3** ("Every descriptor-bucket dedup row is cited"): the section 5b
  table contains a row for every `assigned_bucket = descriptor` row in
  `deduplication-matrix.md`. Implementer runs a diff between the two filtered
  sets before marking the task ready.

There is no unit test harness for this artefact beyond `grep`; the coverage
arithmetic TC-016 (run by T009/T011) will later confirm that every
descriptor-bucket concept/dedup row is accounted for in this document.

## Risks

1. **Upstream dependency missing** — T003/T004/T005 may not be complete when
   T006 launches, in which case `research/concept-mapping.md`,
   `deduplication-matrix.md`, and `pruning-catalog.md` won't yet exist.
   Mitigation: T006 `depends_on: [T003, T004, T005]` is already declared;
   lead/messenger must honour the dependency. If the implementer finds any of
   the three inputs missing, block the task and report (do not fabricate
   citations).
2. **Row-count drift** — if a new stdlib file is added between planning and
   execution, TC-009's static grep list won't catch it but the row-count
   invariant ("every file has a verdict row") will be violated. Mitigation:
   step 2 of implementation runs `ls ark/dsl/stdlib/*.ark` live and compares
   to the 9-row seed list.
3. **Dedup row IDs not stable** — `deduplication-matrix.md` may use
   row labels different from what this design assumes. Mitigation: the
   `concept_refs` / `dedup_refs` columns accept whatever ID scheme T003/T004
   settled on; implementer quotes the IDs verbatim from the source table.
4. **Scope creep into implementation** — the delta report is a plan, not a
   migration. The implementer must resist adding actual code moves, grammar
   patches, or renaming suggestions beyond the verdict table. Any such work
   belongs to the downstream `ADV-Descriptor-Unification` adventure.
5. **AST variant count mismatch** — the seed list of ~40 variants is derived
   from a scan of the two grammar files at planning time; the actual count
   may differ by ±3 variants depending on how `code_graph` is folded.
   Mitigation: the AST family section states the exact count observed from
   `ark.pest` item list and notes the folding decision explicitly.
