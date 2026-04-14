"""
Evolution Verifier
Checks evolution-specific invariants in ARK evolution specs using Z3.

Checks:
  1. Split ratio validity      — train+val+test must sum to 1.0, all >= 0
  2. Fitness weight validity   — dimension weights must sum to 1.0, all >= 0
  3. Gate tolerance bounds     — tolerance must be in (0, 1.0]
  4. Evolution target files    — file reference must be non-empty
  5. Cross-reference integrity — evolution_run refs must resolve
  6. Constraint ref integrity  — evolution_target constraint refs must resolve
  7. Optimizer parameter bounds— iterations > 0, population_size > 0
"""

from z3 import (
    Real, Int, And, Solver, sat, unsat, RealVal, IntVal, Sum,
)

# ============================================================
# RESULT HELPERS
# ============================================================

EVOLUTION_KINDS = {
    "eval_dataset",
    "fitness_function",
    "benchmark_gate",
    "evolution_target",
    "evolution_run",
    "optimizer",
    "constraint",
}


def _pass(check: str, entity: str, message: str) -> dict:
    return {"check": check, "entity": entity, "status": "pass", "message": message}


def _fail(check: str, entity: str, message: str) -> dict:
    return {"check": check, "entity": entity, "status": "fail", "message": message}


def _warn(check: str, entity: str, message: str) -> dict:
    return {"check": check, "entity": entity, "status": "warn", "message": message}


# ============================================================
# HELPERS: Extract items by kind
# ============================================================

def _collect(items: list, kind: str) -> list:
    """Return all items whose 'kind' matches the given kind string."""
    return [it for it in items if isinstance(it, dict) and it.get("kind") == kind]


def _name(item: dict, fallback: str = "<unnamed>") -> str:
    return item.get("name") or item.get("id") or fallback


def _items_from_ark(ark_file: dict) -> list:
    """Extract the flat items list from an ARK AST dict."""
    raw = ark_file.get("items", [])
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        # name-keyed index
        return list(raw.values())
    return []


# ============================================================
# CHECK 1: Split Ratio Validity
# ============================================================

def verify_split_ratios(eval_datasets: list) -> list:
    """For each eval_dataset, verify train+val+test == 1.0, all >= 0.

    Uses Z3 Real variables to model the constraint. If the constraint
    system is UNSAT, the values violate the invariant.

    Returns a list of result dicts.
    """
    results = []

    for ds in eval_datasets:
        name = _name(ds)
        split = ds.get("split") or ds.get("split_ratio") or ds.get("splits") or {}
        if isinstance(split, dict):
            train = split.get("train")
            val   = split.get("val")
            test  = split.get("test")
        else:
            # No split info present — skip with a warning
            results.append(_warn(
                "evolution_split_ratio", name,
                f"Dataset '{name}' has no split_ratio field — skipping"
            ))
            continue

        # If any value is missing, skip with a warning
        if train is None or val is None or test is None:
            results.append(_warn(
                "evolution_split_ratio", name,
                f"Dataset '{name}' missing split fields (train={train}, val={val}, test={test})"
            ))
            continue

        try:
            t = float(train)
            v = float(val)
            te = float(test)
        except (TypeError, ValueError):
            results.append(_warn(
                "evolution_split_ratio", name,
                f"Dataset '{name}' has non-numeric split values"
            ))
            continue

        # Z3 check: train + val + test == 1.0, all >= 0
        z_train = Real("train")
        z_val   = Real("val")
        z_test  = Real("test")
        s = Solver()
        s.add(z_train == RealVal(t))
        s.add(z_val   == RealVal(v))
        s.add(z_test  == RealVal(te))
        s.add(z_train >= RealVal(0))
        s.add(z_val   >= RealVal(0))
        s.add(z_test  >= RealVal(0))
        s.add(z_train + z_val + z_test == RealVal(1))

        result = s.check()
        if result == unsat:
            total = t + v + te
            results.append(_fail(
                "evolution_split_ratio", name,
                f"Dataset '{name}' split ratios do not sum to 1.0: "
                f"{t}+{v}+{te}={total:.6f}"
            ))
        elif result == sat:
            results.append(_pass(
                "evolution_split_ratio", name,
                f"Dataset '{name}' split ratios valid ({t}+{v}+{te}=1.0)"
            ))
        else:
            results.append(_warn(
                "evolution_split_ratio", name,
                f"Dataset '{name}' Z3 returned UNKNOWN for split ratio check"
            ))

    return results


