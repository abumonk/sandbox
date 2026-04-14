"""
evolution_codegen.py — Code generation for evolution .ark artifacts.

Generates from evolution .ark specs:
  - datasets/{name}.jsonl       — JSONL template with placeholder test cases
  - scoring/{name}_scorer.py    — Python scoring script skeleton with rubric constants
  - runs/{name}_config.json     — JSON config with resolved references
  - reports/{name}_report.md    — Markdown report template

Pipeline:  .ark → parse → ArkFile AST → evolution_codegen → .jsonl / .py / .json / .md
"""

import json
import os
from pathlib import Path
from typing import Optional, Union


# ---------------------------------------------------------------------------
# gen_dataset_jsonl
# ---------------------------------------------------------------------------

def gen_dataset_jsonl(eval_dataset) -> str:
    """
    Generate a JSONL template from an EvalDatasetDef AST item.

    Each line is a JSON object representing one placeholder test case.
    The number of lines is determined by the dataset's data_fields or
    defaults to 10. Splits are distributed according to the splits ratios.

    Args:
        eval_dataset: An EvalDatasetDef dataclass instance or dict with fields:
            name, source, splits, scoring_rubric, data_fields, description.

    Returns:
        A string containing newline-delimited JSON objects (JSONL format).
    """
    # Normalise: accept both dataclass and dict
    if isinstance(eval_dataset, dict):
        name = eval_dataset.get("name", "dataset")
        source = eval_dataset.get("source") or ""
        splits = eval_dataset.get("splits") or {}
        scoring_rubric = eval_dataset.get("scoring_rubric") or ""
        data_fields = eval_dataset.get("data_fields") or []
        description = eval_dataset.get("description") or ""
    else:
        name = getattr(eval_dataset, "name", "dataset")
        source = getattr(eval_dataset, "source", None) or ""
        splits = getattr(eval_dataset, "splits", None) or {}
        scoring_rubric = getattr(eval_dataset, "scoring_rubric", None) or ""
        data_fields = getattr(eval_dataset, "data_fields", None) or []
        description = getattr(eval_dataset, "description", None) or ""

    # Determine total size from data_fields or default
    size = 10
    for df in data_fields:
        fname = df.get("name", "") if isinstance(df, dict) else getattr(df, "name", "")
        if fname == "size":
            val = df.get("default") if isinstance(df, dict) else getattr(df, "default", None)
            if isinstance(val, (int, float)):
                size = int(val)
            elif isinstance(val, dict):
                # expr dict from parser — try to extract numeric value
                v = val.get("value") or val.get("num")
                if v is not None:
                    try:
                        size = int(v)
                    except (TypeError, ValueError):
                        pass
            break

    # Resolve splits: default to train/val/test 70/15/15 if not specified
    if splits:
        # Normalise ratios so they sum to 1.0
        total_ratio = sum(float(v) for v in splits.values())
        if total_ratio <= 0:
            total_ratio = 1.0
        split_fracs = {k: float(v) / total_ratio for k, v in splits.items()}
    else:
        split_fracs = {"train": 0.70, "val": 0.15, "test": 0.15}

    # Assign split labels to case indices
    split_labels = []
    remaining = size
    split_names = list(split_fracs.keys())
    for i, sname in enumerate(split_names):
        if i == len(split_names) - 1:
            count = remaining
        else:
            count = round(split_fracs[sname] * size)
        for _ in range(count):
            split_labels.append(sname)
        remaining -= count

    # Pad or trim to exact size
    while len(split_labels) < size:
        split_labels.append(split_names[-1] if split_names else "train")
    split_labels = split_labels[:size]

    # Build extra field names from data_fields (skip "size")
    extra_fields = []
    for df in data_fields:
        fname = df.get("name", "") if isinstance(df, dict) else getattr(df, "name", "")
        if fname and fname != "size":
            extra_fields.append(fname)

    # Emit JSONL lines
    lines = []
    for i in range(size):
        record = {
            "id": f"case_{i}",
            "input": "",
            "expected": "",
            "rubric_hints": scoring_rubric,
            "source": source,
            "split": split_labels[i],
        }
        for ef in extra_fields:
            record[ef] = ""
        lines.append(json.dumps(record, ensure_ascii=False))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gen_scoring_script
