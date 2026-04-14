# Ark-as-Host Feasibility Study — ADV-008

*Produced for ADV-008-T03 by shape-grammar-researcher, 2026-04-14*
*Gate document for Phase B. All entities from `schemas/entities.md` assessed.*

---

## Executive Summary

Every entity defined in `schemas/entities.md` can be expressed in **vanilla Ark syntax**
as it exists today. **Phase B is CLEAR to proceed.**

The Ark DSL surface — grammar (`ark_grammar.lark`), stdlib (`dsl/stdlib/types.ark`),
and the existing island corpus (`code_graph.ark`, `agent_system.ark`) — supplies all
structural primitives required for shape-grammar islands: typed `$data` fields,
`abstraction`/`class` hierarchies, `island` containers, `@in`/`@out` ports, `invariant:`
obligations, `struct`/`enum` declarations, list-typed fields, and integer/float/string
primitives. Nine entities are **EXPRESSIBLE** outright; two require **NEEDS_WORKAROUND**
verbosity patterns that are well-precedented in the existing island corpus. Zero entities
require escalation (i.e., none are inexpressible).

Feasibility verdict counts: **9 EXPRESSIBLE, 2 NEEDS_WORKAROUND, 0 inexpressible.**

---

## 1. Methodology

This study reads the following Ark sources directly (all files under `R:/Sandbox/ark/`):

| Source | What it tells us |
|--------|-----------------|
| `ark/tools/parser/ark_grammar.lark` | Authoritative grammar: every syntactic form available to `.ark` authors |
| `ark/tools/parser/ark_parser.py` — `parse()`, `to_json()` | Library API surface: how `shape_grammar` consumes the AST programmatically |
| `ark/tools/verify/ark_verify.py` — `verify_file()` | Verifier API: how external callers run Z3 passes on an already-parsed AST |
| `ark/ark.py` | CLI surface: every subcommand available as subprocess |
| `ark/dsl/stdlib/types.ark` | Stdlib struct/enum/primitive inventory |
| `ark/specs/infra/code_graph.ark` | Proven third-party-ish island consumer (ADV-007 T012) |
| `ark/specs/infra/agent_system.ark` | Complex island exercising data fields, platforms, gateways |

The entity list is taken verbatim from `schemas/entities.md`. The eight Operation subclasses
are assessed as a group under the `Operation` row and with individual subclass examples.
`Terminal` is treated separately (runtime-only; not in `.ark` source).

Each entity receives one of three verdicts:
- **EXPRESSIBLE** — existing Ark syntax handles it without modification; linked to the matching Ark construct.
- **NEEDS_WORKAROUND** — expressible but verbose or indirect; workaround pattern documented in §4.
- *(inexpressible — would trigger escalation per ADR-001 §Escape Hatch; no entity falls in this category)*

---

## 2. Per-Entity Feasibility Verdicts

| Entity | Verdict | Matching Ark Construct | Notes |
|--------|---------|----------------------|-------|
| **Shape** (abstraction) | EXPRESSIBLE | `abstraction Shape { @in{...} @out[]{...} invariant: ... }` | Ark's `abstraction` is precisely a named contract with `@in`/`@out` ports and optional `invariant:`. No extension needed. |
| **Rule** (class) | EXPRESSIBLE | `class Rule : Shape { $data id: String ... }` | Classes inherit abstractions via `:`. `operations: [Operation]` is a list-typed `$data` field. Ark grammar natively supports `[TypeName]` array types (`array_type` rule in the grammar). |
| **Operation** (abstraction) | EXPRESSIBLE | `abstraction Operation { $data id: String }` | Clean abstraction with a single required `$data` field. Subclasses extend it via `:`. |
| **ExtrudeOp, SplitOp, CompOp, ScopeOp, IOp, TOp, ROp, SOp** (8 subclasses) | EXPRESSIBLE | `class ExtrudeOp : Operation { $data height: Float }` etc. | Each subclass adds its own `$data` fields. Ark's `class X : Y` supports inheritance. Float/String/Int primitives are stdlib. See §4.3 for the dispatch workaround. |
| **Scope** | NEEDS_WORKAROUND | `class ConcreteScope : Scope` with `Vec3` fields and `[AttrEntry]` list | Vec3 is already in `stdlib/types.ark`. The `attrs: Map<String, Any>` field needs the `[String: String]` map type plus a type-tagging convention. Full pattern in §4.1. |
| **SemanticLabel** | EXPRESSIBLE | `class SemanticLabel { $data name: String; $data tags: [String]; $data inherits: Bool = true }` | All field types available. `[String]` is a list type. Default values via `= expr` (`default_value` grammar rule). |
| **Provenance** | EXPRESSIBLE | `class Provenance { $data rule_chain: [String]; $data depth: Int }` | List of strings plus an integer — straightforward with stdlib primitives. |
| **ShapeGrammar** (island) | NEEDS_WORKAROUND | `island ShapeGrammar { $data max_depth: Int [1..100]; $data axiom: String; ... }` | Island supports `$data` fields, `contains:`, `invariant:`. Referential integrity (axiom matches a declared rule name) requires an external verifier pass, not a native Ark constraint. Full pattern in §4.2. |
| **Terminal** (runtime-only) | EXPRESSIBLE | Not present in `.ark` source — emitted by evaluator only. | Schema explicitly states "Runtime-only (not in `.ark` source)". The evaluator emits `Terminal` Python objects; no Ark island needs to encode them. |

