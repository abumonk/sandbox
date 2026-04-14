# Entity Schemas — shape_grammar

Entities are declared in `shape_grammar/specs/*.ark` using **existing Ark syntax**. The schemas below describe the shape of each entity as it will appear in the Ark islands and in the extracted IR.

## Shape

Abstract contract for any node in a derivation tree.

- `@in { scope: Scope, seed: Int }`
- `@out[] { children: [Shape] | terminal: Terminal }`
- Invariants:
  - `derivation_depth <= max_depth`
  - `deterministic_under(seed)`

## Rule

Concrete shape-grammar rule. Non-terminal rules expand to child shapes.

- Fields (`$data`):
  - `id: String` — unique within the island.
  - `lhs: String` — non-terminal symbol this rule matches.
  - `operations: [Operation]` — ordered operation sequence.
  - `label: SemanticLabel` (default inherited).
  - `is_terminal: Bool` (default false).
- Relations:
  - `Rule --produces--> Shape` (child non-terminals or terminals).
  - `Rule --references--> SemanticLabel`.

## Operation

Abstract base for operation primitives. Eight subclasses.

- Fields (`$data` inherited by all):
  - `id: String` — unique; used as RNG fork label.
- Subclasses:
  - `ExtrudeOp` — `$data height: Float`.
  - `SplitOp` — `$data axis: Axis {X, Y, Z}`, `$data sizes: [Float]`.
  - `CompOp` — `$data components: [Component {face, edge, vertex}]`.
  - `ScopeOp` — `$data attrs: Map<String, Any>`.
  - `IOp` — `$data asset: String` (terminal insertion).
  - `TOp` — `$data dx, dy, dz: Float` (translate).
  - `ROp` — `$data rx, ry, rz: Float` (rotate).
  - `SOp` — `$data sx, sy, sz: Float` (scale).

## Scope

Attribute bundle carried through a derivation.

- Fields (`$data`):
  - `translation: Vec3` — `{x, y, z: Float}`.
  - `rotation: Vec3`.
  - `scale: Vec3`.
  - `size: Vec3`.
  - `attrs: Map<String, Any>` — user-defined, inherited by children.
- Operation: `push(override: Map)` → new Scope with override applied.

## SemanticLabel

First-class semantic annotation on every shape node.

- Fields (`$data`):
  - `name: String` — e.g. `"window"`, `"load-bearing"`, `"api-node"`.
  - `tags: [String]` — secondary classifications.
  - `inherits: Bool = true` — whether children inherit this label unless overridden.
- Propagation: see `design-semantic-rendering.md`.

## Provenance

Chain of rule IDs from the axiom to any derived shape.

- Fields (`$data`):
  - `rule_chain: [String]` — ordered list of rule IDs.
  - `depth: Int` — length of chain (= derivation depth).
- Operation: `extend(rule_id: String) -> Provenance` (pure; returns new instance).

## ShapeGrammar (island)

Top-level island declaring a grammar.

- Fields (`$data`):
  - `max_depth: Int` — hard bound on derivation depth (Z3-checked).
  - `seed: Int` — deterministic RNG seed.
  - `axiom: String` — starting non-terminal.
  - `rules: [Rule]`.
  - `semantic_labels: [SemanticLabel]`.
- Relations:
  - `ShapeGrammar --contains--> Rule`.
  - `ShapeGrammar --references--> SemanticLabel`.

## Terminal

Runtime-only (not in `.ark` source; emitted by the evaluator).

- Fields:
  - `shape: GeometryPrimitive` — mesh, sphere, cylinder, etc.
  - `scope: Scope` — final scope state.
  - `label: SemanticLabel`.
  - `provenance: Provenance`.
