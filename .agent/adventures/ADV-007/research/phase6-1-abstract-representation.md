---
task: ADV007-T020
adventure: ADV-007
phase: 6.1
target_conditions: [TC-023]
upstream:
  - .agent/adventures/ADV-007/research/phase2-entity-redesign.md
  - .agent/adventures/ADV-007/research/phase2-concept-catalog.md
  - .agent/adventures/ADV-007/research/phase6-1-complexity-analysis.md
  - .agent/adventures/ADV-007/research/phase6-1-refactoring-strategy.md
researched: 2026-04-14
---

# Phase 6.1 — Abstract Representation Layer

This document specifies the **abstract representation layer** (ARL) for
the unified Claudovka ecosystem. The ARL is the single typed vocabulary
that expresses Adventures, Tasks, Plans, Designs, Roles, Agents,
Permissions, Runs, Lessons, Contracts, and every new Phase-5 concept
(scheduling, human-role, input-storage, recommendations). Each of these
lives in at least one concrete store today — markdown files, SQLite
tables, MCP event streams, WebSocket frames — and will continue to live
in more than one after the unification. The ARL is the invariant that
binds all those stores together.

The ARL is **not a new file format**. It is an algebra: a small set of
types and operations that every concrete store is required to expose,
and that every consumer is allowed to assume. Concrete stores are
generated from, or bound to, the ARL through a small number of
well-defined translations.

The ARL is the substrate that makes the unified entity redesign (T008)
composable: without it, each entity's markdown shape, jsonl shape, and
rendered-view shape would be three independent designs that must stay
in sync by convention. With it, the three shapes are three renderings
of a single source, and divergence is impossible by construction.

---

## 1. Goals

1. **One source of truth per entity.** Any conflict between markdown,
   jsonl, DB row, and wire message is impossible because all four are
   generated from the same ARL value.
2. **Cross-store portability.** A Task moved from `.agent/` markdown
   to binartlab SQLite to an MCP event payload never loses information
   and never requires hand-written conversion.
3. **Round-trip guarantee.** `render(parse(x)) == x` for every concrete
   surface, with an explicit **loss budget** describing what (if
   anything) is allowed to round-trip lossily.
4. **Composability.** The ARL values combine under well-defined
   operations (sum, product, union, slice) so higher-level concepts
   (adventure contains tasks, task contains iterations, iteration
   contains events) can be expressed without additional ceremony.
5. **Incremental adoption.** Concrete stores can adopt the ARL one
   entity at a time, aligned with the M0-M8 milestone plan in TC-022.
6. **Lightweight.** The ARL definition itself is ≤ ~1 500 LOC of Ark
   (plus codegen); consumers bind through a ≤ ~300-line library per
   language.

---

## 2. Core Algebra

The ARL is built from five primitive type constructors and a small set
of operations. The vocabulary is chosen so that every concrete shape in
T007 + T008 has a direct translation.

### 2.1 Primitive constructors

```
Value ::= Atom
        | Record { field: Value, ... }
        | Union  { tag: Atom, payload: Value }
        | List   [ Value ]
        | Stream { offset: Int, entries: List<Value> }
```

- **Atom**: string, int, timestamp, bool, null, id (scoped string
  matching `<kind>-<ulid|numeric>`).
- **Record**: named fields; keys are strings; values are Values.
  Records are the default for headers (task frontmatter, manifest
  header, role prompt).
- **Union**: tagged choice; the `tag` is a short atom; the `payload`
  is a Record (typically). Used for events, status whitelists, and any
  "kind: X" shape.
- **List**: ordered finite sequence; canonical encoding is JSON array
  or markdown table depending on render target.
- **Stream**: append-only sequence keyed by monotonic `offset`. The
  Stream constructor is the ARL's most important addition over plain
  JSON: it encodes the append-only jsonl substrate (T008 §§3, 4, 5, 10,
  11) as a first-class type.

### 2.2 Type constructors

A **Type** is a predicate over Values. The ARL's type language is a
subset of Ark's (T007 §6.2):

```
Type ::= AtomType(name)
       | RecordType { field: Type, ... , *: forbid | any }
       | UnionType  [ (tag, RecordType) ... ]
       | ListType(Type, min=0, max=*)
       | StreamType(UnionType)          -- a stream of event kinds
       | RefType(entity)                 -- a cross-entity pointer
       | ViewType(source, projection)    -- derived read-only
```

