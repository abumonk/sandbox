# Reflexive Evolution — Design

## Overview
Create example .ark specs that use the evolution subsystem to evolve Ark's own agent pipeline artifacts: roles, skills, and spec patterns. This is the "dog-fooding" component that validates the entire system works end-to-end on real targets.

## Target Files
- `ark/specs/meta/evolution_skills.ark` — Evolution spec for Ark's agent skills
- `ark/specs/meta/evolution_roles.ark` — Evolution spec for Ark's agent roles
- `ark/specs/root.ark` — Register evolution specs in SystemRegistry

## Approach

### evolution_skills.ark
Defines evolution of `.claude/skills/` content:

```ark
import stdlib.evolution

// Target: the Ark skill file
evolution_target skill_ark_main {
    tier: Skill
    file: ".claude/skills/ark-dsl/SKILL.md"
    version: "1.0"
    constraints: [size_limit_skill, semantic_preserve_skill]
}

// Constraints
constraint size_limit_skill {
    kind: size_limit
    enforcement: Block
    threshold: 1.2
}

constraint semantic_preserve_skill {
    kind: semantic_preservation
    enforcement: Block
    threshold: 0.8
}

// Eval dataset
eval_dataset skill_eval {
    source: Synthetic
    split: 0.6, 0.2, 0.2
    scoring: skill_fitness
    size: 50
}

// Fitness function
fitness_function skill_fitness {
    dimension procedure_adherence {
        weight: 0.4
        description: "How well the evolved skill follows its stated procedure"
    }
    dimension output_correctness {
        weight: 0.4
        description: "Whether following the skill produces correct outcomes"
    }
    dimension conciseness {
        weight: 0.2
        description: "How concise and clear the skill text is"
    }
    aggregation: WeightedSum
}

// Optimizer
optimizer skill_optimizer {
    engine: GEPA
    iterations: 10
    population: 5
    mutation: Reflective
}

// Benchmark gate
benchmark_gate skill_gate {
    benchmark: "skill_completion_rate"
    tolerance: 0.05
    pass_criteria: "mean_fitness >= 0.7"
}

// Evolution run
evolution_run evolve_skill_v1 {
    target: skill_ark_main
    optimizer: skill_optimizer
    dataset: skill_eval
    gate: skill_gate
    status: Pending
}
```

### evolution_roles.ark
Similar structure targeting `.agent/roles/` files for GEPA-style role description optimization.

### Root Registration
Add to `specs/root.ark` SystemRegistry:
```ark
register EvolutionSkills  { phase: meta, priority: 3 }
register EvolutionRoles   { phase: meta, priority: 4 }
```

### Design Decisions
- These specs serve as both examples and real use-cases
- Specs use all 7 evolution item types to validate the full pipeline
- Constraints are conservative (Block enforcement, 20% size limit, 0.8 semantic threshold)
- Small population (5) and iterations (10) for quick demonstration runs

## Dependencies
- All other designs (this is the integration/validation layer)

## Target Conditions
- TC-040: evolution_skills.ark parses via `python ark.py parse` without errors
- TC-041: evolution_roles.ark parses via `python ark.py parse` without errors
- TC-042: Both specs pass `python ark.py verify` with all checks passing
- TC-043: Both specs are registered in root.ark SystemRegistry
- TC-044: `ark codegen <spec> --target evolution` generates artifacts from reflexive specs
