# Process Schemas — shape_grammar

## IR extraction

### extract_ir(ark_file) -> ShapeGrammarIR

1. Invoke Ark parser: `ast = ark_parser.parse(ark_file)`.
2. Locate the `ShapeGrammar` island in the AST.
3. For each `class Rule : Shape`, extract: id, lhs, operations, label.
4. For each operation class, extract subtype + operation-specific fields.
5. Extract `max_depth`, `seed`, `axiom` from the island's `$data`.
6. Extract semantic labels and build the label dictionary.
7. Build `Provenance` seeds for the axiom.
8. Return `ShapeGrammarIR(max_depth, seed, rules, axiom, semantic_labels, provenance)`.

Error paths:
- AST missing `ShapeGrammar` island → `IRError("no ShapeGrammar island found")`.
- Rule missing `operations` field → `IRError("rule {id} has no operations")`.
- `max_depth` not a positive Int → `IRError("max_depth must be positive Int")`.

## Verifier passes

### verify_termination(ir) -> Result

1. Build Z3 model: `depth(node)` Int var for every rule expansion node.
2. Assert `depth(axiom) == 0`.
3. Assert `forall (parent, child) in expansion_edges: depth(child) == depth(parent) + 1`.
4. Obligation: `exists node: depth(node) > max_depth` is UNSAT.
5. Z3 solve. UNSAT = PASS. SAT = FAIL with counter-example.

Error paths:
- Data-dependent expansion count (SplitOp with runtime-valued `count`) → `PASS_OPAQUE`.
- Z3 timeout (>30s) → `PASS_UNKNOWN`.

### verify_determinism(ir) -> Result

1. Structural scan: every `#process` body references only `$data`, op inputs, or `rng.fork(label)` with literal label.
2. Island has exactly one `$data seed: Int`.
3. No op declared with `unordered: true` (assert absence).
4. Z3 obligation: symbolic evaluation with `seed1 == seed2` produces identical output sequence.
5. UNSAT of `seed1 == seed2 AND output1 != output2` = PASS.

Error paths:
- Wall-clock or env read detected → FAIL with the offending reference.
- Multiple seed fields → FAIL.

### verify_scope(ir) -> Result

1. Build rule graph with scope effects per edge.
2. For each `scope.get(attr)` call, symbolic path analysis: is `attr` defined on every path from axiom to this op?
3. Z3 obligation: `exists path: attr not defined when op executes` = UNSAT.

Error paths:
- Scope attr used before defined → FAIL with path witness.

## Evaluation

### evaluate(ir, seed) -> list[Terminal]

See `design-evaluator.md` for full pseudocode. Summary:

1. Initialize `rng = SeededRng(seed)`, `stack = ScopeStack([Scope.identity()])`.
2. Initialize worklist with `(axiom, initial_scope, default_label, root_provenance)`.
3. Loop: pop FIFO, resolve rule, dispatch ops, emit children or terminal.
4. Guard: `provenance.depth > max_depth` raises `EvaluationError`.
5. Return list of `Terminal`s.

Error paths:
- `max_depth` exceeded at runtime → `EvaluationError` (should not occur if termination pass passed).
- Undefined symbol referenced → `EvaluationError`.

## OBJ emission

### write_obj(terminals, path) -> None

1. Group terminals by `label.name`.
2. For each group, emit an OBJ `g <name>` directive.
3. For each terminal, accumulate vertices (with dedup) and faces.
4. Write `v x y z` and `f i1 i2 i3` lines.
5. Write final file to `path`; caller checks size > 0.

## Adapter invocation

### augment_graph(ark_file, out_html) -> None

1. `subprocess.run(['ark', 'graph', ark_file, '--out', tmp_html])`.
2. Parse the embedded JSON graph data from `tmp_html`.
3. For each node with `class in {Rule, Operation}`, resolve its `SemanticLabel`, inject a CSS class into the HTML.
4. Write augmented HTML to `out_html`.

Error paths:
- `ark graph` nonzero exit → propagate with context.
- Expected JSON blob missing → `AdapterError("visualizer output changed; see research/ark-as-host-feasibility.md")`.

### shape_impact(ark_file, entity) -> dict

1. `subprocess.run(['ark', 'impact', ark_file, entity])` → parsed dict.
2. Load IR; collect every rule referencing `entity` directly or transitively.
3. Merge rule-tree edges into Ark's impact report dict.
4. Return combined dict.

### shape_diff(old_ark, new_ark) -> dict

1. `subprocess.run(['ark', 'diff', old_ark, new_ark])` → structural diff dict.
2. Load old + new IR.
3. Diff rules by id: added, removed, modified (operation sequence, label).
4. Merge with Ark's structural diff.
5. Return combined dict.
