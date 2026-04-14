# ShapeML Architecture Research

*Produced for ADV-008-T01 by shape-grammar-researcher, 2026-04-14*
*Source: https://github.com/stefalie/shapeml*

---

## Project Overview and History

ShapeML is a procedural 3D shape-modeling language implemented in C++17 by Stefan Alie
(ETH Zürich / independent, circa 2020-2022). It provides a compiler-and-runtime pipeline
for generating 3D geometry via a rule-rewriting system that is the direct descendant of
the **Computer Generated Architecture (CGA) shape grammar** formalism introduced by Pascal
Müller et al. at ETH Zürich and later commercialised in Esri CityEngine.

### Intellectual lineage

| Ancestor | Year | Contribution |
|----------|------|--------------|
| Stiny & Gips — Shape Grammars | 1975 | Formal grammar framework for shape rewriting |
| Lindenmayer — L-systems | 1968 | String-rewriting parallel production model |
| Müller et al. — CGA shape grammars | 2006 | Scope-aware 3D rewriting, CityEngine basis |
| Pirkka Aho — ShapeML prototype | ~2016 | Academic ShapeML compiler, ETH |
| Stefan Alie — ShapeML open-source | 2020+ | Production-quality open-source re-implementation |

**Relation to Stiny (1975).** Stiny's original shape grammars operate on arbitrary
geometric shapes with a spatial matching relation. CGA/ShapeML constrains this to *axis-aligned
scopes* (oriented bounding boxes) as the matching substrate, which makes grammar execution
decidable and GPU-friendly. The scope replaces Stiny's unconstrained spatial predicate with
a concrete, inheritable coordinate frame.

**Relation to L-systems.** L-systems rewrite in parallel and produce string sequences;
ShapeML rewrites sequentially (depth-first or breadth-first), targeting 3D geometry rather
than strings. The "terminal vs. non-terminal" distinction mirrors L-systems but the
production alphabet is 3D operations rather than character sequences.

**Relation to CGA / CityEngine.** ShapeML adopts CGA's scope model (translation, rotation,
scale inherited per axis), operation vocabulary (extrude, split, comp, repeat, set),
and the distinction between *shape symbols* (non-terminals) and *mesh terminals*. Its
contribution over CGA is a standalone compiled runtime with cleaner semantics, an open
grammar specification format, and a C++ reference implementation that is not tied to
CityEngine's closed toolchain.

---

## Architecture

ShapeML's codebase is organized around a classical **front-end / IR / back-end** compiler
pipeline, with a tree-walking runtime evaluation stage.

### Source layout (inferred from the public repository)

```
shapeml/
├── src/
│   ├── shapeml/
│   │   ├── interpreter/        # Front-end: lexer, parser, AST
│   │   ├── geometry/           # Geometry primitives, mesh, scope
│   │   ├── exporter/           # OBJ / material exporter
│   │   └── ...
├── tools/                      # Utility scripts, texture tooling
├── grammars/                   # Example .shp grammar files
└── CMakeLists.txt              # Build system
```

### Compiler pipeline

```
.shp source
    │
    ▼
[Lexer]          Token stream (keywords, idents, literals, ops)
    │
    ▼
[Parser]         AST — one node per rule, parameter list, operation call
    │
    ▼
[Semantic check] Type resolution, undefined-symbol detection, parameter arity
    │
    ▼
[Rule table]     Flat map: symbol-name → Rule (with parameter formals + body ops)
    │
    ▼
[Runtime / Evaluator]
  axiom shape → rewriting loop → terminal shape set
    │
    ▼
[Exporter]       OBJ + MTL files
```

The **Rule table** is ShapeML's intermediate representation — a flat dictionary indexed by
rule name. There is no SSA, no CFG, no closure conversion. The IR is intentionally simple
because rule bodies are declarative sequences of operations, not general computation.

### Module layout