# ---------------------------------------------------------------------------

def gen_scoring_script(fitness_function) -> str:
    """
    Generate a Python scoring script skeleton from a FitnessFunctionDef AST item.

    Produces constants for rubric dimensions and weights, and a score() function
    skeleton ready to be filled in with actual judge logic.

    Args:
        fitness_function: A FitnessFunctionDef dataclass instance or dict with fields:
            name, dimensions, aggregation, data_fields, description.

    Returns:
        A string containing the Python scoring script skeleton.
    """
    if isinstance(fitness_function, dict):
        name = fitness_function.get("name", "scorer")
        dimensions = fitness_function.get("dimensions") or []
        aggregation = fitness_function.get("aggregation") or "weighted_average"
        description = fitness_function.get("description") or ""
    else:
        name = getattr(fitness_function, "name", "scorer")
        dimensions = getattr(fitness_function, "dimensions", None) or []
        aggregation = getattr(fitness_function, "aggregation", None) or "weighted_average"
        description = getattr(fitness_function, "description", None) or ""

    lines = []
    lines.append(f'"""')
    lines.append(f'{name}_scorer.py — Generated scoring script skeleton.')
    if description:
        lines.append(f'')
        lines.append(f'{description}')
    lines.append(f'')
    lines.append(f'Generated by evolution_codegen — fill in the judge logic before running.')
    lines.append(f'"""')
    lines.append(f'')
    lines.append(f'from typing import Any')
    lines.append(f'')
    lines.append(f'')
    lines.append(f'# ---------------------------------------------------------------------------')
    lines.append(f'# Rubric constants (from fitness_function "{name}" in .ark spec)')
    lines.append(f'# ---------------------------------------------------------------------------')
    lines.append(f'')

    if dimensions:
        lines.append(f'RUBRIC_DIMENSIONS = [')
        for dim in dimensions:
            if isinstance(dim, dict):
                dim_name = dim.get("name", "unnamed")
                dim_weight = dim.get("weight", 1.0)
                dim_metric = dim.get("metric") or "custom"
            else:
                dim_name = getattr(dim, "name", "unnamed")
                dim_weight = getattr(dim, "weight", 1.0)
                dim_metric = getattr(dim, "metric", None) or "custom"
            lines.append(f'    {{"name": {json.dumps(dim_name)}, "weight": {dim_weight}, "metric": {json.dumps(dim_metric)}}},')
        lines.append(f']')
        lines.append(f'')

        # Emit individual weight constants for convenience
        for dim in dimensions:
            if isinstance(dim, dict):
                dim_name = dim.get("name", "unnamed")
                dim_weight = dim.get("weight", 1.0)
            else:
                dim_name = getattr(dim, "name", "unnamed")
                dim_weight = getattr(dim, "weight", 1.0)
            const_name = dim_name.upper().replace("-", "_").replace(" ", "_")
            lines.append(f'WEIGHT_{const_name} = {dim_weight}')
    else:
        lines.append(f'RUBRIC_DIMENSIONS = []  # No dimensions defined in spec')
        lines.append(f'')

    lines.append(f'')
    lines.append(f'AGGREGATION = {json.dumps(aggregation)}')
    lines.append(f'')
    lines.append(f'')
    lines.append(f'# ---------------------------------------------------------------------------')
    lines.append(f'# Scoring function skeleton')
    lines.append(f'# ---------------------------------------------------------------------------')
    lines.append(f'')
    lines.append(f'def score(output: Any, expected: Any) -> float:')
    lines.append(f'    """')
    lines.append(f'    Score a model output against the expected answer.')
    lines.append(f'    ')
    lines.append(f'    Args:')
    lines.append(f'        output:   The model\'s output to evaluate.')
    lines.append(f'        expected: The reference / ground-truth answer.')
    lines.append(f'    ')
    lines.append(f'    Returns:')
    lines.append(f'        A float in [0.0, 1.0] representing the composite fitness score.')
    lines.append(f'    """')
    lines.append(f'    dim_scores = {{}}')
    lines.append(f'')

    if dimensions:
        for dim in dimensions:
            if isinstance(dim, dict):
                dim_name = dim.get("name", "unnamed")
                dim_metric = dim.get("metric") or "custom"
            else:
                dim_name = getattr(dim, "name", "unnamed")
                dim_metric = getattr(dim, "metric", None) or "custom"
            lines.append(f'    # TODO: implement {json.dumps(dim_name)} scoring (metric: {dim_metric})')
            safe_name = dim_name.replace("-", "_").replace(" ", "_")
            lines.append(f'    dim_scores[{json.dumps(dim_name)}] = 0.0  # replace with real {safe_name} score')
            lines.append(f'')
    else:
        lines.append(f'    # TODO: implement scoring dimensions')
        lines.append(f'    dim_scores["overall"] = 0.0  # replace with real score')
        lines.append(f'')

    lines.append(f'    return _aggregate(dim_scores)')
    lines.append(f'')
    lines.append(f'')
    lines.append(f'def _aggregate(dim_scores: dict) -> float:')
    lines.append(f'    """Aggregate dimension scores using {aggregation}."""')
    lines.append(f'    if not dim_scores:')
    lines.append(f'        return 0.0')

    if aggregation in ("weighted_average", "weighted_sum"):
        lines.append(f'    weights = {{d["name"]: d["weight"] for d in RUBRIC_DIMENSIONS}}')
        lines.append(f'    total_weight = sum(weights.get(k, 1.0) for k in dim_scores)')
        lines.append(f'    if total_weight == 0:')
        lines.append(f'        return 0.0')
        lines.append(f'    return sum(dim_scores[k] * weights.get(k, 1.0) for k in dim_scores) / total_weight')
    elif aggregation == "min":
        lines.append(f'    return min(dim_scores.values())')
    elif aggregation == "max":
        lines.append(f'    return max(dim_scores.values())')
    else:
        lines.append(f'    # aggregation: {aggregation}')
        lines.append(f'    total_weight = sum(d["weight"] for d in RUBRIC_DIMENSIONS) or 1.0')
        lines.append(f'    weights = {{d["name"]: d["weight"] for d in RUBRIC_DIMENSIONS}}')
        lines.append(f'    return sum(dim_scores[k] * weights.get(k, 1.0) for k in dim_scores) / total_weight')

    lines.append(f'')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gen_run_config
