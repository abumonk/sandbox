## Entities

### EvolutionTargetDef
- kind: String ("evolution_target")
- name: String (unique identifier)
- tier: String (EvolutionTier enum value: Skill, ToolDescription, SystemPrompt, Code)
- file: String (path to the target file to evolve)
- version: String (version tag for tracking)
- constraints: [String] (names of constraint items)
- description: String?
- data_fields: [DataField]
- Relations: referenced by EvolutionRunDef via target; references ConstraintDef via constraints

### EvalDatasetDef
- kind: String ("eval_dataset")
- name: String (unique identifier)
- source: String (DataSource enum value: Synthetic, SessionDB, Golden, AutoEval)
- split_train: Float (proportion for training split)
- split_val: Float (proportion for validation split)
- split_test: Float (proportion for test split)
- scoring: String (name of fitness_function to use for scoring)
- size: Int (number of eval cases to generate/load)
- description: String?
- data_fields: [DataField]
- Relations: referenced by EvolutionRunDef via dataset; references FitnessFunctionDef via scoring

### FitnessFunctionDef
- kind: String ("fitness_function")
- name: String (unique identifier)
- dimensions: [{name: String, weight: Float, description: String}]
- aggregation: String (AggregationMethod enum: WeightedSum, Min, Harmonic)
- penalties: [String] (penalty description strings)
- description: String?
- data_fields: [DataField]
- Relations: referenced by EvalDatasetDef via scoring

### OptimizerDef
- kind: String ("optimizer")
- name: String (unique identifier)
- engine: String (OptimizerEngine enum: GEPA, MIPROv2, Darwinian)
- iterations: Int (max generations)
- population: Int (population size per generation)
- mutation: String (MutationStrategy enum: Reflective, Random, Guided, Crossover)
- description: String?
- data_fields: [DataField]
- Relations: referenced by EvolutionRunDef via optimizer

### BenchmarkGateDef
- kind: String ("benchmark_gate")
- name: String (unique identifier)
- benchmark: String (benchmark name/identifier)
- tolerance: Float (regression tolerance, 0.0-1.0)
- pass_criteria: String (pass criteria expression as text)
- description: String?
- data_fields: [DataField]
- Relations: referenced by EvolutionRunDef via gate

### EvolutionRunDef
- kind: String ("evolution_run")
- name: String (unique identifier)
- target: String (name of evolution_target)
- optimizer: String (name of optimizer)
- dataset: String (name of eval_dataset)
- gate: String (name of benchmark_gate)
- status: String (RunStatus enum: Pending, Running, Evaluating, Gating, Complete, Failed)
- description: String?
- data_fields: [DataField]
- Relations: references EvolutionTargetDef, OptimizerDef, EvalDatasetDef, BenchmarkGateDef

### ConstraintDef
- kind: String ("constraint")
- name: String (unique identifier)
- constraint_kind: String (kind: size_limit, semantic_preservation, test_suite, caching_compat)
- enforcement: String (EnforcementLevel enum: Block, Warn)
- threshold: Float (constraint-specific threshold value)
- description: String?
- data_fields: [DataField]
- Relations: referenced by EvolutionTargetDef via constraints list

### ArkFile (extended)
- evolution_targets: {String: EvolutionTargetDef}
- eval_datasets: {String: EvalDatasetDef}
- fitness_functions: {String: FitnessFunctionDef}
- optimizers: {String: OptimizerDef}
- benchmark_gates: {String: BenchmarkGateDef}
- evolution_runs: {String: EvolutionRunDef}
- constraints: {String: ConstraintDef}
- (existing fields unchanged)

### Variant (runtime, not AST)
- id: String (unique variant identifier)
- content: String (the evolved text/code)
- generation: Int (which generation this variant belongs to)
- fitness: Float (aggregated fitness score)
- parent_id: String? (variant it was mutated from)
- constraint_results: [ConstraintResult]

### EvolutionReport (runtime, not AST)
- status: String (complete, failed, gated_out)
- generations: Int (total generations executed)
- best_variant: Variant
- best_fitness: Float
- fitness_history: [Float] (best fitness per generation)
- constraint_violations: [String]
- benchmark_result: {benchmark: String, score: Float, passed: Bool}
- duration_ms: Int