- **interpreter/** — lexer, recursive-descent parser, AST node types, semantic analysis pass.
- **geometry/** — `Scope` (OBB + coordinate frame), `Shape` (symbol + scope + attribute bag),
  `Mesh` (vertex / face storage), geometric operation implementations.
- **exporter/** — OBJ serialization, material library generation.
- No JIT or bytecode VM; evaluation is a direct tree walk over the parsed rule body.

---

## Grammar Surface Syntax

ShapeML grammars are stored in `.shp` files (also seen as `.shape` in some forks). The
syntax is a custom language distinct from any general-purpose PL.

### Rule declaration

```shapeml
RuleName(param1 : Type, param2 : Type) -->
    operation1(args) | operation2(args)
    successor_symbol(param_expr)
```

Key syntactic features:

- **`-->`** separates head (symbol + formals) from body (operation sequence).
- **`|`** separates alternative productions; stochastic weights attach as `{probability}`.
- **Successor invocation** — a non-terminal name in the body position is a recursive call
  that creates a child shape with an inherited scope.
- **Typed parameters** — `float`, `int`, `string`, `bool`. No polymorphism.
- **Attribute references** — `scope.sx`, `scope.sy`, `scope.sz` read the current scope's
  size dimensions; `geometry.area`, `geometry.volume` read derived geometry attributes.

### Operation syntax

```shapeml
extrude(height)
split(X) { relative_size : ChildRule | ~ : ChildRule }
comp(f) { all : FaceSymbol }
repeat(X, tile_size) { StreetTile }
set("material", "concrete")
s(sx, sy, sz)
t(tx, ty, tz)
r(rx, ry, rz)
i("mesh_asset.obj")
```

- **`extrude`** — extrudes the current scope's face along its Y axis.
- **`split`** — partitions the scope along an axis into named sub-scopes.
- **`comp`** — decomposes the current mesh into face/edge/vertex components.
- **`repeat`** — tiles a pattern along an axis.
- **`set`** — attaches a named string attribute to the shape (used for material, semantic
  label, etc.).
- **`s / t / r`** — scale, translate, rotate the scope (local coordinate frame).
- **`i`** — "insert" an external mesh asset (terminal operation).

### Comments and constants

```shapeml
# line comment
const FLOOR_HEIGHT : float = 3.5
```

Constants are grammar-level compile-time values; no mutable global state.

### Stochastic productions

```shapeml
FacadePanel -->
    {0.3} Window | {0.5} Wall | {0.2} Balcony
```

The runtime samples from the distribution using a seeded PRNG. Weights need not sum to 1
(they are normalised); omitting weights makes productions equally probable.

---

## Runtime and Evaluation Model

### Rewriting algorithm

ShapeML uses **sequential rewriting** (not parallel like L-systems). Evaluation is a
work-list loop:

```
worklist ← [axiom_shape]
terminals ← []

while worklist not empty:
    shape ← worklist.pop()
    rule ← lookup(shape.symbol)
    if rule is None or shape is terminal:
        terminals.append(shape)
    else:
        children ← rule.apply(shape)
        worklist.extend(children)
```

In practice this is depth-first when using a stack or breadth-first when using a queue.
The reference implementation uses **depth-first** to keep the call stack structure close
to the grammar's lexical nesting.

### Scope and attribute inheritance

Every shape carries a **Scope** — an oriented bounding box (OBB) defined by:
- **Origin** (translation) — 3D point
- **Rotation** — 3×3 matrix (Euler angles in practice)
- **Size** — (sx, sy, sz) extents

When a rule fires and emits child shapes, each child inherits the parent scope and
applies any `s/t/r` operations to derive its own scope. The scope is **immutable within a
single rule application** — operations accumulate into the child's scope, not mutating
the parent's.

**Attribute bags** are string-keyed dictionaries attached to each shape. Attributes set by
`set(key, value)` propagate to all descendants unless overridden. This is the mechanism
for material assignment and semantic labeling.

### Terminal vs. non-terminal

- **Non-terminal** — a shape whose symbol has a matching rule. Continues rewriting.
- **Terminal** — a shape whose symbol has no matching rule, or a shape that has received
  the `i(...)` mesh-insert operation. Added directly to the output set.

The grammar author controls termination by:
1. Ensuring split/repeat operations produce scopes smaller than the tile threshold.
2. Using a explicit `NIL` symbol or omitting a rule definition for leaf shapes.
3. Depth guards (explicit parameter counter decremented per recursive call).

There is no automatic depth-bound enforced by the runtime — **termination is the grammar
author's responsibility**. This is a safety gap; ShapeML grammars can loop infinitely if
poorly constructed.

### RNG model

ShapeML uses a seeded deterministic PRNG (typically a Mersenne Twister or xoshiro variant
in C++ implementations). The seed is set at evaluation start. Every stochastic production
consumes one sample from the global stream in rule-application order (depth-first). This
means:
- Given the same grammar, seed, and axiom, evaluation is deterministic.
- Any change to rule order or evaluation order changes the RNG stream and thus the output.
- There is no per-symbol seed forking — the RNG state is global.

---

## Key Abstractions

### Shape

A **Shape** is the fundamental unit of computation — a tuple of `(symbol, scope, attributes)`:

- `symbol` — a string naming the rule to apply next (or "terminal" marker).
- `scope` — the oriented bounding box (OBB) defining this shape's local coordinate frame.
- `attributes` — inherited string→value bag (material, semantic label, etc.).

**Maps to Ark as ...** an `abstraction Shape` with `@in{scope: Scope, attributes: AttrBag}`
and `@out[derived_shapes: [Shape]]` in the non-terminal case, or `@out[mesh: MeshRef]`
in the terminal case. The `#process` dispatch block selects between the two via a
boolean `is_terminal` field. The scope and attribute bag become `$data` fields on a
`class ConcreteShape : Shape`. Ark's existing `@in / @out / $data` vocabulary covers
this without extension.

### Rule

A **Rule** binds a symbol name to a list of operations (the rule body) and a list of
typed formal parameters. Rules are the grammar's rewriting productions.

**Maps to Ark as ...** a `class Rule : Shape` where `$data` holds `operations: [Operation]`
and `parameters: [Param]`. The `#process` block iterates `operations`, dispatching each
to its operation class. Multiple alternative rules (stochastic productions) become
multiple `class` entries sharing the same `abstraction` interface, disambiguated by a
weight field and resolved by the evaluator's sampler.

### Module (Grammar island)

A **Module** (called an `island` in Ark terms) is the container for a complete grammar —
the set of rules, the axiom (starting symbol), global constants, and evaluation parameters
(seed, max_depth hint).

**Maps to Ark as ...** an `island ShapeGrammar` wrapping all Rule classes. The `max_depth`
annotation becomes a `$data` field on the island, read by the termination verifier pass.
The `seed` becomes another `$data` field. The axiom is a `$data: axiom: String` field
whose value must match one of the declared rule names — a referential integrity check
enforceable by the scope-safety verifier pass.

### Operation

An **Operation** is a geometric or attribute-setting command executed in a rule body:
extrude, split, comp, repeat, set, s, t, r, i.

**Maps to Ark as ...** an `abstraction Operation` with specialized sub-classes:
`class ExtrudeOp : Operation`, `class SplitOp : Operation`, `class CompOp : Operation`,
`class ScopeOp : Operation` (covers s/t/r), `class InsertOp : Operation` (covers i),
`class SetOp : Operation`. Each class holds its parameters as `$data` fields.
The evaluator (`tools/evaluator.py`) pattern-matches on the operation class name to
dispatch to the correct Python function in `ops.py`. This is a direct structural match
to Ark's existing class hierarchy pattern — no extension needed.

### Scope

A **Scope** is the oriented bounding box (OBB) — the local coordinate frame attached to
each shape. It carries origin, rotation, and size, and is the substrate for all spatial
operations.

**Maps to Ark as ...** a `class Scope` with `$data` fields:
```
origin: Vec3
rotation: Mat3
size: Vec3
```
The `s/t/r` operations produce a new `Scope` by composing transforms. Ark has no built-in
numeric types for Vec3/Mat3, so these would be represented as `[Float]` (length-3 list)
and `[[Float]]` (3×3 list of lists) respectively — verbose but expressible without
extension. **This verbosity is the primary ergonomic cost of the "no Ark modification"
constraint.**

### Attribute (Semantic Label / Material)

An **Attribute** is a string-keyed value attached to a shape via `set(key, value)`.
Material name, semantic label, LOD hint, and any user-defined tag are all attributes.
Attributes propagate by inheritance — a child inherits all parent attributes and may
override them.

**Maps to Ark as ...** a `class AttrBag` with `$data: entries: [AttrEntry]` where
`class AttrEntry` holds `key: String` and `value: String`. Inheritance is modeled as
a merge operation in the evaluator — the child's bag is the parent bag plus any overrides.
Ark's existing list and string primitives cover this fully.

---

## File Format and Deployment

### On-disk format

ShapeML grammars are plain-text `.shp` files. No binary compilation artifact is produced
for the grammar itself — the runtime parses and interprets on every evaluation. This is
appropriate for small-to-medium grammars (hundreds to low thousands of rules) where
parse time is negligible compared to geometry evaluation.

External asset references (via `i("mesh.obj")`) point to standard **OBJ/MTL** files on
disk, located relative to the grammar file or a configured asset path. Textures are
referenced from MTL files in the standard way.

**Output format** — the exporter writes **OBJ + MTL** pairs. Material names in the MTL
correspond to `set("material", name)` attribute values collected from terminal shapes.

There is no bundled binary (no `.shpb` equivalent). The runtime is a native C++ executable
invoked from the command line:

```
shapeml run --grammar city.shp --axiom Lot --seed 42 --out city.obj
```

### Compilation and deployment

- **Build**: CMake + C++17. Dependencies: Eigen (linear algebra), GLM (optionally), and
  standard C++ library. No Boost. Single executable artifact.
- **No dynamic loading**: all operation implementations are compiled into the binary.
  Grammar authors cannot add new operation primitives at grammar level — the operation
  set is closed by the C++ implementation.
- **Grammar hot-reload**: because grammars are parsed at runtime, editing a `.shp` file
  and re-running the evaluator gives immediate feedback without recompiling the runner.

### Packaging for Ark integration

In the ADV-008 design, `.shp` syntax is **not used at all** — grammars are written as
Ark islands (`.ark` files) using existing Ark vocabulary. The shape-grammar evaluator
(`shape_grammar/tools/evaluator.py`) consumes Ark's parsed AST (via `ark parse`) and
produces the same OBJ+MTL output. The `.shp` surface syntax is a reference for
understanding the intended semantics; it is never parsed by the `shape_grammar` package.

---

## Ark Integration Analysis

This table assesses each ShapeML feature against three statuses:
- **EXPRESSIBLE** — directly representable in existing Ark vocabulary.
- **NEEDS WORKAROUND** — expressible but verbose or indirect.
- **WOULD REQUIRE ARK EXTENSION** — genuinely inexpressible without Ark modification.

| ShapeML Feature | Status | Notes |
|-----------------|--------|-------|
| Rule declaration (symbol → operation list) | EXPRESSIBLE | `class Rule : Shape` with `$data: operations: [Operation]` |
| Operation dispatch (extrude, split, comp, …) | EXPRESSIBLE | `abstraction Operation` + subclasses; evaluator pattern-matches |
| Scope (OBB) with origin/rotation/size | NEEDS WORKAROUND | Vec3/Mat3 must be encoded as `[Float]` / `[[Float]]`; verbose but correct |
| Attribute bag inheritance | EXPRESSIBLE | `class AttrBag` with list merge semantics in evaluator |
| Stochastic productions with weights | NEEDS WORKAROUND | Weights are `$data` fields; sampling logic is in evaluator Python, not verified by Ark's Z3 |
| Grammar island (axiom + rules + seed + max_depth) | EXPRESSIBLE | `island ShapeGrammar` with `$data` fields |
| Constants (compile-time float/int values) | EXPRESSIBLE | Ark `$data` fields with literal values serve this role |
| Typed parameters on rules | NEEDS WORKAROUND | Ark's type system is structural; Float/Int/String/Bool types map to Ark primitives but arity checking is external |
| Axiom referential integrity (axiom name matches a rule) | NEEDS WORKAROUND | Enforceable by the scope-safety verifier pass post-Ark-verify; not a native Ark constraint |
| Termination bound (`max_depth` enforced statically) | NEEDS WORKAROUND | Ark verify cannot check this natively; the `termination.py` verifier pass handles it via Z3 |
| Deterministic RNG (seeded, reproducible) | EXPRESSIBLE | `$data: seed: Int` field + evaluator-side seeding |
| External mesh asset reference (`i("mesh.obj")`) | EXPRESSIBLE | `class InsertOp : Operation` with `$data: asset_path: String` |
| Split axis specification (X/Y/Z enum) | EXPRESSIBLE | String-valued `$data: axis: String` with evaluator-side enum check |
| Geometric predicates (`scope.sx > threshold`) | **WOULD REQUIRE ARK EXTENSION** | Ark's `@invariant` blocks use Z3 real arithmetic but do not natively express scope-size comparisons as guard conditions on rule selection. An Ark extension providing guard predicates on `$data` fields (a conditional-dispatch mechanism) would be needed to express geometry-conditioned branching in the Ark spec layer rather than pushing it entirely to the evaluator. |
| Face component access (`comp(f)` → face symbols) | NEEDS WORKAROUND | Representable as a `CompOp` with `$data: component_type: String` but the semantics (iterating mesh faces) are fully external; Ark sees only the operation record |
| Repeat with `~` (fill remainder) | NEEDS WORKAROUND | `~` semantics (fill remaining space) require evaluator arithmetic; expressible as a `SplitSegment` with `fill: Bool` flag in `$data` |
| OBJ+MTL output | EXPRESSIBLE | `obj_writer.py` is entirely external to Ark; the Ark spec records only the terminal set |
| Semantic label propagation | EXPRESSIBLE | `class SemanticLabel` with `$data: label: String, tags: [String]`; propagation is evaluator logic |
| Post-verify Z3 passes (termination, determinism, scope-safety) | EXPRESSIBLE | External Python modules consuming Ark's AST output — exactly the ADR-001 pattern |
| CLI invocation (`ark verify`, `ark parse`) as subprocess | EXPRESSIBLE | Standard subprocess call; Ark is a CLI tool |

### "Would Require Ark Extension" callout

**Geometric guard predicates** — ShapeML allows rules to fire conditionally on scope
geometry (e.g., only add a window if `scope.sx > 0.8`). In the `.shp` syntax this is
expressed inline in the rule body or as a conditional `split` segment. In the Ark island
representation, the equivalent logic must be implemented entirely in the evaluator
(`evaluator.py`) because Ark has no mechanism to express "apply this `class Rule` only
when a `$data` field satisfies a runtime numeric condition." Ark's `@invariant` blocks
assert static Z3 propositions; they are not conditional dispatch guards.

**To fully express geometry-conditional rule selection in the Ark spec layer** (rather than
leaving it as opaque evaluator logic), Ark would need a **conditional class selector**
or **guard predicate on `$data`** — something like:

```ark
class WindowRule : Rule
    $data:
        min_width: Float = 0.8
    @guard { scope.sx >= min_width }
    ...
```

This is currently inexpressible in vanilla Ark. The workaround (ADR-001 escape hatch) is
to encode the guard as a `$data: condition: String` field and handle dispatch in the
evaluator, accepting that the Ark spec layer does not verify the guard — only the evaluator
enforces it at runtime. This is logged here as a finding for a future Ark-extensibility
adventure.

---

## Summary and Implications for ADV-008

ShapeML's core abstractions (Shape, Rule, Operation, Scope, AttrBag, SemanticLabel) map
cleanly to Ark's existing `abstraction / class / island / $data / @in / @out / #process`
vocabulary. The primary costs are:

1. **Verbosity** — Vec3/Mat3 as list-of-lists, operation classes per primitive, weight
   fields on stochastic rules. Acceptable per ADR-001.
2. **External enforcement** — termination, determinism, scope-safety, and geometry-conditional
   dispatch are all enforced by external passes (`tools/verify/`, evaluator dispatch logic)
   rather than by Ark's native verifier. This is by design: Ark is not modified.
3. **One genuine extension gap** — geometry guard predicates. Logged as a future
   Ark-extensibility adventure trigger. The ADV-008 workaround is evaluator-side dispatch.

No features are **BLOCKED** — every ShapeML concept has a representable encoding in Ark,
even if some require workarounds. This confirms the feasibility of the "Ark as host
language" approach (ADR-001) and provides the semantic mapping needed by downstream tasks
(T03 feasibility study, T04-T06 spec authoring, T07 IR extraction, T08 verifier passes).