- `*: forbid` on RecordType makes the record closed (reject unknown
  fields); `*: any` makes it open (permit). The default is `forbid`
  for entity headers and `any` for event payloads.
- `RefType("Task")` is a typed pointer — the concrete store decides
  whether it materialises as a task-id string, a URL, or a foreign key.
- `ViewType(source, projection)` declares a derived value that the
  store must regenerate after any change to `source`; it never writes.

### 2.3 Operations

The ARL declares five operations over Values. Every ARL-bound store
must implement all five.

| Op | Signature | Semantics |
|---|---|---|
| `read` | `(Ref) -> Value` | Fetch the current value of an entity. |
| `append` | `(Ref, Event) -> Offset` | Append to a Stream; returns monotonic offset. |
| `set_header` | `(Ref, Record) -> ()` | Replace a Record-valued header (task.md, manifest header). Must be atomic (fences around X6). |
| `view` | `(Ref, projection) -> Value` | Render a ViewType; side-effect-free. |
| `subscribe` | `(TypeFilter, since=Offset) -> Stream` | Deliver future events matching the filter. |

The five ops are a small closure: `read` + `set_header` describe
single-writer records (Task header, Role file, config); `append` +
`subscribe` describe multi-writer event streams (events.jsonl,
metrics.jsonl, lessons.jsonl, approvals.jsonl); `view` describes every
rendered-view md file. Nothing in T007 or T008 requires a sixth
operation.

### 2.4 Compound operations

Three derived operations are defined in terms of the primitives:

- `replay(Stream) -> Value` = fold-left of events applied to an
  initial Value. Enables `state_rebuild` in the refactoring strategy
  §4.3.
- `snapshot(Ref, at=Offset) -> Value` = read as of a past offset;
  implemented as `replay(Stream.truncated_to(offset))`.