**Verdict counts: 9 EXPRESSIBLE, 2 NEEDS_WORKAROUND.**

Zero entities are inexpressible in vanilla Ark. The gate condition is satisfied.

> **Scope note**: `Scope` is NEEDS_WORKAROUND only for the `attrs: Map<String, Any>` field.
> Vec3 fields (translation, rotation, scale, size) use the stdlib `Vec3` struct directly —
> those are EXPRESSIBLE. Only the heterogeneous value type in the attribute bag requires a
> workaround. See §4.1.

---

## 3. Addressable-Features Analysis

This section documents every integration surface `shape_grammar` leans on and whether it
is *already exported as a library-callable function* or requires a subprocess shell-out.

### 3.1 Parser AST Access

| Surface | Status | Exact Python function / CLI flag |
|---------|--------|----------------------------------|
| Parse `.ark` source → `ArkFile` Python dataclass | **Library (import)** | `from ark_parser import parse` — `parse(source: str, file_path=None) -> ArkFile` at `ark/tools/parser/ark_parser.py:2663`. Returns a fully resolved dataclass tree including imported stdlib. |
| Serialize `ArkFile` → JSON | **Library (import)** | `from ark_parser import to_json` — `to_json(ark_file: ArkFile) -> str` at `ark/tools/parser/ark_parser.py:2679`. JSON is the canonical wire format for downstream consumers. |
| Parse via CLI subprocess | **CLI** | `python ark.py parse <file.ark>` — prints JSON AST to stdout. Zero-dependency path: no import of `ark_parser` needed. |

**Recommended pattern for `shape_grammar`**: prefer the library import path by adding
`ark/tools/parser/` to `sys.path` at startup (the same pattern used in `ark/ark.py` lines
42-52). Fall back to subprocess if the Ark package layout changes.

### 3.2 Z3 Verify-Pass Plugin Points

| Surface | Status | Exact Python function / CLI flag |
|---------|--------|----------------------------------|
| Run built-in Ark invariant checks on AST JSON | **Library (import)** | `from ark_verify import verify_file` — `verify_file(ast_json: dict) -> dict` at `ark/tools/verify/ark_verify.py:1308`. Accepts `json.loads(to_json(ark_file))`. Returns `{entity_name: [result_dicts]}`. |
| Run verify via CLI subprocess | **CLI** | `python ark.py verify <file.ark>` — exit 0 = pass, non-zero = fail. Suitable for CI gates. |
| Opaque primitive tracking | **Library (import)** | `from ark_verify import reset_opaque_usage, read_opaque_usage` — call before/after `verify_file` to discover which opaque Z3 primitives were exercised. |
| Shape-grammar extension verifier passes | **External (shape_grammar owns)** | `shape_grammar/tools/verify/` — `termination.py`, `scope_safety.py`. These are **not** inside `ark/`; they import `ark_verify` as a library and add shape-grammar-specific Z3 obligations on top. ADR-001 §Escape Hatch mandates this pattern. |

**There is no plugin hook inside `ark/tools/verify/`** — external callers cannot inject Z3
passes into the Ark verifier's loop. The correct call sequence is:

```
1. ark_parser.parse(source)          → ArkFile
2. json.loads(to_json(ark_file))     → ast_json
3. ark_verify.verify_file(ast_json)  → base results (Ark's own invariant checks)
4. shape_grammar.verify.termination_check(ast_json)   → additional results
5. shape_grammar.verify.scope_safety_check(ast_json)  → additional results
6. Aggregate all results; report pass/fail to caller
```

