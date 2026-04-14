# Codegen and Reports — Design

## Overview
Implement code generation from evolution .ark specs: dataset JSONL files, fitness scoring scripts, evolution runner CLI commands, and evolution report markdown. Follows the existing codegen pattern (separate module, AST-to-text generation).

## Target Files
- `ark/tools/codegen/evolution_codegen.py` — Code generation for evolution artifacts
- `ark/tools/codegen/ark_codegen.py` — Integration point (add evolution target)

## Approach

### evolution_codegen.py

Generate artifacts from parsed evolution .ark specs:

1. **Dataset JSONL**: From `eval_dataset` items, generate a JSONL template file with placeholder test cases.
   - Output: `{output_dir}/datasets/{dataset_name}.jsonl`
   - Each line: `{"id": "case_N", "input": "", "expected": "", "rubric_hints": "", "source": "{source}", "split": "train|val|test"}`
   - Number of lines based on `size` field, split according to ratios.

2. **Fitness scoring script**: From `fitness_function` items, generate a Python scoring script.
   - Output: `{output_dir}/scoring/{function_name}_scorer.py`
   - Contains rubric dimensions, weights, aggregation method as constants.
   - Provides a `score(output, expected)` function skeleton.

3. **Evolution runner config**: From `evolution_run` items, generate a TOML/JSON config file.
   - Output: `{output_dir}/runs/{run_name}_config.json`
   - Contains all resolved references (target file, dataset path, optimizer params, gate criteria).

4. **Evolution report**: From run results, generate a markdown report.
   - Output: `{output_dir}/reports/{run_name}_report.md`
   - Contains: summary, fitness trajectory table, best variant diff, constraint results, benchmark results.

### Integration with ark_codegen.py

Add `evolution` as a codegen target alongside `rust`, `cpp`, `proto`, `studio`:
- `ark codegen <spec.ark> --target evolution --out <dir>`
- In `ark_codegen.py`, add dispatch to `evolution_codegen.generate(ast_json, output_dir)`

### Key Functions

```python
def generate(ast_json: dict, output_dir: str) -> list[str]:
    """Generate all evolution artifacts. Returns list of generated file paths."""

def gen_dataset_jsonl(dataset_ast: dict, output_dir: str) -> str
def gen_scoring_script(fitness_ast: dict, output_dir: str) -> str
def gen_run_config(run_ast: dict, all_items: dict, output_dir: str) -> str
def gen_report(run_name: str, report: dict, output_dir: str) -> str
```

### Design Decisions
- Follow studio_codegen.py pattern: functions take AST dicts, return strings/paths
- Dataset JSONL is a template — actual test cases are filled by dataset_builder or manually
- Scoring scripts are skeletons with rubric constants — the judge logic is plugged in at runtime
- Report generation is a separate function that takes run results (not AST)

## Dependencies
- design-dsl-surface (all evolution AST items)
- design-evolution-runner (EvolutionReport for report generation)

## Target Conditions
- TC-028: Codegen produces valid JSONL template files from eval_dataset items
- TC-029: Codegen produces Python scoring script skeletons from fitness_function items
- TC-030: Codegen produces JSON config files from evolution_run items
- TC-031: `ark codegen <spec> --target evolution` works end-to-end
<!-- approved: console @ 2026-04-14T21:37:18Z -->