# ============================================================
# CHECK 2: Fitness Weight Validity
# ============================================================

def verify_fitness_weights(fitness_functions: list) -> list:
    """For each fitness_function, verify that dimension weights sum to 1.0.

    Uses Z3 Sum() over Real variables. If unsat, weights are invalid.

    Returns a list of result dicts.
    """
    results = []

    for ff in fitness_functions:
        name = _name(ff)
        dimensions = ff.get("dimensions") or ff.get("rubric") or []
        if not dimensions:
            results.append(_warn(
                "evolution_fitness_weights", name,
                f"Fitness function '{name}' has no dimensions — skipping"
            ))
            continue

        weight_vals = []
        parse_error = False
        for i, dim in enumerate(dimensions):
            if isinstance(dim, dict):
                w = dim.get("weight")
            else:
                w = None
            if w is None:
                results.append(_warn(
                    "evolution_fitness_weights", name,
                    f"Fitness function '{name}' dimension[{i}] missing weight"
                ))
                parse_error = True
                break
            try:
                weight_vals.append(float(w))
            except (TypeError, ValueError):
                results.append(_warn(
                    "evolution_fitness_weights", name,
                    f"Fitness function '{name}' dimension[{i}] non-numeric weight"
                ))
                parse_error = True
                break

        if parse_error:
            continue

        # Z3 check: Sum(weights) == 1.0, all >= 0
        z_weights = [Real(f"w_{i}") for i in range(len(weight_vals))]
        s = Solver()
        for z_w, val in zip(z_weights, weight_vals):
            s.add(z_w == RealVal(val))
            s.add(z_w >= RealVal(0))
        s.add(Sum(z_weights) == RealVal(1))

        result = s.check()
        if result == unsat:
            total = sum(weight_vals)
            results.append(_fail(
                "evolution_fitness_weights", name,
                f"Fitness function '{name}' weights do not sum to 1.0 "
                f"(sum={total:.6f}, weights={weight_vals})"
            ))
        elif result == sat:
            results.append(_pass(
                "evolution_fitness_weights", name,
                f"Fitness function '{name}' weights valid (sum=1.0)"
            ))
        else:
            results.append(_warn(
                "evolution_fitness_weights", name,
                f"Fitness function '{name}' Z3 returned UNKNOWN for weight check"
            ))

    return results


# ============================================================
# CHECK 3: Benchmark Gate Tolerance Bounds
# ============================================================

def verify_gate_tolerances(benchmark_gates: list) -> list:
    """For each benchmark_gate, verify tolerance is in (0, 1.0].

    Uses Z3 Real to check: tolerance > 0 AND tolerance <= 1.0.

    Returns a list of result dicts.
    """
    results = []

    for gate in benchmark_gates:
        name = _name(gate)
        tol = gate.get("tolerance") if "tolerance" in gate else gate.get("threshold")

        if tol is None:
            results.append(_warn(
                "evolution_gate_tolerance", name,
                f"Benchmark gate '{name}' has no tolerance field — skipping"
            ))
            continue

        try:
            tol_val = float(tol)
        except (TypeError, ValueError):
            results.append(_warn(
                "evolution_gate_tolerance", name,
                f"Benchmark gate '{name}' non-numeric tolerance '{tol}'"
            ))
            continue

        # Z3 check: tolerance > 0 AND tolerance <= 1.0
        z_tol = Real("tolerance")
        s = Solver()
        s.add(z_tol == RealVal(tol_val))
        s.add(z_tol > RealVal(0))
        s.add(z_tol <= RealVal(1))

        result = s.check()
        if result == unsat:
            results.append(_fail(
                "evolution_gate_tolerance", name,
                f"Benchmark gate '{name}' tolerance {tol_val} out of bounds (0, 1.0]"
            ))
        elif result == sat:
            results.append(_pass(
                "evolution_gate_tolerance", name,
                f"Benchmark gate '{name}' tolerance {tol_val} in bounds (0, 1.0]"
            ))
        else:
            results.append(_warn(
                "evolution_gate_tolerance", name,
                f"Benchmark gate '{name}' Z3 returned UNKNOWN for tolerance check"
            ))

    return results


