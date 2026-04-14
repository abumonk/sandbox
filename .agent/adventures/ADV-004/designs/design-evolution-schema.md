# Evolution Schema — Design

## Overview
Define Ark stdlib types for the evolution subsystem in `dsl/stdlib/evolution.ark`. This provides the type foundation for all other evolution components: enums for tiers, optimizer engines, data sources, enforcement levels; structs for fitness scores, variants, constraints, benchmark results, and run results.

## Target Files
- `ark/dsl/stdlib/evolution.ark` — New stdlib file with all evolution enums and structs

## Approach

Follow the exact pattern of `dsl/stdlib/studio.ark` and `dsl/stdlib/types.ark`:

### Enums
```
enum EvolutionTier { Skill, ToolDescription, SystemPrompt, Code }
enum OptimizerEngine { GEPA, MIPROv2, Darwinian }
enum DataSource { Synthetic, SessionDB, Golden, AutoEval }
enum EnforcementLevel { Block, Warn }
enum RunStatus { Pending, Running, Evaluating, Gating, Complete, Failed }
enum MutationStrategy { Reflective, Random, Guided, Crossover }
enum AggregationMethod { WeightedSum, Min, Harmonic }
```

### Structs
```
struct FitnessScore { dimension: String, score: Float, weight: Float }
struct Variant { id: String, content: String, generation: Int, fitness: Float, parent_id: String }
struct ConstraintDef { kind: String, enforcement: String, threshold: Float }
struct BenchmarkResult { benchmark: String, score: Float, passed: Bool, tolerance: Float }
struct RunResult { status: String, generations: Int, best_fitness: Float, best_variant_id: String, duration_ms: Int }
struct SplitRatio { train: Float, val: Float, test: Float }
struct RubricDimension { name: String, weight: Float, description: String }
```

### Design Decisions
- Use String for cross-referencing entity names (consistent with studio.ark pattern)
- Keep structs flat — avoid nested generics that complicate Z3 verification
- `SplitRatio` is a separate struct so Z3 can verify train+val+test=1.0
- `RubricDimension` captures both weight and description for codegen of scoring scripts

## Dependencies
None — this is the type foundation layer.

## Target Conditions
- TC-001: evolution.ark parses via `python ark.py parse dsl/stdlib/evolution.ark` without errors
- TC-002: All enums and structs follow existing stdlib patterns (import stdlib.types, correct syntax)
