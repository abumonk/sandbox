# Plan: Verification & Visualization

## Designs Covered
- design-verification: Graph Verification
- design-visualization: Graph Visualization

## Tasks

### Extend verifier for graph invariant checks
- **ID**: ADV002-T013
- **Description**: Edit `R:/Sandbox/ark/tools/verify/ark_verify.py` to add a
  `verify_graph()` function that:
  1. Loads a graph JSON (from `ark codegraph index` output)
  2. Checks "no dangling edges" (every edge source/target exists as a node)
  3. Checks "no inheritance cycles" (DFS cycle detection on InheritsEdge subgraph)
  4. Returns PASS/FAIL per check
  Also ensure `python ark.py verify specs/infra/code_graph.ark` handles the verify
  block without crashing (even if some checks reduce to PASS_OPAQUE).
- **Files**:
  - `R:/Sandbox/ark/tools/verify/ark_verify.py` (EDIT)
- **Acceptance Criteria**:
  - `verify_graph()` function exists and works on a sample graph JSON
  - No-dangling-edges check returns PASS on a valid graph
  - No-dangling-edges check returns FAIL when a fake edge target is added
  - Cycle detection returns PASS on acyclic, FAIL on cyclic
- **Target Conditions**: TC-018, TC-019, TC-020
- **Depends On**: [ADV002-T007]
- **Evaluation**:
  - Access requirements: Read+Write verify tools, Bash for testing
  - Skill set: Python, Z3, graph algorithms (DFS)
  - Estimated duration: 25min
  - Estimated tokens: 35000

### Extend visualizer for code graph rendering
- **ID**: ADV002-T014
- **Description**: Edit `R:/Sandbox/ark/tools/visualizer/ark_visualizer.py` to extend
  `generate_graph_data()` — accept an optional `code_graph_json` parameter and merge
  code-graph nodes (functions, classes, modules) with Ark entity nodes. Add distinct
  colors/shapes for code-graph node kinds. Create
  `R:/Sandbox/ark/tools/codegraph/visualizer.py` with helper functions for color/shape
  mapping and LOD filtering. Edit `ark.py` to add `codegraph graph` subcommand.
- **Files**:
  - `R:/Sandbox/ark/tools/visualizer/ark_visualizer.py` (EDIT)
  - `R:/Sandbox/ark/tools/codegraph/visualizer.py` (NEW)
  - `R:/Sandbox/ark/ark.py` (EDIT — already modified in T012, add graph sub-subcommand)
- **Acceptance Criteria**:
  - `python ark.py codegraph graph R:/Sandbox/ark/tools/` produces an HTML file
  - HTML contains code-graph nodes with appropriate styling
  - LOD switching is functional (zoom threshold changes visible nodes)
- **Target Conditions**: TC-021, TC-022, TC-023
- **Depends On**: [ADV002-T012]
- **Evaluation**:
  - Access requirements: Read+Write visualizer, codegraph, ark.py, Bash
  - Skill set: Python, d3.js/HTML generation, data visualization
  - Estimated duration: 25min
  - Estimated tokens: 35000