# ---------------------------------------------------------------------------

def gen_run_config(evolution_run, ark_file) -> str:
    """
    Generate a JSON run config from an EvolutionRunDef AST item.

    Resolves references (target, optimizer, dataset, gate) by looking them up
    in the ark_file's index dictionaries.

    Args:
        evolution_run: An EvolutionRunDef dataclass instance or dict with fields:
            name, target_ref, optimizer_ref, dataset_ref, gate_ref, status.
        ark_file: An ArkFile instance (or dict-like) whose index dicts are used
            to resolve named references. Accepts either the ArkFile dataclass or
            a plain dict with keys "evolution_targets", "optimizers",
            "eval_datasets", "benchmark_gates".

    Returns:
        A pretty-printed JSON string representing the run configuration.
    """
    if isinstance(evolution_run, dict):
        run_name = evolution_run.get("name", "run")
        target_ref = evolution_run.get("target_ref") or ""
        optimizer_ref = evolution_run.get("optimizer_ref") or ""
        dataset_ref = evolution_run.get("dataset_ref") or ""
        gate_ref = evolution_run.get("gate_ref") or ""
        status = evolution_run.get("status") or "pending"
        description = evolution_run.get("description") or ""
    else:
        run_name = getattr(evolution_run, "name", "run")
        target_ref = getattr(evolution_run, "target_ref", None) or ""
        optimizer_ref = getattr(evolution_run, "optimizer_ref", None) or ""
        dataset_ref = getattr(evolution_run, "dataset_ref", None) or ""
        gate_ref = getattr(evolution_run, "gate_ref", None) or ""
        status = getattr(evolution_run, "status", None) or "pending"
        description = getattr(evolution_run, "description", None) or ""

    # Helper to get an index dict from ark_file (dataclass or dict)
    def _get_index(key: str) -> dict:
        if isinstance(ark_file, dict):
            return ark_file.get(key) or {}
        return getattr(ark_file, key, None) or {}

    evolution_targets = _get_index("evolution_targets")
    optimizers = _get_index("optimizers")
    eval_datasets = _get_index("eval_datasets")
    benchmark_gates = _get_index("benchmark_gates")

    # Resolve target
    target_info = {}
    if target_ref and target_ref in evolution_targets:
        t = evolution_targets[target_ref]
        if isinstance(t, dict):
            target_info = {
                "name": t.get("name", target_ref),
                "file": t.get("file") or "",
                "description": t.get("description") or "",
            }
        else:
            target_info = {
                "name": getattr(t, "name", target_ref),
                "file": getattr(t, "file", None) or "",
                "description": getattr(t, "description", None) or "",
            }
    else:
        target_info = {"name": target_ref, "file": "", "description": ""}

    # Resolve optimizer
    optimizer_info = {}
    if optimizer_ref and optimizer_ref in optimizers:
        o = optimizers[optimizer_ref]
        if isinstance(o, dict):
            optimizer_info = {
                "name": o.get("name", optimizer_ref),
                "engine": o.get("engine") or "",
                "iterations": o.get("iterations") or 0,
                "population_size": o.get("population_size") or 0,
                "mutation_strategy": o.get("mutation_strategy") or "",
            }
        else:
            optimizer_info = {
                "name": getattr(o, "name", optimizer_ref),
                "engine": getattr(o, "engine", None) or "",
                "iterations": getattr(o, "iterations", None) or 0,
                "population_size": getattr(o, "population_size", None) or 0,
                "mutation_strategy": getattr(o, "mutation_strategy", None) or "",
            }
    else:
        optimizer_info = {
            "name": optimizer_ref,
            "engine": "",
            "iterations": 0,
            "population_size": 0,
            "mutation_strategy": "",
        }

    # Resolve dataset
    dataset_info = {}
    if dataset_ref and dataset_ref in eval_datasets:
        d = eval_datasets[dataset_ref]
        if isinstance(d, dict):
            dataset_info = {
                "name": d.get("name", dataset_ref),
                "source": d.get("source") or "",
                "splits": d.get("splits") or {},
                "path": f"datasets/{d.get('name', dataset_ref)}.jsonl",
            }
        else:
            dataset_info = {
                "name": getattr(d, "name", dataset_ref),
                "source": getattr(d, "source", None) or "",
                "splits": getattr(d, "splits", None) or {},
                "path": f"datasets/{getattr(d, 'name', dataset_ref)}.jsonl",
            }
    else:
        dataset_info = {
            "name": dataset_ref,
            "source": "",
            "splits": {},
            "path": f"datasets/{dataset_ref}.jsonl" if dataset_ref else "",
        }

    # Resolve gate
    gate_info = {}
    if gate_ref and gate_ref in benchmark_gates:
        g = benchmark_gates[gate_ref]
        if isinstance(g, dict):
            gate_info = {
                "name": g.get("name", gate_ref),
                "benchmark": g.get("benchmark") or "",
                "tolerance": g.get("tolerance") or 0.0,
                "pass_criteria": g.get("pass_criteria") or "",
            }
        else:
            gate_info = {
                "name": getattr(g, "name", gate_ref),
                "benchmark": getattr(g, "benchmark", None) or "",
                "tolerance": getattr(g, "tolerance", None) or 0.0,
                "pass_criteria": getattr(g, "pass_criteria", None) or "",
            }
    else:
        gate_info = {
            "name": gate_ref,
            "benchmark": "",
            "tolerance": 0.0,
            "pass_criteria": "",
        }

    config = {
        "run_name": run_name,
        "description": description,
        "status": status,
        "target": target_info,
        "optimizer": optimizer_info,
        "dataset": dataset_info,
        "gate": gate_info,
        "scoring_script": f"scoring/{optimizer_ref or run_name}_scorer.py",
        "output_dir": f"runs/{run_name}",
    }

    return json.dumps(config, indent=2)


