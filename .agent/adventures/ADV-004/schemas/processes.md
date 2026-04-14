## Processes

### EvolutionPipeline
1. Parse .ark spec containing evolution items
2. Resolve evolution_run references (target, dataset, optimizer, gate, constraints)
3. Load target file content (seed variant)
4. Build/load evaluation dataset from eval_dataset spec
5. Configure fitness scorer from fitness_function spec
6. Configure optimizer from optimizer spec
7. Initialize population with seed variant
8. For each generation (up to optimizer.iterations):
   a. Evaluate all variants against dataset using fitness scorer
   b. Check constraints on all variants
   c. Discard variants violating block-enforcement constraints
   d. Select survivors via Pareto-front (or rank-based for single-objective)
   e. Generate mutations of survivors to fill population
   f. Check convergence (if fitness improvement < threshold for 3 gens, stop)
9. Run best variant through benchmark gate
10. Generate EvolutionReport
11. Output: best variant content, report, pass/fail status
Error paths:
- Step 2: Unknown reference -> verification error (should be caught by verify)
- Step 3: Target file not found -> FileNotFoundError with clear message
- Step 8c: All variants blocked -> evolution fails, report constraint violations
- Step 8f: Convergence -> early stop, report as complete
- Step 9: Gate fail -> report as gated_out, include benchmark score

### DatasetBuilding
1. Read eval_dataset AST (source, split ratios, size)
2. Based on source type:
   a. Synthetic: Read target file, generate template test cases
   b. Golden: Load JSONL from specified path
   c. AutoEval: Parse code, generate input/output pairs from signatures
3. Assign split labels (train/val/test) using deterministic seed shuffle
4. Output JSONL with id, input, expected, rubric_hints, source, split
Error paths:
- Step 2a: Target file unreadable -> skip with warning
- Step 2b: JSONL file not found -> FileNotFoundError
- Step 3: Invalid ratios (don't sum to 1.0) -> caught by verifier, but runtime check too

### FitnessScoring
1. Load rubric dimensions from fitness_function AST
2. For each test case in dataset:
   a. Run variant (apply variant content, generate output)
   b. Score output against expected using judge_fn callback per dimension
   c. Apply penalties if applicable
   d. Aggregate dimension scores using configured method
3. Compute mean fitness across all cases
4. Return EvalResult with per-case and aggregate scores
Error paths:
- Step 2b: Judge callback fails -> score dimension as 0.0, log warning
- Step 2d: Unknown aggregation method -> default to weighted_sum with warning

### ConstraintChecking
1. Load constraint items referenced by evolution_target
2. For each constraint:
   a. size_limit: compare len(evolved) vs len(original) * threshold
   b. semantic_preservation: call judge_fn(original, evolved), check score >= threshold
   c. test_suite: run test command, check exit code (deferred if no shell)
   d. caching_compat: check prefix preservation
3. Collect results, determine if any block-enforcement constraint failed
4. Return list of ConstraintResult with pass/fail, enforcement, details
Error paths:
- Step 2c: Test command fails to execute -> return deferred result
- Step 2b: Judge callback unavailable -> return warn-level skip

### VerificationPipeline
1. Parse .ark spec
2. Extract evolution items from AST
3. Run checks in order:
   a. Split ratio validity (Z3: train+val+test == 1.0)
   b. Fitness weight validity (Z3: sum(weights) == 1.0)
   c. Gate tolerance bounds (Z3: 0 < tolerance <= 1.0)
   d. Target file references (non-empty check)
   e. Cross-reference integrity (name lookups)
   f. Constraint reference integrity (name lookups)
   g. Optimizer parameter bounds (Z3: iterations > 0, population > 0)
4. Return list of check results
Error paths:
- Z3 unsat -> report as verification failure with counterexample
- Missing items -> report as reference error

### CodegenPipeline
1. Parse .ark spec
2. For each evolution item type, generate corresponding artifact:
   a. eval_dataset -> JSONL template
   b. fitness_function -> Python scorer skeleton
   c. evolution_run -> JSON config
3. Write files to output directory
4. Return list of generated paths
Error paths:
- Output directory not writable -> raise IOError
- AST malformed -> skip item with warning
