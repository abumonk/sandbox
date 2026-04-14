# Codegen, Verification, and Visualization

## Designs Covered
- design-codegen-reports: Evolution artifact code generation
- design-verification: Z3 verification for evolution items
- design-visualization: Visualizer extensions for evolution pipeline graphs

## Tasks

### Implement evolution codegen
- **ID**: ADV004-T012
- **Description**: Create tools/codegen/evolution_codegen.py with functions to generate dataset JSONL templates, scoring script skeletons, and run config JSON files from evolution AST items. Integrate as `evolution` target in ark_codegen.py.
- **Files**: ark/tools/codegen/evolution_codegen.py, ark/tools/codegen/ark_codegen.py
- **Acceptance Criteria**:
  - gen_dataset_jsonl() produces valid JSONL template files
  - gen_scoring_script() produces Python scoring skeletons with rubric constants
  - gen_run_config() produces JSON config with resolved references
  - generate() orchestrates all sub-generators
  - `ark codegen <spec> --target evolution` works end-to-end
  - Follows studio_codegen.py patterns
- **Target Conditions**: TC-028, TC-029, TC-030, TC-031
- **Depends On**: [ADV004-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, codegen
  - Estimated duration: 25min
  - Estimated tokens: 25000

### Implement evolution verification
- **ID**: ADV004-T013
- **Description**: Create tools/verify/evolution_verify.py with Z3 checks for split ratios, fitness weights, gate tolerances, target files, cross-references, constraint references, and optimizer params. Integrate into ark_verify.py.
- **Files**: ark/tools/verify/evolution_verify.py, ark/tools/verify/ark_verify.py
- **Acceptance Criteria**:
  - verify_split_ratios() catches ratios not summing to 1.0 via Z3
  - verify_fitness_weights() catches weights not summing to 1.0 via Z3
  - verify_gate_tolerances() catches out-of-bounds tolerances via Z3
  - verify_cross_references() catches unknown references
  - verify_constraint_refs() catches unknown constraint references
  - verify_optimizer_params() catches invalid iterations/population
  - `ark verify <spec>` runs evolution checks when items present
  - Returns result dicts matching studio_verify.py format
- **Target Conditions**: TC-032, TC-033, TC-034, TC-035, TC-036
- **Depends On**: [ADV004-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, z3, smt
  - Estimated duration: 30min
  - Estimated tokens: 30000

### Extend visualizer for evolution items
- **ID**: ADV004-T014
- **Description**: Extend generate_graph_data() in ark_visualizer.py to extract evolution nodes and edges. Add evolution-specific color coding and tooltips to the d3.js HTML template.
- **Files**: ark/tools/visualizer/ark_visualizer.py
- **Acceptance Criteria**:
  - Evolution items appear as nodes in the graph
  - Cross-reference edges rendered between evolution items
  - Evolution nodes have distinct color group (purple/violet family)
  - Tooltips show key properties (tier, engine, tolerance, etc.)
  - `ark graph <spec>` renders evolution items when present
  - Existing entity/island/studio visualization unchanged
- **Target Conditions**: TC-037, TC-038, TC-039
- **Depends On**: [ADV004-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, d3.js, html
  - Estimated duration: 25min
  - Estimated tokens: 25000