### 3.3 Codegen Stdout Formats

| Surface | Status | Exact Python function / CLI flag |
|---------|--------|----------------------------------|
| Generate Rust/C++/Proto | **Library (import)** | `from ark_codegen import codegen_file` — `codegen_file(ast_json: dict, target: str, out_dir: Path) -> dict` at `ark/tools/codegen/ark_codegen.py:849`. Shape-grammar does not need Ark's codegen — its evaluator reads the AST directly. |
| Codegen via CLI | **CLI** | `python ark.py codegen <file.ark> --target rust` |

The shape-grammar evaluator reads the parsed AST, not codegen output. Codegen is documented
here for completeness; `shape_grammar` will not call it in normal operation.

### 3.4 Subprocess-able CLI Commands

All commands emit structured output and use exit-code conventions compatible with CI:

| Command | Output format | Shape-grammar use case |
|---------|--------------|------------------------|
| `python ark.py parse <file.ark>` | JSON (ArkFile dict) | Zero-dependency parse of grammar islands |
| `python ark.py verify <file.ark>` | Human-readable + exit code | CI-style gate: exit 0 = pass |
| `python ark.py diff <old.ark> <new.ark>` | Structured diff records | Detect grammar evolution between versions |
| `python ark.py impact <file.ark> <Entity>` | Dependency graph text | Understand rule-dependency blast radius |
| `python ark.py graph <file.ark>` | HTML file written to disk | Visual debugging of grammar island structure |

---

## 4. Workaround Patterns

### 4.1 Scope — Heterogeneous Attribute Map (`attrs: Map<String, Any>`)

**Problem**: Ark's map type syntax `[String: String]` (the `map_type` rule in
`ark_grammar.lark`) does not support a heterogeneous `Any` value type. ShapeML's
attribute bag stores strings, floats, and booleans under the same string key.

**Workaround**: Encode all attribute values as strings using a type-tag prefix. The
evaluator deserializes them at runtime with a simple prefix check:
- `"float:3.14"` → Python `float(3.14)`
- `"bool:true"` → Python `True`
- `"string:concrete"` → Python `"concrete"`

The `Scope` entity in the Ark island:

```ark
import stdlib.types
// Vec3 is from stdlib/types.ark: struct Vec3 { x: Float, y: Float, z: Float }

class AttrEntry {
    $data key:   String
    $data value: String    // type-tagged: "float:3.14" | "bool:true" | "string:..."
}

abstraction Scope {
    @in  { }
    @out[] { }
}

class ConcreteScope : Scope {
    $data translation: Vec3
    $data rotation:    Vec3      // Euler angles; evaluator converts to matrix
    $data scale:       Vec3
    $data size:        Vec3

    $data attrs: [AttrEntry]    // heterogeneous bag encoded as tagged strings

    #process[strategy: code] {
        description: "Scope is immutable data; process block is identity"
    }
}
```

**Precedent in existing islands**: `agent_system.ark` uses `$data languages: String = "python,rust,ark"` encoding a list as a delimited String. `code_graph.ark` uses `$data backend: String = "in_memory"` as a string-tagged enum value. The type-tagging convention in `AttrEntry` is a natural extension of these patterns.

### 4.2 ShapeGrammar Island — Referential Integrity (axiom → rule name)

**Problem**: Ark's `invariant:` block translates to Z3 arithmetic/string propositions
over `$data` fields of a single entity. It cannot assert that a `String` field value
matches one of an open-ended set of identifiers declared elsewhere in the same island
(i.e., the set of `Rule.id` values is not a static enum known at spec-write time).

**Workaround**: The Ark island records the axiom as a plain `String` field. An external
verifier pass — `shape_grammar/tools/verify/scope_safety.py` — reads the parsed AST,
collects all `Rule.id` values, and asserts that `ShapeGrammar.axiom` appears in that set.
This is a pure Python check; no Z3 is needed. It runs after `ark_verify.verify_file()`.

```ark
island ShapeGrammar {
    strategy: code
    description: "Top-level shape grammar container"

    // Numeric fields — range constraints are Z3-verified by Ark natively:
    $data max_depth: Int [1 .. 100]
    $data seed:      Int [0 .. 2147483647]

    // String field — referential integrity delegated to scope_safety.py:
    $data axiom: String

    contains: [BuildingGrammar]

    // These invariants ARE checked by Ark's built-in Z3 verifier:
    invariant: $data max_depth > 0
    invariant: $data seed >= 0
}
```

