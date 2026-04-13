## Processes

### IndexSourceTree
1. Receive source_tree path and language list
2. Walk directory tree, filter by language file extensions
3. For each file, dispatch to language-specific parser
4. Parser extracts nodes (Function, Class, Method, Module) and edges (Call, Import, Inherit)
5. Add all nodes and edges to GraphStore
6. Compute complexity metrics for each function
7. Build index (name -> node position)
8. Serialize graph to JSON
Error paths:
- File not readable -> skip with warning, continue
- Parse error in source file -> skip with warning, continue
- Duplicate node name -> append module qualifier (module.name)

### QueryGraph
1. Receive query type and parameters
2. Dispatch to appropriate query handler:
   - callers(fn) -> reverse-traverse CallEdge from fn
   - call_chain(entry) -> BFS/DFS forward from entry via CallEdges
   - dead_code() -> find Functions with zero incoming CallEdges
   - complexity(threshold) -> filter Functions by cyclomatic > threshold
   - subclasses(base) -> forward-traverse InheritsEdge from base
   - importers(module) -> reverse-traverse ImportEdge
   - module_deps(module) -> forward-traverse ImportEdge
3. Return list of matching nodes
Error paths:
- Node not found -> return empty result with warning
- Cycle detected during traversal -> mark visited, break cycle
- Graph not indexed yet -> error message

### VerifyGraph
1. Load graph JSON from file or IndexSourceTree output
2. For each check in verify block:
   a. no_dangling_edges: iterate all edges, check source/target in node index
   b. no_inheritance_cycles: DFS on InheritsEdge subgraph, detect back-edges
   c. exports_reachable: BFS from entry points, check all exported functions reached
3. Report PASS/FAIL per check
Error paths:
- Graph JSON malformed -> parse error with location
- Empty graph -> all checks trivially pass, emit warning

### VisualizeGraph
1. Load graph data (either from JSON or live indexing)
2. Map nodes to d3 visualization format (id, kind, group, properties)
3. Map edges to d3 link format (source, target, kind)
4. Assign colors/shapes by node kind
5. Generate HTML with d3 force-directed layout
6. Embed LOD-switching logic (zoom threshold -> show/hide detail levels)
Error paths:
- Empty graph -> generate HTML with "no data" message
- Missing d3 CDN -> embed d3 inline (existing approach)

### WatchAndReindex
1. Set up file watcher on source_tree (reuse ark_watch.py pattern)
2. On file change event:
   a. Determine language from extension
   b. Re-parse changed file
   c. Remove old nodes/edges for that file from GraphStore
   d. Add new nodes/edges
   e. Recompute affected complexity metrics
3. Emit delta event (nodes_added, nodes_removed, edges_changed)
Error paths:
- File deleted -> remove all nodes from that file, mark edges as dangling
- Rapid changes -> debounce (100ms window)

### SelfIndex
1. Configure indexer with Ark project root (R:/Sandbox/ark/)
2. Index tools/ (Python), dsl/src/ + orchestrator/src/ (Rust), specs/ + dsl/stdlib/ (.ark)
3. Merge into single CodeGraph
4. Save to specs/generated/code_graph.json
5. Run sample queries to validate
6. Print summary: N modules, N functions, N classes, N edges
Error paths:
- Partial index failure (one language fails) -> report partial results, continue with others