# ============================================================
# CHECK 4: Evolution Target File References
# ============================================================

def verify_target_files(evolution_targets: list) -> list:
    """For each evolution_target, check that the file reference is non-empty.

    Simple string check — file existence is a runtime concern, not a
    structural verification concern.

    Returns a list of result dicts.
    """
    results = []

    for target in evolution_targets:
        name = _name(target)
        file_ref = target.get("file_ref") or target.get("file") or target.get("path") or target.get("source")

        if not file_ref or not str(file_ref).strip():
            results.append(_fail(
                "evolution_target_file", name,
                f"Evolution target '{name}' has empty file reference"
            ))
        else:
            results.append(_pass(
                "evolution_target_file", name,
                f"Evolution target '{name}' file reference: '{file_ref}'"
            ))

    return results


# ============================================================
# CHECK 5: Cross-Reference Integrity
# ============================================================

def verify_cross_references(evolution_runs: list, ark_file: dict) -> list:
    """For each evolution_run, verify all refs resolve to known items.

    Checks:
      - target_ref / target  → evolution_target names
      - optimizer_ref / optimizer → optimizer names
      - dataset_ref / dataset → eval_dataset names
      - gate_ref / gate → benchmark_gate names

    Returns a list of result dicts.
    """
    results = []
    items = _items_from_ark(ark_file)

    # Build lookup sets
    targets    = {_name(it) for it in _collect(items, "evolution_target")}
    optimizers = {_name(it) for it in _collect(items, "optimizer")}
    datasets   = {_name(it) for it in _collect(items, "eval_dataset")}
    gates      = {_name(it) for it in _collect(items, "benchmark_gate")}

    for run in evolution_runs:
        name = _name(run)
        all_ok = True

        def _check_ref(ref_val, known_set, kind):
            nonlocal all_ok
            if ref_val is None:
                return  # optional ref — skip
            if ref_val not in known_set:
                results.append(_fail(
                    "evolution_cross_reference", name,
                    f"Evolution run '{name}' references unknown {kind} '{ref_val}'"
                ))
                all_ok = False

        _check_ref(
            run.get("target") or run.get("target_ref"),
            targets,
            "evolution_target"
        )
        _check_ref(
            run.get("optimizer") or run.get("optimizer_ref"),
            optimizers,
            "optimizer"
        )
        _check_ref(
            run.get("dataset") or run.get("dataset_ref"),
            datasets,
            "eval_dataset"
        )
        _check_ref(
            run.get("gate") or run.get("gate_ref"),
            gates,
            "benchmark_gate"
        )

        if all_ok:
            results.append(_pass(
                "evolution_cross_reference", name,
                f"Evolution run '{name}' all references resolved"
            ))

    return results


# ============================================================
# CHECK 6: Constraint Reference Integrity
# ============================================================

def verify_constraint_refs(evolution_targets: list, constraints: list) -> list:
    """For each evolution_target, verify every constraint ref resolves.

    Returns a list of result dicts.
    """
    results = []
    known_constraints = {_name(c) for c in constraints}

    for target in evolution_targets:
        name = _name(target)
        refs = target.get("constraints") or target.get("constraint_refs") or []
        if isinstance(refs, str):
            refs = [refs]
        # Normalise: inline constraint items are dicts — extract their name or skip cross-ref
        ref_names = []
        for ref in refs:
            if isinstance(ref, dict):
                # Inline constraint block — no separate named constraint to resolve
                pass
            else:
                ref_names.append(ref)
        refs = ref_names

        target_ok = True
        for ref in refs:
            if ref not in known_constraints:
                results.append(_fail(
                    "evolution_constraint_ref", name,
                    f"Evolution target '{name}' references unknown constraint '{ref}'"
                ))
                target_ok = False

        if target_ok and refs:
            results.append(_pass(
                "evolution_constraint_ref", name,
                f"Evolution target '{name}' all {len(refs)} constraint ref(s) resolved"
            ))
        elif target_ok and not refs:
            results.append(_pass(
                "evolution_constraint_ref", name,
                f"Evolution target '{name}' has no constraint references"
            ))

    return results