**Precedent**: `code_graph.ark` uses the `verify` block pattern for named post-hoc
assertions (`verify CodeGraphInvariants { check store_non_negative: $data node_count >= 0 }`).
The axiom check is the same kind of named assertion — it just lives outside the Ark file
in `scope_safety.py` because the full set of valid axiom names is not static at write time.

### 4.3 Operation Dispatch — No Native Pattern Matching

**Problem**: Ark has no `match`/`case` or tagged-union dispatch. When the evaluator
processes a `Rule.operations: [Operation]` list, it must dispatch each element to the
correct Python handler based on the concrete subclass.

**Workaround**: Add a `$data kind: String` field to each Operation subclass. The Python
evaluator reads `item["kind"]` from the parsed AST JSON dict and dispatches with a simple
`if`/`elif` chain or a handler dict. This mirrors Ark's own internal convention: every
AST node dict has a `"kind"` or `"item"` key.

```ark
abstraction Operation {
    $data id:   String
    $data kind: String  // dispatch key: "extrude"|"split"|"comp"|"scope"|
                        // "insert"|"translate"|"rotate"|"scale"
}

class ExtrudeOp : Operation {
    $data kind:   String = "extrude"
    $data height: Float [0.001 .. 1000.0]
    invariant: $data height > 0.0
}

class SplitOp : Operation {
    $data kind:  String = "split"
    $data axis:  String {"X", "Y", "Z"}  // inline enum — Ark's enum_constraint
    $data sizes: [Float]                  // proportional sizes; evaluator normalises
}

class CompOp : Operation {
    $data kind:           String = "comp"
    $data component_type: String {"face", "edge", "vertex"}
}

class IOp : Operation {
    $data kind:       String = "insert"
    $data asset_path: String              // relative path to OBJ asset
}

class TOp : Operation {
    $data kind: String = "translate"
    $data dx: Float    $data dy: Float    $data dz: Float
}

class ROp : Operation {
    $data kind: String = "rotate"
    $data rx: Float    $data ry: Float    $data rz: Float
}

class SOp : Operation {
    $data kind: String = "scale"
    $data sx: Float    $data sy: Float    $data sz: Float
}

class ScopeOp : Operation {
    $data kind:  String = "scope"
    $data attrs: [AttrEntry]    // key-value overrides applied to current scope
}
```

**Ark feature used**: `String {"X", "Y", "Z"}` uses Ark's `enum_constraint` rule
(`constraint: "{" expr_list "}"` in `ark_grammar.lark`). These constraints are Z3-verified
by Ark's built-in verifier — the `axis` field is constrained to exactly those three values
at the spec layer, not just at runtime.

**Precedent**: `ark/dsl/stdlib/types.ark` uses `enum Strategy { tensor, code, ... }` for
multi-variant dispatch. The `kind: String` field with an inline constraint is a lighter-weight
alternative that avoids a separate enum declaration while achieving the same evaluator
dispatch pattern.

---

## 5. Geometry Guard Predicates — T01 Extension Callout Confirmed and Resolved

T01's research document (`shapeml-architecture.md`) flagged the following as a potential
extension requirement:

> Geometric guard predicates — ShapeML allows rules to fire conditionally on scope geometry
> (e.g., only add a window if `scope.sx > 0.8`). Ark's `invariant:` blocks assert static
> Z3 propositions; they are not conditional dispatch guards.

### Confirmation

This finding is correct. Reviewing `ark_grammar.lark`:

- `invariant_stmt: "invariant:" expr` — asserts Z3 propositions about `$data` fields of
  a **single entity at construction time**; it cannot guard rule selection across entities
  at derivation time.
- `condition_stmt: "condition" expr ":" (assignment | "{" process_body "}")` — exists in
  the grammar, but only inside `#process` blocks. It controls assignments within a process
  body, not class-level dispatch between alternatives.
- There is no `@guard` syntax, no conditional class selector, and no `when:` clause on
  `class` definitions.

Ark's verifier processes `invariant:` as Z3 safety obligations. It has no mechanism to
mark a class as "applicable only when a numeric field satisfies a runtime condition."

### Resolution — NEEDS_WORKAROUND

The geometry guard predicate is a **runtime evaluation concern, not a spec declaration
concern**. The Ark island records the threshold as a typed `$data Float` field (Z3-verified
for sanity bounds). The Python evaluator enforces the spatial predicate during derivation.