# ---------------------------------------------------------------------------
# gen_evolution_report
# ---------------------------------------------------------------------------

def gen_evolution_report(evolution_run, results: Optional[dict] = None) -> str:
    """
    Generate a markdown report template from an EvolutionRunDef and optional results.

    Args:
        evolution_run: An EvolutionRunDef dataclass instance or dict with name/description.
        results: Optional dict with run results containing keys like:
            "best_score", "iterations", "fitness_trajectory", "best_variant",
            "constraint_results", "benchmark_results".

    Returns:
        A string containing the markdown report template.
    """
    if isinstance(evolution_run, dict):
        run_name = evolution_run.get("name", "run")
        description = evolution_run.get("description") or ""
        target_ref = evolution_run.get("target_ref") or ""
        optimizer_ref = evolution_run.get("optimizer_ref") or ""
        dataset_ref = evolution_run.get("dataset_ref") or ""
        gate_ref = evolution_run.get("gate_ref") or ""
    else:
        run_name = getattr(evolution_run, "name", "run")
        description = getattr(evolution_run, "description", None) or ""
        target_ref = getattr(evolution_run, "target_ref", None) or ""
        optimizer_ref = getattr(evolution_run, "optimizer_ref", None) or ""
        dataset_ref = getattr(evolution_run, "dataset_ref", None) or ""
        gate_ref = getattr(evolution_run, "gate_ref", None) or ""

    if results is None:
        results = {}

    best_score = results.get("best_score", "N/A")
    iterations = results.get("iterations", "N/A")
    fitness_trajectory = results.get("fitness_trajectory") or []
    best_variant = results.get("best_variant") or ""
    constraint_results = results.get("constraint_results") or []
    benchmark_results = results.get("benchmark_results") or []

    lines = []
    lines.append(f"# Evolution Run Report: {run_name}")
    lines.append(f"")
    if description:
        lines.append(f"> {description}")
        lines.append(f"")

    lines.append(f"## Summary")
    lines.append(f"")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Run name | `{run_name}` |")
    lines.append(f"| Target | `{target_ref}` |")
    lines.append(f"| Optimizer | `{optimizer_ref}` |")
    lines.append(f"| Dataset | `{dataset_ref}` |")
    lines.append(f"| Gate | `{gate_ref}` |")
    lines.append(f"| Best score | {best_score} |")
    lines.append(f"| Iterations completed | {iterations} |")
    lines.append(f"")

    lines.append(f"## Fitness Trajectory")
    lines.append(f"")
    if fitness_trajectory:
        lines.append(f"| Iteration | Score | Delta |")
        lines.append(f"|-----------|-------|-------|")
        prev_score = None
        for entry in fitness_trajectory:
            if isinstance(entry, dict):
                it = entry.get("iteration", "?")
                sc = entry.get("score", "?")
                delta = (sc - prev_score) if (prev_score is not None and isinstance(sc, (int, float)) and isinstance(prev_score, (int, float))) else "—"
                if isinstance(delta, float):
                    delta = f"{delta:+.4f}"
                lines.append(f"| {it} | {sc} | {delta} |")
                prev_score = sc
            else:
                lines.append(f"| ? | {entry} | — |")
    else:
        lines.append(f"<!-- Fill in fitness trajectory after run completes -->")
        lines.append(f"")
        lines.append(f"| Iteration | Score | Delta |")
        lines.append(f"|-----------|-------|-------|")
        lines.append(f"| 1 | — | — |")
    lines.append(f"")

    lines.append(f"## Best Variant")
    lines.append(f"")
    if best_variant:
        lines.append(f"```diff")
        lines.append(best_variant)
        lines.append(f"```")
    else:
        lines.append(f"<!-- Paste the diff of the best-scoring variant here -->")
        lines.append(f"")
        lines.append(f"```diff")
        lines.append(f"# Best variant diff will appear here after run completes")
        lines.append(f"```")
    lines.append(f"")

    lines.append(f"## Constraint Results")
    lines.append(f"")
    if constraint_results:
        lines.append(f"| Constraint | Status | Details |")
        lines.append(f"|------------|--------|---------|")
        for cr in constraint_results:
            if isinstance(cr, dict):
                cname = cr.get("name", "unknown")
                cstatus = cr.get("status", "unknown")
                cdetail = cr.get("details", "")
                lines.append(f"| {cname} | {cstatus} | {cdetail} |")
            else:
                lines.append(f"| {cr} | unknown | |")
    else:
        lines.append(f"<!-- Constraint verification results appear here -->")
        lines.append(f"")
        lines.append(f"| Constraint | Status | Details |")
        lines.append(f"|------------|--------|---------|")
        lines.append(f"| (none) | — | — |")
    lines.append(f"")

    lines.append(f"## Benchmark Results")
    lines.append(f"")
    if benchmark_results:
        lines.append(f"| Benchmark | Score | Pass |")
        lines.append(f"|-----------|-------|------|")
        for br in benchmark_results:
            if isinstance(br, dict):
                bname = br.get("benchmark", "unknown")
                bscore = br.get("score", "?")
                bpass = "yes" if br.get("pass") else "no"
                lines.append(f"| {bname} | {bscore} | {bpass} |")
            else:
                lines.append(f"| {br} | ? | — |")
    else:
        lines.append(f"<!-- Benchmark gate results appear here -->")
        lines.append(f"")
        lines.append(f"| Benchmark | Score | Pass |")
        lines.append(f"|-----------|-------|------|")
        lines.append(f"| (gate: {gate_ref or 'none'}) | — | — |")
    lines.append(f"")

    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*Generated by evolution_codegen — fill in results after the run completes.*")
    lines.append(f"")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# generate — main orchestrator
