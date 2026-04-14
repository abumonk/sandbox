# Z3 Verification — Design

## Overview
Implement Z3-based verification for evolution .ark specs in `tools/verify/evolution_verify.py`. Checks structural integrity, mathematical constraints, and cross-reference validity of evolution items.

## Target Files
- `ark/tools/verify/evolution_verify.py` — Z3 verification for evolution items
- `ark/tools/verify/ark_verify.py` — Integration point (call evolution verifier)

## Approach

### Verification Checks

Following the studio_verify.py pattern (separate module, returns list of result dicts):

1. **Split ratio validity**: For every `eval_dataset`, verify train + val + test = 1.0 and all >= 0.
   - Z3: `Real('train') + Real('val') + Real('test') == 1.0`, `train >= 0`, etc.
   - Error: "Dataset '{name}' split ratios do not sum to 1.0: {train}+{val}+{test}={sum}"

2. **Fitness weight validity**: For every `fitness_function`, verify dimension weights sum to 1.0.
   - Z3: `Sum(weights) == 1.0`, all `weight >= 0`.
   - Error: "Fitness function '{name}' weights do not sum to 1.0"

3. **Benchmark gate tolerance bounds**: For every `benchmark_gate`, verify tolerance > 0 and tolerance <= 1.0.
   - Z3: `Real('tolerance') > 0`, `Real('tolerance') <= 1.0`
   - Error: "Benchmark gate '{name}' tolerance {val} out of bounds (0, 1.0]"

4. **Evolution target file reference**: For every `evolution_target`, verify the `file:` path is non-empty.
   - Simple string check (not Z3 — file existence is a runtime check).
   - Error: "Evolution target '{name}' has empty file reference"

5. **Cross-reference integrity**: For every `evolution_run`:
   - `target:` must reference an existing `evolution_target` name
   - `optimizer:` must reference an existing `optimizer` name
   - `dataset:` must reference an existing `eval_dataset` name
   - `gate:` must reference an existing `benchmark_gate` name
   - Error: "Evolution run '{name}' references unknown {kind} '{ref}'"

6. **Constraint reference integrity**: For every `evolution_target`, each name in `constraints:` must reference an existing `constraint` item.
   - Error: "Evolution target '{name}' references unknown constraint '{ref}'"

7. **Optimizer parameter bounds**: For every `optimizer`:
   - `iterations > 0`
   - `population > 0`
   - Z3 for numeric bound checks
   - Error: "Optimizer '{name}' has invalid {param}: {val}"

### Integration with ark_verify.py

Add to `verify_file()`:
```python
# After existing studio verify integration
if has_evolution_items(ast_json):
    from evolution_verify import verify_evolution
    results.extend(verify_evolution(ast_json))
```

### Key Functions

```python
def verify_evolution(ast_json: dict) -> list[dict]:
    """Run all evolution verification checks. Returns list of result dicts."""

def verify_split_ratios(datasets: list[dict]) -> list[dict]
def verify_fitness_weights(fitness_fns: list[dict]) -> list[dict]
def verify_gate_tolerances(gates: list[dict]) -> list[dict]
def verify_target_files(targets: list[dict]) -> list[dict]
def verify_cross_references(runs: list[dict], all_items: dict) -> list[dict]
def verify_constraint_refs(targets: list[dict], constraints: list[dict]) -> list[dict]
def verify_optimizer_params(optimizers: list[dict]) -> list[dict]
```

### Result Format (same as studio_verify.py)
```python
{"check": "evolution_split_ratio", "entity": name, "status": "pass"|"fail", "message": str}
```

### Design Decisions
- Follow PASS_OPAQUE pattern from ADV-002: evolution-specific semantics are verified structurally, not semantically
- Z3 used for numeric constraint checks (split ratios, weights, tolerances, bounds)
- Cross-reference checks are simple name lookups (no Z3 needed)
- Separate module per knowledge base pattern: "Separate Domain Modules"

## Dependencies
- design-dsl-surface (evolution AST items for verification input)
- design-evolution-schema (types referenced in verification)

## Target Conditions
- TC-032: Split ratio verification catches ratios not summing to 1.0
- TC-033: Fitness weight verification catches weights not summing to 1.0
- TC-034: Benchmark gate tolerance verification catches out-of-bounds values
- TC-035: Cross-reference verification catches unknown target/optimizer/dataset/gate references
- TC-036: `ark verify <spec>` runs evolution checks when evolution items are present