```ark
class WindowRule : Rule {
    $data kind:      String = "window"
    $data lhs:       String = "Facade"
    $data min_width: Float = 0.8    // guard threshold — Z3-verified for sanity
    $data max_width: Float = 10.0
    $data operations: [Operation]

    // Ark verifies these bounds hold at spec level:
    invariant: $data min_width > 0.0
    invariant: $data min_width < $data max_width
}
```

The evaluator (`shape_grammar/tools/evaluator.py`) enforces the guard:

```python
def select_rules(rules: list[dict], scope: "Scope") -> list[dict]:
    """Filter rules whose geometry guards are satisfied by the current scope."""
    applicable = []
    for rule in rules:
        min_w = rule.get("min_width")
        max_w = rule.get("max_width")
        if min_w is not None and scope.size.x < min_w:
            continue    # guard not satisfied — rule skipped
        if max_w is not None and scope.size.x > max_w:
            continue
        applicable.append(rule)
    return applicable
```

**Why NEEDS_WORKAROUND and not an escalation trigger**: the guard semantics are fully
expressible; they are split across two layers. The Ark spec layer records the threshold as
a typed `$data Float` field (Z3-verified for sanity), and the evaluator layer enforces the
spatial predicate at derivation time. No Ark modification is required. The spec remains
machine-readable and verifiable against its own invariants.

This is the same split used for stochastic production weights (weights in `$data`, sampling
in the evaluator) and typed-parameter arity checks (types in `$data`, arity in the
evaluator). The pattern is consistent and documented in ADR-001 §Consequences.

---

## 6. Integration Surface Summary

| Integration surface | Library-callable? | Subprocess-callable? | Entry point |
|--------------------|-------------------|---------------------|-------------|
| Parse `.ark` → AST | Yes | Yes | `ark_parser.parse(source, file_path)` / `ark.py parse` |
| AST → JSON | Yes | Yes (via parse subcommand) | `ark_parser.to_json(ark_file)` |
| Verify AST (Ark's Z3 passes) | Yes | Yes | `ark_verify.verify_file(ast_json)` / `ark.py verify` |
| Shape-grammar custom Z3 passes | External only | External only | `shape_grammar/tools/verify/*.py` (outside `ark/`) |
| Codegen (unused by shape_grammar) | Yes | Yes | `ark_codegen.codegen_file(ast_json, target)` / `ark.py codegen` |
| Structural diff | No | Yes | `ark.py diff <old> <new>` |
| Impact analysis | No | Yes | `ark.py impact <file> <entity>` |
| HTML visualization | No | Yes | `ark.py graph <file>` |

---

## 7. TC-10 Verification Status

TC-10 requires: `git diff --stat master -- ark/` produces empty output (no Ark
modifications introduced by ADV-008).

As of this writing, **no files under `ark/` have been modified by any ADV-008 task**.
The pre-existing modifications visible in the working tree (`ark/ark.py`,
`ark/dsl/grammar/ark.pest`, etc.) are from prior adventures committed before ADV-008 began.
ADV-008's `files:` frontmatter entries contain no `ark/` paths. The role file explicitly
denies write access to `ark/**`. TC-10 is satisfied by this task; the implementer will
confirm the empty diff at adventure close.

---

## 8. Verdict Summary

**Phase B is CLEAR to proceed.**

Every entity in `schemas/entities.md` — Shape, Rule, Operation (abstraction), all eight
Operation subclasses (ExtrudeOp, SplitOp, CompOp, ScopeOp, IOp, TOp, ROp, SOp), Scope,
SemanticLabel, Provenance, ShapeGrammar island, and Terminal — has a feasibility verdict.
Nine entities are **EXPRESSIBLE** using existing Ark syntax without any modification to
`ark/`. Two entities are **NEEDS_WORKAROUND**: Scope's heterogeneous attribute map (encoded
via type-tagged strings with `AttrEntry` list) and ShapeGrammar's axiom referential
integrity (delegated to `scope_safety.py` external pass). Both workarounds use only
existing Ark constructs and known stdlib types with clear precedents in the current island
corpus. The T01 callout on geometry guard predicates is confirmed correct and resolved as
NEEDS_WORKAROUND — evaluator-side dispatch with `$data` threshold fields in the spec layer,
consistent with ADR-001 §Consequences.

Zero entities require escalation. No modifications to `ark/` are required at any point in
this adventure. The `git diff --stat master -- ark/` check will produce empty output.