# ---------------------------------------------------------------------------

def generate(ark_file, output_dir: Optional[Union[str, Path]] = None) -> dict:
    """
    Generate all evolution artifacts from a parsed ArkFile or JSON dict.

    Produces:
      - datasets/{dataset_name}.jsonl     for each EvalDatasetDef
      - scoring/{function_name}_scorer.py for each FitnessFunctionDef
      - runs/{run_name}_config.json       for each EvolutionRunDef
      - reports/{run_name}_report.md      for each EvolutionRunDef

    Args:
        ark_file: A parsed ArkFile instance or JSON AST dict.
            When an ArkFile, uses .eval_datasets, .fitness_functions,
            .evolution_runs index dicts. When a dict, uses the "items" list.
        output_dir: Optional path. If provided, files are written to disk.

    Returns:
        dict mapping relative filename (str) → file content (str).
    """
    artifacts = {}

    eval_datasets = []
    fitness_functions = []
    evolution_runs = []

    # Accept both ArkFile dataclass and raw JSON AST dict
    if isinstance(ark_file, dict):
        # JSON AST path — iterate items list
        for item in ark_file.get("items", []):
            kind = item.get("kind", "")
            if kind == "eval_dataset":
                eval_datasets.append(item)
            elif kind == "fitness_function":
                fitness_functions.append(item)
            elif kind == "evolution_run":
                evolution_runs.append(item)
    else:
        # ArkFile dataclass path — use pre-built indices
        for ds in getattr(ark_file, "eval_datasets", {}).values():
            eval_datasets.append(ds)
        for ff in getattr(ark_file, "fitness_functions", {}).values():
            fitness_functions.append(ff)
        for er in getattr(ark_file, "evolution_runs", {}).values():
            evolution_runs.append(er)

        # Also scan items list in case indices are incomplete
        for item in getattr(ark_file, "items", []):
            try:
                from ark_parser import EvalDatasetDef, FitnessFunctionDef, EvolutionRunDef
            except ImportError:
                try:
                    from tools.parser.ark_parser import EvalDatasetDef, FitnessFunctionDef, EvolutionRunDef
                except ImportError:
                    EvalDatasetDef = FitnessFunctionDef = EvolutionRunDef = type(None)

            if isinstance(item, EvalDatasetDef):
                if not any(
                    (d.get("name") if isinstance(d, dict) else getattr(d, "name", None))
                    == getattr(item, "name", None)
                    for d in eval_datasets
                ):
                    eval_datasets.append(item)
            elif isinstance(item, FitnessFunctionDef):
                if not any(
                    (f.get("name") if isinstance(f, dict) else getattr(f, "name", None))
                    == getattr(item, "name", None)
                    for f in fitness_functions
                ):
                    fitness_functions.append(item)
            elif isinstance(item, EvolutionRunDef):
                if not any(
                    (r.get("name") if isinstance(r, dict) else getattr(r, "name", None))
                    == getattr(item, "name", None)
                    for r in evolution_runs
                ):
                    evolution_runs.append(item)

    # Generate dataset JSONL files
    for ds in eval_datasets:
        ds_name = ds.get("name") if isinstance(ds, dict) else getattr(ds, "name", "dataset")
        filename = f"datasets/{ds_name}.jsonl"
        artifacts[filename] = gen_dataset_jsonl(ds)

    # Generate scoring scripts
    for ff in fitness_functions:
        ff_name = ff.get("name") if isinstance(ff, dict) else getattr(ff, "name", "scorer")
        filename = f"scoring/{ff_name}_scorer.py"
        artifacts[filename] = gen_scoring_script(ff)

    # Generate run configs and report templates
    for er in evolution_runs:
        er_name = er.get("name") if isinstance(er, dict) else getattr(er, "name", "run")
        config_filename = f"runs/{er_name}_config.json"
        report_filename = f"reports/{er_name}_report.md"
        artifacts[config_filename] = gen_run_config(er, ark_file)
        artifacts[report_filename] = gen_evolution_report(er)

    # Write to disk if output_dir provided
    if output_dir is not None:
        out = Path(output_dir)
        for rel_path, content in artifacts.items():
            full_path = out / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

    return artifacts