# ============================================================
# CHECK 7: Optimizer Parameter Bounds
# ============================================================

def verify_optimizer_params(optimizers: list) -> list:
    """For each optimizer, verify iterations > 0 and population_size > 0.

    Uses Z3 Int variables to model the bounds.

    Returns a list of result dicts.
    """
    results = []

    for opt in optimizers:
        name = _name(opt)
        iterations   = opt.get("iterations")
        population   = (opt["population_size"] if "population_size" in opt
                        else opt.get("population"))

        opt_ok = True

        for param_name, param_val in [("iterations", iterations),
                                       ("population_size", population)]:
            if param_val is None:
                results.append(_warn(
                    "evolution_optimizer_params", name,
                    f"Optimizer '{name}' missing {param_name} — skipping bound check"
                ))
                continue

            try:
                int_val = int(param_val)
            except (TypeError, ValueError):
                results.append(_warn(
                    "evolution_optimizer_params", name,
                    f"Optimizer '{name}' non-integer {param_name}='{param_val}'"
                ))
                opt_ok = False
                continue

            # Z3 check: param > 0
            z_param = Int(param_name)
            s = Solver()
            s.add(z_param == IntVal(int_val))
            s.add(z_param > IntVal(0))

            result = s.check()
            if result == unsat:
                results.append(_fail(
                    "evolution_optimizer_params", name,
                    f"Optimizer '{name}' has invalid {param_name}: {int_val} (must be > 0)"
                ))
                opt_ok = False
            elif result != sat:
                results.append(_warn(
                    "evolution_optimizer_params", name,
                    f"Optimizer '{name}' Z3 returned UNKNOWN for {param_name} check"
                ))
                opt_ok = False

        if opt_ok:
            results.append(_pass(
                "evolution_optimizer_params", name,
                f"Optimizer '{name}' parameter bounds valid"
            ))

    return results


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def verify_evolution(ark_file: dict) -> list:
    """Run all evolution verification checks on a parsed ARK AST dict.

    Expected structure: ark_file with an 'items' key containing a list of
    dicts each with a 'kind' field identifying the evolution item type.

    Returns a flat list of result dicts with keys:
      - check: str — check identifier
      - entity: str — item name
      - status: "pass" | "fail" | "warn"
      - message: str — human-readable detail
    """
    items = _items_from_ark(ark_file)

    datasets         = _collect(items, "eval_dataset")
    fitness_fns      = _collect(items, "fitness_function")
    gates            = _collect(items, "benchmark_gate")
    targets          = _collect(items, "evolution_target")
    runs             = _collect(items, "evolution_run")
    optimizers       = _collect(items, "optimizer")
    constraints      = _collect(items, "constraint")

    print(f"\n{'='*60}")
    print("  Evolution Verification")
    print(f"{'='*60}")

    results: list = []

    def _run_check(label: str, check_results: list) -> None:
        results.extend(check_results)
        fails = [r for r in check_results if r["status"] == "fail"]
        warns = [r for r in check_results if r["status"] == "warn"]
        if fails:
            print(f"  x [{label}] {len(fails)} failure(s)")
            for r in fails:
                print(f"    -> {r['message']}")
        elif warns:
            print(f"  ? [{label}] {len(warns)} warning(s)")
            for r in warns:
                print(f"    -> {r['message']}")
        elif check_results:
            print(f"  v [{label}] {len(check_results)} item(s) OK")
        else:
            print(f"  - [{label}] no items to check")

    _run_check("split_ratios",    verify_split_ratios(datasets))
    _run_check("fitness_weights", verify_fitness_weights(fitness_fns))
    _run_check("gate_tolerances", verify_gate_tolerances(gates))
    _run_check("target_files",    verify_target_files(targets))
    _run_check("cross_refs",      verify_cross_references(runs, ark_file))
    _run_check("constraint_refs", verify_constraint_refs(targets, constraints))
    _run_check("optimizer_params",verify_optimizer_params(optimizers))

    total  = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    warned = sum(1 for r in results if r["status"] == "warn")

    print(f"\n  Evolution summary: {passed}/{total} passed, {failed} failed, {warned} warnings")
    print(f"{'='*60}")

    return results