- `amend(Ref, offset, Event) -> Offset` = append a correction event
  that shadows the event at `offset`. The view layer honours the
  correction in future reads. Resolves T008 §19.2 ("human edit-ability
  of append-only state").

---

## 3. Entity Catalog in ARL Form

The following table maps every entity from T008 into an ARL type
expression. These are the authoritative types; every concrete store is
a rendering or projection of these.

| Entity | ARL type |
|---|---|
| Task | `RecordType { id, stage, status, iterations_ref:RefType(Stream), log_ref:RefType(Stream), …, *: forbid }` + two Streams |
| AdventureManifest | `RecordType { id, state, concept, env, *: forbid }` + `targets:StreamType(TargetEvent)` + `evaluations:StreamType(EvalEvent)` |
| AdventureLog | `StreamType(LogEvent)` — `LogEvent = UnionType[(spawn|step|complete|error, …)]` |
| MetricsLedger | `StreamType(MetricEvent)` — `MetricEvent = RecordType { agent, task, tokens_in, tokens_out, duration_ms, turns, status }` |
| Knowledge (Lessons) | `StreamType(LessonEvent)` — `LessonEvent = UnionType[(pattern|issue|decision|procedure, …)]` |
| Role | `RecordType { id, prompt, default_model, memory_ref:RefType }, *: forbid` |
| Agent | `RecordType { id, role_ref, permission_spec_ref, … }` |
| LeadState | `active:StreamType(ActiveEvent)` + per-session `RecordType` |
| Messenger | `channels:RecordType(ChannelDecl), approvals:StreamType(ApprovalEvent)` |
| Permissions | `RecordType { scope, capabilities:List, boundary:List, *: forbid }` per scope |
| Session | `UnionType[(LeadSession, LockSession, ClientConnection)]` — each a RecordType |
| Trigger | `RecordType { event, action, args, *: forbid }` in a generated registry |
| Config | `RecordType { working_folders, model_rates, flags, … }` |
| Run | `RecordType { id, pipeline_ref, started_at, status } + events:StreamType` |
| Contract | `RecordType { edge_id, producer, consumer, transport, schema, version }` |
| Lesson | (see Knowledge row) |
| Project | `RecordType { id, path, repo, agent_dir, *: forbid }` |
| Schedule | `StreamType(ScheduleEvent)` + views |
| Human | `RecordType { id, profile, inbox_ref:Stream, availability_ref:Stream }` |
| InputItem | `RecordType { cid, kind, content_ref, provenance, *: any }` |
| Recommendation | (per T018 §4) `StreamType(RecommendationEvent)` |

Every entity is either a Record, a Stream, or a (Record + one-or-more
Streams) composite. No other shapes are needed. This is the completeness
claim: the ARL's algebra covers the union of T008 + T018 without
extension.

---

## 4. Rendering to Concrete Stores

A **renderer** is a total function from ARL Value to a concrete byte
layout. Four renderers are required for the unified ecosystem.

### 4.1 Markdown (+ YAML frontmatter) renderer

`render_md(Value, template) -> String`

- Record headers → YAML frontmatter block.
- Record body → markdown sections per `template` declaration.
- List → markdown table (columns from RecordType fields).
- Stream (in a rendered view) → markdown list; each entry rendered
  per its Union tag's template.

Inverse: `parse_md(String) -> Value`, with the loss-budget constraints
in §5.2 below.

### 4.2 JSONL renderer

`render_jsonl(Stream) -> String`

- Each entry is one JSON object per line; order matches offset order;
  the offset is not stored in the line (it is implicit from byte
  position).
- Atomic append is the renderer's contract: a new line is written only
  after the previous line is fully flushed. Combined with the
  single-writer discipline, this removes the non-atomic-write hazard
  (X6).

Inverse: line-by-line JSON parse; trailing partial line is discarded
and re-written on next append (treat as crash recovery).

### 4.3 Database renderer (binartlab SQLite)

`render_sql(Value, table_schema) -> RowSet`

- Record → one row with columns mapped by field name.
- Stream → one row per event in an event table; offset becomes the
  primary key.
- List → one row per element in a child table with FK to parent.

The DB renderer is the one case where `render_sql` is **not** the
write path for durable state: SQLite is a **derived read-optimised
mirror** of the ARL values held in the markdown+jsonl substrate. The
write path is `append`/`set_header` on the markdown side; the DB is
regenerated by a materialiser (same class as the rendered-view
generator).

### 4.4 Event (MCP notification / WebSocket) renderer

`render_event(UnionValue) -> MCPNotification | WSFrame`

- The Union tag becomes the event `type`.
- The payload Record becomes the event `payload`.
- The offset becomes the event `id`.
- The subscriber-side parser inverts this to reproduce the Union
  value exactly.

This renderer is the canonical bridge between the persistent substrate
(jsonl) and the real-time consumers (UIs, notifications). In-memory
"ring buffers" become a subscription with a finite backlog window,
eliminating the durability gap identified in T007 §4.3.

---

## 5. Translation Semantics

### 5.1 Canonical form

Every ARL Value has a **canonical form**: the smallest byte sequence
produced by `render_jsonl` with sorted keys, RFC 3339 timestamps, and
NFC-normalised strings. Two Values are equal iff their canonical forms
are byte-identical. Equality is decided on the canonical form, never
on the individual renders.

### 5.2 Round-trip rules and loss budget

For every renderer R, the pair `(render_R, parse_R)` satisfies:

```
parse_R( render_R( v ) ) == v          -- full round-trip (no loss)
render_R( parse_R( s ) ) ≡ s          -- canonicalising round-trip
                                         (byte-equal to canonical form)
```

The first rule is strict — it never admits loss. The second rule
admits canonicalisation differences (whitespace, key order) but never
information loss.

**Loss budget per renderer:**

- `render_md` / `parse_md`: **no information loss**, but permits
  whitespace, heading-style, and table-column-width canonicalisation.
  Unknown markdown (freely authored prose body below the structured
  sections) is preserved verbatim as an `extra_body:` field in the
  Record.
- `render_jsonl`: **no loss**; canonical form. Parse rejects malformed
  lines (recorded as `parse_error` events in a sibling
  `events.errors.jsonl`).
- `render_sql`: the **only renderer with a permitted loss budget**.
  Because SQLite is derived, the DB may drop fields not declared in
  the table schema. The materialiser's contract: *every field it drops
  must be recoverable from the markdown/jsonl source*. The loss-budget
  rule: never drop a field referenced by a query.
- `render_event`: **no loss** for scalar payloads; binary payloads are
  replaced by a content-addressed reference (`input-storage://<cid>`,
  T018 §3) whose bytes the consumer fetches on demand.

### 5.3 Identity and equality across renderers

Two stored artefacts represent the same entity iff:

1. Their Record / Stream ARL types are the same.
2. Their `id` atoms are equal.
3. Their canonical forms are equal (after applying the renderer's
   inverse).

This lets the UI, the MCP, and the filesystem all compare entities
without privileged access to any single store. A check
`adventure_manifest_equal(repo_path_A, repo_path_B)` reduces to
`canonical(parse_md(A)) == canonical(parse_md(B))`.

### 5.4 Versioning

Every ARL Type carries a `schema_version`. Concrete renderers embed
the version in their output (YAML frontmatter `schema_version:`,
JSONL `{"v":N,…}` first field, event `schema_version` header). Parsers
accept versions in a declared compatibility window; outside the window
they emit a `schema_too_new` error and refuse to proceed.

Migration between schema versions is a dedicated tool
(`pipeline.migrate(scope, from, to)`, phase6 MCP-ops §2.5) which
replays events through the new ARL type and rewrites the stored
canonical form.

---

## 6. Relation to the Unified Entity Redesign (T008)

The ARL is the type-theoretic backbone of T008. Every redesign choice
in that document is expressible as an ARL construct:

| T008 redesign | ARL expression |
|---|---|
| Task file → Task directory | `Task` = Record + 2 Streams (log, iterations) |
| Manifest → header + targets.jsonl + evaluations.jsonl | Record + 2 Streams |
| adventure.log → events.jsonl | `StreamType(UnionType[…])` |
| metrics.md → metrics.jsonl | `StreamType(MetricEvent)` |
| knowledge/* + agent-memory → lessons.jsonl | `StreamType(LessonEvent)` with optional `role:` field |
| lead-state.md → lead-state/active.jsonl + sessions/ | Stream + per-session Record |
| messenger.md → channels.md + approvals.jsonl | Record + Stream |
| permissions.md → permissions/<scope>/spec.md | per-scope Record |
| Session formalisation | UnionType of three Records |
| Trigger registry (generated) | Record list generated from source tree |
| Config (preserved) | one Record |
| Rendered views | `ViewType(stream, projection)` |

The one-to-one correspondence means T008's 15 entities plus the 7
Phase-5 additions map onto 22 ARL types. No T008 decision lacks an ARL
expression; no ARL construct is introduced without a T008 use case.

### 6.1 The parallelism guarantee, re-stated

T008 §18.1 claims that 10 of 15 entities eliminate a read-modify-write
hazard by moving to append-only jsonl. In ARL terms the claim is:

> For every entity whose representation uses `StreamType`, write
> contention is impossible because the only write operation is
> `append`, which is lock-free over a monotonic offset.

The proof is one-line: `append` on a jsonl file with `O_APPEND` is
atomic on POSIX up to `PIPE_BUF` bytes (4 KB); ARL events are bounded
to 4 KB by construction (see §7.1 below); therefore concurrent appends
never interleave within a line. The single-writer discipline on
Record-valued `set_header` ops closes the remaining hazard.

### 6.2 The token-economy guarantee, re-stated

T008 §18.2 claims auto-inject reductions of -68 % to -87 %. In ARL
terms:

> `ViewType(source, projection)` always produces a value bounded by
> the projection's declared size, regardless of `source` length.

Consequence: role-scoped knowledge views, sharded permissions, and
manifest headers have sizes determined by ARL projection declarations,
not by event-log growth. The rankers that pick which Lessons survive
a ~3 KB role-view budget are ARL projection definitions, not ad-hoc
scripts.

---

## 7. Constraints and Non-Goals

### 7.1 Event size bound

Every event on a StreamType is ≤ 4 KB. Payloads exceeding the bound
store a reference to `input-storage://<cid>` (T018 §3) and keep only
metadata inline. This is the ingredient that makes the atomic-append
argument in §6.1 work and caps token cost per event.

### 7.2 No schemaless entries

Every stored Value declares its Type. A JSONL line without a
`schema_version` or a Record without a frontmatter declaration is
rejected. This is a hard constraint; there is no "metadata" escape
hatch.

### 7.3 No write outside the five ops

Every MCP tool, every agent, every UI click maps to one of the five
ARL operations. Tools named `task_create`, `metrics_append`,
`lesson_append` are syntactic sugar; their bodies all reduce to
`append` + `set_header` with type checks. A tool whose body cannot be
expressed this way is rejected in code review.

### 7.4 Non-goals

- **General-purpose DB replacement.** ARL is not a relational model;
  joins are expressed as views, not as first-class ops.
- **Transaction boundaries larger than one Record.** Multi-entity
  atomic updates are out of scope; use a **saga** pattern — a
  correlated sequence of events where the last event is the "commit"
  marker.
- **User authentication.** Identity and authentication remain the
  responsibility of the host Claude Code session or binartlab project;
  the ARL's `Agent` and `Human` types refer to authenticated
  principals but do not authenticate them.

---

## 8. Minimum Viable ARL and Growth Path

### 8.1 MV (lands in M1-M2)

- Primitive constructors (Atom, Record, Union, List, Stream).
- Three renderers (markdown, jsonl, event).
- The five core ops (`read`, `append`, `set_header`, `view`,
  `subscribe`).
- Types for Task, AdventureManifest, AdventureLog, MetricsLedger —
  the four entities touched by M2.

### 8.2 Growth stages

- **M3-M4**: add types for LeadState (Session union), Knowledge
  (Lesson union), Permissions (scoped Records). Introduce the `amend`
  op.
- **M5**: add types for Trigger, Schedule, Messenger; introduce
  `replay` / `snapshot` as library functions.
- **M6**: publish the Ark codegen that generates ARL type definitions
  into the target languages (Rust, TypeScript, Python). Retire
  hand-written zod.
- **M7-M8**: add types for Run, Contract, Project; the SQL renderer
  (read-only mirror); golden-file tests for every renderer inverse.

Each stage extends the ARL without breaking earlier stages. The
`schema_version` field lets a consumer built against MV read an M6
artefact (by ignoring unknown Unions) and lets an M6 consumer read an
MV artefact (by recognising the older version and applying the
backward-compat shim).

---

## 9. Verification

### 9.1 Property tests

Every renderer pair `(render_R, parse_R)` ships with a property test:

```
forall v :: ValidType, v == parse_R(render_R(v))
forall s :: CanonicalString_R, s == render_R(parse_R(s))
```

The property tests are generated from the Ark codegen; no human
writes them. A failure is treated as a schema-break — the only valid
remedy is a `schema_version` bump and a migration.

### 9.2 Contract-level tests

Every edge E1-E14 from T006 ships a contract test that exercises the
full `render → transport → parse` pipeline with an ARL Value, asserts
the Value round-trips identically, and asserts every intermediate hop
preserves the canonical form.

### 9.3 Benchmarks

Three benchmarks watch the ARL's runtime cost (per TC-024 benchmark
design):

- `render_jsonl` throughput: ≥ 10 000 events/s on a single writer.
- `view` regeneration: ≤ 100 ms per event on a 10 k-event Stream.
- `replay(Stream)` cold start: ≤ 1 s for a full adventure's event
  history.

Any milestone that regresses these budgets by > 25 % fails the gate.

---

## 10. Acceptance Checklist (this document)

- [x] Goals articulated (§1).
- [x] Core algebra with primitive type constructors and ops (§2).
- [x] Derived operations: replay, snapshot, amend (§2.4).
- [x] Entity catalog mapped onto ARL types (§3).
- [x] Rendering to markdown, jsonl, SQL, events (§4).
- [x] Translation semantics with round-trip rules and loss budget
  (§5).
- [x] Schema-versioning strategy (§5.4).
- [x] Correspondence to the unified entity redesign T008 (§6).
- [x] Parallelism and token-economy guarantees re-stated in ARL terms
  (§6.1-§6.2).
- [x] Constraints and non-goals declared (§7).
- [x] Minimum-viable scope and growth path (§8).
- [x] Verification strategy (property tests, contract tests,
  benchmarks) (§9).