# ---------------------------------------------------------------------------
# Inline smoke-test
# ---------------------------------------------------------------------------

def _smoke_test():
    """Quick self-test using mock dataclass instances (no parser needed)."""
    from dataclasses import dataclass, field as dc_field
    from typing import Optional as Opt

    @dataclass
    class MockEvalDataset:
        kind: str = "eval_dataset"
        name: str = "PromptQuality"
        source: Opt[str] = "internal"
        splits: dict = dc_field(default_factory=lambda: {"train": 0.7, "val": 0.15, "test": 0.15})
        scoring_rubric: Opt[str] = "correctness+clarity"
        data_fields: list = dc_field(default_factory=list)
        description: Opt[str] = "Test prompt quality"

    @dataclass
    class MockFitnessFunction:
        kind: str = "fitness_function"
        name: str = "ResponseQuality"
        dimensions: list = dc_field(default_factory=lambda: [
            {"name": "correctness", "weight": 0.5, "metric": "exact_match"},
            {"name": "clarity", "weight": 0.3, "metric": "human_eval"},
            {"name": "conciseness", "weight": 0.2, "metric": "length_penalty"},
        ])
        aggregation: Opt[str] = "weighted_average"
        data_fields: list = dc_field(default_factory=list)
        description: Opt[str] = "Overall response quality"

    @dataclass
    class MockEvolutionRun:
        kind: str = "evolution_run"
        name: str = "run_v1"
        target_ref: Opt[str] = "ResponseAgent"
        optimizer_ref: Opt[str] = "GridSearch"
        dataset_ref: Opt[str] = "PromptQuality"
        gate_ref: Opt[str] = "PerfGate"
        status: Opt[str] = "pending"
        data_fields: list = dc_field(default_factory=list)
        description: Opt[str] = "Initial evolution run"

    class MockArkFile:
        def __init__(self):
            self.items = []
            self.eval_datasets = {}
            self.fitness_functions = {}
            self.optimizers = {}
            self.benchmark_gates = {}
            self.evolution_targets = {}
            self.evolution_runs = {}

    # --- gen_dataset_jsonl ---
    ds = MockEvalDataset()
    jsonl = gen_dataset_jsonl(ds)
    lines = [l for l in jsonl.split("\n") if l.strip()]
    assert len(lines) == 10, f"Expected 10 JSONL lines, got {len(lines)}"
    first = json.loads(lines[0])
    assert first["id"] == "case_0"
    assert first["source"] == "internal"
    assert first["rubric_hints"] == "correctness+clarity"
    assert first["split"] in ("train", "val", "test")
    # Check split distribution (train should be ~70%)
    splits_found = [json.loads(l)["split"] for l in lines]
    assert splits_found.count("train") >= 6, f"Expected at least 6 train cases, got {splits_found.count('train')}"
    print("gen_dataset_jsonl: PASS")

    # --- gen_scoring_script ---
    ff = MockFitnessFunction()
    script = gen_scoring_script(ff)
    assert "RUBRIC_DIMENSIONS" in script
    assert "WEIGHT_CORRECTNESS" in script
    assert "WEIGHT_CLARITY" in script
    assert "WEIGHT_CONCISENESS" in script
    assert "AGGREGATION" in script
    assert "weighted_average" in script
    assert "def score(" in script
    assert "def _aggregate(" in script
    assert "correctness" in script
    assert "clarity" in script
    print("gen_scoring_script: PASS")

    # --- gen_run_config ---
    er = MockEvolutionRun()
    ark_file = MockArkFile()
    config_json = gen_run_config(er, ark_file)
    config = json.loads(config_json)
    assert config["run_name"] == "run_v1"
    assert config["target"]["name"] == "ResponseAgent"
    assert config["optimizer"]["name"] == "GridSearch"
    assert config["dataset"]["name"] == "PromptQuality"
    assert config["gate"]["name"] == "PerfGate"
    assert "output_dir" in config
    print("gen_run_config: PASS")

    # --- gen_evolution_report ---
    report = gen_evolution_report(er)
    assert "# Evolution Run Report: run_v1" in report
    assert "## Summary" in report
    assert "## Fitness Trajectory" in report
    assert "## Best Variant" in report
    assert "## Constraint Results" in report
    assert "## Benchmark Results" in report
    assert "ResponseAgent" in report
    print("gen_evolution_report: PASS")

    # --- generate (orchestrator with dict input) ---
    ast_json = {
        "items": [
            {"kind": "eval_dataset", "name": "TestDS", "source": "test", "splits": {"train": 1.0},
             "scoring_rubric": "", "data_fields": [], "description": ""},
            {"kind": "fitness_function", "name": "TestFF", "dimensions": [
                {"name": "accuracy", "weight": 1.0, "metric": "exact_match"}
            ], "aggregation": "weighted_average", "data_fields": [], "description": ""},
            {"kind": "evolution_run", "name": "TestRun", "target_ref": "T1",
             "optimizer_ref": "O1", "dataset_ref": "TestDS", "gate_ref": "G1",
             "status": "pending", "data_fields": [], "description": ""},
        ]
    }
    result = generate(ast_json)
    assert "datasets/TestDS.jsonl" in result
    assert "scoring/TestFF_scorer.py" in result
    assert "runs/TestRun_config.json" in result
    assert "reports/TestRun_report.md" in result
    # Verify JSONL content
    lines = [l for l in result["datasets/TestDS.jsonl"].split("\n") if l.strip()]
    assert len(lines) == 10
    # Verify config content
    cfg = json.loads(result["runs/TestRun_config.json"])
    assert cfg["run_name"] == "TestRun"
    print("generate (dict AST): PASS")

    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    _smoke_test()
